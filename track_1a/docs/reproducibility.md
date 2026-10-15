# Reproducibility — Track 1A (`make run`)

## What `make run` does

From the repository root (clean checkout):

    make run

1. If Docker is available: it builds the minimal image (`Dockerfile`,
   `python:3.12-slim`, no `pip install`) and runs the reproduction **inside the
   container**. If Docker is missing or the daemon is unresponsive, it falls back
   automatically to `make run-local` (the same reproduction, python3 directly).
2. It runs `track_1a/src/reproduce.py` in **replay** mode:
   - reads the packaged points `track_1a/data/reproduce_points.json` (id, prompt,
     expected, the recorded model answer, the recorded verdict) for **every
     walkthrough** of the 5 findings — **65 points** (F1–F4 from 10 each: 5 original
     + 5 paraphrases; F5 from 25: 20 sq + 5 de/fr/it/en);
   - applies the same comparison logic as `apertus_harness.py`
     (`krahaso()`: normalisation, word-boundary matching, limited R12 suffixes,
     R13 parenthetical asides, known refusals in 5 languages R15, refusal masked
     with facts R16);
   - prints for every point the id, PROMPT, EXPECTED, the model answer (quoted)
     and the verdict; at the end the summary (**Mismatches vs. the recording: 0**),
     the walkthrough coverage (**50/50** have their own packaged point) and the
     reproducibility information; the last line for the jury:
     `REPRODUCED 65/65 recorded verdicts (0 mismatches); 50/50 findings walkthroughs backed by a packaged point`.

The output is human-readable text; the exit code = 0 (findings are documented,
they are not an execution error).

## Live mode (optional): `make run-live`

With `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_NAME` in the environment (or in `.env`),
`reproduce.py --live` calls the OpenAI-compatible endpoint for every point with the
same parameters (temperature 0.0, seed 42, max_tokens 512), compares the LIVE
answer with the same `krahaso()` and sets it against the recorded verdict
(`verdict = recording N/M`). Safeguards:

- **Fingerprint guard:** if the server's `system_fingerprint` differs from the
  recorded one, live mode stops (remaining points → replay) — the answers are no
  longer comparable bit-for-bit.
- **Hard limit ≤50 calls** per run (`--max-calls`, cannot be exceeded).
- Every call is stored as a receipt (raw JSON, usage, fp, ms) in
  `track_1a/out/live-<ts>.json` (outside git).
- Without `LLM_API_KEY` → falls back to replay with a warning, so that `make run`
  passes end-to-end even without a key.

In Docker: `docker run --rm -e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME hackapertus-1a:local python3 track_1a/src/reproduce.py --live`.

## Walkthrough format (Apertus response format)

Every string in `apertus_response_walkthroughs` is the full conversation as the
Apertus v1.5 chat template renders it for one `user` message without a
`system` message (what the recording harness and `reproduce.py --live` send):

    <s><|system_start|>You are Apertus 1.5 Omni, … respond in text.<|system_end|><|developer_start|>Deliberation: disabled
    Tool Capabilities: disabled<|developer_end|><|user_start|>{prompt}<|user_end|><|assistant_start|>{response}<|assistant_end|>

The template was taken from the public Hub model-info API
(`https://huggingface.co/api/models/swiss-ai/Apertus-v1.5-8B` →
`config.chat_template_jinja`, revision `a411d838`, sha256 `d23af285…`; the raw
repository files are gated). `track_1a/src/walkthrough_format.py` renders and
parses it (stdlib) and also accepts the legacy `PROMPT: …` form;
`python3 track_1a/src/walkthrough_format.py --check` verifies 50/50 walkthroughs
are canonical and match a packaged point byte-for-byte.

## Tests: `make test`

`python3 -m unittest discover -s track_1a/tests -t .` — stdlib only (**36 tests**). They cover
`krahaso()` (R7/R12/R13/R15/R16), data integrity (every submitted walkthrough has its
own packaged point with the same answer; the recomputed verdict = the recorded one),
the schema of `findings/*.json` (keys within the official schema, 1..10 walkthroughs,
S/B in {0,1,2,5,10}, justifications ≤500 chars), the Apertus format of the walkthroughs
(`walkthrough_format.py`: template reference, round-trip, legacy format, 50/50 canonical,
CLI `--check`), `make run-local` end-to-end and live mode against a local stub server
(call counting, receipts, the fingerprint guard, the 50-call limit).

## Requirements

| Item | Value |
| --- | --- |
| Runtime | Python 3.9+ — **stdlib only** (no `pip install`); Docker optional (`make run` uses it if present) |
| Hardware | none specific; CPU, under 1 second (replay) |
| API keys | **not required** for `make run` (replay); only for `make run-live` |
| Model weights | not included; the model was served at the CSCS endpoint |
| Network | **no** in replay; yes in live |

## Reproducibility (meta)

- Model: `swiss-ai/Apertus-v1.5-8B`
- Endpoint: `https://api.inference.cscs.ch/v1`
- Seed: `42` | Temperature: `0.0` | Max tokens: `512`
- System fingerprint: `vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180`
- Sha256 of the measurer (`apertus_harness.py`, the frozen reference from which `krahaso()` was ported):
  `d9730610354a1bf2905a11d1f7d87d58cb023b383e53ef17a4543381b1d5cf5b`
- Sources of the recordings (04.10.2026; their sha256 live in `reproduce_points.json` → `sources_sha256`):
  `harness-20261004T064802Z.json` (battery) · `harness-20261004T064909Z.json` (synthetic)
  · `parafraza-20261004.json` (F1–F4 paraphrases) · `b35-4g-20261004.json` (synthetic de/fr/it/en, F5)
- `reproduce.py` and `reproduce_points.json` print their own sha256 on every run.

Note: the recordings were produced with earlier versions of the measurer; the packaged
`krahaso()` port is **AST-identical** to the frozen reference and was verified
point-by-point over the 65 packaged points (and over the 215 points of the 4 source
runs): **0 verdict differences**.

## Licensing & attribution

Code and Makefiles: Apache-2.0 (`LICENSE`); findings files and reproduction data: CDLA-Permissive-2.0; technical report: CC-BY-4.0.
Expected answers of the fact points (F1–F4) quote/paraphrase Wikipedia (CC-BY-SA 4.0) — the article URL is in each finding's `notes` ("Source (K-a)") and `steps_to_reproduce`; synthetic personas (F5) are fictional (no real-person data).
Model outputs are from `swiss-ai/Apertus-v1.5-8B` via the CSCS endpoint, reproduced under the Apertus license terms; built by a solo developer with his AI agent (OpenClaw) — the agent did tooling/measurement/documentation, never the model under test.

## How the report PDF was built

The submitted report `ArberArifi_Report.pdf` is rendered from `technical_report.md`
with `pandoc` + `weasyprint` using `docs/report.css` (A4, 2 cm margins, 11 pt).
Note: weasyprint ignores pandoc's `geometry` variable, so the margins are declared
in the CSS; without it, the default layout exceeds the official 6-page limit.
Result: **6 pages** (official limit: max. 6).
