"""
Offline check that experiments/check_plumbing.py handles multi-game logs (stub, no API calls).

Run:  python tests/test_check_plumbing.py
"""

import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "experiments"))
os.environ.setdefault("OPENROUTER_API_KEY", "offline-test")

import test_voting as V
import check_plumbing as C


class UniqueStub(V.SincereStub):
    """Private messages unique per call (custom_ids repeat every round)."""
    n = 0

    def execute_parallel(self, reqs):
        out = super().execute_parallel(reqs)
        for r in reqs:
            if "_pm" in r["custom_id"]:
                UniqueStub.n += 1
                out[r["custom_id"]] = {"message": f"SECRET<{r['custom_id']}#{UniqueStub.n}>"}
        return out


def make_run(tmp, leak_into=None, note_into=None, history="full", stale_into=None):
    client = UniqueStub()
    with contextlib.redirect_stdout(io.StringIO()):
        rounds = V.run_all_trials(
            game_type="voting", agent_names=V.AGENTS, game_params={},
            llm_client=V.StubLLM(), parallel_client=client, n_trials=2, n_rounds=3,
            round_robin=True, show_progress=False, private_channel="instructed", seed=7,
            run_judge=False, private_history=history,
        )
    reqs = client.requests
    if leak_into:
        secret = rounds[0]["trials"][1]["private_channel"]["messages"][0]["message"]
        for r in reqs:
            if r["custom_id"] == leak_into:
                r["messages"][1]["content"] += secret
                break
    if stale_into:  # (custom_id, occurrence): put round-1 message of game 0 into a later prompt
        secret = rounds[0]["trials"][0]["private_channel"]["messages"][0]["message"]
        hits = [r for r in reqs if r["custom_id"] == stale_into[0]]
        hits[stale_into[1]]["messages"][1]["content"] += f'\n  Agent X -> Agent Y: "{secret}"'
    if note_into:
        for r in reqs:
            if r["custom_id"] == note_into:
                r["messages"][0]["content"] += "\n\nSECRET TEAM: planted"
                break
    res, dump = os.path.join(tmp, "res.json"), os.path.join(tmp, "dump.jsonl")
    json.dump({"metadata": {"game_type": "voting"}, "rounds": rounds}, open(res, "w"))
    with open(dump, "w") as f:
        for r in reqs:
            f.write(json.dumps({"request": r, "response": None}) + "\n")
    return res, dump


def test_multi_game_pass():
    with tempfile.TemporaryDirectory() as tmp:
        out = C.check(*make_run(tmp))
        assert [o[0] for o in out] == [0, 1]
        assert all(not o[5] and not o[6] for o in out), out


def test_leak_in_second_game_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        from src.endogenous.core.private_channel import choose_pair
        outsider = next(a for a in V.AGENTS if a not in choose_pair(7, 1, V.AGENTS))
        out = C.check(*make_run(tmp, leak_into=f"t1_s3_{outsider}"))
        assert not out[0][5]
        assert any("LEAK" in f for f in out[1][5]), out[1][5]


def test_team_note_in_wrong_system_prompt_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        from src.endogenous.core.private_channel import choose_pair
        outsider = next(a for a in V.AGENTS if a not in choose_pair(7, 0, V.AGENTS))
        out = C.check(*make_run(tmp, note_into=f"t0_s2_{outsider}"))
        assert any("SECRET TEAM note wrong" in f for f in out[0][5]) and not out[1][5]


def test_current_history_pass_and_stale_message_caught():
    from src.endogenous.core.private_channel import choose_pair
    a = choose_pair(7, 0, V.AGENTS)[0]
    with tempfile.TemporaryDirectory() as tmp:
        out = C.check(*make_run(tmp, history="current"))
        assert all(not o[5] for o in out), [o[5] for o in out]
    with tempfile.TemporaryDirectory() as tmp:
        out = C.check(*make_run(tmp, history="current", stale_into=(f"t0_s3_{a}", 2)))
        assert any("shows earlier r1 message" in f for f in out[0][5]), out[0][5]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
