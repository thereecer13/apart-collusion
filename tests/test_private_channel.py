"""
Offline checks for the private channel (no API calls; a stub client returns canned answers).

Run:  python tests/test_private_channel.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# settings.py requires a key to exist; the stub client never sends anything.
os.environ.setdefault("OPENROUTER_API_KEY", "offline-test")

from src.endogenous.core.trial_runner import run_all_trials
from src.endogenous.core.private_channel import choose_pair

AGENTS = ["F", "G", "J", "M", "Q", "T", "Z"]
MODEL = "meta-llama/llama-3.3-70b-instruct"


class StubLLM:
    model = MODEL
    temperature = 1.0


class StubParallel:
    """Records every request and returns a canned response by request type."""

    def __init__(self):
        self.requests = []

    def execute_parallel(self, reqs):
        out = {}
        for r in reqs:
            self.requests.append(r)
            cid = r["custom_id"]
            if "_s1_" in cid:
                out[cid] = {"intended_action": "GO", "reasoning": "plan"}
            elif "_s2_" in cid:
                out[cid] = {"stated_action": "GO", "message": "public msg"}
            elif "_s3_" in cid:
                out[cid] = {"choice": "STAY", "reasoning": "final"}
            elif "_pm" in cid:
                out[cid] = {"message": f"SECRET<{cid}>"}
            elif "_refl_" in cid:
                out[cid] = {"score": 3, "assessment": "ok"}
            elif "_judge_" in cid:
                out[cid] = {"primary_label": "Honest Consistency", "confidence": 3}
        return out


def run(condition, n_trials=2, n_rounds=2, exchanges=1, seed=7, run_judge=True):
    client = StubParallel()
    rounds = run_all_trials(
        game_type="elfarol", agent_names=AGENTS, game_params={"threshold": 0.5},
        llm_client=StubLLM(), parallel_client=client,
        n_trials=n_trials, n_rounds=n_rounds, round_robin=True, show_progress=False,
        private_channel=condition, private_exchanges=exchanges, seed=seed,
        run_judge=run_judge,
    )
    return rounds, client.requests


def agent_of(req):
    """Which agent a request is for (the focal agent), from its custom_id."""
    cid = req["custom_id"]
    if "_refl_" in cid:
        return cid.split("_refl_")[1].split("_about_")[0]
    return cid.rsplit("_", 1)[1]


def text(req):
    return req["messages"][0]["content"] + "\n" + req["messages"][1]["content"]


def test_off_is_unchanged():
    # No channel arguments at all vs. explicitly off: identical requests.
    _, reqs_default = run(None)
    client = StubParallel()
    run_all_trials(
        game_type="elfarol", agent_names=AGENTS, game_params={"threshold": 0.5},
        llm_client=StubLLM(), parallel_client=client,
        n_trials=2, n_rounds=2, round_robin=True, show_progress=False,
    )
    assert reqs_default == client.requests
    assert not any("_pm" in r["custom_id"] for r in reqs_default)


def test_none_condition_records_pair_but_changes_nothing():
    rounds, reqs = run("none")
    _, reqs_off = run(None)
    assert reqs == reqs_off  # no prompt changes, no private calls
    for r in rounds:
        for t in r["trials"]:
            pc = t["private_channel"]
            assert pc["condition"] == "none"
            assert pc["pair"] == choose_pair(7, t["trial_id"], AGENTS)
            assert pc["messages"] == []


def check_visibility(condition, exchanges=1):
    n_rounds = 3
    rounds, reqs = run(condition, n_rounds=n_rounds, exchanges=exchanges)
    for tid in range(2):
        pair = choose_pair(7, tid, AGENTS)
        trial_reqs = [r for r in reqs if r["custom_id"].startswith(f"t{tid}_")]

        # Private calls: 2 per exchange per round, A then B alternating
        pm = [r for r in trial_reqs if "_pm" in r["custom_id"]]
        assert len(pm) == 2 * exchanges * n_rounds
        assert [agent_of(r) for r in pm] == [pair[0], pair[1]] * (exchanges * n_rounds)

        for r in trial_reqs:
            if "SECRET<" in text(r):
                assert agent_of(r) in pair, f"leak to {agent_of(r)} in {r['custom_id']}"
            if agent_of(r) not in pair:
                assert "SECRET" not in text(r) and "secret team" not in text(r).lower()
                assert "PRIVATE CHANNEL" not in text(r)

        # Pair members see this round's messages in Stage 2, Stage 3 and reflection
        for r in trial_reqs:
            if agent_of(r) in pair and any(s in r["custom_id"] for s in ("_s2_", "_s3_", "_refl_")):
                assert "SECRET<" in text(r), r["custom_id"]

        # Log: messages stored per round with sender/receiver, separate from public msgs
        for rd in rounds:
            t = rd["trials"][tid]
            msgs = t["private_channel"]["messages"]
            assert len(msgs) == 2 * exchanges
            for m in msgs:
                assert m["round"] == rd["round_id"]
                assert {m["sender"], m["receiver"]} == set(pair)
            assert all("SECRET" not in a["stage2"]["message"] for a in t["agents"].values())
    return rounds, reqs


def test_instructed():
    rounds, reqs = check_visibility("instructed")
    pair = choose_pair(7, 0, AGENTS)
    s1 = [r for r in reqs if r["custom_id"] == f"t0_s1_{pair[0]}"]
    # Round 1 planning: note but no messages yet; round 2+ planning: earlier messages
    assert "SECRET TEAM" in s1[0]["messages"][0]["content"]
    assert "(no private messages yet)" in s1[0]["messages"][1]["content"]
    assert "SECRET<" in s1[1]["messages"][1]["content"]
    # Own-payoff goal lines are replaced by the team goal in every pair system prompt
    for r in reqs:
        if r["custom_id"].startswith("t0_") and agent_of(r) in pair and "_judge_" not in r["custom_id"]:
            sys_p = r["messages"][0]["content"]
            assert "maximize your final payout" not in sys_p, r["custom_id"]
            assert "maximize your outcome" not in sys_p, r["custom_id"]
            assert "combined payoff of you and Agent" in sys_p


def test_channel_only():
    _, reqs = check_visibility("channel_only")
    assert not any("SECRET TEAM" in text(r) for r in reqs)
    assert not any("combined payoff" in text(r) for r in reqs)


def test_multiple_exchanges():
    check_visibility("instructed", exchanges=2)


def test_no_judge():
    rounds, reqs = run("instructed", run_judge=False)
    _, reqs_judged = run("instructed")
    assert not any("_judge_" in r["custom_id"] for r in reqs)
    # Everything except the judge calls is unchanged
    assert reqs == [r for r in reqs_judged if "_judge_" not in r["custom_id"]]
    for rd in rounds:
        for t in rd["trials"]:
            for a in t["agents"].values():
                assert a["judge"] == {"skipped": True, "_parse_ok": False}


def test_pair_is_seeded():
    assert choose_pair(7, 0, AGENTS) == choose_pair(7, 0, AGENTS)
    pairs = {tuple(choose_pair(s, t, AGENTS)) for s in range(5) for t in range(5)}
    assert len(pairs) > 5


if __name__ == "__main__":
    import contextlib, io
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            with contextlib.redirect_stdout(io.StringIO()):
                fn()
            print(f"PASS {name}")
