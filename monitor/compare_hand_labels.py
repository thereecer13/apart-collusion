"""
Compare hand labels (results/hand_labels/hand_labels_template.json, filled in) with the
labeler's per-round extractions (results/labels/channel_only_v2_labels.json).

Per round: agreement (yes/no), conditional (among agreements), and votes (among rounds both
call an unconditional agreement). Reports raw agreement and Cohen's kappa for agreement.

Run:  python monitor/compare_hand_labels.py HAND.json LABELS.json
"""

import json
import os
import sys


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


if __name__ == "__main__":
    hand = [h for h in json.load(open(sys.argv[1])) if h["agreement"] is not None]
    labels = json.load(open(sys.argv[2]))["games"]
    llm = {}
    for g in labels:
        gid = f"{os.path.basename(g['file'])[:-5]}/t{g['trial_id']}"
        for r in g["rounds"]:
            llm[(gid, r["round"])] = r["extracted"] or {}
    agree, cond, votes = [], [], []
    for h in hand:
        e = llm.get((h["game"], h["round"]))
        if e is None:
            continue
        agree.append((bool(h["agreement"]), bool(e.get("agreement"))))
        if h["agreement"] and e.get("agreement"):
            cond.append((bool(h["conditional"]), bool(e.get("conditional"))))
            if not h["conditional"] and not e.get("conditional"):
                ev = {k: str(v or "").upper() for k, v in (e.get("actions") or {}).items()}
                votes.append(all(str(v or "").upper() == ev.get(k) for k, v in h["votes"].items()))
    print(f"rounds compared: {len(agree)}")
    if agree:
        print(f"agreement: raw {sum(a == b for a, b in agree)}/{len(agree)}, kappa {kappa(agree)}")
        print(f"  hand yes {sum(a for a, _ in agree)}, labeler yes {sum(b for _, b in agree)}")
    if cond:
        print(f"conditional (both said agreement): raw {sum(a == b for a, b in cond)}/{len(cond)}")
    if votes:
        print(f"votes match (both unconditional agreement): {sum(votes)}/{len(votes)}")
