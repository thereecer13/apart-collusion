"""
Render the pair's prompts for each private channel condition into
docs/private_channel_prompts.md (offline, stub model, no API calls).

Run:  python tests/render_prompts.py
"""

import contextlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.environ.setdefault("OPENROUTER_API_KEY", "offline-test")

import test_private_channel as T
from src.endogenous.core.private_channel import choose_pair


class Placeholder(T.StubParallel):
    def execute_parallel(self, reqs):
        out = super().execute_parallel(reqs)
        for r in reqs:
            if "_pm" in r["custom_id"]:
                out[r["custom_id"]] = {"message": "<private message text>"}
        return out


def render(condition):
    client = Placeholder()
    with contextlib.redirect_stdout(io.StringIO()):
        T.run_all_trials(
            game_type="elfarol", agent_names=T.AGENTS, game_params={"threshold": 0.5},
            llm_client=T.StubLLM(), parallel_client=client, n_trials=1, n_rounds=2,
            round_robin=True, show_progress=False, private_channel=condition, seed=7,
        )
    a, b = choose_pair(7, 0, T.AGENTS)

    def get(cid, i):
        return [r for r in client.requests if r["custom_id"] == cid][i]["messages"]

    pm = get(f"t0_pm0_{a}", 1)   # round 2, so the history is non-empty
    s2 = get(f"t0_s2_{b}", 1)
    return "\n".join([
        f"## `{condition}` (pair: A = Agent {a}, B = Agent {b})\n",
        f"### Private message prompt (Agent {a}, round 2)\n",
        f"**System:**\n```\n{pm[0]['content']}\n```\n",
        f"**User:**\n```\n{pm[1]['content']}\n```\n",
        f"### Public announcement prompt (Agent {b}, round 2), user prompt\n",
        f"```\n{s2[1]['content']}\n```\n",
    ])


if __name__ == "__main__":
    doc = [
        "# Private channel prompts (rendered)\n",
        "Rendered offline with a stub model: plans, public messages and private messages are",
        "placeholders. Only the pair's prompts change; every other agent's prompts are identical",
        "to the original harness. The same system-prompt changes and history block are added to",
        "the pair's Stage 1, Stage 2, Stage 3 and reflection prompts.\n",
        "The `none` condition changes no prompts; the pair is only recorded in the log.\n",
        render("instructed"),
        render("channel_only"),
    ]
    path = os.path.join(os.path.dirname(HERE), "docs", "private_channel_prompts.md")
    with open(path, "w") as f:
        f.write("\n".join(doc))
    print(f"Wrote {path}")
