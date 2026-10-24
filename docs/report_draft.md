# REPORT DRAFT (for the participant to edit; not final)

> Drafting notes:
> - Everything marked **[TBD]** waits for the v3 results.
> - Everything marked **[VERIFY]** is a claim about a cited paper taken from the sprint's
>   Resources page summary. Check it against the paper before submitting; made-up results or
>   references can disqualify a project.
> - Final format: the official template (see `docs/sprint_requirements.md`), at most 8 pages
>   before references and appendices, abstract 150–250 words.

## Title (options)
1. *Talk Is Cheap, Votes Are Not: Combining Messages and Actions Does Not Help LLM Monitors Detect Collusion* [TBD: depends on the v3 result]
2. *Can a Monitor Catch Vote-Trading AI Agents from What They Say and Do?*
3. *Detecting Covert Vote Trading Among LLM Agents: Messages, Actions, and Private Reasoning*

## Abstract [TBD, 150–250 words, written last]
Skeleton:
- Problem: monitors of multi-agent systems usually see either what agents say or what they do.
  Does combining the two help detect collusion?
- Setup: a 7-agent committee-vote game designed so that collusion (vote trading by a secret
  pair) pays and shows up in the conjunction of talk and actions. Matched games with no
  collusion, naive colluders, and competent colluders.
- Monitors: two LLM monitors (Llama 3.3 70B, frozen prompt; DeepSeek V3.1 as a robustness
  check) and non-LLM heuristics, each given five views of each game.
- Main result [TBD].
- Takeaway [TBD].

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
     bound as a positive control. [TBD: headline numbers.]
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
- Main data: v3 `instructed` and `instructed_hint` [TBD: confirm counts], plus `none`.
  `channel_only` from v2.
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
- Models: **Llama 3.3 70B** (frozen as the monitor before the sprint), temperature 0. As a
  **post-hoc robustness check**, **DeepSeek V3.1** with the same prompt, added after the Llama
  results were seen.
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

## 4. Results [TBD]
- 4.1 Manipulation check: bloc-vote rate and matched gain, for naive vs competent colluders.
  [TBD]
- 4.2 Main figure: AUROC by view, naive vs competent, two monitors, plus the best heuristic,
  with the `plans` upper bound marked. [TBD]
- 4.3 Does combining help? Paired differences `both − public`, `both − actions`. [TBD]
- 4.4 False positives and pair identification; hard negatives (`channel_only`). [TBD]
- 4.5 Heuristics vs LLM monitors. In v2 (naive colluders), `against_stake` reached AUROC 0.61
  [0.54, 0.69] with FPR 0.05, beating both LLM monitors on every main view. [TBD: v3]

## 5. Discussion [TBD]
- What the result means for 2.2. [TBD]
- Test-set validity: naive colluders often do not act collusively. Only 9 of 40 v2 naive games
  had a bloc vote. Evaluations of collusion monitors must check that collusion actually
  happened.
- LLM monitors leave behavioural evidence unused: a one-line rule beats them on the actions
  view [TBD: v3]. Private reasoning access (`plans`) works.
- Monitor calibration: DeepSeek flags collusion in almost every game under this prompt;
  Llama's suspicion scores are nearly binary.
- Future work:
  - side payments, so selfish `channel_only` agents could share gains;
  - stronger or mixed agent models;
  - more games (El Farol was dropped);
  - monitor prompts that ask for explicit stake and vote consistency checks;
  - pinning the inference provider.

## Appendix A: Limitations and Dual-Use / Ethical Considerations (required)
**What the results do and do not establish**
- One game, one agent model (Llama 3.3 70B), 40 games per condition, 6 rounds.
- Collusion is induced by instruction (red-team colluders), not emergent. We make no claims
  about whether LLM agents would collude on their own; `channel_only` pairs did not, but they
  also had no way to share gains.
- Monitor prompt frozen before the sprint. DeepSeek and the heuristic baselines were added
  after the first results were known, so they are post-hoc analyses.
- OpenRouter routing was not pinned to one inference provider for the agents or the monitors,
  so outputs come from a mix of providers.
- The data went through three generations (v1–v3), with fixes driven by observed confounds.
  Each fix was validated against criteria set before the run, and earlier data are reported in
  the appendix.
- `channel_only` hard negatives used full private history, while v3 positives used
  current-round history.
- Labels follow the condition (instructed = colluding), not realized behaviour. We report
  realized-collusion subsets separately.

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
