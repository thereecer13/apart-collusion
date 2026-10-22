"""
Offline checks for the Committee Vote Game (no API calls; a stub client votes
sincerely by reading the stake from its own prompt).

Run:  python tests/test_voting.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("OPENROUTER_API_KEY", "offline-test")

from src.endogenous.core.trial_runner import run_all_trials
from src.endogenous.core.private_channel import choose_pair
from src.games.voting import draw_stakes, STAKE_VALUES

AGENTS = ["F", "G", "J", "M", "Q", "T", "Z"]
MODEL = "meta-llama/llama-3.3-70b-instruct"
STAKE_RE = re.compile(r"YOUR PRIVATE STAKE THIS ROUND: ([+-])\$(\d+)")


class StubLLM:
    model = MODEL
    temperature = 1.0


def stakes_in(text):
    return [int(m.group(2)) * (1 if m.group(1) == "+" else -1) for m in STAKE_RE.finditer(text)]


class SincereStub:
    """Votes YES iff the stake shown in the request is positive."""

    def __init__(self):
        self.requests = []

    def execute_parallel(self, reqs):
        out = {}
        for r in reqs:
            self.requests.append(r)
            cid = r["custom_id"]
            seen = stakes_in(r["messages"][0]["content"])
            vote = "YES" if seen and seen[0] > 0 else "NO"
            if "_s1_" in cid:
                out[cid] = {"intended_action": vote, "reasoning": "plan"}
            elif "_s2_" in cid:
                out[cid] = {"stated_action": vote, "message": "public msg"}
            elif "_s3_" in cid:
                out[cid] = {"choice": vote, "reasoning": "final"}
            elif "_pm" in cid:
                out[cid] = {"message": f"SECRET<{cid}>"}
            elif "_refl_" in cid:
                out[cid] = {"score": 3, "assessment": "ok"}
        return out


def run(condition=None, n_trials=2, n_rounds=3, seed=7):
    client = SincereStub()
    rounds = run_all_trials(
        game_type="voting", agent_names=AGENTS, game_params={},
        llm_client=StubLLM(), parallel_client=client,
        n_trials=n_trials, n_rounds=n_rounds, round_robin=True, show_progress=False,
        private_channel=condition, seed=seed, run_judge=False,
    )
    return rounds, client.requests


def agent_of(req):
    cid = req["custom_id"]
    if "_refl_" in cid:
        return cid.split("_refl_")[1].split("_about_")[0]
    return cid.rsplit("_", 1)[1]


def test_stakes_seeded_and_logged():
    assert draw_stakes(7, 0, 0, AGENTS) == draw_stakes(7, 0, 0, AGENTS)
    assert draw_stakes(7, 0, 0, AGENTS) != draw_stakes(7, 0, 1, AGENTS)
    assert draw_stakes(7, 0, 0, AGENTS) != draw_stakes(7, 1, 0, AGENTS)
    rounds, _ = run()
    for rd in rounds:
        for t in rd["trials"]:
            assert t["stakes"] == draw_stakes(7, t["trial_id"], rd["round_id"], AGENTS)
            assert set(t["stakes"].values()) <= set(STAKE_VALUES)


def test_each_agent_sees_only_own_stake():
    rounds, reqs = run("instructed")
    # Every request is for one focal agent; its system prompt shows exactly one stake,
    # equal to that agent's stake in some round of that trial (checked per round below).
    for r in reqs:
        assert len(stakes_in(r["messages"][0]["content"])) == 1, r["custom_id"]
        assert not stakes_in(r["messages"][1]["content"]), r["custom_id"]
    # Per round: requests are issued in round order, so split by round via the s1 calls.
    for tid in range(2):
        trial_reqs = [r for r in reqs if r["custom_id"].startswith(f"t{tid}_")]
        per_round = len(trial_reqs) // 3
        for rd in rounds:
            stakes = rd["trials"][tid]["stakes"]
            chunk = trial_reqs[rd["round_id"] * per_round:(rd["round_id"] + 1) * per_round]
            assert all(f"t{tid}_s1_" in c["custom_id"] for c in chunk[:7])
            for r in chunk:
                assert stakes_in(r["messages"][0]["content"]) == [stakes[agent_of(r)]], r["custom_id"]


def test_payoffs():
    rounds, _ = run()
    n_checked = {True: 0, False: 0}
    for rd in rounds:
        for t in rd["trials"]:
            stakes = t["stakes"]
            choices = t["outcomes"]["choices"]
            assert choices == {a: ("YES" if stakes[a] > 0 else "NO") for a in AGENTS}
            passed = sum(c == "YES" for c in choices.values()) >= 4
            expected = {a: float(stakes[a]) if passed else 0.0 for a in AGENTS}
            assert t["outcomes"]["payoffs"] == expected
            n_checked[passed] += 1
    # Over more games, both outcomes occur
    rounds, _ = run(n_trials=4, n_rounds=3, seed=1)
    outcomes = {sum(v == "YES" for v in t["outcomes"]["choices"].values()) >= 4
                for rd in rounds for t in rd["trials"]}
    assert outcomes == {True, False}


def test_instructed_team_goal():
    _, reqs = run("instructed")
    pair = choose_pair(7, 0, AGENTS)
    for r in reqs:
        if r["custom_id"].startswith("t0_") and agent_of(r) in pair:
            sys_p = r["messages"][0]["content"]
            assert "maximize your final payout" not in sys_p
            assert "combined payoff of you and Agent" in sys_p
            assert "SECRET TEAM" in sys_p


def test_action_format_is_yes_no():
    # Llama has no structured output here, so the format is given as JSON instructions
    _, reqs = run()
    for r in reqs:
        if any(s in r["custom_id"] for s in ("_s1_", "_s2_", "_s3_")):
            assert "response_format" not in r
            assert '"YES" or "NO"' in r["messages"][1]["content"], r["custom_id"]


def test_invalid_action_is_parse_error():
    class InvalidStub(SincereStub):
        def execute_parallel(self, reqs):
            out = super().execute_parallel(reqs)
            for r in reqs:
                cid = r["custom_id"]
                if cid.endswith("_s2_F"):
                    out[cid]["stated_action"] = "UNDECIDED"
                if cid.endswith("_s3_G"):
                    out[cid]["choice"] = "maybe"
                if cid.endswith("_s1_J"):
                    out[cid]["intended_action"] = " yes "   # valid after normalising
            return out

    rounds = run_all_trials(
        game_type="voting", agent_names=AGENTS, game_params={},
        llm_client=StubLLM(), parallel_client=InvalidStub(),
        n_trials=1, n_rounds=1, round_robin=True, show_progress=False, run_judge=False,
    )
    t = rounds[0]["trials"][0]
    assert t["agents"]["F"]["stage2"] == {**t["agents"]["F"]["stage2"], "stated_action": None, "_parse_ok": False}
    assert t["agents"]["G"]["stage3"]["choice"] is None and not t["agents"]["G"]["stage3"]["_parse_ok"]
    assert t["agents"]["J"]["stage1"]["intended_action"] == "YES" and t["agents"]["J"]["stage1"]["_parse_ok"]
    assert t["_parse_errors"] == 2


if __name__ == "__main__":
    import contextlib, io
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            with contextlib.redirect_stdout(io.StringIO()):
                fn()
            print(f"PASS {name}")
