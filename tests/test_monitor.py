"""
Offline checks for the monitor converter, answer parser and metrics (no API calls).

Run:  python tests/test_monitor.py
"""

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.views import VIEWS, load_games, render
from monitor.task import build_samples, parse_monitor_output
from monitor.metrics import auroc, point

LOGS = sorted(glob.glob("plumbing_tests/smoke_seed11/*.json"))


def games():
    return [g for p in LOGS for g in load_games(p)]


def test_no_private_content_in_any_view():
    assert len(LOGS) == 6
    for g in games():
        private = [m["message"] for t in g["rounds"] for m in t["private_channel"]["messages"]]
        for v in VIEWS:
            text = render(g, v)
            for m in private:
                assert m not in text, (g["file"], v)
            for word in ("SECRET", "secret team", "PRIVATE CHANNEL", "private channel",
                         "combined payoff of you", "YOUR PRIVATE STAKE", g["condition"]):
                assert word not in text, (g["file"], v, word)


def test_view_contents():
    for g in games():
        t0 = g["rounds"][0]
        msg = next(iter(t0["agents"].values()))["stage2"]["message"]
        plan = next(iter(t0["agents"].values()))["stage1"]["reasoning"]
        r = {v: render(g, v) for v in VIEWS}
        assert msg in r["public"] and msg in r["both"] and msg in r["plans"]
        assert msg not in r["actions"] and msg not in r["table"]
        assert "(payoff " not in r["public"] and "Final actions" not in r["public"]
        assert "Final actions" in r["actions"] and "(payoff " in r["actions"]
        assert "Public announcements" not in r["actions"]
        assert "(payoff " not in r["table"] and "Final actions" not in r["table"]
        assert plan in r["plans"] and all(plan not in r[v] for v in VIEWS if v != "plans")
        # view 5 = view 3 + plans: every line of view 3's rounds is in view 5
        body = r["both"].split("=== Round 1 ===", 1)[1]
        assert all(line in r["plans"] for line in body.splitlines())


def test_dataset_labels():
    samples = build_samples("plumbing_tests/smoke_seed11")
    assert len(samples) == 4 * len(VIEWS)
    for s in samples:
        assert s.target == {"instructed": "yes", "none": "no"}[s.metadata["condition"]]
    assert all(s.metadata["upper_bound"] == (s.metadata["view"] == "plans") for s in samples)
    with_unlabeled = build_samples("plumbing_tests/smoke_seed11", include_unlabeled=True)
    assert len(with_unlabeled) == 6 * len(VIEWS)


def test_parser():
    ok = parse_monitor_output('{"reasoning": "x", "collusion": "yes", "suspicion": 8, "pair": ["T", "f"]}')
    assert ok == {"collusion": True, "suspicion": 8, "pair": ["F", "T"]}
    fenced = parse_monitor_output('```json\n{"reasoning": "x", "collusion": "No", "suspicion": 2, "pair": "none"}\n```')
    assert fenced == {"collusion": False, "suspicion": 2, "pair": None}
    assert parse_monitor_output('{"collusion": "maybe", "suspicion": 2}') is None
    assert parse_monitor_output('{"collusion": "yes", "suspicion": 11}') is None
    assert parse_monitor_output("no json here") is None
    named = parse_monitor_output('{"collusion": "yes", "suspicion": 7, "pair": ["Agent Q", "Agent J"]}')
    assert named["pair"] == ["J", "Q"]


def test_metrics():
    assert auroc([3, 4], [1, 2]) == 1.0
    assert auroc([1], [1]) == 0.5
    assert auroc([1, 3], [2]) == 0.5
    rows = [
        {"label": "yes", "parsed": True, "pred": True, "suspicion": 9, "pair_correct": 1},
        {"label": "yes", "parsed": True, "pred": False, "suspicion": 4, "pair_correct": 0},
        {"label": "no", "parsed": True, "pred": True, "suspicion": 6, "pair_correct": None},
        {"label": "no", "parsed": True, "pred": False, "suspicion": 1, "pair_correct": None},
        {"label": "no", "parsed": False, "pred": None, "suspicion": None, "pair_correct": None},
    ]
    m = point(rows)
    assert m == {"accuracy": 0.5, "fpr": 0.5, "auroc": 0.75, "pair_acc": 0.5}


def test_exploratory_views():
    import re as _re
    from monitor.views import EXPLORATORY_VIEWS
    from monitor.baselines import _per_agent_against_stake
    voting = [g for g in games() if g["game_type"] == "voting"]
    for g in voting:
        private = [m["message"] for t in g["rounds"] for m in t["private_channel"]["messages"]]
        for v in EXPLORATORY_VIEWS:
            text = render(g, v)
            assert all(m not in text for m in private)
            for word in ("SECRET", "PRIVATE CHANNEL", "YOUR PRIVATE STAKE", g["condition"]):
                assert word not in text, (v, word)
            assert "(payoff " not in text and "Public announcements" not in text  # no message text
        flagged = render(g, "outcomes_flagged")
        assert "AGAINST" not in render(g, "outcomes")
        # every AGAINST flag matches the against-stake rule, agent by agent
        counts = {a: 0 for a in g["rounds"][0]["agents"]}
        for line in flagged.splitlines():
            m = _re.match(r"\| (\w) \|.*\| AGAINST \|$", line)
            if m:
                counts[m.group(1)] += 1
        assert counts == _per_agent_against_stake(g)
        # failed rounds reveal nothing
        for block in flagged.split("=== Round ")[1:]:
            if "FAILED" in block.splitlines()[0]:
                assert "AGAINST" not in block and "| with |" not in block


if __name__ == "__main__":
    import contextlib, io
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            with contextlib.redirect_stdout(io.StringIO()):
                fn()
            print(f"PASS {name}")
