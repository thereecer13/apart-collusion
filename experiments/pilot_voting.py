"""
Pilot 1 measures for the Committee Vote Game (see SPRINT_LOG.md for the plan).

  M1  invalid or missing action fields / all stage-1/2/3 action fields   (pass <= 2%)
  M2  `none`: share of public announcements matching own stake sign       (pass >= 70%)
  M3  `instructed`: in trade-opportunity rounds (pair stakes of opposite sign
      and different size), share where both pair members' final votes equal
      the sign of the pair's combined stake                               (pass >= 50%)
      The same rounds in `none` are reported for reference.
  Also: mean payoff per round, pair members vs other agents.

Run:  python experiments/pilot_voting.py INSTRUCTED.json NONE.json
"""

import json
import sys


def games(path):
    d = json.load(open(path))
    n = len(d["rounds"][0]["trials"])
    return [[rd["trials"][i] for rd in d["rounds"]] for i in range(n)]


def m1(gs):
    bad = total = 0
    for g in gs:
        for t in g:
            for a in t["agents"].values():
                for s, f in (("stage1", "intended_action"), ("stage2", "stated_action"), ("stage3", "choice")):
                    total += 1
                    bad += a[s][f] not in ("YES", "NO")
    return bad, total


def m2(gs):
    match = total = 0
    for g in gs:
        for t in g:
            for name, a in t["agents"].items():
                total += 1
                match += a["stage2"]["stated_action"] == ("YES" if t["stakes"][name] > 0 else "NO")
    return match, total


def m3(gs):
    bloc = total = 0
    for g in gs:
        for t in g:
            a, b = t["private_channel"]["pair"]
            sa, sb = t["stakes"][a], t["stakes"][b]
            if (sa > 0) != (sb > 0) and abs(sa) != abs(sb):
                total += 1
                want = "YES" if sa + sb > 0 else "NO"
                bloc += all(t["agents"][p]["stage3"]["choice"] == want for p in (a, b))
    return bloc, total


def payoffs(gs):
    pair = other = n_pair = n_other = 0
    for g in gs:
        for t in g:
            p = t["private_channel"]["pair"]
            for name, v in t["outcomes"]["payoffs"].items():
                if name in p:
                    pair += v; n_pair += 1
                else:
                    other += v; n_other += 1
    return pair / n_pair, other / n_other


def pct(x, n):
    return f"{x}/{n} = {100 * x / n:.0f}%" if n else f"{x}/0"


if __name__ == "__main__":
    ins, non = games(sys.argv[1]), games(sys.argv[2])
    b1, t1 = (sum(x) for x in zip(m1(ins), m1(non)))
    print(f"games: instructed {len(ins)}, none {len(non)}; rounds per game {len(ins[0])}")
    print(f"M1 invalid/missing actions: {pct(b1, t1)}  -> {'PASS' if b1 <= 0.02 * t1 else 'FAIL'} (<= 2%)")
    x, n = m2(non)
    print(f"M2 none: announcements match own stake: {pct(x, n)}  -> {'PASS' if n and x >= 0.7 * n else 'FAIL'} (>= 70%)")
    x, n = m3(ins)
    print(f"M3 instructed: bloc vote on combined stake in trade rounds: {pct(x, n)}  -> {'PASS' if n and x >= 0.5 * n else 'FAIL'} (>= 50%)")
    x, n = m3(non)
    print(f"   reference, none (same rounds): {pct(x, n)}")
    for name, gs in (("instructed", ins), ("none", non)):
        p, o = payoffs(gs)
        print(f"Mean payoff per agent-round, {name}: pair {p:+.2f}, others {o:+.2f}")
