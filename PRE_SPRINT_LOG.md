# Pre-sprint work log

Everything done before the Apart AI Collusion Research Sprint (Fri Oct 23, 2026).
Listed for disclosure in the sprint report. Dates are in UTC.

## 2026-10-21

### Setup
- Imported starter code from https://github.com/Jerick-1380/LLM-Trust-Breaking at
  commit `fd11aca` (Shi et al. 2026, "When Agents Lie"), unmodified, as the first commit
  of this repo. The upstream repo has **no LICENSE file**.
- Created a Python 3.12 venv and installed `requirements.txt`. No dependency problems.

### Step 1: harness check
- Read the code (summary in the Step 1 checkpoint notes below).
- Offline check, no LLM calls: n=7 works without code changes. Agent names are
  `F G J M Q T Z`. El Farol payoffs are correct: 3 goers get +10 each, 4 goers get −5 each.
- **Blocked:** could not run a real game. No `OPENROUTER_API_KEY`/`OPENAI_API_KEY` in the
  environment, and the sandbox network policy blocks `openrouter.ai` and `api.openai.com`.
  No game logs or costs yet.

### Ways the harness differs from the sprint brief
1. Between rounds, agents carry forward only their trust scores and assessments from the
   reflection step. Stage 1 planning does not see previous rounds' announcements, actions or
   payoffs, except as summarised in their own assessments.
2. The round-robin announcement order is fixed and alphabetical, and identical every round.
3. Every round has an extra LLM-as-judge call per agent, hard-coded to `openai/gpt-5-mini`.
   This is a second model and an added cost.
4. Reflection is one call per (agent, target) pair, so 42 calls per round at n=7. This
   dominates call count and cost.
5. There is no per-game seed. Every request sends `seed=42` and temperature 1.0, and the
   agent names come from `random.seed(42)`.
6. Any model whose name starts with `gpt-` or `o1`/`o3` is routed to the OpenAI API directly,
   even with an `openai/` OpenRouter prefix. The non-queued runner crashes for OpenAI models
   (`parallel_client=None`). In queued mode with a non-OpenAI agent model, the
   `openai/gpt-5-mini` judge requests are silently dropped when there is no OpenAI key.
7. The harness does not track tokens or cost.

## 2026-10-22
- Network access fixed: `openrouter.ai` is now reachable (HTTP 200).
- Still blocked: no OpenRouter API key in the environment. No environment variable is set,
  and a direct call to `/api/v1/key` returns 401 "No cookie auth credentials found", so the
  proxy isn't injecting one either. No games run yet.
- Scope for pre-sprint work, as set by the participant: read the code, set up the
  environment, add the private channel, run small test runs only to check that things work,
  and draft the Inspect monitor skeleton. Data-generation runs are saved for the hackathon.
  Test runs before then are for checking plumbing only and are not used as results.

### Step 2: private channel (code only, no LLM calls)
- New `src/endogenous/core/private_channel.py`: the three conditions (`instructed`,
  `channel_only`, `none`), per-game pair choice from the seed, the prompt text for each
  condition, the private message prompt, and the channel's message history.
- `src/endogenous/core/trial_runner.py`: optional `channel` argument on Stage 1, Stage 2,
  Stage 3 and reflection. When a channel is set, the pair's prompts get the condition note
  (added to the system prompt) and the message history (added to the start of the user
  prompt). New `_run_private_channel` runs after Stage 1 and before Stage 2: A sends, then B,
  repeated `n_exchanges` times. Each trial result gets a `private_channel` record
  (`condition`, `pair`, `n_exchanges`, and `messages` with round, exchange, sender, receiver
  and message). This record is separate from the public `stage2` messages.
- `experiments/run_endogenous.py`: new flags `--private-channel {instructed,channel_only,none}`,
  `--private-exchanges N` (default 1) and `--seed S` (default 0). Not supported with
  `--use-queue`; the runner errors out if both are given.
- Checks (offline, stub client, no API calls), in `tests/test_private_channel.py`:
  - With the flags off, all 420 requests and the log for a 2-game, 3-round run are
    byte-for-byte identical to the original upstream code.
  - `none` changes no prompts and records the seeded pair.
  - Private messages appear only in the pair's prompts and are logged per round.
  - Multiple exchanges work.
  - The pair is fully determined by the seed.
- Rendered prompts for each condition are in `docs/private_channel_prompts.md`.
- Decisions after the Step 2 review:
  - `instructed`: in the pair's system prompts, the two own-payoff goal lines ("Your goal is
    to maximize your final payout." and "...maximize your outcome.") are replaced with
    "...maximize the combined payoff of you and Agent {partner}." `channel_only` and
    non-pair agents are unchanged. The judge prompt is never modified.
  - The pair's prompts show the full private message history (all rounds so far).
  - Agent model for test runs: `meta-llama/llama-3.3-70b-instruct` (OpenRouter).
- Tests updated and passing. Flags-off output is still byte-for-byte identical to upstream.
  Added `tests/render_prompts.py` to regenerate `docs/private_channel_prompts.md`.
- Added `--no-judge` (non-queued runner only): skips the per-agent `openai/gpt-5-mini`
  LLM-as-judge call. Each agent's `judge` entry is then `{"skipped": true, "_parse_ok": false}`,
  which the existing analyzer already leaves out of its counts. The default is unchanged,
  so the judge still runs. Test added; flags-off output is still identical to upstream.
