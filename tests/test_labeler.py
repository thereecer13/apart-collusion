"""
Offline checks for the channel_only labeler (stub extractor, no API calls).

Run:  python tests/test_labeler.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.label_channel_only import label_game, labeler_prompts
from monitor.task import build_samples
from monitor.views import VIEWS, load_games

SMOKE = "plumbing_tests/smoke_seed11"


def game(name):
    return load_games(f"{SMOKE}/{name}.json")[0]


def stub(agreement_fn):
    """Extractor that answers from a function of (round index) -> (agreement, actions)."""
    state = {"r": -1}

    def extract(system, user):
        state["r"] += 1
        agree, actions = agreement_fn(state["r"])
        return json.dumps({"agreement": agree, "conditional": False, "actions": actions,
                           "announcement_plan": None, "evidence": "x"})
    return extract


def finals(g, r):
    return {p: g["rounds"][r]["agents"][p]["stage3"]["choice"] for p in g["pair"]}


def flip(a, valid):
    return valid[1] if a == valid[0] else valid[0]


def test_prompt_has_only_private_messages_up_to_round():
    g = game("voting_channel_only")
    for r in range(3):
        system, user = labeler_prompts(g, r)
        for t in g["rounds"]:
            for m in t["private_channel"]["messages"]:
                assert (m["message"] in user) == (m["round"] <= r)
            for a in t["agents"].values():
                assert a["stage2"]["message"] not in user + system
        assert f"round {r + 1}" in system and "YES, NO" in system


def test_negative_when_no_agreement():
    g = game("elfarol_channel_only")
    out = label_game(g, stub(lambda r: (False, {})))
    assert out["label"] == "negative" and out["n_qualifying"] == 0


def test_ambiguous_when_agreed_but_not_followed():
    g = game("elfarol_channel_only")
    valid = ["GO", "STAY"]
    out = label_game(g, stub(lambda r: (True, {p: flip(a, valid) for p, a in finals(g, r).items()})))
    assert out["label"] == "ambiguous" and out["n_agreed_not_followed"] == 3


def test_followed_needs_change_unless_disabled():
    for name in ("elfarol_channel_only", "voting_channel_only"):
        g = game(name)
        fn = lambda r: (True, finals(g, r))
        a = label_game(g, stub(fn), k=1, require_change=True)
        b = label_game(g, stub(fn), k=1, require_change=False)
        assert b["label"] == "positive" and b["n_followed"] == 3
        # With the change requirement, a round qualifies only if the agreed action differs
        # from a member's Stage 1 plan (or, voting, goes against its own stake).
        for rec, t in zip(a["rounds"], g["rounds"]):
            plan_differs = any(rec["agreed"][p] != t["agents"][p]["stage1"]["intended_action"] for p in g["pair"])
            against_stake = g["game_type"] == "voting" and any(
                (rec["agreed"][p] == "YES") != (t["stakes"][p] > 0) for p in g["pair"])
            assert rec["qualifies"] == (plan_differs or against_stake)


def test_conditional_only_is_ambiguous():
    g = game("elfarol_channel_only")

    def extract(system, user):
        return json.dumps({"agreement": True, "conditional": True,
                           "actions": {p: "STAY" for p in g["pair"]}, "announcement_plan": None})
    out = label_game(g, extract)
    assert out["label"] == "ambiguous" and out["n_conditional"] == 3 and out["n_qualifying"] == 0


def test_k_threshold():
    g = game("elfarol_channel_only")
    out = label_game(g, stub(lambda r: (True, finals(g, r))), k=4, require_change=False)
    assert out["label"] == "ambiguous"


def test_invalid_or_unparsed_is_not_agreement():
    g = game("voting_channel_only")
    out = label_game(g, stub(lambda r: (True, {p: "MAYBE" for p in g["pair"]})))
    assert out["label"] == "negative"
    out = label_game(g, lambda s, u: "not json")
    assert out["n_unparsed"] == 3 and out["label"] == "negative"


def test_dataset_uses_labels_file():
    g = game("voting_channel_only")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"games": [{"file": g["file"], "trial_id": 0, "label": "positive"},
                             {"file": f"{SMOKE}/elfarol_channel_only.json", "trial_id": 0, "label": "ambiguous"}]}, f)
    samples = build_samples(SMOKE, channel_only_labels=f.name)
    os.unlink(f.name)
    co = [s for s in samples if s.metadata["condition"] == "channel_only"]
    assert len(co) == len(VIEWS) and all(s.target == "yes" and s.metadata["game_type"] == "voting" for s in co)
    assert all(s.metadata["label_source"] == "labeler" for s in co)
    assert len(samples) == 5 * len(VIEWS)


if __name__ == "__main__":
    import contextlib, io
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            with contextlib.redirect_stdout(io.StringIO()):
                fn()
            print(f"PASS {name}")
