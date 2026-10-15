# Build journal — Track 1A (Red-Teaming Apertus)

> What was done, when, with which evidence — so that a judge can retrace the path without asking anyone.
> The full, commit-by-commit timeline is in the repository root: [`../../docs/BUILD-JOURNAL.md`](../../docs/BUILD-JOURNAL.md).

| Date | Step | Evidence |
|---|---|---|
| 02.10 | Package structure + Apache-2.0 licence (repo root) | initial commits |
| 04.10 | Question battery + collection harness; fingerprint guard | `harness-20261004T064802Z.json` (sha256 in `data/reproduce_points.json`) |
| 06.10 | 135 API calls (temperature 0, seed 42) → 48 candidates | receipt log, 1 line per call |
| 07.10 | Comparator hardened: 45 candidates → 5 findings | `data/reproduce_points.json` (65 points) |
| 09–10.10 | Call-budget ceiling fixed (530 self-imposed); PDF kept at 6 pages | `technical_report.md` §Reproducibility |
| 11.10 | Internal review round (two independent readers against the official rubric) → three fixes applied: A/B language-asymmetry table, "why not the official eval suite", 5-line "what the judge should see" header | commit `50f672b` |
| 11.10 | Licence copied inside `track_1a/`; figures renamed (number = name) | commit of that step |
| 12–13.10 | Submission (12.10), re-submission with the final PDF (13.10, organisers asked to keep the latest); +50 verification calls on 13.10 after submission | `out/live-20261013T102553Z.json`, `out/NOTA-live-post-submit.md` |
| 15.10 | Report reframed for the organiser's population (Switzerland first, Swiss-law finding F3 first in the report); all jury-facing text translated to English; `notes` fields brought within the schema's 2000-character limit. Numbers, model responses, walkthroughs and verdicts unchanged (`make run` 65/65). | commits of 15.10 |
