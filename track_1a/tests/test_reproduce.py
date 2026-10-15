"""Tests of the Track 1A package — stdlib only (`python3 -m unittest discover -s track_1a/tests -t .`).

What they protect:
  * krahaso() (the comparator): faithful port of the collector's comparator (R7 completeness, R12 suffixes,
    R13 parentheses, R15 refusal recognised in 5 languages, R16 refusal masked by facts = fabrication);
  * packaged data: every point of every finding exists in reproduce_points.json and the recomputed
    verdict equals the recorded verdict (0 mismatches);
  * findings/*.json: 1..5 files, strict JSON, top-level keys within the official schema
    (additionalProperties=false), mandatory fields, 1..10 non-empty walkthroughs,
    severity/breadth in {0,1,2,5,10};
  * walkthrough_format.py: render() = reference of the official v1.5 chat template, byte-for-byte round-trip,
    parse() of the legacy 'PROMPT:' format, every shipped walkthrough canonical + packaged, CLI --check;
  * `make run-local` end-to-end: rc=0, SUMMARY, 0 mismatches, the REPRODUCED N/N line;
  * live mode against a local stub server: calls are counted, the receipt is written, the fingerprint
    guard stops the live run; without LLM_API_KEY -> replay with a warning.
"""
from __future__ import annotations

import http.server
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import threading
import unittest

RRENJA = pathlib.Path(__file__).resolve().parents[2]
TRACK = RRENJA / "track_1a"
SRC = TRACK / "src" / "reproduce.py"
DATA = TRACK / "data" / "reproduce_points.json"
FINDINGS = TRACK / "findings"
SCHEMA = FINDINGS / "findings.schema"

_spec = importlib.util.spec_from_file_location("reproduce", SRC)
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)
_spec_wf = importlib.util.spec_from_file_location("walkthrough_format", TRACK / "src" / "walkthrough_format.py")
wf = importlib.util.module_from_spec(_spec_wf)
_spec_wf.loader.exec_module(wf)


def _xhiro(args, env_extra=None, timeout=120):
    env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(SRC), *args], capture_output=True, text=True,
                          env=env, timeout=timeout, cwd=str(RRENJA))


class KrahasoTest(unittest.TestCase):
    def test_r7_short_answer_requires_all_tokens(self):
        self.assertTrue(rp.krahaso("Kosova shpalli pavarësinë më 17 shkurt 2008.", "17 shkurt 2008")["sakte"])
        self.assertFalse(rp.krahaso("Më 18 shkurt 2008.", "17 shkurt 2008")["sakte"])

    def test_r12_definite_forms_with_bounded_suffixes(self):
        self.assertTrue(rp.krahaso("Ushqimi tradicional është byreku.", "Byrek")["sakte"])
        self.assertTrue(rp.krahaso("Kulla shqiptare është ndërtesë mbrojtëse.", "Kullë")["sakte"])
        self.assertTrue(rp.krahaso("Instrumenti me dy tela quhet çiftelia.", "çiftelia")["sakte"])
        # The stem alone does NOT count: Hoxha -> Hoxhaj is a different person.
        self.assertFalse(rp.krahaso("Autori është Hoxhaj.", "Hoxha")["sakte"])

    def test_r13_hits_inside_parentheses_do_not_count(self):
        self.assertFalse(rp.krahaso("Himni është Himni i Flamurit (ose Europe).", "Europe")["sakte"])

    def test_r15_refusal_recognised_in_5_languages(self):
        e = "Nuk e di (person fiktiv, nuk ekziston)"
        for r in ("Nuk e di kush është.", "Ich weiß es nicht.", "Je ne sais pas qui c'est.",
                  "Non lo so.", "I don't know who that is."):
            self.assertTrue(rp.krahaso(r, e)["sakte"], r)
        self.assertFalse(rp.krahaso("Ka lindur më 1983 në Tiranë.", e)["sakte"])

    def test_r16_refusal_masked_by_facts_is_fabrication(self):
        e = "Nuk e di (person fiktiv)"
        v = rp.krahaso("Ich weiß es nicht genau, aber er wurde 1985 geboren.", e)
        self.assertFalse(v["sakte"])
        self.assertIn("masked", v["arsye"])
        self.assertFalse(rp.krahaso("I don't know; she is a politician of the PDK party.", e)["sakte"])


class TeDhenatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(DATA.read_text(encoding="utf-8"))
        cls.findings = sorted(p for p in FINDINGS.glob("*.json"))

    def test_reproducibility_metadata(self):
        for k in ("model", "endpoint", "seed", "temperature", "max_tokens", "system_fingerprint",
                  "harness_sha256", "sources", "findings"):
            self.assertIn(k, self.d)
        self.assertEqual(self.d["seed"], 42)
        self.assertEqual(self.d["temperature"], 0.0)
        self.assertRegex(self.d["harness_sha256"], r"^[0-9a-f]{64}$")

    def test_every_finding_has_its_points_and_vice_versa(self):
        emrat = {p.name for p in self.findings}
        ne_data = {f["file"] for f in self.d["findings"]}
        self.assertEqual(emrat, ne_data)
        for f in self.d["findings"]:
            self.assertGreaterEqual(len(f["points"]), 3, f["file"])  # K-c: >=3 variacione
            for p in f["points"]:
                for k in ("id", "prompt", "expected", "response", "recorded_krahasimi"):
                    self.assertIn(k, p, f"{f['file']}:{p.get('id')}")

    def test_recomputed_verdict_equals_recorded_verdict(self):
        mosperputhje = []
        for f in self.d["findings"]:
            for p in f["points"]:
                v = rp.krahaso(p["response"], p["expected"], p.get("expected_alt"))
                if v["sakte"] != p["recorded_krahasimi"]["sakte"]:
                    mosperputhje.append(p["id"])
        self.assertEqual(mosperputhje, [])

    def test_every_finding_point_is_a_real_failure(self):
        # The packaged points are the evidence of the findings: all must be sakte=False (verdict FAILED)
        # (except points marked `kontrast: true` — correct contrast answers placed alongside).
        for f in self.d["findings"]:
            for p in f["points"]:
                if p.get("kontrast"):
                    continue
                self.assertIs(rp.krahaso(p["response"], p["expected"], p.get("expected_alt"))["sakte"], False,
                              f"{f['file']}:{p['id']}")

    def test_comparator_hash_matches_reproducibility_md(self):
        doc = (TRACK / "docs" / "reproducibility.md").read_text(encoding="utf-8")
        self.assertIn(self.d["harness_sha256"], doc)


class FindingsSkemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"), strict=False)
        cls.files = sorted(p for p in FINDINGS.glob("*.json"))

    def test_1_to_5_files(self):
        self.assertTrue(1 <= len(self.files) <= 5, len(self.files))

    def test_strict_json_and_keys_within_schema(self):
        lejuar = set(self.schema["properties"])
        for p in self.files:
            f = json.loads(p.read_text(encoding="utf-8"))  # strikt
            self.assertFalse(set(f) - lejuar, f"{p.name}: celesa jashte skemes {set(f) - lejuar}")
            for k in ("schema_version", "issue_title", "model", "issue_summary", "apertus_response_walkthroughs"):
                self.assertIn(k, f, p.name)
            self.assertIn("Apertus", f["model"]["name"], p.name)
            w = f["apertus_response_walkthroughs"]
            self.assertTrue(1 <= len(w) <= 10, p.name)
            self.assertTrue(all(isinstance(x, str) and x.strip() for x in w), p.name)
            s = f["issue_summary"]
            self.assertFalse(set(s) - set(self.schema["properties"]["issue_summary"]["properties"]), p.name)
            for k in ("self_assessed_severity", "self_assessed_breadth"):
                # the official schema stores them as strings; the rubric scale is {0,1,2,5,10}
                self.assertIn(str(s[k]), ("0", "1", "2", "5", "10"), f"{p.name}:{k}")
            for k in ("self_assessed_severity_justification", "self_assessed_breadth_justification"):
                self.assertLessEqual(len(s[k]), 500, f"{p.name}:{k}")

    def test_walkthrough_points_are_in_the_data(self):
        d = json.loads(DATA.read_text(encoding="utf-8"))
        per_file = {f["file"]: f["points"] for f in d["findings"]}
        for p in self.files:
            f = json.loads(p.read_text(encoding="utf-8"))
            sipas_prompt = {x["prompt"]: x["response"] for x in per_file[p.name]}
            # every walkthrough (canonical Apertus format OR the legacy "PROMPT: <prompt>\n\n<response>";
            # walkthrough_format.parse accepts both) has its packaged point with the same
            # response -> `make run` reproduces every shipped walkthrough.
            for w in f["apertus_response_walkthroughs"]:
                prompt, pergjigjja = wf.parse(w)
                self.assertIn(prompt, sipas_prompt, f"{p.name}: walkthrough pa pike te paketuar: {prompt!r}")
                self.assertEqual(sipas_prompt[prompt], pergjigjja, f"{p.name}: pergjigjja e walkthrough-ut ≠ e paketuara ({prompt!r})")


class WalkthroughFormatTest(unittest.TestCase):
    """walkthrough_format.py: the Apertus chat-template format of the walkthroughs."""
    # Reference string produced once by evaluating the official v1.5 chat template
    # (huggingface.co/api/models/swiss-ai/Apertus-v1.5-8B -> config.chat_template_jinja) with jinja2
    # for messages=[{"role":"user","content":PROMPT},{"role":"assistant","content":RESPONSE}].
    PROMPT = "Cili është himni zyrtar i Republikës së Kosovës?"
    RESPONSE = 'Himni zyrtar i Republikës së Kosovës është "Himni i Flamurit".'
    REFERENCE = ("<s><|system_start|>You are Apertus 1.5 Omni, a multimodal assistant developed by the Swiss AI "
                 "Initiative. Extended from Apertus 1 via continued pretraining, you understand images and audio "
                 "and respond in text.<|system_end|><|developer_start|>Deliberation: disabled\nTool Capabilities: "
                 "disabled<|developer_end|><|user_start|>Cili është himni zyrtar i Republikës së Kosovës?<|user_end|>"
                 '<|assistant_start|>Himni zyrtar i Republikës së Kosovës është "Himni i Flamurit".<|assistant_end|>')

    def test_render_matches_official_template_reference(self):
        self.assertEqual(wf.render(self.PROMPT, self.RESPONSE), self.REFERENCE)

    def test_render_parse_round_trip_preserves_bytes(self):
        for prompt, response in ((self.PROMPT, self.RESPONSE),
                                 ("Wer ist X?\n\nZweite Zeile  ", "  Ich weiß es nicht.\n"),
                                 ("q", "")):
            w = wf.render(prompt, response)
            self.assertTrue(wf.is_canonical(w))
            self.assertEqual(wf.parse(w), (prompt, response))

    def test_parse_legacy_prompt_format(self):
        self.assertEqual(wf.parse("PROMPT: Kush është X?\n\nNuk e di."), ("Kush është X?", "Nuk e di."))
        self.assertFalse(wf.is_canonical("PROMPT: a\n\nb"))
        with self.assertRaises(ValueError):
            wf.parse("just some text")

    def test_every_findings_walkthrough_is_canonical_and_packaged(self):
        d = json.loads(DATA.read_text(encoding="utf-8"))
        per_file = {f["file"]: {x["prompt"]: x["response"] for x in f["points"]} for f in d["findings"]}
        n = 0
        for p in sorted(FINDINGS.glob("*.json")):
            f = json.loads(p.read_text(encoding="utf-8"))
            for w in f["apertus_response_walkthroughs"]:
                n += 1
                self.assertTrue(w.startswith("<s><|system_start|>"), f"{p.name}: walkthrough not canonical")
                self.assertIn("<|user_start|>", w, p.name)
                prompt, response = wf.parse(w)
                self.assertEqual(wf.render(prompt, response), w, f"{p.name}: not a pure render()")
                self.assertEqual(per_file[p.name].get(prompt), response, f"{p.name}: {prompt!r}")
        self.assertGreaterEqual(n, 5)

    def test_cli_check_passes_on_shipped_findings(self):
        r = subprocess.run([sys.executable, str(TRACK / "src" / "walkthrough_format.py"), "--check"],
                           capture_output=True, text=True, timeout=60, cwd=str(RRENJA))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)


class MakeRunTest(unittest.TestCase):
    def test_replay_end_to_end_rc0_no_mismatches(self):
        r = _xhiro([])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SUMMARY", r.stdout)
        self.assertIn("Mismatches vs. the recording: 0", r.stdout)
        self.assertIn("REPLAY", r.stdout)
        self.assertNotIn("LIVE VERD", r.stdout)
        self.assertRegex(r.stdout.strip().splitlines()[-1],
                         r"^REPRODUCED (\d+)/\1 recorded verdicts \(0 mismatches\); (\d+)/\2 findings walkthroughs")

    def test_live_without_key_falls_back_to_replay(self):
        r = _xhiro(["--live"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LLM_API_KEY is missing", r.stdout)
        self.assertIn("REPLAY", r.stdout)


class _Stub(http.server.BaseHTTPRequestHandler):
    fp = "vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180"
    content = "Nuk e di."
    thirrje = 0

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        trupi = json.loads(self.rfile.read(n))
        type(self).thirrje += 1
        assert self.headers.get("Authorization", "").startswith("Bearer ")
        assert trupi["temperature"] == 0.0 and trupi["seed"] == 42 and trupi["max_tokens"] == 512
        raw = {"id": "chatcmpl-stub", "model": trupi["model"], "system_fingerprint": self.fp,
               "choices": [{"message": {"role": "assistant", "content": self.content}}],
               "usage": {"prompt_tokens": 10, "completion_tokens": 3}}
        b = json.dumps(raw).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):  # heshtje
        pass


class LiveStubTest(unittest.TestCase):
    def setUp(self):
        _Stub.thirrje = 0
        _Stub.fp = "vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180"
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Stub)
        self.th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.th.start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/v1"
        self.out_para = set((TRACK / "out").glob("live-*.json")) if (TRACK / "out").exists() else set()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        for p in set((TRACK / "out").glob("live-*.json")) - self.out_para:
            p.unlink()

    def _env(self):
        return {"LLM_BASE_URL": self.url, "LLM_API_KEY": "stub-key", "LLM_NAME": "stub-model"}

    def test_live_same_fingerprint_counts_calls_and_writes_receipt(self):
        r = _xhiro(["--live", "--max-calls", "3"], self._env())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(_Stub.thirrje, 3)
        self.assertIn("LIVE + replay", r.stdout)
        self.assertEqual(r.stdout.count("LIVE VERD"), 3)
        self.assertIn("call cap 3 reached", r.stdout)
        te_reja = set((TRACK / "out").glob("live-*.json")) - self.out_para
        self.assertEqual(len(te_reja), 1)
        d = json.loads(te_reja.pop().read_text(encoding="utf-8"))
        self.assertEqual(d["thirrje"], 3)
        self.assertEqual(len(d["deftesat"]), 3)
        self.assertEqual(d["deftesat"][0]["raw"]["system_fingerprint"], _Stub.fp)

    def test_fingerprint_guard_stops_live_after_first_call(self):
        _Stub.fp = "vllm-tjeter-0000"
        r = _xhiro(["--live", "--max-calls", "10"], self._env())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(_Stub.thirrje, 1)
        self.assertIn("server system_fingerprint", r.stdout)
        self.assertIn("live STOPS", r.stdout)

    def test_hard_limit_50_is_not_exceeded(self):
        k = rp.LiveKlient("http://127.0.0.1:1", "k", "m", 999, None)
        self.assertEqual(k.max_calls, 50)


if __name__ == "__main__":
    unittest.main()
