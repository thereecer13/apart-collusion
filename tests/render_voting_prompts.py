"""
Render Committee Vote Game prompts into docs/voting_game_prompts.md
(offline, stub model, no API calls).

Run:  python tests/render_voting_prompts.py
"""

import contextlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.environ.setdefault("OPENROUTER_API_KEY", "offline-test")

import test_voting as V
from src.endogenous.core.private_channel import choose_pair


class Placeholder(V.SincereStub):
    def execute_parallel(self, reqs):
        out = super().execute_parallel(reqs)
        for r in reqs:
            cid = r["custom_id"]
            if "_pm" in cid:
                out[cid] = {"message": "<private message text>"}
            elif "_s2_" in cid:
                out[cid]["message"] = "<public message text>"
        return out


def block(title, msgs, system=True):
    parts = [f"### {title}\n"]
    if system:
        parts.append(f"**System:**\n```\n{msgs[0]['content']}\n```\n")
    parts.append(f"**User:**\n```\n{msgs[1]['content']}\n```\n")
    return "\n".join(parts)


if __name__ == "__main__":
    client = Placeholder()
    with contextlib.redirect_stdout(io.StringIO()):
        V.run_all_trials(
            game_type="voting", agent_names=V.AGENTS, game_params={},
            llm_client=V.StubLLM(), parallel_client=client, n_trials=1, n_rounds=2,
            round_robin=True, show_progress=False, private_channel="instructed", seed=7,
            run_judge=False,
        )
    a, b = choose_pair(7, 0, V.AGENTS)
    other = next(x for x in V.AGENTS if x not in (a, b))

    def get(cid, i):
        return [r for r in client.requests if r["custom_id"] == cid][i]["messages"]

    doc = [
        "# Committee Vote Game prompts (rendered)\n",
        "Rendered offline with a stub model that votes its own stake; plans and messages are",
        f"placeholders. Condition `instructed`, seed 7, pair A = Agent {a}, B = Agent {b}.",
        "The stake line is the only per-agent difference in a non-pair agent's prompts.\n",
        f"## Non-pair agent (Agent {other}), round 1\n",
        block("Stage 1: private planning", get(f"t0_s1_{other}", 0)),
        block("Stage 3: final vote", get(f"t0_s3_{other}", 0)),
        f"## Pair member (Agent {a}), round 2\n",
        block("Private message", get(f"t0_pm0_{a}", 1)),
        block("Stage 2: public announcement", get(f"t0_s2_{a}", 1), system=False),
    ]
    path = os.path.join(os.path.dirname(HERE), "docs", "voting_game_prompts.md")
    with open(path, "w") as f:
        f.write("\n".join(doc))
    print(f"Wrote {path}")
