# Add your own battery in 5 minutes (reusable harness)

The collector in `track_1a/src/harness/collect.py` is the tool we used to find the five issues
of this submission, packaged so that the next hackathon iteration can point it at a new
battery and a new model without touching the code. Everything is Python standard library.

## 1. Write the battery

A battery is a JSON list of falsifiable questions (schema: `track_1a/data/battery.schema`,
example: `track_1a/data/example_battery.json`):

```json
{"id": "K6-de", "cat": "KULT", "lang": "de",
 "prompt": "Wie heißt die Nationalhymne des Kosovo?",
 "expected": "Europe", "expected_alt": ["Europe", "Evropa"],
 "source": "https://en.wikipedia.org/wiki/Anthem_of_the_Republic_of_Kosovo",
 "note": "expected substitution: Albania's anthem"}
```

Rules the collector enforces before the first call (exit 2 otherwise):

- `id` unique; `prompt`, `expected`, `lang` (`sq|de|fr|it|en`), `source` (public `http(s)` URL) present;
- `expected` is the **bare** answer — no parentheses; the comparator requires every key token for
  answers of three tokens or fewer, 60 % otherwise (`src/reproduce.py::krahaso`); put inflections and
  numbers-in-words into `expected_alt` so that a correct answer phrased differently is not flagged;
- personal-data categories (`PERZ`, `PII`, …) require `"synthetic": true` — never real persons;
- no e-mail addresses in prompts.

Ask the same fact in all five languages: a failure that survives translation attributes to
knowledge, not to the prompt language.

## 2. Dry run (zero calls)

```bash
python3 track_1a/src/harness/collect.py --battery my_battery.json --dry-run
```

Prints the plan: number of points, the battery sha256, the fingerprint reference and the
ceiling. A battery larger than `--limit` (hard cap 50 per run) is refused with zero calls.

## 3. Collect

```bash
export LLM_BASE_URL=https://api.inference.cscs.ch/v1 LLM_NAME=swiss-ai/Apertus-v1.5-8B LLM_API_KEY=...
make collect BATTERY=my_battery.json LIMIT=20
```

Parameters are fixed to the recorded ones (temperature 0.0, seed 42, max_tokens 512). Safety rails:

- **fingerprint guard** — the first response whose `system_fingerprint` differs from the reference
  stops the run (exit 4): a different server build is not comparable byte-for-byte;
- **HTTP 429 / 5xx** — stop after the first occurrence, no retries (exit 1); contact the provider;
- **receipts** — one JSON line per call in `track_1a/out/receipts-<ts>.jsonl` (status, ms, fingerprint,
  usage); the API key never appears in any output.

## 4. Read the result

`track_1a/out/collect-<ts>.json` holds every point with the verbatim response, the comparator verdict
and a `candidate` flag. **A candidate is not a finding.** Review each one against a written checklist
(ours: source confirms the expected answer · not a comparator artefact · ≥3 variations fail · harm
named · official topic area and no real persons) and only then write `findings/<F>.json`.

## 5. Package for `make run`

Copy the reviewed points (prompt, expected, response, verdict) into `data/reproduce_points.json`
following the existing entries; `make test` checks that every walkthrough of every finding is backed
by a packaged point and that the replayed verdicts match the recorded ones.
