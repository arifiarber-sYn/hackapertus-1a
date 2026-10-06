#!/usr/bin/env python3
"""collect.py — fail-closed collector for a red-teaming battery against an OpenAI-compatible endpoint.

Designed to be adopted as-is in the next iteration of the hackathon:

* **Input**: a battery JSON (list of points) validated against `data/battery.schema`
  (id, prompt, expected, lang, source URL; optional expected_alt, cat, synthetic, note).
* **Endpoint**: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_NAME` from the environment (or `.env` via the Makefile).
  The key is read only from the environment and is never written to stdout, receipts or artefacts.
* **Determinism**: temperature 0.0, seed 42, max_tokens 512 (same parameters as the recorded findings).
* **Hard ceiling**: at most `HARD_CAP` calls per run; a battery larger than `--limit` is refused with
  **zero calls** (exit 3) instead of being silently truncated.
* **Fingerprint guard**: the first response with a `system_fingerprint` different from the reference
  (default: the one recorded in `data/reproduce_points.json`) stops collection (exit 4).
* **Rate limits / server errors**: HTTP 429 or 5xx stop collection after the first occurrence (exit 1);
  every call — successful or not — leaves a receipt line in `out/receipts-<ts>.jsonl`.
* **Comparator**: every response is labelled with the same `krahaso()` as `make run` (src/reproduce.py);
  a point whose response does not match the expected answer becomes a *candidate*. Candidates are
  not findings: a human review against a written checklist decides (see technical report, "Review port").
* **Output**: `out/collect-<ts>.json` (plan, parameters, per-point response + verdict, summary) and the
  receipts file. `--dry-run` validates the battery and prints the plan with zero calls.

Exit codes: 0 ok · 1 stopped on HTTP 429/5xx · 2 configuration/battery error · 3 plan exceeds the ceiling ·
4 fingerprint mismatch.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
TRACK = HERE.parent.parent
DATA = TRACK / "data"
OUT = TRACK / "out"
SCHEMA = DATA / "battery.schema"
REPRODUCE_POINTS = DATA / "reproduce_points.json"

HARD_CAP = 50
SEED = 42
TEMPERATURE = 0.0
MAX_TOKENS = 512
TIMEOUT_S = 60
LANGS = {"sq", "de", "fr", "it", "en"}
PERSONAL_CATS = {"PERZ", "PII", "PERSONAL", "PRIVATE"}

EXIT_OK, EXIT_HTTP, EXIT_CONFIG, EXIT_CAP, EXIT_FP = 0, 1, 2, 3, 4


class BatteryError(ValueError):
    pass


def _load_comparator():
    """krahaso() from src/reproduce.py — one comparator for collection and replay."""
    spec = importlib.util.spec_from_file_location("reproduce", HERE.parent / "reproduce.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.krahaso


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_battery(points: list) -> list[str]:
    """Returns the list of problems (empty = valid). Mirrors data/battery.schema plus the cross-point rules."""
    problems: list[str] = []
    if not isinstance(points, list) or not points:
        return ["battery must be a non-empty JSON list of points"]
    seen: set[str] = set()
    for i, p in enumerate(points):
        where = f"point[{i}]"
        if not isinstance(p, dict):
            problems.append(f"{where}: not an object")
            continue
        pid = str(p.get("id", "")).strip()
        where = f"point[{i}] {pid or '?'}"
        for f in ("id", "prompt", "expected", "lang", "source"):
            if not str(p.get(f, "")).strip():
                problems.append(f"{where}: missing '{f}'")
        if pid in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(pid)
        if p.get("lang") not in LANGS:
            problems.append(f"{where}: lang must be one of {sorted(LANGS)}")
        src = str(p.get("source", ""))
        if not (src.startswith("http://") or src.startswith("https://")):
            problems.append(f"{where}: source must be a public http(s) URL")
        exp = str(p.get("expected", ""))
        if "(" in exp or ")" in exp:
            problems.append(f"{where}: expected must be the bare answer (no parentheses) — put remarks in 'note'")
        alt = p.get("expected_alt")
        if alt is not None and not (isinstance(alt, list) and alt and all(isinstance(a, str) and a.strip() for a in alt)):
            problems.append(f"{where}: expected_alt must be a non-empty list of non-empty strings")
        cat = str(p.get("cat", "")).upper()
        if cat in PERSONAL_CATS and p.get("synthetic") is not True:
            problems.append(f"{where}: personal-data category '{cat}' requires \"synthetic\": true (no real persons)")
        if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", str(p.get("prompt", ""))):
            problems.append(f"{where}: prompt contains an e-mail address — not allowed")
    return problems


def load_battery(path: pathlib.Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise BatteryError(f"{path}: {e}") from e
    if isinstance(data, dict) and "points" in data:
        data = data["points"]
    problems = validate_battery(data)
    if problems:
        raise BatteryError("battery invalid:\n  - " + "\n  - ".join(problems))
    return data


def reference_fingerprint() -> str | None:
    if REPRODUCE_POINTS.exists():
        try:
            return json.loads(REPRODUCE_POINTS.read_text(encoding="utf-8")).get("system_fingerprint")
        except ValueError:
            return None
    return None


class Client:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = TIMEOUT_S):
        self.base_url = base_url.rstrip("/")
        self._key = api_key
        self.model = model
        self.timeout = timeout

    def ask(self, prompt: str) -> dict:
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                "temperature": TEMPERATURE, "seed": SEED, "max_tokens": MAX_TOKENS}
        req = urllib.request.Request(self.base_url + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {self._key}"}, method="POST")
        t0 = _dt.datetime.now(_dt.timezone.utc)
        r: dict = {"ts": t0.isoformat(timespec="seconds"), "ok": False, "http": None}
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            r.update(ok=True, http=200, content=(raw.get("choices") or [{}])[0].get("message", {}).get("content", "") or "",
                     fp=raw.get("system_fingerprint"), usage=raw.get("usage"), model=raw.get("model"))
        except urllib.error.HTTPError as e:
            r.update(http=e.code, error=e.read()[:300].decode("utf-8", "replace"))
        except Exception as e:  # network / timeout / JSON
            r.update(error=f"{type(e).__name__}: {e}")
        r["ms"] = int((_dt.datetime.now(_dt.timezone.utc) - t0).total_seconds() * 1000)
        return r


def run(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--battery", required=True, type=pathlib.Path)
    ap.add_argument("--limit", type=int, default=HARD_CAP, help=f"max calls this run (hard cap {HARD_CAP})")
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    ap.add_argument("--dry-run", action="store_true", help="validate + plan, zero calls")
    ap.add_argument("--fingerprint", help="reference system_fingerprint (default: data/reproduce_points.json)")
    ap.add_argument("--no-fp-guard", action="store_true", help="do not stop on a fingerprint change (diagnostics only)")
    ap.add_argument("--timeout", type=int, default=TIMEOUT_S)
    a = ap.parse_args(argv)

    try:
        points = load_battery(a.battery)
    except BatteryError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_CONFIG
    limit = max(0, min(a.limit, HARD_CAP))
    plan = {"battery": str(a.battery), "battery_sha256": sha256_file(a.battery), "points": len(points),
            "calls_planned": len(points), "limit": limit, "hard_cap": HARD_CAP,
            "model_env": os.environ.get("LLM_NAME", ""), "seed": SEED, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}
    fp_ref = None if a.no_fp_guard else (a.fingerprint or reference_fingerprint())
    plan["fingerprint_reference"] = fp_ref
    if len(points) > limit:
        print(json.dumps({"ok": False, "reason": f"plan {len(points)} calls > limit {limit} — trim the battery or raise --limit (hard cap {HARD_CAP})",
                          "calls_made": 0, "plan": plan}, ensure_ascii=False))
        return EXIT_CAP
    if a.dry_run:
        print(json.dumps({"DRY-RUN": True, "calls_made": 0, "plan": plan}, ensure_ascii=False))
        return EXIT_OK

    base = os.environ.get("LLM_BASE_URL", "").strip()
    key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_NAME", "").strip()
    if not (base and key and model):
        print("ERROR: LLM_BASE_URL, LLM_API_KEY and LLM_NAME must be set (or use --dry-run)", file=sys.stderr)
        return EXIT_CONFIG

    krahaso = _load_comparator()
    client = Client(base, key, model, a.timeout)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    a.out.mkdir(parents=True, exist_ok=True)
    receipts_path = a.out / f"receipts-{ts}.jsonl"
    result = {"schema": "apertus-1a/collect/1.0", "ts": ts, "plan": plan, "endpoint": base, "model": model,
              "points": [], "calls_made": 0, "errors": 0, "candidates": 0, "stopped": None}
    rc = EXIT_OK
    with receipts_path.open("a", encoding="utf-8") as receipts:
        for p in points:
            r = client.ask(p["prompt"])
            result["calls_made"] += 1
            receipt = {k: r.get(k) for k in ("ts", "ok", "http", "ms", "fp", "usage", "model", "error")}
            receipt["id"] = p["id"]
            receipts.write(json.dumps(receipt, ensure_ascii=False) + "\n")
            entry = {"id": p["id"], "lang": p["lang"], "cat": p.get("cat"), "prompt": p["prompt"], "expected": p["expected"],
                     "expected_alt": p.get("expected_alt", []), "source": p["source"], "http": r.get("http"),
                     "ms": r.get("ms"), "fp": r.get("fp"), "response": r.get("content"), "comparison": None, "candidate": False}
            if not r["ok"]:
                result["errors"] += 1
                entry["error"] = r.get("error")
                result["points"].append(entry)
                if r.get("http") == 429 or (isinstance(r.get("http"), int) and r["http"] >= 500):
                    result["stopped"] = f"HTTP {r['http']} — stopped after the first occurrence; no retries"
                    rc = EXIT_HTTP
                    break
                continue
            if fp_ref and r.get("fp") and r["fp"] != fp_ref:
                entry["fp_guard"] = "REFUSED"
                result["points"].append(entry)
                result["stopped"] = f"system_fingerprint {r['fp']!r} != reference {fp_ref!r} — responses not comparable"
                rc = EXIT_FP
                break
            entry["comparison"] = krahaso(r.get("content", ""), p["expected"], p.get("expected_alt"))
            entry["candidate"] = entry["comparison"].get("sakte") is False
            result["candidates"] += int(entry["candidate"])
            result["points"].append(entry)
    out_path = a.out / f"collect-{ts}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    for e in result["points"]:
        flag = "CANDIDATE" if e["candidate"] else ("ERROR    " if e.get("error") else "match    ")
        print(f"{flag}  {e['id']:<22} {e['lang']}  {(e.get('response') or e.get('error') or '')[:70]!r}")
    print(f"\nCANDIDATES {result['candidates']}/{result['calls_made']} calls · errors {result['errors']}"
          + (f" · STOPPED: {result['stopped']}" if result["stopped"] else "")
          + f"\nartefact: {out_path}\nreceipts: {receipts_path}")
    return rc


if __name__ == "__main__":
    sys.exit(run())
