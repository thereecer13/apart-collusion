# Does combining what agents say with what they do help a monitor detect collusion?

Project for the **Apart AI Collusion Research Sprint** (Oct 23–25, 2026), Track 2 (Detection and
Audit of Collusion), question 2.2. Seven LLM agents play a repeated committee-vote game. In some
games, two of them collude through a hidden private channel. LLM monitors and simple heuristic
baselines see different views of each game (public talk, actions, both, a said-vs-did table, and
an upper-bound view that adds private plans) and must say whether a colluding pair is present and
which agents it is.

## Provenance: what is preexisting and what is new

The sprint rules ask that all work done before the sprint be marked as preexisting. There are
three layers. The full dated record is in [`PRE_SPRINT_LOG.md`](PRE_SPRINT_LOG.md) (before the
sprint) and [`SPRINT_LOG.md`](SPRINT_LOG.md) (during the sprint).

### 1. Upstream starter code (not ours)
Imported unmodified in commit `8b3ab8f` from
[Jerick-1380/LLM-Trust-Breaking](https://github.com/Jerick-1380/LLM-Trust-Breaking) at commit
`fd11aca` (Shi et al. 2026, "When Agents Lie"). This includes the three-stage harness
(private plan → public announcement → final action → reflection), the six original games, and
the analyzer. The upstream repo has no LICENSE file. The upstream README is kept below, under
"Original upstream README".

### 2. Preexisting work by this project, written before the sprint (Oct 21–22, 2026)
Commits `8b3ab8f..cb47c04`. No research data was generated before the sprint, only small
plumbing tests (in `plumbing_tests/`, marked NOT DATA).
- **Private channel** between two agents, with conditions `instructed`, `channel_only` and
  `none`: new `src/endogenous/core/private_channel.py`; changes to
  `src/endogenous/core/trial_runner.py` and `experiments/run_endogenous.py` (flags
  `--private-channel`, `--private-exchanges`, `--seed`, `--no-judge`, `--dump-requests`).
- **Committee Vote Game** (`--game voting`): new `src/games/voting.py`; changes to
  `src/games/__init__.py` and `src/endogenous/core/prompt_builders.py` (per-agent private
  stakes).
- A fix in `trial_runner.py`: invalid actions count as parse errors.
- **Monitor pipeline in Inspect**: `monitor/views.py`, `monitor/prompt.py` (monitor prompt
  frozen as v1 before the sprint), `monitor/task.py`, `monitor/metrics.py`; the `channel_only`
  labeler `monitor/label_channel_only.py`.
- Plumbing checker `experiments/check_plumbing.py`; docs in `docs/`; tests in `tests/`
  (`test_private_channel.py`, `test_voting.py`, `test_monitor.py`, `test_labeler.py`,
  `render_*.py`).

### 3. New work during the sprint (Oct 23–25, 2026)
Commits after `cb47c04`. **All games and monitor results used in the report were generated
during the sprint.**
- Pilots that chose the main game and tested fixes; the main data batches (`data/`); the monitor
  runs (`results/`).
- **Stake reminder**, `--private-history current`, and the "competent colluder" condition
  `instructed_hint`: changes to `src/endogenous/core/private_channel.py`,
  `src/endogenous/core/trial_runner.py`, `src/games/voting.py` and
  `experiments/run_endogenous.py`.
- Analysis and run scripts: `experiments/analyze_voting_behaviour.py`,
  `experiments/pilot_voting.py`, `experiments/monitor_on_realized.py`,
  `experiments/run_main_voting.sh`.
- Heuristic baselines `monitor/baselines.py`; hand-label comparison
  `monitor/compare_hand_labels.py`; OpenRouter routing `monitor/openrouter_routing.yaml`.
- Changes to `monitor/task.py` and `monitor/metrics.py` (condition filters, hard negatives) and
  to `experiments/check_plumbing.py` (multi-game logs, the new conditions, false-positive fixes).
- New tests: `tests/test_baselines.py`, `tests/test_check_plumbing.py`; additions to
  `tests/test_voting.py`.
- Later in the sprint:
  - main figure `experiments/make_figure.py`;
  - exploratory claims-vs-outcomes views (`outcomes`, `outcomes_flagged` in `monitor/views.py`);
  - exploratory prompt v2 (`monitor/prompt.py`; v1 unchanged) and the paired comparison
    `experiments/compare_prompts.py`;
  - provider configs `monitor/openrouter_pinned.yaml` and `monitor/openrouter_reasoning.yaml`
    (DeepSeek V3.1 thinking mode);
  - tie-round analysis `experiments/tie_round_analysis.py` (pre-submission review), and
    `experiments/talk_counterfactual.py` (what talk could add: the best case for stated stakes);
  - the report: `docs/report_draft.md` and `docs/report.md`, superseded by `docs/submission/`,
    whose `build_report.py` fills the official template from `content.py`.

## Reproducing

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r monitor/requirements.txt
export OPENROUTER_API_KEY=...          # agents and monitors run via OpenRouter

# offline tests (no API calls)
for t in private_channel voting monitor labeler check_plumbing baselines; do python tests/test_$t.py; done

# one game: 7 agents, 6 rounds, voting game, competent colluders, current-round private history
python experiments/run_endogenous.py --game voting --agents 7 --trials 1 --rounds 6 \
  --model meta-llama/llama-3.3-70b-instruct --round-robin --no-judge \
  --private-channel instructed_hint --private-history current --seed 1000

# monitor (frozen v1 prompt) on a folder of game logs; then metrics by view
inspect eval monitor/task.py --model openrouter/meta-llama/llama-3.3-70b-instruct \
  --model-config monitor/openrouter_routing.yaml -T logs=data/main_voting_v2 --log-dir outputs/monitor
python monitor/metrics.py outputs/monitor --positives instructed --negatives none

# heuristic baselines (no API calls)
python monitor/baselines.py data/main_voting_v2 --positives instructed --negatives none

# numbers in the report (no API calls): behaviour (Table 1), tie rounds and the rule both ways,
# monitors on realized collusion, and the paired comparison of two monitor runs
python experiments/analyze_voting_behaviour.py data/main_voting_v3
python experiments/tie_round_analysis.py data/main_voting_v3
python experiments/talk_counterfactual.py data/main_voting_v3
python experiments/monitor_on_realized.py data/main_voting_v3 results/monitor_v3_llama
python experiments/compare_prompts.py results/monitor_v3_deepseek results/monitor_v3_deepseek_thinking \
  --positives instructed_hint --negatives none

# thinking-mode monitor (DeepSeek V3.1, same frozen prompt; ~$2)
inspect eval monitor/task.py --model openrouter/deepseek/deepseek-chat-v3.1 \
  --model-config monitor/openrouter_reasoning.yaml -T logs=data/main_voting_v3 \
  -T views=actions,public,both -T conditions=instructed_hint,none --max-tokens 16000 \
  --log-dir results/monitor_v3_deepseek_thinking
```

Always pass `--no-judge` and do not use `--use-queue`: the private channel, the voting game and
`--no-judge` are implemented only in the non-queued runner.

---

# Original upstream README

## Overview

This research framework measures how large language models engage in **strategic deception** (promise-breaking) and how **trust evolves** when models repeatedly deceive each other across 10 rounds of strategic games.

![Methodology](methodology.png)

---

## Quick Start

```bash
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env: add OPENAI_API_KEY and OPENROUTER_API_KEY

# Run a 10-round experiment
python experiments/run_endogenous.py \
  --game diners \
  --agents 5 \
  --trials 20 \
  --rounds 10 \
  --model openai/gpt-5.2 \
  --use-queue \
  --round-robin
```

**Output:** JSON with all stages + deception classifications → `outputs/experiments/{game}/5agents/`

---

## Research Questions

### 1. Do LLMs engage in strategic deception?
**Yes.** Commitment-breaking rates: 15–98% depending on model and game.

### 2. Is deception premeditated or impulsive?
**Premeditated.** 75–99% of commitment-breakers planned the deception in Stage 1 (private planning).

### 3. Does trust evolve over repeated interactions?
**Partially.** Trust scores shift by 0.5–1.0 points over 10 rounds but remain low (2.0–3.5 out of 5). Deception rates persist.

### 4. Do heterogeneous model groups show different dynamics?
**Yes.** Asymmetric exploitation emerges:
- **Claude + GPT:** Both defect 100%, mutual distrust, payoff parity
- **Llama + GPT:** Llama trusts GPT (82% compliance), GPT ignores Llama (4% compliance) → systematic payoff gaps

---

## Key Findings

### Deception Rates by Model (Diners Game, 10 rounds)

| Model | Commitment Breaking | Premeditation Rate | Trust Score (Final) |
|-------|-------------------|-------------------|-------------------|
| **GPT-5.2** | 96.7% | 99.9% | 2.80/5 |
| **Claude Opus 4.6** | 26.7% | 98.1% | 4.60/5 |
| **Llama 4 Maverick** | 98.4% | 99.8% | 2.09/5 |

### Heterogeneous Groups: Payoff Asymmetries

**Diners (pos1, all rounds average):**

| Configuration | Minority Mean Payoff | Majority Mean Payoff | Gap |
|--------------|---------------------|---------------------|-----|
| GPT minority + Llama majority | **4.15** | 2.60 | **+1.55** |
| Llama minority + GPT majority | **0.82** | 2.37 | **-1.55** |

**Interpretation:** When GPT is the numerical minority (1 agent vs 4), it exploits the Llama majority. When Llama is the minority, it gets exploited by GPT.

### Model-Specific Behavioral Patterns

- **GPT-5.2:** Always defects (96–100%), ignores announcements (0–10% compliance), low trust in others
- **Claude Opus 4.6:** Cooperates initially (70% honest in R0), learns to defect by R9 (51% breaking), maintains high outgoing trust
- **Llama 4 Maverick:** Always defects in homogeneous settings (98%), but complies with GPT announcements (82%) in heterogeneous settings → exploited

---

## Experimental Protocol

### Three-Stage Endogenous Promises

Each trial has 3 sequential stages that isolate strategic intent:

**Stage 1 — Private Planning** *(not shared)*
- Agent privately states intended action + strategic reasoning
- In rounds 2–10: sees trust assessments from prior rounds

**Stage 2 — Public Announcement** *(round-robin)*
- Agent publicly announces intended action + persuasive message
- Sees announcements from agents who spoke earlier (positions 1→5)
- Can lie: announcement ≠ private plan

**Stage 3 — Final Decision** *(sees all announcements)*
- Agent makes binding choice after seeing all public messages
- Can break commitment: choice ≠ announcement

**Reflection — Trust Update** *(after each round)*
- Agent observes all announcements, choices, and payoffs
- Updates trust score (1–5) for each other agent
- Writes 1–2 sentence assessment

### Deception Classification

By comparing stages, we classify each agent:

| Private Plan → Announcement | Announcement → Choice | Label |
|---|---|---|
| Same → Same | — | **Fully Honest** |
| Different → Same | Complied | **Intended Deception (Complied)** |
| Same → Different | Broke | **Impulsive Deviation** |
| Different → Different | Broke | **Premeditated Deception** |

**Premeditation Rate** = (Premeditated Deceivers) / (All Commitment Breakers)

---

## Games Tested

Six symmetric social dilemmas with varying strategic structures:

| Game | Actions | Key Mechanic | Payoff Range |
|------|---------|-------------|-------------|
| **Diners** | EXPENSIVE/CHEAP | Cost-sharing temptation | [1.8, 6.8] |
| **El Farol** | GO/STAY | Anti-coordination (capacity limit) | [-5.0, 10.0] |
| **Fishing** | 0–5 fish | Tragedy of commons (collapse at 15 total) | [0.0, 5.0] |
| **Volunteer** | YES/NO | Volunteer's dilemma | [-5.0, 1.0] |
| **Public Goods** | 0–5 tokens | Contribution game (1.5× multiplier) | [5.0, 12.5] |
| **Weakest Link** | 0–5 effort | Minimum coordination | [-10.0, 5.0] |

**Best signal:** Diners (binary, simple payoffs) shows clearest trust/deception patterns.

---

## Repository Structure

```
LLM-Strategic-Deception/
├── README.md                    # This file
├── CLAUDE.md                    # Developer guide for AI assistants
├── methodology.png              # Visual protocol diagram
├── requirements.txt
├── .env.example
│
├── src/                         # Core library code
│   ├── games/                   # 6 game implementations
│   │   ├── diners.py
│   │   ├── elfarol.py
│   │   ├── fishing.py
│   │   ├── volunteer.py
│   │   ├── publicgoods.py
│   │   └── weakestlink.py
│   ├── endogenous/
│   │   ├── core/
│   │   │   ├── trial_runner.py       # 3-stage orchestration + multi-round
│   │   │   └── prompt_builders.py    # Stage prompts + trust injection
│   │   └── analysis/
│   │       └── endogenous_analyzer.py # Deception typology classifier
│   ├── llm/
│   │   ├── client_factory.py         # Model routing (OpenAI/OpenRouter)
│   │   └── providers/
│   │       ├── queued_openai.py      # Async batching for OpenAI
│   │       └── queued_openrouter.py  # Async batching for OpenRouter
│   ├── visualization/
│   │   └── transcripts.py            # Human-readable trial transcripts
│   └── scenario_enumeration/         # Alternative protocol (exhaustive)
│
├── experiments/                 # Executable scripts
│   ├── run_endogenous.py             # Main runner
│   ├── run_scenario_enumeration.py
│   ├── run_scenario_enumeration_resume.py
│   ├── run_all_games.sh
│   ├── analysis/                     # Analysis scripts (10 files)
│   │   ├── announcement_compliance_analysis.py
│   │   ├── endogenous_comprehensive_analysis.py
│   │   ├── homogeneous_trust_analysis.py
│   │   ├── round_by_round_analysis.py
│   │   └── ...
│   └── plot/                         # Visualization scripts
│       ├── plot_trust.py             # Trust evolution over rounds
│       ├── plot_all.py
│       └── plot_judge.py
│
└── outputs/                     # Generated data (gitignored)
    └── experiments/{game}/5agents/
        ├── {model}_endogenous.json              # Homogeneous experiments
        └── {model}_endogenous_imposter_{pos}.json # Heterogeneous experiments
```

---

## Running Experiments

### Homogeneous Groups (All Same Model)

```bash
python experiments/run_endogenous.py \
  --game diners \
  --agents 5 \
  --trials 20 \
  --rounds 10 \
  --model openai/gpt-5.2 \
  --use-queue \
  --round-robin
```

### Heterogeneous Groups (Mixed Models)

Create `my_models.json`:
```json
{
  "J": "meta-llama/llama-4-maverick",
  "M": "openai/gpt-5.2",
  "Q": "openai/gpt-5.2",
  "T": "openai/gpt-5.2",
  "Z": "openai/gpt-5.2"
}
```

```bash
python experiments/run_endogenous.py \
  --game diners \
  --agents 5 \
  --trials 20 \
  --rounds 10 \
  --model openai/gpt-5.2 \
  --agent-models-file my_models.json \
  --use-queue \
  --round-robin \
  --run-suffix imposter_llama_pos1
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--game` | Game type: `diners`, `fishing`, `elfarol`, `volunteer`, `publicgoods`, `weakestlink` |
| `--agents` | Number of agents (default: 5) |
| `--trials` | Independent trials per round (default: 50) |
| `--rounds` | Sequential rounds with memory (default: 1) |
| `--model` | Base model for homogeneous or fallback (e.g., `openai/gpt-5.2`) |
| `--agent-models-file` | JSON mapping agent names to models (for heterogeneous) |
| `--use-queue` | **Use async batching** (10–50× faster) |
| `--round-robin` | Agents see prior announcements before speaking |
| `--run-suffix` | Append to output filename (e.g., `_imposter_llama`) |

**Tip:** Always use `--use-queue` for experiments with >10 trials.

---

## Analysis & Visualization

### Generate Trust Evolution Plots

```bash
python experiments/plot/plot_trust.py \
  outputs/experiments/diners/5agents/gpt-5.2_endogenous.json
```

Output: `outputs/plots/trust/{game}/{model}/trial_XX.png` (one plot per trial showing trust scores over 10 rounds)

### Comprehensive Analysis

```bash
# Cross-experiment summary statistics
python experiments/analysis/endogenous_comprehensive_analysis.py

# Announcement compliance rates (behavioral trust)
python experiments/analysis/announcement_compliance_analysis.py

# Round-by-round deception trends
python experiments/analysis/round_by_round_analysis.py
```

### Generate Human-Readable Transcripts

```bash
python -m src.visualization.transcripts \
  outputs/experiments/diners/5agents/gpt-5.2_endogenous.json \
  --output-dir outputs/transcripts/diners/gpt-5.2/
```

---

## Output Format

Each experiment generates a JSON file with this structure:

```json
{
  "metadata": {
    "game_type": "diners",
    "model": "openai/gpt-5.2",
    "n_agents": 5,
    "n_trials": 20,
    "n_rounds": 10,
    "protocol": "endogenous"
  },
  "per_round": [
    {
      "round_id": 0,
      "summary": {
        "promise_deception_rate": 0.96,
        "commitment_breaking_rate": 0.97,
        "premeditation_rate": 0.999,
        "mean_trust_given": 2.06,
        "mean_trust_received": 2.06
      }
    }
  ],
  "rounds": [
    {
      "round_id": 0,
      "trials": [
        {
          "trial_id": 0,
          "agents": {
            "J": {
              "stage1": {"intended_action": "EXPENSIVE", "reasoning": "...", "_parse_ok": true},
              "stage2": {"stated_action": "CHEAP", "message": "...", "_parse_ok": true},
              "stage3": {"choice": "EXPENSIVE", "reasoning": "...", "_parse_ok": true},
              "promise_deception": true,
              "commitment_breaking": true,
              "typology": "premeditated_deception",
              "reflection": {
                "takeaways": {
                  "M": {"score": 1, "assessment": "Announced CHEAP but chose EXPENSIVE..."},
                  ...
                },
                "_parse_ok": true
              }
            }
          },
          "outcomes": {
            "choices": {"J": "EXPENSIVE", "M": "CHEAP", ...},
            "payoffs": {"J": 6.8, "M": 1.8, ...},
            "description": "1 expensive, 4 cheap - mixed orders"
          }
        }
      ]
    }
  ]
}
```
