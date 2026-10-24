"""
Monitor metrics restricted to `instructed` games where collusion actually showed in actions
(at least one bloc vote in a trade-opportunity round), against all `none` games.

Run:  python experiments/monitor_on_realized.py LOG_DIR EVAL_DIR
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_voting_behaviour import load, trade_rounds
from monitor.metrics import load_rows, bootstrap, fmt

if __name__ == "__main__":
    games = load(sys.argv[1])
    realized = {f"voting/instructed_seed{s}/t{t}" for (s, t), r in games["instructed"].items()
                if trade_rounds(r)[1] > 0}
    # eval dirs can also hold channel_only games scored as hard negatives; keep only `none`
    rows = [r for r in load_rows(sys.argv[2])
            if (r["label"] == "no" and r["condition"] == "none") or r["game_id"] in realized]
    print(f"positives: {len(realized)} instructed games with >=1 bloc vote; negatives: all none games")
    res = bootstrap(rows)
    for name, m in res.items():
        if name.startswith("view="):
            print(f"{name:14s} n {m['n_pos']}/{m['n_neg']}  acc {fmt(m['accuracy']):22s} AUROC {fmt(m['auroc']):22s} "
                  f"TPR {sum(r['pred'] for r in rows if r['view'] == name[5:] and r['label'] == 'yes')}/{m['n_pos']}  "
                  f"pair {fmt(m['pair_acc'])}")
