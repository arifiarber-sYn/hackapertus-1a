# Riprodhueshmëria — Track 1A (`make run`)

## Çka bën `make run`

Nga rrënja e repo-s (checkout i pastër):

    make run

Ekzekuton `track_1a/src/reproduce.py` — një **riprodhim offline** i gjetjeve:

1. Lexon pikat e paketuara në repo: `track_1a/data/reproduce_points.json`
   (id, prompt, expected, përgjigjja e regjistruar e modelit) për çdo pikë që
   përmendet në `findings/` (5 gjetje, 40 pika).
2. Aplikon të njëjtën logjikë krahasimi si `apertus_harness.py` (`krahaso()`):
   normalizim, puthje në kufi fjale, mbaresa të kufizuara (R12) dhe refuzimi i
   njohur në 5 gjuhë (R15).
3. Printon për çdo pikë: id, PROMPT, EXPECTED, përgjigjja e modelit (e cituar)
   dhe verdiktin; në fund përmbledhjen dhe informacionin e riprodhueshmërisë.

Dalja është tekst i lexueshëm; kodi i kthimit = 0 (gjetjet dokumentohen, nuk
janë gabim ekzekutimi).

## Pse offline (pa rrjet, pa çelësa API)

Gjyqtarët nuk kanë aksesin tonë CSCS. Prandaj `make run` **nuk bën thirrje
API**: riprodon përgjigjet e regjistruara të modelit (04.10.2026) dhe u aplikon
të njëjtin matës. Kështu xhiro është deterministe dhe pa varësi të jashtme.

## Kërkesat

| Zëri | Vlera |
| --- | --- |
| Runtime | Python 3.9+ — **vetëm stdlib** (pa `pip install`, pa Docker, pa rrjet) |
| Hardware | asnjë specifik; CPU, nën 1 sekondë |
| Çelësa API | **nuk kërkohen** për `make run` |
| Peshat e modelit | nuk përfshihen; modeli u servua në endpoint-in CSCS |

## Riprodhueshmëri (meta)

- Model: `swiss-ai/Apertus-v1.5-8B`
- Endpoint: `https://api.inference.cscs.ch/v1`
- Seed: `42` | Temperature: `0.0` | Max tokens: `512`
- System fingerprint: `vllm-0.23.1rc1.dev1029+ga601a9d99-2d880180`
- Sha256 i matësit (`apertus_harness.py`): `46f8cb18d845155b268e0317cec9ff53dde4039cf7ee296fb995037dca7947a3`
- Burimet: `harness-20261004T064802Z.json` (bateria) + `harness-20261004T064909Z.json` (sintetike)
- `reproduce.py` dhe `reproduce_points.json` printojnë sha256-n e tyre në çdo xhiro.

Shënim: regjistrimet e 06:48Z u prodhuan para se harness-i të shtonte fushën
`harness_sha256`; hash-i i mësipërm është i gjendjes së tanishme të
`apertus_harness.py`, prej së cilës u portua `krahaso()`. Porta u verifikua
pikë-për-pikë mbi të 135 pikat e regjistruara: **0 dallime**.

## Xhiro e drejtpërdrejtë (opsionale, jashtë `make run`)

Për të riprodhuar live kundër CSCS nevojitet çelësi i CSCS (`LLM_API_KEY`)
dhe rrjeti; kjo nuk kryhet nga `make run`.
