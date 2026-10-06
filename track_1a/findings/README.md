# Licensing & attribution — findings

The findings JSON files in this directory (`F1_K6_himni.json` … `F5_persona_sintetike.json`)
are released under **CDLA-Permissive-2.0**, as required by the Track 1A README and the
Hack Apertus Terms & Conditions §6. The schema file `findings.schema` is a copy of the
official Track 1A schema.

- **Code** (`track_1a/src/`, `track_1a/tests/`, Makefiles, `Dockerfile`): Apache-2.0 — see
  `LICENSE` at the repository root.
- **Technical report** (`track_1a/technical_report.md`, `track_1a/ArberArifi_Report.pdf`):
  CC-BY-4.0.
- **Expected answers of the fact points** (F1–F4) quote or paraphrase Wikipedia articles,
  licensed **CC-BY-SA 4.0**; the article URL for each finding is recorded in the `notes`
  field and in `steps_to_reproduce`.
- **Model outputs** come from `swiss-ai/Apertus-v1.5-8B` via the CSCS OpenAI-compatible
  endpoint (temperature 0.0, seed 42), reproduced here under the Apertus license terms.
- All personas referenced in the privacy findings are **synthetic** (no real persons).
