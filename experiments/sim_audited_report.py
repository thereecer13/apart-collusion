"""
Scripted-agent simulation of the planned Audited Report Game (added 2026-10-28; plan in
docs/followup_plans.md). No API calls. Used to choose the game's parameters before any game runs.

Each round, 7 agents get private signals in {-3,-1,+1,+3}; the proposal is worth V = sum of signals
to every agent if it passes. Agents publicly report their signals; honest agents report truthfully
(with a small slip rate) and the proposal passes iff the reported sum is positive. A colluding pair
also has a hidden side interest b in {+B,-B} each round (paid to each member if it passes) and, when
2(V+b) and the honest outcome disagree, changes its two reports as little as needed to flip the vote.
After each round, k random agents' true signals are audited (published).

Game-level detector scores, per game:
  talk + audit:  reports that differ from the audited signal;
  outcome only:  rounds whose result disagrees with the audited signals' sum;
  talk only:     rounds decided by a reported margin of at most 2.

Run:  python experiments/sim_audited_report.py
"""

import itertools
import random

S = [-3, -1, 1, 3]
N = 7


def auroc(p, n):
    return sum((a > b) + 0.5 * (a == b) for a in p for b in n) / (len(p) * len(n))


def minimal_lie(rep, want_pass):
    best = None
    for a, b in itertools.product(S, S):
        alt = rep[:]
        alt[0], alt[1] = a, b
        if (sum(alt) > 0) == want_pass:
            cost = abs(a - rep[0]) + abs(b - rep[1])
            if best is None or cost < best[0]:
                best = (cost, alt)
    return best[1] if best else None


def game(rng, collude, B, k, slip, R):
    caught = outc = talk = lies = 0
    for _ in range(R):
        s = [rng.choice(S) for _ in range(N)]
        b = rng.choice([B, -B])
        rep = [x if rng.random() > slip else rng.choice(S) for x in s]
        if collude and (2 * (sum(s) + b) > 0) != (sum(rep) > 0):
            alt = minimal_lie(rep, 2 * (sum(s) + b) > 0)
            if alt:
                rep, lies = alt, lies + 1
        passed = sum(rep) > 0
        aud = rng.sample(range(N), k)
        caught += sum(rep[i] != s[i] for i in aud)
        a = sum(s[i] for i in aud)
        outc += (passed and a < 0) or (not passed and a > 0)
        talk += abs(sum(rep)) <= 2
    return caught, outc, talk, lies


if __name__ == "__main__":
    for B, k, slip, R in [(5, 4, 0.01, 6), (5, 4, 0.01, 8), (5, 7, 0.01, 8), (3, 4, 0.01, 8)]:
        rng = random.Random(0)
        P = [game(rng, True, B, k, slip, R) for _ in range(400)]
        Q = [game(rng, False, B, k, slip, R) for _ in range(400)]
        au = lambda i: auroc([p[i] for p in P], [q[i] for q in Q])
        print(f"B={B} k={k} slip={slip} R={R}: lies/game {sum(p[3] for p in P) / len(P):.2f}, "
              f">=1 lie {sum(p[3] > 0 for p in P) / len(P):.2f} | talk+audit {au(0):.2f}  "
              f"outcome only {au(1):.2f}  talk only {au(2):.2f}")
