# Hack Apertus — project template

Template repository for [Hack Apertus](https://hackapertus.ch/) submissions.
Every project keeps almost the same layout, so organizers and judges find the
same things in the same place.

## Select your track

This repository holds one example project per track:

- `track_1a/`
- `track_1b/`
- `track_2a/`
- `track_2b/`

Keep the directory for the track you are competing in **exactly as it is** —
don't rename it or move its files — and delete the other track directories.
That directory is your project root. Keep the files and directories as shown
below.

## The structure

| Path | What it is |
| --- | --- |
| `README.md` | The challenge description and submission requirements for your track |
| `technical_report.md` | The deeper write-up: architecture, evaluation, limitations |
| `Makefile` | `make run` must spin up your project |
| `src/` | Your code |
| `data/` | Datasets — `track_1a`, `track_2a` and `track_2b` only; max. 100 MB |
| `findings/` | Issue files — `track_1a` only |
| `docs/` | Diagrams, notes, longer write-ups |

## Run it

Judges run `make run` from the root of the project, on a clean checkout:

```bash
make run
```

`make run` is expected to run the project using Docker, since that
is how the judges will run it.
- If you used other local open-weight models, include instructions for running the project in your technical report.
- Use the following environment variables:
```
LLM_NAME — name and version of the model
LLM_BASE_URL — endpoint base URL
LLM_API_KEY — your API key
```

## Quick start for judges (this submission: Track 1A, `track_1a/`)

| Command | What it does | Needs |
| --- | --- | --- |
| `make run` | Builds the minimal Docker image (`python:3.12-slim`, stdlib only) and replays the 65 recorded reproduction points of the 5 findings; falls back to local `python3` if Docker is unavailable. Ends with `REPRODUCED 65/65 recorded verdicts (0 mismatches) …`. | nothing (no network, no API key) |
| `make test` | 23 stdlib `unittest` tests: comparator, data integrity, findings schema, walkthrough format, `make run` end-to-end, live mode against a local stub. | nothing |
| `make run-live` | Same replay plus live calls to the Apertus endpoint (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_NAME`; `--max-calls`, hard cap 50) with a `system_fingerprint` guard; receipts in `track_1a/out/`. | `LLM_API_KEY` |

Deliverables: `track_1a/findings/*.json` (5 findings, 10 walkthroughs each in the Apertus chat-template format),
`track_1a/technical_report.md` + `track_1a/ArberArifi_Report.pdf`, `track_1a/docs/reproducibility.md`.

### Replay vs. live — what `make run` proves, and what it does not

`make run` is a **deterministic replay**: it does **not** call the model. It re-applies the frozen comparator
(`krahaso()`, strategy hash `d9730610`) to the 65 recorded prompt/response pairs in
`track_1a/data/reproduce_points.json` and checks that every recorded verdict is re-derived exactly.
*What this proves:* the findings are precisely what the packaged evidence says — the response texts, the
recording parameters and the source-file hashes are in the repo, so nothing was edited after the fact — and
the classification is reproducible with no network, no API key and no GPU.
*What it does not prove:* that the live model answers the same way today. That is what `make run-live` is for:
it re-queries the endpoint with identical parameters (temperature 0.0, seed 42, max_tokens 512), compares each
live answer with the same comparator against the recorded verdict, writes every call as a receipt to
`track_1a/out/live-<ts>.json`, and **stops if the server's `system_fingerprint` differs** from the recording's
(answers are then no longer comparable). Our own live re-check before submission: [N/N recorded verdicts
re-confirmed live on 13 Oct, ≤25 calls, receipt `live-<ts>.json`]. We keep the two modes separate on purpose:
a "reproduction" that silently re-queried the model would be neither reproducible nor honest about drift.

## Getting started

1. Click **Use this template** to create your own repository.
2. Delete the other track directories. Don't rename or restructure yours.
3. Read its `README.md` and fill in `technical_report.md`.
4. Make `make run` work from the root of the project, on a clean checkout.

## License

All Hack Apertus projects are open-sourced. Please check our Terms & Conditions for specific licensing details (6. What you build is open source): https://hackapertus.ch/terms-and-conditions

## Licensing & attribution

- **Code** (`track_1a/src/`, `track_1a/tests/`, `Makefile`, `track_1a/Makefile`, `Dockerfile`): Apache-2.0 — see [`LICENSE`](LICENSE).
- **Findings files** (`track_1a/findings/*.json`) and **battery / reproduction data** (`track_1a/data/reproduce_points.json`): CDLA-Permissive-2.0, as required by the Track 1A README and the Hack Apertus T&C §6.
- **Technical report** (`track_1a/technical_report.md`, `track_1a/ArberArifi_Report.pdf`): CC-BY-4.0.
- **Expected answers of the fact points** (F1–F4) quote or paraphrase Wikipedia articles, licensed CC-BY-SA 4.0. The article URL for each finding is recorded in the `notes` field ("Burimi (K-a): Wikipedia …") and in `steps_to_reproduce` of the corresponding findings file.
- **Synthetic personas** (F5): fictional names and biographies generated for this study; no real-person data is used or disclosed.
- **Model outputs**: all recorded responses come from `swiss-ai/Apertus-v1.5-8B` via the CSCS OpenAI-compatible endpoint (temperature 0.0, seed 42) and are reproduced here under the Apertus license terms.
- Built by a solo developer with his AI agent (OpenClaw); the agent did tooling, measurement and documentation — never the model under test.
