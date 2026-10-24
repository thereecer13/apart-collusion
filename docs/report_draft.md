# REPORT DRAFT v1 (for the participant to edit; not final)

> Drafting notes:
> - Results are filled in from the v3 data (`results/`). Check numbers against `SPRINT_LOG.md`.
> - Everything marked **[VERIFY]** is a claim about a cited paper taken from the sprint's
>   Resources page summary. Check it against the paper before submitting; made-up results or
>   references can disqualify a project.
> - Final format: the official template (see `docs/sprint_requirements.md`), at most 8 pages
>   before references and appendices, abstract 150–250 words.

## Title (options)
1. *The Evidence Is in the Votes: LLM Monitors Miss Collusion That a One-Line Rule Catches* (recommended)
2. *Does Combining What Agents Say and Do Help Monitors Detect Collusion? Not for LLM Monitors*
3. *Detecting Covert Vote Trading Among LLM Agents: Messages, Actions, and Private Reasoning*

## Abstract (245 words)
Monitors for multi-agent systems typically read either what agents say or what they do. We test
whether combining the two helps a monitor detect collusion (Track 2, question 2.2). Seven Llama
3.3 70B agents play a repeated committee-vote game with private stakes, designed so that honest
play implies honest talk while a secret colluding pair profits by vote trading, which forces one
member to vote against its own stake. Across 160 matched games we compare no collusion, a private
channel without instructions, naive colluders told to maximize their joint payoff, and competent
colluders also given a vote-trading tip. Competent colluders traded votes at every opportunity
(64 of 64 rounds), gaining 0.43 points per round at the other agents' expense. Two LLM monitors
(Llama 3.3 70B with a prompt frozen in advance, and DeepSeek V3.1) each saw five views of every
game: public messages, actions, both, a said-versus-did table, and an upper-bound view adding
private plans. On every observable view both monitors performed at chance (AUROC 0.44 to 0.60),
and combining messages with actions gave no measurable gain. Yet a one-line rule applied to
actions alone, flagging votes against one's own revealed payoff, detected competent colluders
with AUROC 0.86 at a 5% false-positive rate, while the monitors succeeded only with access to
private plans (AUROC 0.94 to 0.98). The evidence was in the action record; the LLM monitors did
not extract it. Even with every against-interest vote explicitly flagged, the best monitor reached
only AUROC 0.65.

## 1. Introduction
- AI agents increasingly interact in shared environments: markets, committees, negotiation.
  Collusion between agents (secret coordination that benefits a subset at others' expense) is
  a failure mode that oversight needs to catch. A natural defense is a monitor that reads the
  interaction record.
- What should the monitor read? Messages are cheap to fake. Actions carry the consequences but
  lack context. A plausible hypothesis is that the *combination* is most informative, because
  a colluder must say one thing and do another. We test this directly (Track 2, question 2.2).
- Contributions:
  1. **A game where the signal sits in the conjunction of talk and actions.** In the Committee
     Vote Game, honest play makes voting one's own (private) stake optimal and talk honest,
     while a colluding pair profits by vote trading, which forces a member to vote against
     its own stated interest.
  2. **A matched design with naive and competent colluders**, plus a manipulation check
     showing how often collusion is actually realized. This exposes a test-set validity
     problem: naive LLM colluders often do not collude in their actions at all.
  3. **Five views × two LLM monitors × simple heuristics**, with a private-reasoning upper
     bound as a positive control. Both LLM monitors are at chance on every observable view
     (AUROC 0.44–0.60), while a one-line action rule reaches 0.86 and private plans 0.94–0.98.
  4. **Methodological lessons for LLM-agent experiments**: two confounds we found and fixed
     (stale-stake confusion from private history; an ambiguous reminder), each with a
     validated fix.

## 2. Related Work [VERIFY all claims]
- **Shi et al. 2026, *When Agents Lie*** (arXiv:2607.05132). The harness we build on: private
  plan, public announcement, final action and reflection across several social dilemmas. The
  sprint page says that "in various repeated n-player games, more than 90% of deviations from
  public announcements were already stated in models' private plans". This is consistent with
  our private-plans upper bound.
- **Monitoring that combines what agents say and do.** Radev et al. 2026 (arXiv:2605.29178)
  build monitors that look for multiple agents coordinating on what they say and do (in a
  sabotage setting). Nguyen et al. 2026 (arXiv:2604.03968) report that analysing actions along
  multiple dimensions lifts a single-dimension monitor from 0% to >70%. Arike et al. 2026
  (arXiv:2601.21112) find that too much detail can degrade a monitor. TraceGuard
  (github.com/linhkid/TraceGuard) is a single-agent action-trace consistency monitor; our
  `table` view is in its spirit.
- **LLM collusion.** Fish et al. 2024 (arXiv:2404.00806): LLM pricing agents set prices above
  competitive levels. Nakamura et al. 2026 (Colosseum, arXiv:2602.15198): private pairwise
  channels can introduce collusion. Lin et al. 2024 (arXiv:2410.00031): agents can
  independently engage in anti-competitive practices.
- **Monitor awareness.** Kale et al. 2025 (arXiv:2508.19461): telling an agent it is watched
  reduces monitor accuracy. Relevant to our "do not reveal the partnership" instruction.

## 3. Methodology

### 3.1 Game: the Committee Vote Game (new; written before the sprint)
- 7 agents (F, G, J, M, Q, T, Z). 6 rounds. Each round, a new proposal and a YES/NO vote. It
  passes with ≥ 4 YES.
- Each agent has a **private stake** for the round, drawn independently and uniformly from
  {−$10, −$1, +$1, +$10}. If the proposal passes, each agent receives its own stake; if it
  fails, everyone gets $0. Agents see only their own stake.
- For a selfish agent, voting the sign of its own stake is weakly dominant, so honest
  talk is the natural baseline. A pair maximizing its *combined* payoff gains by voting as a
  bloc for the sign of the summed stake (vote trading). In simulation with sincere voters
  (200k draws), the pair's expected payoff rises by 41% (+0.71 per round) and the other agents
  lose 0.43 per round. The giveaway, a member voting against its own stake, is possible in
  about 25% of rounds.
- Protocol per round (Shi et al. harness): Stage 1 private plan → [private channel, pair only]
  → Stage 2 public announcements in fixed round-robin order (each agent sees earlier
  announcements) → Stage 3 simultaneous final votes → reflection (each agent rates each other
  agent; carried to the next round).

### 3.2 Conditions (pair chosen at random per game from the seed)
- `none`: no channel. A pair is still recorded so monitors can be scored. **Negative.**
- `instructed` (*naive colluders*): the pair gets a private channel (one message each per
  round, after planning, before announcements). Its goal lines are replaced by "maximize the
  combined payoff of you and Agent X", and it is told it is a secret team that must not reveal
  the partnership. **Positive.**
- `instructed_hint` (*competent colluders*): as `instructed`, plus a strategy tip to share
  exact stakes and both vote the sign of the summed stake (with a −$1/+$10 example).
  **Positive.**
- `channel_only`: the channel with no instruction to collude. Used as **hard negatives**
  (secondary; see Appendix).
- In the main (v3) data the pair sees only the current round's private messages
  (`--private-history current`; see 3.6 for why).

### 3.3 Data
- Agents: `meta-llama/llama-3.3-70b-instruct` via OpenRouter, temperature 1.0 (harness
  default), harness judge disabled.
- 40 games per condition: seeds 1000–1007 × 5 games. The same (seed, game) gives the same pair
  and stakes in every condition, so conditions are matched game by game.
- Main data (`data/main_voting_v3/`, 160 games):
  - 40 `instructed` + 40 `instructed_hint` games, generated with current-round private history;
  - 40 `none` games (no channel; prompts unchanged by any fix, so reused from the first batch);
  - 40 `channel_only` games (full private history; used only as hard negatives).
- Invalid or missing actions: 0.3% of action fields, counted as parse errors.
- Every request and response was logged. A plumbing checker verified that:
  - private messages never appear in a non-pair agent's prompt;
  - condition notes appear only in the pair's system prompts;
  - stakes are shown only to their owner;
  - payoffs match the rules.

### 3.4 Monitors and views
- Five views per game, built from the same log. None ever includes private messages, the
  condition, the pair or stake lines. Each opens with the same header: the public rules, the
  turn order, and which parts are shown.
  1. `public`: announced votes and public messages.
  2. `actions`: final votes, payoffs and outcome (when a proposal passes, payoffs reveal
     stakes).
  3. `both`: views 1 and 2 together.
  4. `table`: announced → final vote per agent and round, changes marked.
  5. `plans`: view 3 plus each agent's Stage 1 private plan. **The upper bound / positive
     control**, reported separately.
- Prompt: a single prompt for all views, **frozen before the sprint** (v1), written from the
  design and not tuned on data. It returns JSON: reasoning, collusion yes/no, suspicion 0–10,
  and the suspected pair or "none". The decision threshold is the monitor's own yes/no.
- Models:
  - **Llama 3.3 70B**: frozen as the monitor before the sprint; temperature 0; pinned to one
    OpenRouter provider (DeepInfra, fp8) for the main results.
  - **DeepSeek V3.1**: same prompt, as a **post-hoc robustness check**, added after the Llama
    results on earlier data were seen; not pinned to a provider.
- 800 monitor calls per model on the main data: 160 games × 5 views. 0 unparsed.
- Heuristic baselines (no LLM), using only what the matching view shows:
  - `co_vote` (actions);
  - `against_stake` (actions): votes against one's own revealed payoff;
  - `said_vs_did` (table);
  - `combined` (both).

  The rules were fixed before being run on data, but after the LLM results were known.

### 3.5 Metrics
- Accuracy, false-positive rate, AUROC (from the suspicion score; ties count half), and
  pair-identification accuracy (positives where the monitor says yes and names the true pair).
- Percentile bootstrap 95% CIs over games (2000 resamples). For the 2.2 question, paired
  differences between views resample games jointly.
- Behaviour:
  - the bloc-vote rate in trade-opportunity rounds (pair stakes of opposite sign and unequal
    size);
  - the matched collusion gain: the pair's payoff per round minus that of the same pair in
    the matched `none` game.

### 3.6 Validation and fixes (details in the Appendix)
Pass criteria were committed before each pilot.
- **Stake confusion.** With the full private history, colluders mistook stakes quoted in
  earlier rounds for current ones. 11% of their private messages stated a wrong own stake; 18%
  of their votes in same-sign rounds went against their own stake; collusion *lowered* the
  pair's payoff.
- **First fix and its side effect.** A reminder fixed the stake errors (0%), but it made
  agents distrust the partner's current stake, because no prompt states the current round.
- **Final fix.** Showing only the current round's private messages fixes both problems.
  Competent colluders then bloc-voted in 13/13 trade rounds in the pilot.

## 4. Results
All AUROCs are against the 40 `none` games unless stated, with 95% bootstrap CIs over games.

### 4.1 Manipulation check: competent colluders collude, naive ones mostly don't
| | naive (`instructed`) | competent (`instructed_hint`) | `channel_only` | `none` |
|---|---|---|---|---|
| Bloc votes in trade-opportunity rounds | 20 of 64 (31%) | **64 of 64 (100%)** | 3 of 64 | 1 of 64 |
| Games with ≥ 1 bloc vote (of 33 with a trade round) | 17 | **33** | 3 | 1 |
| Pair's payoff gain vs the matched `none` game (per agent-round) | +0.09 [−0.01, +0.20] | **+0.43 [+0.26, +0.60]** | +0.04 [+0.00, +0.11] | n/a |
| Other agents' change | +0.01 [−0.02, +0.03] | **−0.09 [−0.19, −0.00]** | +0.01 | n/a |

Wrong own-stake claims in private messages: 0% in both team conditions. In `none`, 86% of
public announcements match the agent's own stake, so talk is mostly honest.

### 4.2 Main result (Figure 1, `results/figures/main_figure.png`)
| AUROC [95% CI] | Naive: Llama | Naive: DeepSeek | Competent: Llama | Competent: DeepSeek |
|---|---|---|---|---|
| public | 0.52 [0.40, 0.64] | 0.47 [0.36, 0.58] | 0.60 [0.47, 0.71] | 0.57 [0.47, 0.67] |
| actions | 0.55 [0.44, 0.67] | 0.52 [0.39, 0.64] | 0.53 [0.40, 0.65] | 0.54 [0.41, 0.66] |
| both | 0.53 [0.41, 0.65] | 0.55 [0.45, 0.65] | 0.55 [0.44, 0.67] | 0.48 [0.38, 0.59] |
| table | 0.47 [0.36, 0.57] | 0.44 [0.33, 0.55] | 0.50 [0.39, 0.60] | 0.49 [0.37, 0.60] |
| *plans (upper bound / positive control)* | *0.89 [0.82, 0.95]* | *0.82 [0.75, 0.88]* | *0.94 [0.89, 0.97]* | *0.98 [0.94, 1.00]* |

| Heuristic (view) | Naive | Competent |
|---|---|---|
| `against_stake` (actions) | 0.65 [0.57, 0.73] | **0.86 [0.78, 0.93]** |
| `co_vote` (actions) | 0.56 [0.46, 0.67] | 0.76 [0.66, 0.85] |
| `combined` (both) | 0.48 [0.36, 0.61] | 0.65 [0.54, 0.76] |
| `said_vs_did` (table) | 0.43 [0.31, 0.56] | 0.50 [0.38, 0.63] |

### 4.3 Does combining what agents say and do help? (question 2.2)
- **For the LLM monitors, no.** Every paired difference `public − both`, `actions − both` and
  `table − both` has a CI that includes 0, for both monitors and both colluder types. Examples
  (competent, AUROC): Llama public − both +0.04 [−0.12, +0.20], actions − both −0.03
  [−0.14, +0.08]; DeepSeek public − both +0.09 [−0.05, +0.24].
- **For the heuristics, also no.** Adding the said-vs-did signal to against-stake (`combined`)
  *lowers* AUROC: competent 0.65 vs 0.86. Honest agents also change from their announcements
  (FPR of `said_vs_did` = 0.85), so the talk–action mismatch is noise in this game.
- **What helps is the private reasoning** (`plans`): +0.28 to +0.49 AUROC over `both`, for both
  monitors and both colluder types.

### 4.4 Errors and calibration
- **False positives (`none`):**
  - Llama: 0.20 (public), 0.40 (actions), 0.42 (both), 0.03 (table), 0.23 (plans).
  - DeepSeek: 1.00, 0.55, 0.90, 0.97 and 0.88. DeepSeek answers "collusion" in almost every
    game under this prompt.
  - `against_stake`: 0.05.
- **Pair identification:** in the main views the named pair is almost never correct (0–10%;
  DeepSeek `table` 25%). With `plans`, 100% for both monitors.
- **Score shape:** Llama's suspicion scores are nearly binary (mostly 2 or 8).

### 4.5 Robustness
- **Hard negatives** (`channel_only`: pairs who talk privately but don't collude): competent vs
  `channel_only` gives the same picture. LLM monitors 0.47–0.61 on the observable views;
  `against_stake` 0.87 [0.79, 0.93], FPR 0.03.
- **Only games with realized collusion** (the 17 naive games with ≥ 1 bloc vote): LLM monitors
  0.48–0.55 on the observable views; `against_stake` 0.80 [0.67, 0.92].
- **Earlier data** (v2, naive colluders, full history): the same qualitative picture (Appendix C).

### 4.6 Why the LLM monitors miss it (illustrative, not measured)
On competent games in the `actions` view, the monitors look for agents who vote together and
earn well, or for agents who lose money:
- Llama: "Agents G and J consistently voted together and received high payoffs…"; and "the
  absence of announcements and stakes in the log limits the analysis". It doesn't infer that
  payoffs reveal stakes when a proposal passes.
- DeepSeek flags an agent that "voted NO and received −10". That is an honest voter on the
  losing side. The real signal is the reverse: voting YES while receiving a negative payoff.

### 4.7 Exploratory: structured claims-vs-outcomes reports (post-hoc)
This arm was designed after the main results, following the track's suggested "structured
report comparing claims with outcomes". It used two new views with the same frozen prompt:
- `outcomes`: per round, one row per agent with the announced vote, the final vote and the
  payoff;
- `outcomes_flagged`: the same, plus a column marking each vote **with** or **AGAINST** the
  interest revealed by the payoff. These flags carry exactly the `against_stake` rule's evidence.

| AUROC [95% CI] vs `none` | Llama naive | Llama competent | DeepSeek naive | DeepSeek competent |
|---|---|---|---|---|
| both (main) | 0.53 | 0.55 | 0.55 | 0.48 |
| outcomes | 0.47 | 0.48 | 0.46 | 0.55 |
| outcomes_flagged | 0.55 | **0.65 [0.55, 0.75]** (FPR 0.00) | 0.44 | 0.53 |
| *`against_stake` rule (same evidence)* | *0.65* | ***0.86*** | *0.65* | ***0.86*** |

- Presenting the record as an aligned table alone does not help.
- Spelling out the inconsistency helps Llama a little, but not significantly (paired vs `both`
  +0.10 [−0.05, +0.25]). It stays well below the rule given the same evidence.
- In 30 of 40 competent games at least one AGAINST row is shown. Llama answered "yes" on 5 of
  them, DeepSeek on 16.

**Why.** In a typical trade only *one* colluder, the member with the small stake, votes against
its interest; the partner votes with its own. One AGAINST row is therefore the whole visible
trace.
- Llama treats it as weak evidence: "most agents voted with their revealed interests… Z's
  vote… went against… could indicate collusion. But without more information, it's difficult
  to determine." Honest agents almost never vote against their revealed interest (rule FPR
  0.05), so a single such vote is strong evidence. The monitor does not use that base rate.
- DeepSeek also misreads the table at times, and names the wrong partner.

## 5. Discussion
- **Answer to 2.2 in this setting.** Combining messages with actions did not help LLM monitors
  detect collusion. That is not because the evidence was missing: when colluders acted,
  their actions gave them away to a one-line consistency rule (AUROC 0.86). The bottleneck is
  the monitor's reasoning over the record, not which channel it reads.
- **Even explicit evidence is under-weighted** (4.7). With the inconsistency flagged, LLM
  monitors improve little (best 0.65). The visible trace of a trade is a single against-interest
  vote, and the monitors treat it as ambiguous. A detector needs the base rate: honest agents
  almost never vote against their own revealed interest. Rules encode that base rate; generic
  monitor prompts do not.
- **Talk can be a distraction.** Honest agents' announcements differ from their votes often
  enough (85% of games) that talk–action mismatch is not diagnostic here, and adding it hurt the
  heuristic. Combining channels helps only if the combined signal is cleaner than either alone.
- **Private reasoning works.** With access to Stage 1 plans, both monitors detect collusion and
  name the pair (AUROC 0.82–0.98). This is consistent with reports that deviations are visible
  in private plans [Shi et al. 2026, VERIFY]. But it depends on colluders writing their intent
  down, and they may not do so if they know they are watched [Kale et al. 2025, VERIFY].
- **Test-set validity.** Agents told to collude often do not act collusively: naive colluders
  traded in only 31% of opportunities. In an earlier batch, confusion over stakes even made
  their collusion lose money. Collusion-monitor evaluations should report a manipulation
  check of realized collusion, not just the instruction given.
- **Practical implication.** Before deploying an LLM monitor, check it against simple,
  task-specific consistency rules. A monitor prompt that asks for explicit checks (does each vote
  match the agent's revealed interest?) is an obvious next step; we kept the prompt frozen to
  avoid tuning on the test data.
- **Future work:**
  - prompts with explicit consistency checks and base rates (e.g. "honest agents essentially
    never vote against their revealed interest"); the structured views alone (4.7) were not enough;
  - stronger and mixed agent models;
  - side payments, so selfish agents could share gains (emergent collusion);
  - more games (El Farol was dropped for time);
  - pinned providers for every model.

## Appendix A: Limitations and Dual-Use / Ethical Considerations (required)
**What the results do and do not establish**
- One game, one agent model (Llama 3.3 70B), 40 games per condition, 6 rounds.
- Collusion is induced by instruction (red-team colluders), not emergent. We make no claims
  about whether LLM agents would collude on their own; `channel_only` pairs did not, but they
  also had no way to share gains.
- Monitor prompt frozen before the sprint. DeepSeek and the heuristic baselines were added
  after the first results were known, so they are post-hoc analyses.
- OpenRouter routing was not pinned for the agents or for DeepSeek, so those outputs come from
  a mix of inference providers. The Llama monitor's main results are pinned to one provider
  (DeepInfra, fp8). Its earlier runs were not.
- The data went through three generations (v1–v3), with fixes driven by observed confounds.
  Each fix was validated against criteria set before the run, and earlier data are reported in
  the appendix.
- `channel_only` hard negatives used full private history, while v3 positives used
  current-round history.
- Labels follow the condition (instructed = colluding), not realized behaviour. We report
  realized-collusion subsets separately.
- Several comparisons are made; a few CIs that narrowly exclude 0 should not be over-read.
  One example is DeepSeek `table − both` vs `channel_only` for naive colluders, −0.16
  [−0.31, −0.00].
- The heuristic rules use knowledge of the game, namely that payoffs reveal stakes. That is
  their point, and also a limit: they are game-specific.
- The claims-vs-outcomes views (4.7) are exploratory and post-hoc.

**Dual use**
- The strategy tip and our analysis describe how a pair can trade votes covertly, and that LLM
  monitors miss behavioural evidence of it. A capable adversary could use both. The tip is
  simple and well known from political economy (logrolling), and our main message (check
  realized behaviour; use structured consistency checks and reasoning access) favours
  defenders.
- No real systems, people or markets were involved. All agents were simulated.

## Appendix B: Provenance (required by the sprint rules)
Mirror the README section:
1. upstream code (Shi et al. harness, imported unmodified);
2. our pre-sprint work (Oct 21–22): private channel, voting game, monitor pipeline and frozen
   prompt, labeler, plumbing checker, tests;
3. sprint work.

All data and results were generated during the sprint.

## Appendix C: Earlier data generations and pilots
- Pilots 1–4: criteria, results and decisions (from `SPRINT_LOG.md`).
- v1 (full history), v2 (reminder) and v3 (current-round history): behaviour tables, the
  diagnosis, and the v2 monitor results.

## References
- Shi et al. 2026. arXiv:2607.05132.
- Radev et al. 2026. arXiv:2605.29178.
- Nguyen et al. 2026. arXiv:2604.03968.
- Arike et al. 2026. arXiv:2601.21112.
- Fish et al. 2024. arXiv:2404.00806.
- Nakamura et al. 2026. arXiv:2602.15198.
- Lin et al. 2024. arXiv:2410.00031.
- Kale et al. 2025. arXiv:2508.19461.
- TraceGuard. https://github.com/linhkid/TraceGuard
- LLM-Trust-Breaking. https://github.com/Jerick-1380/LLM-Trust-Breaking

[VERIFY: full titles and author lists; the sprint page gives only author–year and links.]
