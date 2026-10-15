#!/usr/bin/env python3
"""figures.py — regenerates the report figures from the packaged data (0 API calls).

Inputs (all in the repository):
  * track_1a/data/reproduce_points.json  — the 65 replayed points of F1–F5 with the recorded verdicts
  * track_1a/docs/figures_data.json      — aggregated counts with the sha256 of the collection artefacts

Outputs: track_1a/docs/figures/fig3_heatmap.png, fig4_f5_refusal.png, fig1_funnel.png, fig2_battery_by_language.png

This script is documentation tooling, not part of `make run` (which stays stdlib-only). It needs matplotlib:
    python3 -m pip install matplotlib && python3 track_1a/docs/figures.py
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "reproduce_points.json"
AGG = HERE / "figures_data.json"
OUT = HERE / "figures"
LANGS = ["sq", "de", "fr", "it", "en"]
LANG_LABEL = {"sq": "Albanian", "de": "German", "fr": "French", "it": "Italian", "en": "English"}
FINDING_LABEL = {
    "F1_K6_himni.json": "F1 anthem\n(symbol substituted)",
    "F2_LPK176_afati_ankeses.json": "F2 LPK 176 appeal\n(15 days → 30 days)",
    "F3_AIG47_bashkimi_familjar.json": "F3 AIG 47 reunification\n(5 years → 1–3 years)",
    "F4_H5_data.json": "F4 1991 date\n(date invented)",
    "F5_persona_sintetike.json": "F5 synthetic persons\n(PII fabricated)",
}


def _lang_of(point: dict) -> str:
    lang = point.get("lang")
    if lang in LANGS:
        return lang
    suffix = str(point.get("id", "")).rsplit("-", 1)[-1]
    return suffix if suffix in LANGS else "sq"


def heatmap_matrix(d: dict, agg: dict):
    """Rows = findings, cols = languages; cell = (failures, n). F5 uses the full synthetic batteries from figures_data."""
    rows, mat = [], []
    for f in d["findings"]:
        rows.append(FINDING_LABEL.get(f["file"], f["file"]))
        if f["file"].startswith("F5"):
            fab, n = agg["f5_by_language"]["fabricated"], agg["f5_by_language"]["n_per_language"]
            mat.append([(fab[l], n[l]) for l in LANGS])
            continue
        cells = []
        for l in LANGS:
            pts = [p for p in f["points"] if _lang_of(p) == l]
            fails = sum(1 for p in pts if p.get("recorded_krahasimi", {}).get("sakte") is False)
            cells.append((fails, len(pts)))
        mat.append(cells)
    return rows, mat


def main() -> int:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing: python3 -m pip install matplotlib", file=sys.stderr)
        return 2
    d = json.loads(DATA.read_text(encoding="utf-8"))
    agg = json.loads(AGG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

    # Fig 1 — heatmap findings x languages (share of failing points)
    rows, mat = heatmap_matrix(d, agg)
    share = [[(f / n if n else 0.0) for f, n in r] for r in mat]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    im = ax.imshow(share, cmap="Greys", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(LANGS)), [LANG_LABEL[l] for l in LANGS])
    ax.set_yticks(range(len(rows)), rows)
    for i, r in enumerate(mat):
        for j, (f, n) in enumerate(r):
            ax.text(j, i, f"{f}/{n}", ha="center", va="center", color="white" if share[i][j] > 0.55 else "black")
    ax.set_title("Failing points per finding and prompt language (temperature 0, seed 42)")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="share of points failing")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Fig 2 — F5: fabricated vs refused per language
    f5 = agg["f5_by_language"]
    fab = [f5["fabricated"][l] for l in LANGS]
    ref = [f5["refused"][l] for l in LANGS]
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    x = range(len(LANGS))
    ax.bar(x, fab, color="#444444", label="fabricated profile")
    ax.bar(x, ref, bottom=fab, color="#cccccc", label="refused / abstained")
    for i in x:
        ax.text(i, fab[i] + ref[i] + 0.3, f"{fab[i]}/{fab[i] + ref[i]}", ha="center", va="bottom")
    ax.set_xticks(list(x), [LANG_LABEL[l] for l in LANGS])
    ax.set_ylabel("fictional persons (of 10)")
    ax.set_ylim(0, 14)
    ax.set_title("F5 — same 10 fictional persons: profile fabricated vs. abstained")
    ax.legend(frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout()
    fig.savefig(OUT / "fig4_f5_refusal.png", dpi=300)
    plt.close(fig)

    # Fig 3 — funnel 135 -> 48 -> 45 -> 5
    fun = agg["funnel"]
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    labels = [s.get("short", s["label"]) for s in fun][::-1]
    ns = [s["n"] for s in fun][::-1]
    ax.barh(range(len(ns)), ns, color=["#222222", "#555555", "#888888", "#bbbbbb"][::-1])
    for i, n in enumerate(ns):
        ax.text(n + 2, i, str(n), va="center")
    ax.set_yticks(range(len(ns)), labels)
    ax.set_xlim(0, max(ns) * 1.15)
    ax.set_xlabel("count")
    ax.set_title("From API calls to findings", loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_funnel.png", dpi=300)
    plt.close(fig)

    # Fig 4 — core battery: flagged points per language (21 facts each)
    b = agg["battery_by_language"]
    vals = [b["flagged"][l] for l in LANGS]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.bar(range(len(LANGS)), vals, color="#555555")
    ax.axhline(b["facts_per_language"], color="#999999", linestyle="--", linewidth=0.8)
    ax.text(len(LANGS) - 0.5, b["facts_per_language"] + 0.3, f"{b['facts_per_language']} facts asked per language", ha="right")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.3, str(v), ha="center")
    ax.set_xticks(range(len(LANGS)), [LANG_LABEL[l] for l in LANGS])
    ax.set_ylabel("flagged responses")
    ax.set_ylim(0, b["facts_per_language"] + 3)
    ax.set_title("Core battery (105 points): responses flagged by the comparator, per language")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_battery_by_language.png", dpi=300)
    plt.close(fig)

    for p in sorted(OUT.glob("*.png")):
        print(p.relative_to(HERE.parent.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
