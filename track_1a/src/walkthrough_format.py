#!/usr/bin/env python3
"""walkthrough_format.py — Apertus chat-template ("Apertus response format") for walkthroughs.

The findings schema (`findings/findings.schema`, `apertus_response_walkthroughs`) asks for
"canonical walkthroughs in Apertus response format": the full conversation as one string,
exactly as the model's chat template renders it. This module renders and parses that format
with the standard library only.

Where the template comes from
-----------------------------
The model under test is `swiss-ai/Apertus-v1.5-8B`. Its repository files are gated on the Hub
(`.../raw/main/chat_template.jinja` and `tokenizer_config.json` answer HTTP 401 without a
token), but the public model-info API exposes the template verbatim in the config metadata:

    https://huggingface.co/api/models/swiss-ai/Apertus-v1.5-8B  ->  config.chat_template_jinja
    repo revision a411d838600baf0e3635a3daf66fb7c55fc97bb6 (lastModified 2026-07-24),
    template sha256 d23af2850029e9df88bb017e06e0c14a0462604588f1dbe4f519cdfac3e260e0

For a request like ours — a single `user` message, no `system` message, no tools, thinking
not enabled (what `reproduce.py --live` and the recording harness send to the OpenAI-compatible
endpoint) — that template renders:

    <s><|system_start|>{DEFAULT_SYSTEM}<|system_end|><|developer_start|>Deliberation: disabled
    Tool Capabilities: disabled<|developer_end|><|user_start|>{prompt}<|user_end|><|assistant_start|>{response}<|assistant_end|>

The default system prompt is a constant in the v1.5 template (no date, so the render is
deterministic), and the developer block is always emitted by the template, which is why it is
part of the canonical string. The render was cross-checked once against a jinja2 evaluation of
the downloaded template; `tests/test_reproduce.py` pins that reference string.
(For comparison, the public `swiss-ai/Apertus-8B-Instruct-2509` template has the same token
layout but a different default system prompt that includes the current date.)

API
---
    render(prompt, response, system=None, developer=None) -> str
    parse(walkthrough) -> (prompt, response)      # canonical AND legacy "PROMPT: ...\\n\\n..." formats
    is_canonical(walkthrough) -> bool

CLI
---
    python3 track_1a/src/walkthrough_format.py --convert track_1a/findings/*.json [--check]
        Rewrites every walkthrough into the canonical format, preserving prompt and response
        byte-for-byte (verified by a parse round-trip before writing). JSON is written as the
        files already are: indent=1, ensure_ascii=False, trailing newline.
    python3 track_1a/src/walkthrough_format.py --check [files]
        Verifies every walkthrough is canonical, parses back, and matches a packaged point in
        data/reproduce_points.json (same prompt, identical response). Exit 0 iff all pass.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TRACK = HERE.parent
FINDINGS_DIR = TRACK / "findings"
DATA = TRACK / "data" / "reproduce_points.json"

TEMPLATE_SOURCE = ("https://huggingface.co/api/models/swiss-ai/Apertus-v1.5-8B "
                   "(config.chat_template_jinja, revision a411d838, sha256 d23af285…)")

BOS = "<s>"
SYSTEM_START, SYSTEM_END = "<|system_start|>", "<|system_end|>"
DEVELOPER_START, DEVELOPER_END = "<|developer_start|>", "<|developer_end|>"
USER_START, USER_END = "<|user_start|>", "<|user_end|>"
ASSISTANT_START, ASSISTANT_END = "<|assistant_start|>", "<|assistant_end|>"

# Default system prompt of the Apertus v1.5 chat template (emitted when no system message is sent).
DEFAULT_SYSTEM = ("You are Apertus 1.5 Omni, a multimodal assistant developed by the Swiss AI Initiative. "
                  "Extended from Apertus 1 via continued pretraining, you understand images and audio "
                  "and respond in text.")
# Developer block the template always emits (enable_thinking unset, no tools).
DEFAULT_DEVELOPER = "Deliberation: disabled\nTool Capabilities: disabled"

LEGACY_PREFIX = "PROMPT:"


def render(prompt: str, response: str, system: str | None = None, developer: str | None = None) -> str:
    """Render one user turn + one assistant turn exactly as the v1.5 chat template would."""
    system = DEFAULT_SYSTEM if system is None else system
    developer = DEFAULT_DEVELOPER if developer is None else developer
    return (f"{BOS}{SYSTEM_START}{system}{SYSTEM_END}"
            f"{DEVELOPER_START}{developer}{DEVELOPER_END}"
            f"{USER_START}{prompt}{USER_END}"
            f"{ASSISTANT_START}{response}{ASSISTANT_END}")


def is_canonical(walkthrough: str) -> bool:
    return (walkthrough.startswith(BOS + SYSTEM_START)
            and USER_START in walkthrough and USER_END in walkthrough
            and ASSISTANT_START in walkthrough and ASSISTANT_END in walkthrough)


def is_legacy(walkthrough: str) -> bool:
    return walkthrough.startswith(LEGACY_PREFIX)


def _between(s: str, start: str, end: str) -> str:
    i = s.index(start) + len(start)
    j = s.index(end, i)
    return s[i:j]


def parse(walkthrough: str) -> tuple[str, str]:
    """Return (prompt, response) from a canonical walkthrough or from the legacy
    'PROMPT: <prompt>\\n\\n<response>' format. Nothing is stripped: bytes are preserved."""
    if is_canonical(walkthrough):
        prompt = _between(walkthrough, USER_START, USER_END)
        response = _between(walkthrough, ASSISTANT_START, ASSISTANT_END)
        return prompt, response
    if is_legacy(walkthrough):
        body = walkthrough[len(LEGACY_PREFIX):]
        if body.startswith(" "):
            body = body[1:]
        prompt, sep, response = body.partition("\n\n")
        if not sep:
            raise ValueError("legacy walkthrough without blank line between prompt and response")
        return prompt, response
    raise ValueError("walkthrough is neither canonical (<s><|system_start|>…) nor legacy (PROMPT: …)")


# --- CLI helpers ---
def _load_points(data_path: pathlib.Path) -> dict[str, dict[str, str]]:
    """{finding file name: {prompt: response}} from reproduce_points.json."""
    d = json.loads(data_path.read_text(encoding="utf-8"))
    return {f["file"]: {p["prompt"]: p["response"] for p in f["points"]} for f in d["findings"]}


def _write_like_existing(path: pathlib.Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def convert_file(path: pathlib.Path) -> tuple[int, int]:
    """Rewrite walkthroughs of one findings file to canonical. Returns (converted, total).
    Aborts (ValueError) if any walkthrough would not round-trip byte-for-byte."""
    f = json.loads(path.read_text(encoding="utf-8"))
    out, converted = [], 0
    for w in f["apertus_response_walkthroughs"]:
        if is_canonical(w):
            out.append(w)
            continue
        prompt, response = parse(w)
        canon = render(prompt, response)
        if parse(canon) != (prompt, response):
            raise ValueError(f"{path.name}: round-trip failed for prompt {prompt!r}")
        out.append(canon)
        converted += 1
    if converted:
        f["apertus_response_walkthroughs"] = out
        _write_like_existing(path, f)
    return converted, len(out)


def check_file(path: pathlib.Path, points: dict[str, dict[str, str]]) -> tuple[int, list[tuple[int, str]]]:
    """Check one findings file. Returns (number of walkthroughs, [(index, problem), ...]);
    an empty problem list means every walkthrough is canonical, round-trips and matches a
    packaged point (same prompt, identical response)."""
    f = json.loads(path.read_text(encoding="utf-8"))
    walkthroughs = f["apertus_response_walkthroughs"]
    per_prompt = points.get(path.name)
    if per_prompt is None:
        return len(walkthroughs), [(k, f"no packaged points for {path.name} in {DATA.name}")
                                   for k in range(1, len(walkthroughs) + 1)]
    problems = []
    for k, w in enumerate(walkthroughs, 1):
        if not is_canonical(w):
            problems.append((k, "not canonical"))
            continue
        prompt, response = parse(w)
        if render(prompt, response) != w:
            problems.append((k, "not byte-identical to render(prompt, response)"))
        if prompt not in per_prompt:
            problems.append((k, f"prompt has no packaged point: {prompt!r}"))
        elif per_prompt[prompt] != response:
            problems.append((k, f"response differs from the packaged point: {prompt!r}"))
    return len(walkthroughs), problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render/parse/convert walkthroughs in Apertus response format.")
    ap.add_argument("files", nargs="*", type=pathlib.Path,
                    help=f"findings files (default: {FINDINGS_DIR}/*.json)")
    ap.add_argument("--convert", action="store_true", help="rewrite legacy walkthroughs to canonical")
    ap.add_argument("--check", action="store_true",
                    help="verify canonical format + round-trip + match with reproduce_points.json")
    ap.add_argument("--data", type=pathlib.Path, default=DATA, help="reproduce_points.json path")
    a = ap.parse_args(argv)
    files = a.files or sorted(FINDINGS_DIR.glob("*.json"))
    if not files:
        print("no findings files given", file=sys.stderr)
        return 2
    if not a.convert and not a.check:
        a.check = True
    rc = 0
    if a.convert:
        for p in files:
            n, tot = convert_file(p)
            print(f"convert {p.name}: {n}/{tot} walkthroughs rewritten to canonical"
                  + ("" if n else " (already canonical)"))
    if a.check:
        points = _load_points(a.data)
        tot = bad = 0
        for p in files:
            n, probs = check_file(p, points)
            tot += n
            bad += len({k for k, _ in probs})
            for k, msg in probs:
                print(f"  PROBLEM {p.name}[{k}]: {msg}")
                rc = 1
        print(f"check: {tot - bad}/{tot} walkthroughs canonical, round-trip OK and matching a packaged"
              f" point ({'OK' if rc == 0 else 'FAIL'}; template: {TEMPLATE_SOURCE})")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
