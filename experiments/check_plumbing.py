"""
Plumbing checks for a run with a private channel condition (one or more games).

Uses the results JSON plus the --dump-requests JSONL (optionally .gz) from the
same run. Checks each game separately: parsing, private-message routing and
logging, condition prompts, voting stakes, and payoffs. It does not look at
behaviour. Parse problems (invalid or missing actions, which the harness counts
as parse errors) are reported separately from plumbing failures.

Run:  python experiments/check_plumbing.py RESULTS.json REQUESTS.jsonl[.gz]
"""

import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("OPENROUTER_API_KEY", "offline-check")

from src.games import create_game

VALID_ACTIONS = {"voting": {"YES", "NO"}, "elfarol": {"GO", "STAY"}}
STAKE_RE = re.compile(r"YOUR PRIVATE STAKE THIS ROUND: ([+-])\$(\d+)")
REMINDER_RE = re.compile(r"Your stake for THIS round's proposal is ([+-])\$(\d+)\.")


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
    """All requests in send order, as dicts with custom_id, stage, agent and prompts."""
    opener = gzip.open if path.endswith(".gz") else open
    out = []
    with opener(path, "rt") as f:
        for line in f:
            rec = json.loads(line)
            cid = rec["request"]["custom_id"]
            msgs = rec["request"]["messages"]
            out.append({"cid": cid, "stage": stage_of(cid), "agent": focal_agent(cid),
                        "system": msgs[0]["content"], "user": msgs[1]["content"]})
    return out


def tag_rounds(reqs):
    """Tag one game's requests with their round: a new round starts at the first s1 after a non-s1."""
    rnd, prev = -1, None
    for r in reqs:
        if r["stage"] == "s1" and prev != "s1":
            rnd += 1
        prev = r["stage"]
        r["round"] = rnd
    return reqs


def check_game(data, tid, reqs):
    """Checks for one game (trial index tid); reqs = that game's requests only."""
    game_type = data["metadata"]["game_type"]
    rounds = [{"round_id": rd["round_id"], "trials": [rd["trials"][tid]]} for rd in data["rounds"]]
    reqs = tag_rounds(reqs)
    fails, parse_issues = [], []

    def expect(cond, msg, parse=False):
        if not cond:
            (parse_issues if parse else fails).append(msg)

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
                expect(ad[s]["_parse_ok"] and ad[s][field] in valid,
                       f"r{rd['round_id']+1} {a} {s} invalid/missing action {ad[s][field]!r}", parse=True)
            if "reflection" in ad:
                expect(ad["reflection"]["_parse_ok"], f"r{rd['round_id']+1} {a} reflection parse failed", parse=True)
        for m in t["private_channel"]["messages"]:
            expect(m["_parse_ok"] and m["message"].strip(), f"r{rd['round_id']+1} private message parse failed", parse=True)

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
        if not text.strip():
            continue  # empty message (already a parse issue); "" would match every prompt
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

    # 3. Condition prompts appear only where they should. The notes and team goal are
    #    inserted into the system prompt, so check there: user prompts contain other agents'
    #    public messages, which may use the same words. The private-history block is the
    #    start of the user prompt.
    team_goal = "Your goal is to maximize the combined payoff of you and Agent"
    for r in reqs:
        in_pair = r["agent"] in pair
        expect(("SECRET TEAM:" in r["system"]) == (condition == "instructed" and in_pair), f"SECRET TEAM note wrong in {r['cid']}")
        expect(("PRIVATE CHANNEL:" in r["system"]) == (condition == "channel_only" and in_pair), f"channel note wrong in {r['cid']}")
        expect((team_goal in r["system"]) == (condition == "instructed" and in_pair), f"team goal wrong in {r['cid']}")
        has_history = r["user"].startswith("Private messages between you and Agent")
        expect(has_history == (condition != "none" and in_pair), f"private history block wrong in {r['cid']}")

    # 4. Voting stakes: each prompt shows exactly the focal agent's own stake for that round.
    #    The pair's stake reminder (from round 2, if the run used it) shows the same stake.
    if game_type == "voting":
        reminder_on = trial0["private_channel"].get("stake_reminder", False)
        for r in reqs:
            seen = [int(g) * (1 if s == "+" else -1) for s, g in STAKE_RE.findall(r["system"] + r["user"])]
            want = rounds[r["round"]]["trials"][0]["stakes"][r["agent"]]
            expect(seen == [want], f"{r['cid']} round {r['round']+1}: stakes shown {seen}, expected [{want}]")
            rem = [int(g) * (1 if s == "+" else -1) for s, g in REMINDER_RE.findall(r["user"])]
            should = reminder_on and r["agent"] in pair and r["round"] > 0
            expect(rem == ([want] if should else []), f"{r['cid']} round {r['round']+1}: stake reminder {rem}, expected {[want] if should else []}")

    # 5. Payoffs, recomputed from the game class
    for rd in rounds:
        t = rd["trials"][0]
        params = {"stakes": t["stakes"]} if game_type == "voting" else {"threshold": 0.5}
        game = create_game(game_type, agents, **params)
        expect(game.evaluate(t["outcomes"]["choices"]) == t["outcomes"]["payoffs"],
               f"r{rd['round_id']+1} payoffs do not match the rules")

    return condition, pair, len(reqs), len(all_msgs), fails, parse_issues


def check(results_path, requests_path):
    """Check every game in a results file. Returns a list of per-game results."""
    data = json.load(open(results_path))
    all_reqs = load_requests(requests_path)
    out = []
    for tid, t in enumerate(data["rounds"][0]["trials"]):
        prefix = f"t{t['trial_id']}_"
        reqs = [r for r in all_reqs if r["cid"].startswith(prefix)]
        out.append((t["trial_id"],) + check_game(data, tid, reqs))
    return out




if __name__ == "__main__":
    any_fail = False
    for tid, condition, pair, n_req, n_msg, fails, parse_issues in check(sys.argv[1], sys.argv[2]):
        any_fail |= bool(fails)
        print(f"{os.path.basename(sys.argv[1])} t{tid}: condition={condition} pair={pair} "
              f"requests={n_req} private_messages={n_msg} -> {'PASS' if not fails else 'FAIL'}"
              f" (parse issues: {len(parse_issues)})")
        for f in fails[:20]:
            print("   ", f)
        for f in parse_issues[:5]:
            print("    parse:", f)
    sys.exit(1 if any_fail else 0)
