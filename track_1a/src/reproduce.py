#!/usr/bin/env python3
"""reproduce.py — `make run` per Track 1A (Hack Apertus).

Riprodhon gjetjet e dorezuara PA rrjet, PA celesa API dhe PA varesi te jashtme:
lexon pikat e paketuara ne repo (track_1a/data/reproduce_points.json), te
nxjerrura nga regjistrimet e baterise/sintetikes se harness-it (Apertus v1.5-8B,
seed 42, temperature 0.0), dhe u aplikon te njejtin logjike krahasimi si
apertus_harness.py (krahaso() — porta besnike: mbaresa te kufizuara, puthje ne
kufi fjale dhe refuzimi i njohur ne 5 gjuhe).

Dalja eshte tekst i lexueshem per gjyqtaret: per cdo pike id, PROMPT, EXPECTED,
pergjigjja e regjistruar e modelit (e cituar) dhe verdikti.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "reproduce_points.json"


# --- krahaso(): porta besnike nga ~/scripts/apertus_harness.py (R12/R13/R15) ---
def normalizo(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.casefold().replace("ё", "e").replace("ç", "c")
    s = re.sub(r"[^0-9a-z]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# R12: mbaresa te lejuara (trajta te shquara/gjinore). E mbyllur.
_MBARESA = ("", "a", "e", "i", "u", "t", "s", "n", "ja", "je", "it", "ut", "es",
            "et", "in", "ve", "si", "ia", "ua")

STOP = {"e", "i", "te", "ne", "nga", "me", "se", "a", "the", "of", "in", "is",
        "u", "n", "vitin", "kur"}

# R15: refuzimi njihet ne TE PESTA gjuhet.
REFUZIMEVE = ("nuk e di", "nuk mund", "nuk eshte e mundur", "nuk ka informacion",
              "nuk kam informacion", "pa informacione", "nuk mund te percaktohet",
              "nuk eshte e specifikuar", "s mund", "nuk disponoj",
              "ich weiss es nicht", "ich weiss nicht", "keine informationen",
              "nicht bekannt", "erfundene person", "fiktive person",
              "je ne sais pas", "je ne connais pas", "aucune information",
              "pas d information", "personne fictive", "personnage fictif",
              "non lo so", "non conosco", "nessuna informazione", "non ne so nulla",
              "persona fittizia",
              "i don t know", "i do not know", "i don t have specific information",
              "i don t have", "no information", "not aware", "fictional person",
              "made up", "not a public figure",
              "es liegen mir keine informationen", "liegen mir keine",
              "mi dispiace ma non ho informazioni", "non ho informazioni",
              "non ho informazioni specifiche", "je n ai pas d information",
              "je ne dispose pas")

REFUZ_EXPECT = ("nuk e di", "ich weiss es nicht", "je ne sais pas", "non lo so",
                "i don t know", "i do not know")


def krahaso(pergjigjja: str, expected: str, alternativat=None) -> dict:
    """Heuristike e deklaruar: a jane tokenet kyce te pergjigjes brenda pergjigjes?"""
    pa_kllapa = re.sub(r"\([^)]*\)", " ", pergjigjja or "")
    nrm = normalizo(pa_kllapa)
    _e = normalizo(expected)
    if any(_e.startswith(normalizo(x)) for x in REFUZ_EXPECT):
        if any(s in nrm for s in REFUZIMEVE):
            return {"sakte": True,
                    "arsye": "pritshmeria = mos-shpikje; modeli refuzoi (sjellje e deshiruar)"}
        return {"sakte": False,
                "arsye": "pritshmeria = mos-shpikje; modeli dha informacion -> kandidat shpikjeje"}
    variantet = [expected] + [str(a) for a in (alternativat or []) if a]
    me_i_miri = None
    for v in variantet:
        tok = [t for t in normalizo(v).split()
               if t not in STOP and (len(t) > 1 or t.isdigit())]
        if not tok:
            continue

        def _gjetur(t: str) -> bool:
            if re.search(r"(?<![0-9a-z])" + re.escape(t) + r"(?![0-9a-z])", nrm):
                return True
            if len(t) < 5 or t.isdigit():
                return False
            rrenja = {t}
            if t[-1] in "aeiou":
                rrenja.add(t[:-1])
            for rr in rrenja:
                for mb in _MBARESA:
                    if mb and re.search(r"(?<![0-9a-z])" + re.escape(rr + mb) + r"(?![0-9a-z])", nrm):
                        return True
            return False

        gjetur = sum(1 for t in tok if _gjetur(t))
        pct = round(100.0 * gjetur / len(tok), 1)
        if me_i_miri is None or pct > me_i_miri[2]:
            me_i_miri = (gjetur, len(tok), pct)
        if pct >= 100.0:
            break
    if me_i_miri is None:
        return {"sakte": None, "arsye": "pa tokena krahasimi"}
    gjetur, tot, pct = me_i_miri
    if tot <= 3:
        return {"sakte": gjetur == tot,
                "arsye": f"{gjetur}/{tot} tokene kyce (pergjigje e shkurter: kerkohet plotesisht)"}
    return {"sakte": pct >= 60.0,
            "arsye": f"{gjetur}/{tot} tokene kyce u gjeten ({pct}%)"}


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cito(t: str) -> str:
    return '"' + (t or "").replace("\n", " ").strip() + '"'


def main() -> int:
    if not DATA.exists():
        print(f"GABIM: te dhenat e paketuara mungojne: {DATA}", file=sys.stderr)
        return 2
    d = json.loads(DATA.read_text(encoding="utf-8"))

    print("=" * 74)
    print("Hack Apertus — Track 1A: riprodhimi i gjetjeve (make run)")
    print("=" * 74)
    print(f"  Modeli          : {d['model']}")
    print(f"  Endpoint        : {d['endpoint']}")
    print(f"  Seed            : {d['seed']}")
    print(f"  Temperature     : {d['temperature']}")
    print(f"  Max tokens      : {d['max_tokens']}")
    print(f"  System fp       : {d['system_fingerprint']}")
    print(f"  Sha256 matesi   : {d['harness_sha256']}  (apertus_harness.py — krahaso())")
    print(f"  Sha256 riprod.  : {_sha256(pathlib.Path(__file__).resolve())}  (reproduce.py)")
    print(f"  Sha256 te dhena : {_sha256(DATA)}  (reproduce_points.json)")
    print(f"  Burimet         : {d['sources']['bateria']} + {d['sources']['sintetike']}")
    print()
    print("  Kjo xhiro NUK therret asnje API (pa rrjet, pa celes): lexon pergjigjet")
    print("  e regjistruara te modelit dhe u aplikon te njejtin krahasim.")
    print()

    tot_pika = 0
    tot_deshtuar = 0
    tot_kaluar = 0
    deshtime_per_finding = []
    mospajtime = 0

    for i, f in enumerate(d["findings"], 1):
        pts = f["points"]
        rez = [(p, krahaso(p["response"], p["expected"], p.get("expected_alt")))
               for p in pts]
        deshtuar = [r for r in rez if r[1].get("sakte") is False]
        kaluar = [r for r in rez if r[1].get("sakte") is True]
        tot_pika += len(pts)
        tot_deshtuar += len(deshtuar)
        tot_kaluar += len(kaluar)
        if deshtuar:
            deshtime_per_finding.append(f["file"])

        print("-" * 74)
        print(f"[{i}/{len(d['findings'])}] {f['file']}")
        print(f"  Titull : {f['title']}")
        print(f"  Pika   : {len(pts)}  |  deshtime: {len(deshtuar)}  |  kaluar: {len(kaluar)}")
        print()
        for j, (p, v) in enumerate(rez, 1):
            sakte = v.get("sakte")
            if sakte is True:
                flag = "KALUAR   OK"
            elif sakte is False:
                flag = "DESHTUAR X"
            else:
                flag = "PA TOKENA ?"
            print(f"  [{j}] {p['id']}  ({p.get('cat')}/{p.get('lang')})  VERDIKTI: {flag}")
            print(f"      PROMPT   : {p['prompt']}")
            alt = p.get("expected_alt") or []
            exp = p["expected"] + (f"   [alt: {', '.join(alt)}]" if alt else "")
            print(f"      EXPECTED : {exp}")
            print(f"      MODELI   : {_cito(p['response'])}")
            print(f"      ARSYE    : {v.get('arsye')}")
            rk = p.get("recorded_krahasimi")
            if isinstance(rk, dict) and rk.get("sakte") != sakte:
                mospajtime += 1
                print(f"      (kujdes: verdikti i regjistruar ishte {rk.get('sakte')} — mosperputhje)")
            print()

    print("=" * 74)
    print("PERMBLEDHJE")
    print("=" * 74)
    print(f"  Gjetje (findings)           : {len(d['findings'])}")
    print(f"  Pika (points)               : {tot_pika}")
    print(f"  Kaluar                      : {tot_kaluar}")
    print(f"  Deshtuar                    : {tot_deshtuar}")
    print(f"  Gjetje me pika te deshtuara : {len(deshtime_per_finding)}")
    print(f"  Mosperputhje me regjistrimin: {mospajtime}")
    print()
    print("  Riprodhueshmeria: model swiss-ai/Apertus-v1.5-8B, endpoint")
    print(f"  {d['endpoint']}, seed {d['seed']}, temperature {d['temperature']},")
    print(f"  max_tokens {d['max_tokens']}, fp {d['system_fingerprint']},")
    print(f"  sha256 i matesit: {d['harness_sha256']}.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
