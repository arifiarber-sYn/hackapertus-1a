# Riprodhueshmëria — Track 1A (`make run`)

## Çka bën `make run`

Nga rrënja e repo-s (checkout i pastër):

    make run

1. Nëse Docker është i disponueshëm: ndërton imazhin minimal (`Dockerfile`,
   `python:3.12-slim`, pa `pip install`) dhe xhiron riprodhimin **brenda
   kontejnerit**. Nëse Docker mungon ose daemon-i nuk përgjigjet, bie
   automatikisht te `make run-local` (i njëjti riprodhim, python3 direkt).
2. Ekzekuton `track_1a/src/reproduce.py` në modën **replay**:
   - lexon pikat e paketuara `track_1a/data/reproduce_points.json` (id, prompt,
     expected, përgjigjja e regjistruar e modelit, verdikti i regjistruar) për
     **çdo walkthrough** të 5 gjetjeve — **65 pika** (F1–F4 nga 10: 5 origjinale
     + 5 parafraza; F5 nga 25: 20 sq + 5 de/fr/it/en);
   - u aplikon të njëjtën logjikë krahasimi si `apertus_harness.py`
     (`krahaso()`: normalizim, puthje në kufi fjale, mbaresa të kufizuara R12,
     asidet në kllapa R13, refuzimi i njohur në 5 gjuhë R15, refuzimi i maskuar
     me fakte R16);
   - printon për çdo pikë id, PROMPT, EXPECTED, përgjigjen e modelit (të cituar)
     dhe verdiktin; në fund përmbledhjen (**Mosperputhje me regjistrimin: 0**)
     dhe informacionin e riprodhueshmërisë.

Dalja është tekst i lexueshëm; kodi i kthimit = 0 (gjetjet dokumentohen, nuk
janë gabim ekzekutimi).

## Moda live (opsionale): `make run-live`

Me `LLM_BASE_URL`, `LLM_API_KEY` dhe `LLM_NAME` në mjedis (ose në `.env`),
`reproduce.py --live` thërret endpoint-in OpenAI-compatible për çdo pikë me të
njëjtat parametra (temperature 0.0, seed 42, max_tokens 512), e krahason
përgjigjen LIVE me të njëjtin `krahaso()` dhe e vë përballë verdiktit të
regjistruar (`verdikt = regjistrimi N/M`). Mbrojtje:

- **Roja e fingerprint-it:** nëse `system_fingerprint` i serverit ndryshon nga ai
  i regjistrimit, moda live ndalet (pikat e mbetura → replay) — përgjigjet nuk
  janë më të krahasueshme bit-për-bit.
- **Kufi i fortë ≤50 thirrje** për xhiro (`--max-calls`, nuk kapërcehet).
- Çdo thirrje ruhet si dëftesë (raw JSON, usage, fp, ms) në
  `track_1a/out/live-<ts>.json` (jashtë git-it).
- Pa `LLM_API_KEY` → bie në replay me paralajmërim, që `make run` të kalojë
  end-to-end edhe pa çelës.

Në Docker: `docker run --rm -e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME hackapertus-1a:local python3 track_1a/src/reproduce.py --live`.

## Testet: `make test`

`python3 -m unittest discover -s track_1a/tests -t .` — vetëm stdlib. Mbulojnë
`krahaso()` (R7/R12/R13/R15/R16), integritetin e të dhënave (çdo walkthrough i
dorëzuar ka pikën e vet të paketuar me të njëjtën përgjigje; verdikti i
rillogaritur = i regjistruari), skemën e `findings/*.json` (celësat brenda
skemës zyrtare, 1..10 walkthroughs, S/B në {0,1,2,5,10}, justifikimet ≤500),
`make run-local` end-to-end dhe modën live kundër një serveri stub lokal
(numërimi i thirrjeve, dëftesa, roja e fingerprint-it, kufiri 50).

## Kërkesat

| Zëri | Vlera |
| --- | --- |
| Runtime | Python 3.9+ — **vetëm stdlib** (pa `pip install`); Docker opsional (`make run` e përdor nëse ekziston) |
| Hardware | asnjë specifik; CPU, nën 1 sekondë (replay) |
| Çelësa API | **nuk kërkohen** për `make run` (replay); vetëm për `make run-live` |
| Peshat e modelit | nuk përfshihen; modeli u servua në endpoint-in CSCS |
| Rrjet | **jo** në replay; po në live |

## Riprodhueshmëri (meta)

- Model: `swiss-ai/Apertus-v1.5-8B`
- Endpoint: `https://api.inference.cscs.ch/v1`
- Seed: `42` | Temperature: `0.0` | Max tokens: `512`
- System fingerprint: `vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180`
- Sha256 i matësit (`apertus_harness.py`, referenca e ngrirë nga e cila u portua `krahaso()`):
  `d9730610354a1bf2905a11d1f7d87d58cb023b383e53ef17a4543381b1d5cf5b`
- Burimet e regjistrimeve (04.10.2026; sha256 të tyre te `reproduce_points.json` → `sources_sha256`):
  `harness-20261004T064802Z.json` (bateria) · `harness-20261004T064909Z.json` (sintetike)
  · `parafraza-20261004.json` (parafrazat F1–F4) · `b35-4g-20261004.json` (sintetike de/fr/it/en, F5)
- `reproduce.py` dhe `reproduce_points.json` printojnë sha256-n e tyre në çdo xhiro.

Shënim: regjistrimet u prodhuan me versione të mëparshme të matësit; porta
`krahaso()` e paketuar është **AST-identike** me referencën e ngrirë dhe u
verifikua pikë-për-pikë mbi të 65 pikat e paketuara (dhe mbi 215 pikat e 4
xhirimeve burimore): **0 dallime** në verdikte.

## Licensing & attribution

Code and Makefiles: Apache-2.0 (`LICENSE`); findings files and reproduction data: CDLA-Permissive-2.0; technical report: CC-BY-4.0.
Expected answers of the fact points (F1–F4) quote/paraphrase Wikipedia (CC-BY-SA 4.0) — the article URL is in each finding's `notes` ("Burimi (K-a)") and `steps_to_reproduce`; synthetic personas (F5) are fictional (no real-person data).
Model outputs are from `swiss-ai/Apertus-v1.5-8B` via the CSCS endpoint, reproduced under the Apertus license terms; built by a solo developer with his AI agent (OpenClaw) — the agent did tooling/measurement/documentation, never the model under test.
