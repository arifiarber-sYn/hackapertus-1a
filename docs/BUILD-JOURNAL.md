# Build Journal — Hack Apertus Track 1A (timestamped)

This is the timestamped record behind every claim in `track_1a/technical_report.md`.
Each row is a commit in this repository (see `git log`); the raw agent journal
and the evidence files live alongside the private collection tooling (which is
deliberately *not* part of this submission — see `track_1a/docs/reproducibility.md`).

## Timeline (Europe/Belgrade `+0200`)

| Timestamp | Commit | Milestone |
|---|---|---|
| 2026-10-02 10:26 | artefakt `determinizem-20261002T102603Z.json` | Determinism precondition measured: 4 questions × 5 repeats at temperature 0 / seed 42 (max_tokens 128) → **20/20 byte-identical (100 %)**. |
| 2026-10-02 11:40 | `e6a64b9` | Repository created from the official `HackApertus/project-template` (other tracks removed). |
| 2026-10-02 13:15 | `a8bdc61` | Pre-submission hygiene: example findings moved to `docs/`; harness candidates git-ignored; `findings/` holds the schema. |
| 2026-10-03 20:15 | `fcfc97d` | R8/K4: evaluation battery excluded from the submission (`battery*.json`). |
| 2026-10-04 12:12 | `e7ab2a6` | Findings F1–F5 written (official `topic_area`, PROMPT before each walkthrough). |
| 2026-10-04 12:21 | `bcb84a6` | Language-asymmetry observation (I1/K1) recorded; F6 evaluated. |
| 2026-10-04 12:30 | `6bf13b1` | F5 rebuilt from ids; official `topic_area` on all findings. |
| 2026-10-04 13:12 | `701ed6a` | F6 did **not** pass criterion K-c → kept as an observation in `docs/`, findings remain 5. |
| 2026-10-04 13:25 | `cde5ccf` | `make run` real replay (no API keys, no network) from the repo root. |
| 2026-10-04 13:26 | `a4e70ce` | `docs/reproducibility.md`: runtime, hardware, key handling, hashes. |
| 2026-10-04 13:51 | `9f29e3b` | B10: breadth justifications (3 phrasings × 5 languages) + 10 walkthroughs per finding. |
| 2026-10-04 14:30 | `540fc9f` | Rubric v2 applied after verification against the official README. |
| 2026-10-04 15:04 | `936361c` | Schema blocker removed (validate 5/5 PASS); `self_assessed_novelty` removed (novelty left to the jury). |
| 2026-10-04 15:07 | `c3242ed` | Schema `additionalProperties=false` honoured; F5 justification made distinct. |
| 2026-10-04 15:21 | `00204bf` | Regression reverted: source URLs and sha restored. |
| 2026-10-04 19:12 | `79f5a69` | B36: Dockerfile + 18 stdlib tests; comparator = frozen reference `d9730610`; 65 packaged points; `--live` mode (≤50 calls, fingerprint guard). |
| 2026-10-04 19:33 | `98c8445` | B36 merged after independent review: `make test` OK, `make run` rc=0, comparator `d9730610`. |
| 2026-10-04 19:44 | `21d38f4` | Live run 5/5 recorded as reproducibility evidence. |
| 2026-10-05 08:47 | `1fab75a` | `technical_report.md` completed (6 pages) + `ArberArifi_Report.pdf`; number-to-artefact map. |
| 2026-10-05 10:15 | `276a92c` | Full sha256 receipts added to findings notes. |
| 2026-10-05 10:29 | `dd598b3` | Harm paragraph (§4.2) added; PDF rebuilt (6 pages). |
| 2026-10-05 10:42 | `3e7a486` | Walkthroughs reformatted to `USER:/ASSISTANT:`. |
| 2026-10-05 10:57 | `c413c1f` | F5 fr walkthrough corrected to `P8s-fr`. |
| 2026-10-05 10:59 | `34d64ae` | Revert: walkthroughs keep the canonical `PROMPT:` format required by the repo test. |
| 2026-10-05 16:46 | `55bee76` | A1: report PDF moved to `track_1a/` (official README line 55); PDFs excluded from the Docker image. |
| 2026-10-05 16:47 | `04ae49d` | A3 / T&C §6: `Licensing & attribution` section in the root README. |
| 2026-10-05 16:51 | `8412779` | A2: walkthroughs in the v1.5 chat format (50/50, byte-for-byte). |
| 2026-10-05 16:51 | `e1a99ed` | Quick start for judges (`make run` / `make test` / `make run-live`); `REPRODUCED 65/65`. |
| 2026-10-06 08:42 | `bb393f5` | Merge of the corrections branch: A1 + A2 + A3 + quick start (23 tests OK). |
| 2026-10-06 (post-merge) | — | Report integrity pass: validation wording corrected to agent-reviewed + independently re-checked + developer-approved; private collection tooling disambiguated from the repo; census figure cited; number-to-artefact map updated. |

> **Honest negatives kept in the record:** F6 (language asymmetry) was evaluated and did **not** meet criterion K-c, so it was not submitted as a finding; it is preserved in `track_1a/docs/`. The 48 → 45 → 5 candidate reduction (3 comparator artefacts removed, 40 non-selected candidates) is disclosed in the report's Discovery Process.
