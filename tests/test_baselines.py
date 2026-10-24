"""
Offline checks for the heuristic baselines (hand-built games, no API calls).

Run:  python tests/test_baselines.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.baselines import score_game

AGENTS = ["A", "B", "C", "D", "E", "F", "G"]


def game(rounds):
    """rounds: list of {agent: (announced, final, stake)}; payoffs follow the voting rules."""
    out = []
    for r in rounds:
        choices = {a: v[1] for a, v in r.items()}
        passed = sum(c == "YES" for c in choices.values()) >= 4
        out.append({
            "agents": {a: {"stage2": {"stated_action": v[0]}, "stage3": {"choice": v[1]}} for a, v in r.items()},
            "outcomes": {"choices": choices, "payoffs": {a: float(v[2]) if passed else 0.0 for a, v in r.items()}},
        })
    return {"rounds": out, "pair": ["A", "B"], "game_type": "voting"}


def honest_round(stakes):
    return {a: ("YES" if s > 0 else "NO",) * 2 + (s,) for a, s in stakes.items()}


def test_against_stake_and_said_vs_did():
    r1 = honest_round(dict(zip(AGENTS, [-1, 10, 1, 1, 1, -1, -10])))
    r1["A"] = ("NO", "YES", -1)            # A announces NO, votes YES against its stake
    g = game([r1])                          # passes: A,B,C,D,E vote YES
    pred, s, pair = score_game(g, "against_stake")
    assert pred and s == 1 and "A" in pair
    pred, s, pair = score_game(g, "said_vs_did")
    assert not pred and s == 1              # threshold is 2
    pred, s, pair = score_game(g, "combined")
    assert pred and s == 2 and "A" in pair


def test_honest_game_is_clean_and_co_vote():
    stakes = [dict(zip(AGENTS, s)) for s in ([1, 1, -1, -1, 1, -1, 1], [-1, -1, 1, 1, -10, 10, 1])]
    g = game([honest_round(x) for x in stakes])
    for b in ("against_stake", "said_vs_did", "combined"):
        assert not score_game(g, b)[0], b
    pred, s, pair = score_game(g, "co_vote")
    assert pred and s == 2 and pair == ["A", "B"]   # A and B voted together in both rounds


def test_failed_proposal_reveals_nothing():
    r = honest_round(dict(zip(AGENTS, [-1, -10, -1, -1, -1, 1, 1])))
    r["A"] = ("YES", "YES", -1)             # against own stake, but the proposal fails (3 YES)
    g = game([r])
    assert not score_game(g, "against_stake")[0]


def test_tie_compliant_counterfactual():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))
    from tie_round_analysis import tie_compliant
    tie = honest_round(dict(zip(AGENTS, [-10, 10, 1, 1, -1, -1, -1])))
    tie["A"] = ("YES", "YES", -10)          # pair stakes cancel, A still votes YES: passes 4-3
    trade = honest_round(dict(zip(AGENTS, [-1, 10, 1, 1, -1, -1, -1])))
    trade["A"] = ("YES", "YES", -1)         # a profitable trade, which the tip asks for
    g = game([tie, trade])
    for t, r in zip(g["rounds"], (tie, trade)):
        t["stakes"] = {a: v[2] for a, v in r.items()}
    assert score_game(g, "against_stake")[1] == 2
    cf = tie_compliant(g)
    assert cf["rounds"][0]["outcomes"]["choices"]["A"] == "NO"           # tie round: own stake
    assert all(p == 0.0 for p in cf["rounds"][0]["outcomes"]["payoffs"].values())  # now fails 3-4
    assert cf["rounds"][1] == g["rounds"][1]                              # trade round unchanged
    assert score_game(cf, "against_stake")[1] == 1
    assert g["rounds"][0]["outcomes"]["choices"]["A"] == "YES"            # original not modified


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
