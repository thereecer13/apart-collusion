"""
Paired comparison of two monitor runs on the same games (e.g. prompt v1 vs v2): per view,
AUROC(B) - AUROC(A) with a bootstrap 95% CI over games, plus each run's AUROC, FPR and pair-ID.

Run:  python experiments/compare_prompts.py EVAL_DIR_A EVAL_DIR_B --positives instructed_hint --negatives none
"""

import argparse
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.metrics import auroc, load_rows, point

N_BOOT = 2000


def keep(rows, pos, neg):
    return [r for r in rows if r["parsed"] and
            ((r["label"] == "yes" and r["condition"] in pos) or (r["label"] == "no" and r["condition"] in neg))]


def by_view_game(rows):
    out = defaultdict(dict)
    for r in rows:
        out[r["view"]][r["game_id"]] = r
    return out


def view_auroc(rows_by_game, games):
    pos = [rows_by_game[g]["suspicion"] for g in games if g in rows_by_game and rows_by_game[g]["label"] == "yes"]
    neg = [rows_by_game[g]["suspicion"] for g in games if g in rows_by_game and rows_by_game[g]["label"] == "no"]
    return auroc(pos, neg)


def ci(vals):
    v = sorted(x for x in vals if x is not None)
    return [v[int(0.025 * len(v))], v[min(len(v) - 1, int(0.975 * len(v)))]] if len(v) >= 20 else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--positives", required=True)
    ap.add_argument("--negatives", required=True)
    args = ap.parse_args()
    pos, neg = set(args.positives.split(",")), set(args.negatives.split(","))
    A, B = by_view_game(keep(load_rows(args.a), pos, neg)), by_view_game(keep(load_rows(args.b), pos, neg))
    rng = random.Random(0)
    print(f"A = {args.a}\nB = {args.b}")
    print(f"{'view':18s} {'n(+/-)':>8s} {'AUROC A':>8s} {'AUROC B':>8s}  {'B - A [95% CI]':24s} {'FPR A':>6s} {'FPR B':>6s} {'pair A':>7s} {'pair B':>7s}")
    for view in sorted(set(A) & set(B)):
        games = sorted(set(A[view]) & set(B[view]))
        n_pos = sum(A[view][g]["label"] == "yes" for g in games)
        a, b = view_auroc(A[view], games), view_auroc(B[view], games)
        diffs = []
        for _ in range(N_BOOT):
            s = [rng.choice(games) for _ in games]
            # duplicates matter for AUROC: build resampled row lists
            ra = [A[view][g] for g in s]
            rb = [B[view][g] for g in s]
            pa = auroc([r["suspicion"] for r in ra if r["label"] == "yes"], [r["suspicion"] for r in ra if r["label"] == "no"])
            pb = auroc([r["suspicion"] for r in rb if r["label"] == "yes"], [r["suspicion"] for r in rb if r["label"] == "no"])
            diffs.append(None if pa is None or pb is None else pb - pa)
        c = ci(diffs)
        ma, mb = point([A[view][g] for g in games]), point([B[view][g] for g in games])
        print(f"{view:18s} {n_pos:>3d}/{len(games) - n_pos:<4d} {a:8.2f} {b:8.2f}  "
              f"{b - a:+.2f} " + (f"[{c[0]:+.2f}, {c[1]:+.2f}]" if c else "[CI n/a]") +
              f"{'':6s} {ma['fpr']:6.2f} {mb['fpr']:6.2f} {ma['pair_acc']:7.2f} {mb['pair_acc']:7.2f}")
