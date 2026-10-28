"""
Paired comparison of the against_stake rule and an LLM monitor on the same games (added 2026-10-28,
SPRINT_LOG.md "Claude Haiku 5.5 as monitor"). No API calls.

For each view: AUROC of the rule's score (number of votes against revealed interest) and of the
monitor's suspicion, and the paired difference rule - monitor with a 95% bootstrap CI over games
(positives and negatives resampled separately). Only games with a parsed monitor answer are used.

Run:  python experiments/rule_vs_monitor.py EVAL_DIR LOG_DIR --positives instructed_hint --negatives none
"""

import argparse
import glob
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.baselines import score_game
from monitor.metrics import auroc, load_rows
from monitor.views import load_games

N_BOOT = 2000


def paired(P, N, seed=0):
    """P, N: lists of (rule score, monitor suspicion). Returns rule AUROC, monitor AUROC, CI of rule - monitor."""
    rng = random.Random(seed)
    au = lambda p, n, i: auroc([x[i] for x in p], [x[i] for x in n])
    diffs = []
    for _ in range(N_BOOT):
        p = [rng.choice(P) for _ in P]
        n = [rng.choice(N) for _ in N]
        diffs.append(au(p, n, 0) - au(p, n, 1))
    diffs.sort()
    return au(P, N, 0), au(P, N, 1), (diffs[int(0.025 * N_BOOT)], diffs[int(0.975 * N_BOOT)])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("eval_dir")
    ap.add_argument("log_dir")
    ap.add_argument("--positives", default="instructed_hint")
    ap.add_argument("--negatives", default="none")
    args = ap.parse_args()
    games = {}
    for path in sorted(glob.glob(os.path.join(args.log_dir, "*.json"))):
        for g in load_games(path):
            if g["game_type"] == "voting":
                games[f"voting/{os.path.basename(path)[:-5]}/t{g['trial_id']}"] = g
    rows = [r for r in load_rows(args.eval_dir) if r["parsed"] and r["game_id"] in games]
    for view in sorted({r["view"] for r in rows}):
        rs = [r for r in rows if r["view"] == view]
        P = [(score_game(games[r["game_id"]], "against_stake")[1], r["suspicion"]) for r in rs if r["condition"] == args.positives]
        N = [(score_game(games[r["game_id"]], "against_stake")[1], r["suspicion"]) for r in rs if r["condition"] == args.negatives]
        if not P or not N:
            continue
        rule, mon, (lo, hi) = paired(P, N)
        print(f"{view:9s} n={len(P)}+{len(N)}  rule {rule:.2f}  monitor {mon:.2f}  rule - monitor {rule - mon:+.2f} [{lo:+.2f}, {hi:+.2f}]")
