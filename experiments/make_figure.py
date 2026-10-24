"""
Main results figure: AUROC (95% bootstrap CI over games) by monitor view, one panel per
colluder type, for the LLM monitors and the heuristic baselines. Negatives = `none` games.

Config (JSON): {"panels": [{"title": str, "positives": [cond, ...], "logs": DIR,
                            "llama": [EVAL_DIR, ...], "deepseek": [EVAL_DIR, ...]}, ...]}

Run:  python experiments/make_figure.py CONFIG.json OUT_BASENAME   (writes .png and .pdf)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from monitor.baselines import baseline_rows
from monitor.metrics import bootstrap, load_rows

VIEWS = ["public", "actions", "both", "table", "plans"]
VIEW_LABELS = {"public": "Public\nmessages", "actions": "Actions", "both": "Messages\n+ actions",
               "table": "Said vs did\ntable", "plans": "+ private\nplans (UB)"}
# Heuristic shown in each view (the rule that uses only that view's information)
HEURISTIC_FOR_VIEW = {"actions": ["against_stake", "co_vote"], "table": ["said_vs_did"], "both": ["combined"]}
HEURISTIC_SHORT = {"against_stake": "against-stake", "co_vote": "co-vote", "said_vs_did": "said≠did",
                   "combined": "combined"}

# Reference palette (dataviz skill, light mode), first three categorical slots;
# validated all-pairs. Aqua is < 3:1 on the surface, so marker shapes + labels carry identity.
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = {
    "Llama 3.3 70B monitor": ("#2a78d6", "o"),
    "DeepSeek V3.1 monitor": ("#eb6834", "s"),
    "Heuristic (no LLM)":    ("#1baf7a", "D"),
}


def panel_points(p):
    keep = lambda r: (r["label"] == "no" and r["condition"] == "none") or \
                     (r["label"] == "yes" and r["condition"] in p["positives"])
    pts = {}
    for name, key in (("Llama 3.3 70B monitor", "llama"), ("DeepSeek V3.1 monitor", "deepseek")):
        rows = [r for d in p.get(key, []) for r in load_rows(d) if keep(r)]
        if rows:
            res = bootstrap(rows)
            pts[name] = {v: res.get(f"view={v}", {}).get("auroc") for v in VIEWS}
    rows = [r for r in baseline_rows(p["logs"]) if keep(r)]
    res = bootstrap(rows)
    pts["Heuristic (no LLM)"] = {
        v: [(h, res.get(f"view=baseline:{h}", {}).get("auroc")) for h in HEURISTIC_FOR_VIEW.get(v, [])]
        for v in VIEWS}
    n_pos = len({r["game_id"] for r in rows if r["label"] == "yes"})
    n_neg = len({r["game_id"] for r in rows if r["label"] == "no"})
    return pts, n_pos, n_neg


def draw(panels, out):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2})
    fig, axes = plt.subplots(1, len(panels), figsize=(3.6 * len(panels) + 0.6, 3.6),
                             sharey=True, facecolor=SURFACE)
    axes = [axes] if len(panels) == 1 else list(axes)
    offsets = {"Llama 3.3 70B monitor": -0.26, "DeepSeek V3.1 monitor": -0.06, "Heuristic (no LLM)": 0.14}
    for ax, p in zip(axes, panels):
        pts, n_pos, n_neg = panel_points(p)
        ax.set_facecolor(SURFACE)
        ax.axvspan(len(VIEWS) - 1.5, len(VIEWS) - 0.5, color="#f1f0ec", zorder=0)
        ax.axhline(0.5, color=INK2, lw=1, ls=(0, (4, 3)), zorder=1)
        ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
        for name, (color, marker) in SERIES.items():
            if name not in pts:
                continue
            for i, v in enumerate(VIEWS):
                ms = pts[name][v]
                entries = ms if name == "Heuristic (no LLM)" else [(None, ms)]
                for j, (h, m) in enumerate(entries):
                    if not m or m.get("est") is None:
                        continue
                    x = i + offsets[name] + 0.2 * j
                    lo, hi = m["ci95"] if m.get("ci95") else (m["est"], m["est"])
                    ax.plot([x, x], [lo, hi], color=color, lw=2, solid_capstyle="round", zorder=2)
                    hollow = h == "co_vote"
                    ax.plot(x, m["est"], marker=marker, ms=7 if marker != "D" else 6,
                            mfc=SURFACE if hollow else color, mec=color if hollow else SURFACE,
                            mew=1.5, ls="none", zorder=3)
                    if h:
                        ax.annotate(HEURISTIC_SHORT[h], (x, lo), xytext=(0, -3), textcoords="offset points",
                                    ha="center", va="top", fontsize=6.5, color=INK2, rotation=90)
        ax.set_xticks(range(len(VIEWS)))
        ax.set_xticklabels([VIEW_LABELS[v] for v in VIEWS], fontsize=7.5)
        ax.set_xlim(-0.6, len(VIEWS) - 0.4)
        ax.set_ylim(0.0, 1.02)
        ax.set_title(f"{p['title']}\n{n_pos} colluding vs {n_neg} no-collusion games",
                     fontsize=9.5, color=INK, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("AUROC (95% CI over games)")
    for ax in axes:
        ax.text(len(VIEWS) - 0.45, 0.49, "chance", fontsize=7, color=INK2, ha="right", va="top")
    handles = [plt.Line2D([], [], color=c, marker=m, mfc=c, mec=SURFACE, ls="-", lw=2, ms=7)
               for c, m in SERIES.values()]
    fig.legend(handles, list(SERIES), loc="lower center", ncol=3, frameon=False, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(f"{out}.{ext}", dpi=200, facecolor=SURFACE)
    print(f"wrote {out}.png and {out}.pdf")


if __name__ == "__main__":
    draw(json.load(open(sys.argv[1]))["panels"], sys.argv[2])
