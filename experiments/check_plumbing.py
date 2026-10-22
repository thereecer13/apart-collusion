"""
Plumbing checks for one game run with a private channel condition.

Uses the results JSON plus the --dump-requests JSONL from the same run.
Checks parsing, private-message routing and logging, condition prompts,
voting stakes, and payoffs. It does not look at behaviour.

Run:  python experiments/check_plumbing.py RESULTS.json REQUESTS.jsonl
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("OPENROUTER_API_KEY", "offline-check")

from src.games import create_game

VALID_ACTIONS = {"voting": {"YES", "NO"}, "elfarol": {"GO", "STAY"}}
STAKE_RE = re.compile(r"YOUR PRIVATE STAKE THIS ROUND: ([+-])\$(\d+)")


def focal_agent(cid):
    if "_refl_" in cid:
        return cid.split("_refl_")[1].split("_about_")[0]
    return cid.rsplit("_", 1)[1]


def stage_of(cid):
    for s in ("_s1_", "_pm", "_s2_", "_s3_", "_refl_", "_judge_"):
        if s in cid:
            return s.strip("_")
    return "?"


def load_requests(path):
    """Requests in send order, each tagged with its round (a new round starts at the first s1 after a non-s1)."""
    out, rnd, prev = [], -1, None
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            cid = rec["request"]["custom_id"]
            st = stage_of(cid)
            if st == "s1" and prev != "s1":
                rnd += 1
            prev = st
            msgs = rec["request"]["messages"]
            out.append({"cid": cid, "stage": st, "agent": focal_agent(cid), "round": rnd,
                        "system": msgs[0]["content"], "user": msgs[1]["content"]})
    return out


def check(results_path, requests_path):
    data = json.load(open(results_path))
    game_type = data["metadata"]["game_type"]
    reqs = load_requests(requests_path)
    rounds = data["rounds"]
    fails = []

    def expect(cond, msg):
        if not cond:
            fails.append(msg)

    trial0 = rounds[0]["trials"][0]
    pc0 = trial0["private_channel"]
    condition, pair = pc0["condition"], pc0["pair"]
    agents = list(trial0["agents"])
    expect(max(r["round"] for r in reqs) == len(rounds) - 1, "round count in dump != log")

    # 1. Parsing. The harness marks any non-empty action as parsed, so also check
    #    that each action is one of the game's valid values.
    valid = VALID_ACTIONS[game_type]
    fields = {"stage1": "intended_action", "stage2": "stated_action", "stage3": "choice"}
    for rd in rounds:
        t = rd["trials"][0]
        for a, ad in t["agents"].items():
            for s, field in fields.items():
                expect(ad[s]["_parse_ok"], f"r{rd['round_id']+1} {a} {s} parse failed")
                expect(ad[s][field] in valid, f"r{rd['round_id']+1} {a} {s} invalid action {ad[s][field]!r}")
            if "reflection" in ad:
                expect(ad["reflection"]["_parse_ok"], f"r{rd['round_id']+1} {a} reflection parse failed")
        for m in t["private_channel"]["messages"]:
            expect(m["_parse_ok"] and m["message"].strip(), f"r{rd['round_id']+1} private message parse failed")

    # 2. Private messages: count, routing, visibility in later prompts, separate logging
    all_msgs = [m for rd in rounds for m in rd["trials"][0]["private_channel"]["messages"]]
    n_expected = 0 if condition == "none" else 2 * pc0["n_exchanges"] * len(rounds)
    expect(len(all_msgs) == n_expected, f"{len(all_msgs)} private messages, expected {n_expected}")
    expect(all(m["sender"] in pair and m["receiver"] in pair and m["sender"] != m["receiver"]
               for m in all_msgs), "private message sender/receiver not the pair")
    pm_reqs = [r for r in reqs if r["stage"] == "pm"]
    expect(len(pm_reqs) == n_expected, "private message requests != logged messages")
    for m in all_msgs:
        text = m["message"]
        for r in reqs:
            seen = text in r["user"] or text in r["system"]
            if r["agent"] not in pair:
                expect(not seen, f"LEAK: r{m['round']+1} message from {m['sender']} in {r['cid']} round {r['round']+1}")
            else:
                later = r["round"] > m["round"] or (r["round"] == m["round"] and r["stage"] in ("s2", "s3", "refl"))
                if later:
                    expect(seen, f"pair prompt {r['cid']} round {r['round']+1} missing r{m['round']+1} message")
        public = " ".join(a["stage2"]["message"] for rd in rounds for a in rd["trials"][0]["agents"].values())
        expect(text not in public, "private message text logged in public messages")

    # 3. Condition prompts appear only where they should
    for r in reqs:
        both = r["system"] + r["user"]
        in_pair = r["agent"] in pair
        expect(("SECRET TEAM" in both) == (condition == "instructed" and in_pair), f"SECRET TEAM note wrong in {r['cid']}")
        expect(("PRIVATE CHANNEL:" in both) == (condition == "channel_only" and in_pair), f"channel note wrong in {r['cid']}")
        expect(("combined payoff" in both) == (condition == "instructed" and in_pair), f"team goal wrong in {r['cid']}")

    # 4. Voting stakes: each prompt shows exactly the focal agent's own stake for that round
    if game_type == "voting":
        for r in reqs:
            seen = [int(g) * (1 if s == "+" else -1) for s, g in STAKE_RE.findall(r["system"] + r["user"])]
            want = rounds[r["round"]]["trials"][0]["stakes"][r["agent"]]
            expect(seen == [want], f"{r['cid']} round {r['round']+1}: stakes shown {seen}, expected [{want}]")

    # 5. Payoffs, recomputed from the game class
    for rd in rounds:
        t = rd["trials"][0]
        params = {"stakes": t["stakes"]} if game_type == "voting" else {"threshold": 0.5}
        game = create_game(game_type, agents, **params)
        expect(game.evaluate(t["outcomes"]["choices"]) == t["outcomes"]["payoffs"],
               f"r{rd['round_id']+1} payoffs do not match the rules")

    return condition, pair, len(reqs), len(all_msgs), fails


if __name__ == "__main__":
    condition, pair, n_req, n_msg, fails = check(sys.argv[1], sys.argv[2])
    print(f"{os.path.basename(sys.argv[1])}: condition={condition} pair={pair} "
          f"requests={n_req} private_messages={n_msg} -> {'PASS' if not fails else 'FAIL'}")
    for f in fails[:20]:
        print("   ", f)
    sys.exit(1 if fails else 0)
