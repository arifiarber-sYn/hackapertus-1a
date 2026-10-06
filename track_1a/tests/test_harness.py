"""Tests of the reusable collector (track_1a/src/harness/collect.py) — stdlib only, no network beyond a local stub.

What they protect:
  * battery validation (schema rules + cross-point rules) refuses bad input with exit 2 and zero calls;
  * the ceiling: a plan above --limit / the hard cap exits 3 with zero calls; --dry-run makes zero calls;
  * fingerprint guard stops collection (exit 4) on the first foreign fingerprint;
  * HTTP 429 stops collection (exit 1) after the first occurrence, with a receipt for the failed call;
  * a successful run labels candidates with the same comparator as reproduce.py, writes the artefact and
    receipts, and the API key appears nowhere in the outputs;
  * the shipped example battery validates and `make collect-dry` plans 5 calls.
"""
from __future__ import annotations

import http.server
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import unittest

RRENJA = pathlib.Path(__file__).resolve().parents[2]
TRACK = RRENJA / "track_1a"
COLLECT = TRACK / "src" / "harness" / "collect.py"
EXAMPLE = TRACK / "data" / "example_battery.json"

_spec = importlib.util.spec_from_file_location("collect", COLLECT)
col = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(col)

GOOD = [
    {"id": "A-sq", "lang": "sq", "prompt": "Cili është kryeqyteti i Kosovës?", "expected": "Prishtina",
     "expected_alt": ["Pristina"], "source": "https://en.wikipedia.org/wiki/Pristina"},
    {"id": "A-de", "lang": "de", "prompt": "Hauptstadt des Kosovo?", "expected": "Pristina",
     "source": "https://en.wikipedia.org/wiki/Pristina"},
]


def _run(args, env_extra=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(COLLECT), *args], capture_output=True, text=True, env=env,
                          timeout=120, cwd=str(RRENJA))


class ValidationTest(unittest.TestCase):
    def test_good_battery_has_no_problems(self):
        self.assertEqual(col.validate_battery(GOOD), [])

    def test_example_battery_validates(self):
        self.assertEqual(col.validate_battery(json.loads(EXAMPLE.read_text(encoding="utf-8"))), [])

    def test_rules(self):
        bad = [
            dict(GOOD[0], id="A-sq"), dict(GOOD[1], id="A-sq"),                      # duplicate id
            dict(GOOD[0], id="B", lang="es"),                                          # lang
            dict(GOOD[0], id="C", source="wikipedia.org/x"),                          # source not URL
            dict(GOOD[0], id="D", expected="Prishtina (kryeqyteti)"),                 # parentheses
            dict(GOOD[0], id="E", expected_alt=[]),                                   # empty alt
            dict(GOOD[0], id="F", cat="PERZ"),                                        # personal w/o synthetic
            dict(GOOD[0], id="G", prompt="Shkruaj te zelinx@gmail.com"),              # e-mail
            dict(GOOD[0], id="H", expected=""),                                       # missing expected
        ]
        problems = col.validate_battery(bad)
        for frag in ("duplicate id", "lang must be", "public http(s) URL", "no parentheses",
                     "expected_alt must be", "requires \"synthetic\": true", "e-mail address", "missing 'expected'"):
            self.assertTrue(any(frag in p for p in problems), msg=f"{frag!r} not reported: {problems}")

    def test_invalid_battery_exits_2_with_zero_calls(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "b.json"
            p.write_text(json.dumps([dict(GOOD[0], source="no-url")]), encoding="utf-8")
            r = _run(["--battery", str(p), "--dry-run"])
        self.assertEqual(r.returncode, col.EXIT_CONFIG, r.stderr)
        self.assertIn("battery invalid", r.stderr)


class CeilingTest(unittest.TestCase):
    def test_plan_above_limit_exits_3_zero_calls(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "b.json"
            p.write_text(json.dumps(GOOD), encoding="utf-8")
            r = _run(["--battery", str(p), "--limit", "1"], {"LLM_BASE_URL": "http://127.0.0.1:9", "LLM_API_KEY": "k", "LLM_NAME": "m"})
        self.assertEqual(r.returncode, col.EXIT_CAP, r.stdout)
        self.assertEqual(json.loads(r.stdout)["calls_made"], 0)

    def test_limit_is_capped_at_hard_cap(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "b.json"
            p.write_text(json.dumps([dict(GOOD[0], id=f"P{i}") for i in range(col.HARD_CAP + 1)]), encoding="utf-8")
            r = _run(["--battery", str(p), "--limit", "999", "--dry-run"])
        self.assertEqual(r.returncode, col.EXIT_CAP)
        self.assertEqual(json.loads(r.stdout)["plan"]["limit"], col.HARD_CAP)

    def test_dry_run_zero_calls_and_sha(self):
        r = _run(["--battery", str(EXAMPLE), "--dry-run"])
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d["DRY-RUN"])
        self.assertEqual(d["calls_made"], 0)
        self.assertEqual(d["plan"]["calls_planned"], 5)
        self.assertEqual(d["plan"]["battery_sha256"], col.sha256_file(EXAMPLE))

    def test_missing_env_exits_2(self):
        r = _run(["--battery", str(EXAMPLE)])
        self.assertEqual(r.returncode, col.EXIT_CONFIG)


class _Stub(http.server.BaseHTTPRequestHandler):
    fp = "vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180"
    content = "Kryeqyteti është Prishtina."
    status = 200
    calls = 0
    seen_auth: list[str] = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n))
        type(self).calls += 1
        type(self).seen_auth.append(self.headers.get("Authorization", ""))
        assert body["temperature"] == 0.0 and body["seed"] == 42 and body["max_tokens"] == 512
        if self.status != 200:
            b = b'{"error":"rate limited"}'
            self.send_response(self.status)
        else:
            raw = {"id": "chatcmpl-stub", "model": body["model"], "system_fingerprint": self.fp,
                   "choices": [{"message": {"role": "assistant", "content": self.content}}],
                   "usage": {"prompt_tokens": 10, "completion_tokens": 3}}
            b = json.dumps(raw).encode()
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


class StubCollectTest(unittest.TestCase):
    KEY = "stub-secret-key-0123456789"

    def setUp(self):
        _Stub.calls, _Stub.status, _Stub.seen_auth = 0, 200, []
        _Stub.fp = "vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180"
        _Stub.content = "Kryeqyteti është Prishtina."
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Stub)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.td = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.td.name) / "out"
        self.bat = pathlib.Path(self.td.name) / "b.json"
        self.bat.write_text(json.dumps(GOOD), encoding="utf-8")
        self.env = {"LLM_BASE_URL": f"http://127.0.0.1:{self.srv.server_address[1]}/v1",
                    "LLM_API_KEY": self.KEY, "LLM_NAME": "stub-model"}

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.td.cleanup()

    def _outputs(self):
        art = next(self.out.glob("collect-*.json"))
        rec = next(self.out.glob("receipts-*.jsonl"))
        return json.loads(art.read_text(encoding="utf-8")), rec.read_text(encoding="utf-8")

    def test_success_labels_candidates_and_hides_key(self):
        r = _run(["--battery", str(self.bat), "--out", str(self.out)], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        art, rec = self._outputs()
        self.assertEqual(art["calls_made"], 2)
        self.assertEqual(_Stub.calls, 2)
        self.assertTrue(all(a == f"Bearer {self.KEY}" for a in _Stub.seen_auth))
        # sq: "Prishtina" matches; de: expected "Pristina" without alt → candidate (comparator, not opinion)
        by_id = {p["id"]: p for p in art["points"]}
        self.assertFalse(by_id["A-sq"]["candidate"])
        self.assertTrue(by_id["A-de"]["candidate"])
        self.assertEqual(art["candidates"], 1)
        self.assertEqual(len(rec.strip().splitlines()), 2)
        for blob in (r.stdout, r.stderr, json.dumps(art), rec):
            self.assertNotIn(self.KEY, blob)

    def test_fingerprint_change_stops_with_exit_4(self):
        _Stub.fp = "vllm-other-build"
        r = _run(["--battery", str(self.bat), "--out", str(self.out)], self.env)
        self.assertEqual(r.returncode, col.EXIT_FP, r.stdout)
        art, rec = self._outputs()
        self.assertEqual(art["calls_made"], 1)
        self.assertIn("system_fingerprint", art["stopped"])
        self.assertEqual(len(rec.strip().splitlines()), 1)

    def test_no_fp_guard_continues(self):
        _Stub.fp = "vllm-other-build"
        r = _run(["--battery", str(self.bat), "--out", str(self.out), "--no-fp-guard"], self.env)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(self._outputs()[0]["calls_made"], 2)

    def test_http_429_stops_with_receipt(self):
        _Stub.status = 429
        r = _run(["--battery", str(self.bat), "--out", str(self.out)], self.env)
        self.assertEqual(r.returncode, col.EXIT_HTTP, r.stdout)
        art, rec = self._outputs()
        self.assertEqual(art["calls_made"], 1)
        self.assertEqual(_Stub.calls, 1)
        self.assertIn("HTTP 429", art["stopped"])
        line = json.loads(rec.strip().splitlines()[0])
        self.assertFalse(line["ok"])
        self.assertEqual(line["http"], 429)


class MakeTest(unittest.TestCase):
    def test_make_collect_dry_plans_example(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
        r = subprocess.run(["make", "--no-print-directory", "collect-dry"], capture_output=True, text=True,
                           cwd=str(RRENJA), env=env, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"calls_planned": 5', r.stdout)


if __name__ == "__main__":
    unittest.main()
