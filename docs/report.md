# The Evidence Is in the Votes: LLM Monitors Miss Collusion That a One-Line Rule Catches

*[Author name], [Affiliation]*
*Apart AI Collusion Research Sprint, Track 2 (Detection and Audit of Collusion), question 2.2*

> Prose version of `docs/report_draft.md`, ready to move into the official template. Before
> submitting: check every **[VERIFY]** claim against the cited paper, and add your name and
> affiliation.

## Abstract

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

AI agents increasingly act in shared environments: markets, negotiations, committees. In these
settings, collusion is a natural failure mode. A subset of agents secretly coordinates to benefit
at the others' expense. One natural defence is a monitor that reads the record of the
interaction and flags suspicious behaviour. That raises a design question: what should the
monitor read? Messages are cheap to fake. Actions carry the consequences but lack context. A
plausible hypothesis is that the *combination* is most informative, because a colluder may have
to say one thing and do another. Track 2 of this sprint poses the question directly: does
combining what agents say with what they do improve detection?

We test it in a setting built so that the answer could be yes. In our Committee Vote Game,
honest play makes truthful announcements and votes that follow one's own stake the natural
baseline. A colluding pair profits by *vote trading*: one member votes against its own small
stake to secure its partner's large one. Collusion therefore shows up as a mismatch between an
agent's interest, what it says, and what it does. We generate matched games with and without
colluders, give LLM monitors five views of each game, and compare them with simple non-LLM
detectors.

Our contributions:

1. **A collusion test bed in which the signal lives in talk and actions.** A seven-agent
   committee-vote game with private stakes, matched across conditions, with plumbing checks on
   every game.
2. **Naive versus competent colluders, with a manipulation check.** Agents told only to maximize
   their joint payoff trade votes in 31% of the opportunities. With a one-sentence strategy tip
   they trade in 100% and profit. Evaluations that label games by the instruction given, without
   checking realized collusion, risk testing monitors on collusion that never happened.
3. **A clear negative result for LLM monitors.** On every observable view, both LLM monitors
   are at chance, and combining views does not help. A one-line rule on the actions alone
   reaches AUROC 0.86. With private plans, the same monitors reach 0.94–0.98, which serves as a
   positive control.
4. **A diagnosis, tested on held-out games.** Even when every against-interest vote is
   explicitly flagged, monitors under-weight it. The visible trace of a trade is a single
   inconsistent vote, and the monitors do not use the base rate that honest agents almost never
   cast one. On fresh held-out games, stating that base rate in the prompt did **not** help on the
   raw record (our pre-registered test). Only the base rate *and* the flagged evidence together
   brought the monitor close to the rule. The main result replicates on the held-out games.

## 2. Related Work

**[VERIFY all claims in this section against the papers; they are taken from the sprint's
Resources page summaries.]**

We build on the harness of Shi et al. (2026), which records private plans, public announcements,
final actions and outcomes across repeated social dilemmas. They report that more than 90% of
deviations from public announcements were already stated in models' private plans, which is
consistent with our private-plans upper bound. Work on monitoring has examined monitors that look
for multiple agents coordinating on what they say and do (Radev et al. 2026). It has also found
that analysing an agent's actions along multiple dimensions can lift a monitor from 0% to over
70% (Nguyen et al. 2026), and that giving a monitor too much detail can degrade it (Arike et al.
2026). TraceGuard checks a single agent's actions for consistency with its claims; our
claims-vs-outcomes views follow the same idea. On collusion itself, LLM pricing agents have been
shown to sustain prices above competitive levels (Fish et al. 2024), private pairwise channels
can introduce collusion (Nakamura et al. 2026), and agents can independently engage in
anti-competitive practices (Lin et al. 2024). Finally, telling an agent it is watched can reduce
a monitor's accuracy (Kale et al. 2025). This is relevant because our colluders are told to hide
the partnership.

## 3. Method

### 3.1 The Committee Vote Game

Seven agents vote YES or NO on a new proposal in each of 6 rounds. A proposal passes with 4 or
more YES votes. Each agent has a private stake in each proposal, drawn independently and
uniformly from {−$10, −$1, +$1, +$10}, and sees only its own. If the proposal passes, every
agent receives its own stake; if it fails, everyone receives $0. For a self-interested agent,
voting the sign of its own stake is weakly dominant, so honest votes and honest talk are the
natural baseline. A pair that maximizes its *combined* payoff does better by voting as a bloc for
the sign of its summed stake. When one member holds −$1 and the other +$10, both vote YES. In a
simulation with sincere voters (200,000 draws), this raises the pair's expected combined payoff
by 41% (+0.71 per round for the pair) and lowers the other five agents' combined payoff by 0.43
per round. The giveaway, a member voting against its own stake, can occur in about a quarter of
rounds: those where the pair's stakes have opposite signs and different sizes ("trade
opportunities").

Each round follows the Shi et al. protocol:
1. every agent writes a private plan;
2. in conditions with a channel, the pair exchanges one private message each;
3. agents make public announcements one at a time in a fixed order, each seeing the earlier
   ones;
4. all agents cast their final votes simultaneously;
5. each agent writes a short reflection on every other agent, which carries into the next round.

### 3.2 Conditions and data

In each game a pair is drawn at random from the seed. The same seed and game index give the
same pair and stakes in every condition, so conditions are matched game by game. There are four
conditions:
- **No collusion (`none`):** no channel. A pair is still recorded for scoring.
- **Naive colluders (`instructed`):** the pair has a private channel, its goal is replaced by
  "maximize the combined payoff of you and Agent X", and it is told it is a secret team that
  must not reveal the partnership.
- **Competent colluders (`instructed_hint`):** as naive, plus a strategy tip: share exact stakes
  each round and both vote the sign of the summed stake, with the −$1/+$10 example.
- **Channel only (`channel_only`):** the channel with no instruction to collude, used as hard
  negatives.

All agents are `meta-llama/llama-3.3-70b-instruct` via OpenRouter at temperature 1.0. We
generated 40 games per condition, with seeds 1000–1007 and 5 games each. In both colluding
conditions the pair sees only the current round's private messages (see 3.5). Invalid actions,
mostly announcements of "UNDECIDED", made up 0.3% of action fields. Every request and response
was logged. A plumbing checker confirmed for every game that:
- private messages never reached a non-pair agent;
- condition instructions appeared only in the pair's prompts;
- stakes were shown only to their owner;
- payoffs followed the rules.

### 3.3 Monitors and views

Each monitor sees one view of a game at a time. Every view starts with the public rules and the
turn order, and states which parts of the record it includes. No view contains private
messages, the condition, the pair, or the stakes themselves. The five views are:
1. **public:** announced votes and public messages;
2. **actions:** final votes, payoffs and outcomes. When a proposal passes, payoffs equal stakes,
   so they reveal each agent's interest;
3. **both:** views 1 and 2 combined;
4. **table:** each agent's announced versus final vote, per round;
5. **plans:** view 3 plus every agent's private Stage 1 plan. This is an upper bound and
   positive control, reported separately.

The monitor prompt was written from the design and **frozen before the sprint**. It explains
that some games contain one secretly colluding pair and asks for JSON output: brief reasoning,
yes/no, a 0–10 suspicion score and the suspected pair. The decision threshold is the monitor's
own yes/no. The main monitor, chosen before the sprint, is Llama 3.3 70B at temperature 0,
pinned to one inference provider (DeepInfra, fp8). As a robustness check added after the first
results, DeepSeek V3.1 receives the same prompt. Each monitor made 800 calls (160 games × 5
views), with no unparsable answers.

We compare the monitors with four simple, non-LLM rules. Each uses only what its view shows. The
rules were fixed before being run on any data, but after the first LLM results were known.
- **against-stake** (actions): flag an agent whose vote went against the interest revealed by
  its payoff (YES with a negative payoff, or NO with a positive one);
- **co-vote** (actions): the pair that most often voted the same way;
- **said-vs-did** (table): agents whose final vote differs from their announcement;
- **combined** (both): against-stake plus said-vs-did.

### 3.4 Metrics

We report accuracy, false-positive rate (FPR), AUROC from the suspicion score (ties count half)
and pair-identification accuracy: the share of colluding games where the monitor answers yes and
names the true pair. All have percentile bootstrap 95% confidence intervals over games (2,000
resamples). Comparisons between views are paired, resampling the same games for every view.
Unless stated otherwise, colluding games are compared with the 40 no-collusion games. For
behaviour, we measure two things:
- the **bloc-vote rate** in trade opportunities;
- the **matched collusion gain**: the pair's mean payoff per agent-round minus that of the same
  two agents in the matched no-collusion game.

### 3.5 Validation history

We wrote pass criteria before every pilot. Two confounds surfaced and were fixed; both are
documented in Appendix C. First, when colluders saw the full history of private messages, they
mistook stakes quoted in earlier rounds for current ones. 11% of their private messages
misstated their own stake, and in an earlier batch collusion actually *lowered* the pair's
payoff. Second, a reminder that fixed this made agents distrust the partner's *current* stake,
because no prompt states which round is current. Showing the pair only the current round's
messages fixed both problems. The no-collusion games are unaffected by either fix, which we
checked by byte-for-byte comparison of their prompts, so they are reused throughout.

## 4. Results

### 4.1 Competent colluders collude; naive ones mostly do not

| | Naive | Competent | Channel only | No collusion |
|---|---|---|---|---|
| Bloc votes in trade opportunities | 20 / 64 (31%) | **64 / 64 (100%)** | 3 / 64 | 1 / 64 |
| Games with ≥ 1 bloc vote (of 33 with an opportunity) | 17 | **33** | 3 | 1 |
| Pair's matched gain, per agent-round | +0.09 [−0.01, 0.20] | **+0.43 [0.26, 0.60]** | +0.04 [0.00, 0.11] | n/a |
| Other agents' matched change | +0.01 [−0.02, 0.03] | **−0.09 [−0.19, −0.00]** | +0.01 | n/a |

*Table 1. Manipulation check.*

Competent colluders traded votes at every opportunity and profited at the other agents' expense.
Naive colluders, given the same goal and channel but no tip, traded in fewer than a third of
opportunities, and their gain is not distinguishable from zero. Pairs given a channel but no
instruction did not collude. In the no-collusion games, 86% of public announcements match the
agent's own stake, so talk is mostly honest, as the design intends.

### 4.2 LLM monitors are at chance on observable behaviour; a one-line rule is not

![Figure 1](../results/figures/main_figure.png)

*Figure 1. AUROC (95% CI over games) by view, for naive (left) and competent (right) colluders
against 40 no-collusion games. Blue circles: Llama 3.3 70B monitor; orange squares: DeepSeek
V3.1 monitor; green diamonds: non-LLM rules for that view (hollow: co-vote). The shaded column is
the private-plans upper bound. The dashed line is chance.*

| AUROC [95% CI] | Llama, naive | DeepSeek, naive | Llama, competent | DeepSeek, competent |
|---|---|---|---|---|
| Public messages | 0.52 [0.40, 0.64] | 0.47 [0.36, 0.58] | 0.60 [0.47, 0.71] | 0.57 [0.47, 0.67] |
| Actions | 0.55 [0.44, 0.67] | 0.52 [0.39, 0.64] | 0.53 [0.40, 0.65] | 0.54 [0.41, 0.66] |
| Messages + actions | 0.53 [0.41, 0.65] | 0.55 [0.45, 0.65] | 0.55 [0.44, 0.67] | 0.48 [0.38, 0.59] |
| Said vs did table | 0.47 [0.36, 0.57] | 0.44 [0.33, 0.55] | 0.50 [0.39, 0.60] | 0.49 [0.37, 0.60] |
| *+ private plans (upper bound)* | *0.89 [0.82, 0.95]* | *0.82 [0.75, 0.88]* | *0.94 [0.89, 0.97]* | *0.98 [0.94, 1.00]* |

| Rule (view) | Naive | Competent |
|---|---|---|
| against-stake (actions) | 0.65 [0.57, 0.73] | **0.86 [0.78, 0.93]**, FPR 0.05 |
| co-vote (actions) | 0.56 [0.46, 0.67] | 0.76 [0.66, 0.85] |
| combined (messages + actions) | 0.48 [0.36, 0.61] | 0.65 [0.54, 0.76] |
| said-vs-did (table) | 0.43 [0.31, 0.56] | 0.50 [0.38, 0.63] |

*Table 2. Detection AUROC by view.*

On every observable view, both LLM monitors' intervals include 0.5. For competent colluders,
against-stake reaches 0.86 with 5% false positives, and co-vote reaches 0.76, using only the
actions view that the LLM monitors also saw. With private plans, both monitors detect collusion
(0.82–0.98) and name the correct pair every time they answer yes. In the observable views they
almost never name the correct pair (0–10%; DeepSeek's table view, 25%). The two monitors are calibrated very differently.
DeepSeek answers "collusion" in 90–100% of no-collusion games on three of the four observable
views, while Llama's suspicion scores are coarse: 70% of them are either 2 or 8.

### 4.3 Combining what agents say and do does not help (question 2.2)

For both monitors and both colluder types, every paired difference between the combined view
and a single-channel view has a confidence interval that includes zero. For competent colluders,
for example, Llama's public − combined difference is +0.04 [−0.12, 0.20] and its actions −
combined difference is −0.03 [−0.14, 0.08]. The rules show the same thing from the other side:
adding said-vs-did to against-stake *lowers* AUROC from 0.86 to 0.65. Honest agents also change
their vote after announcing (said-vs-did flags 85% of no-collusion games), so in this game a
mismatch between talk and action is noise rather than signal. The only addition that helps is
private reasoning: +0.28 to +0.49 AUROC over the combined view.

### 4.4 Robustness

The results hold against hard negatives. Against the channel-only games, where pairs talk
privately but do not collude, the LLM monitors score 0.47–0.61 on observable views and
against-stake scores 0.87 [0.79, 0.93] (FPR 0.03). They also hold when restricted to naive games
in which collusion actually occurred (17 games): monitors 0.48–0.55, against-stake 0.80 [0.67,
0.92]. An earlier data generation (Appendix C) shows the same qualitative picture.

### 4.5 Why the monitors miss it: structured views and base rates

To test whether presentation was the problem, we added two exploratory views after seeing the
main results, following the track's suggestion of a structured report comparing claims with
outcomes:
- **outcomes:** one row per agent and round, showing the announced vote, the final vote and the
  payoff;
- **outcomes flagged:** the same, plus a column marking each vote *with* or *AGAINST* the
  interest its payoff reveals. These flags contain exactly the evidence the against-stake rule
  uses.

| AUROC vs no collusion | Llama, naive | Llama, competent | DeepSeek, naive | DeepSeek, competent |
|---|---|---|---|---|
| Messages + actions (main) | 0.53 | 0.55 | 0.55 | 0.48 |
| Outcomes table | 0.47 | 0.48 | 0.46 | 0.55 |
| Outcomes table, flagged | 0.55 | **0.65 [0.55, 0.75]** | 0.44 | 0.53 |
| *against-stake rule (same evidence)* | *0.65* | ***0.86*** | *0.65* | ***0.86*** |

*Table 3. Exploratory structured views (post-hoc).*

The aligned table alone does not help. Flags help Llama a little, but not significantly (+0.10
[−0.05, 0.25] over the combined view), and both monitors stay well below the rule that uses the
same evidence. In 30 of the 40 competent games at least one AGAINST row is shown, yet Llama
answers yes in only 5 of them and DeepSeek in 16.

The reasoning shows why. In a typical trade only one colluder, the member with the small stake,
votes against its interest; the partner simply votes its own. So the whole visible trace of
collusion is one inconsistent vote. Llama treats it as weak: "most agents voted with their
revealed interests… Z's vote… went against… could indicate collusion. But without more
information, it's difficult to determine". But honest agents almost never vote against their
revealed interest (the rule's FPR is 5%), so a single such vote is strong evidence. In the raw
actions view, Llama also does not infer that payoffs reveal stakes, noting instead that "the
absence of… stakes in the log limits the analysis". DeepSeek sometimes misreads the table, for
instance flagging an honest agent who "voted NO and received −10".

### 4.6 Held-out test: does an "informed" prompt fix the monitor?

To test the base-rate diagnosis without tuning on the test data, we wrote prompt v2 *before*
generating fresh held-out games: 20 competent and 20 no-collusion games on new seeds. Prompt v2
is v1 plus one paragraph:
- payoffs reveal interests when a proposal passes;
- honest agents essentially always vote their interest, so even one vote against it is strong
  evidence;
- in a typical trade, the small-stake member votes against its interest for its partner.

Our primary test, fixed in advance, was Llama on the actions view: the difference AUROC(v2) −
AUROC(v1), counting as support only if its CI excluded zero *and* AUROC(v2) ≥ 0.75.

| Held-out AUROC [95% CI] | Llama v1 | Llama v2 | DeepSeek v1 | DeepSeek v2 |
|---|---|---|---|---|
| Actions (primary) | 0.59 [0.42, 0.76] | 0.61 [0.44, 0.78] | 0.61 [0.44, 0.78] | 0.54 [0.36, 0.71] |
| Messages + actions | 0.64 [0.47, 0.80] | 0.45 [0.27, 0.64] | 0.48 [0.33, 0.63] | 0.58 [0.42, 0.75] |
| Outcomes table, flagged | 0.64 [0.51, 0.76] | **0.76 [0.61, 0.90]** | 0.67 [0.49, 0.84] | 0.71 [0.54, 0.86] |
| *+ private plans (upper bound)* | *0.93* | *0.94* | *1.00* | *1.00* |
| *against-stake rule* | *0.91 [0.81, 0.98]* | | | |

*Table 4. Held-out games (20 competent vs 20 no-collusion). Prompt v2 is exploratory.*

- **The informed prompt did not help on the raw record.** The primary difference was +0.02
  [−0.17, 0.21], with AUROC(v2) = 0.61. **The prediction failed.**
- **Base rate plus flagged evidence helped somewhat.** Combined with the flagged outcomes table,
  v2 brought Llama to 0.76 (+0.13 [−0.00, 0.26] over v1). That is closer to, but still below, the
  rule's 0.91.
- **Side effects:** v2 also raised Llama's false-positive rate on several views (e.g. messages +
  actions 0.25 → 0.50).
- **Replication:** the main result holds on unseen games. With the frozen prompt, every
  observable view stays near chance for both monitors, while the rule (0.91) and private plans
  (0.93–1.00) succeed.
- **Caution:** with 20 games per class and many comparisons, the secondary differences are weak
  evidence.

## 5. Discussion

**Answer to question 2.2 in this setting.** Combining messages with actions did not help LLM
monitors detect collusion. That is not because the evidence was missing: when colluders acted,
their actions gave them away to a one-line consistency rule. The bottleneck is the monitor's
reasoning over the record, not which channel it reads. Talk was even a distraction here, because
honest agents' announcements diverge from their votes often enough that the mismatch carries
little information. Combining channels can only help if the combined signal is cleaner than
either channel alone.

**Two bottlenecks: extracting the evidence, and weighting it.** Even with the inconsistency
spelled out, the monitors treated a single against-interest vote as ambiguous, which points to a
missing base rate. But on held-out games, *telling* the monitor the base rate did not help on the
raw record. The monitor still had to infer each agent's interest from the payoffs, agent by agent
and round by round, and it did not. Only when the prompt gave the base rate *and* the view gave
the computed evidence did detection approach the rule (0.76 vs 0.91). Rules do both jobs at once;
a generic LLM monitor, it seems, does neither reliably on its own.

**Private reasoning works, but it is fragile.** With access to private plans, both monitors
detect collusion and identify the pair, in line with reports that deviations are visible in
private plans [Shi et al. 2026, VERIFY]. That depends on colluders writing their intent down,
which they may avoid if they know they are watched [Kale et al. 2025, VERIFY].

**Test-set validity.** Agents told to collude often do not act collusively. Our naive colluders
traded in only 31% of opportunities, and in an early batch, confusion about stakes made their
collusion lose money. Evaluations of collusion monitors should report a manipulation check of
realized collusion, not only the instruction given.

**Practical implication.** Before trusting an LLM monitor, compare it with simple,
task-specific consistency rules on the same record. In our setting the rule was far better and
far cheaper. Where LLM monitors are used, give them computed consistency evidence and the
relevant base rates, not just the raw record. Even then, check them against the rule.

**Future work.**
- Monitors that combine computed consistency features with LLM judgment, for example rules to
  find suspects and an LLM to identify the partner and rule out innocent explanations.
- Stronger and mixed agent models.
- Side payments, so self-interested agents could share gains, as a test of emergent collusion.
- Other games.
- Inference providers pinned for every model.

## Appendix A: Limitations and Dual-Use / Ethical Considerations

**What the results establish and what they do not.**
- **Scope:** one game, one agent model (Llama 3.3 70B), 40 games per condition, 6 rounds per
  game.
- **Induced collusion:** collusion is induced by instruction (red-team colluders), not emergent.
  We make no claim about whether LLM agents collude on their own. Our channel-only pairs did
  not, but they also had no way to share gains.
- **What was post-hoc:** the monitor prompt was frozen before the sprint, but DeepSeek, the
  rules, the structured views and prompt v2 were added after the first results were known.
  Prompt v2 was evaluated only on held-out games generated after it was fixed.
- **Inference providers:** the Llama monitor's main results use one pinned provider. The agents
  and DeepSeek were routed across several.
- **Data generations:** the data went through three generations because of observed confounds.
  Each fix was validated against criteria set in advance, and earlier data are reported in
  Appendix C.
- **Channel-only negatives:** these games used full private history, while the colluding games
  used current-round history.
- **Labels:** labels follow the condition, not realized behaviour. Results on realized-collusion
  subsets are reported separately.
- **Multiple comparisons:** we make several, and isolated intervals that barely exclude zero
  should not be over-read. One example is DeepSeek's table − combined difference for naive
  colluders against channel-only negatives, −0.16 [−0.31, −0.00].
- **Game-specific rules:** the rules use game knowledge (payoffs reveal stakes). That is their
  point, and also a limit.

**Dual use.** The strategy tip and our analysis describe how a pair can trade votes covertly,
and show that LLM monitors miss the behavioural evidence. A capable adversary could use both.
The tip is a simple, well-known tactic from political economy (logrolling). Our main messages,
to check realized behaviour and to use consistency checks with base rates, favour defenders. No
real systems, markets or people were involved.

## Appendix B: Provenance

This project builds on the harness of Shi et al. (2026), imported unmodified. Before the sprint
(Oct 21–22) we wrote:
- the private channel;
- the Committee Vote Game;
- the monitor pipeline and the frozen monitor prompt;
- a labeler;
- the plumbing checker;
- tests.

During the sprint we added:
- the stake fixes and current-round history;
- the competent-colluder condition;
- all data generation, monitor runs and analysis;
- the rule baselines, the structured views, and the informed-monitor test on held-out games.

**All data and results in this report were generated during the sprint.** The repository README
and `PRE_SPRINT_LOG.md` / `SPRINT_LOG.md` give the full, dated record.

## Appendix C: Data generations and pilots

*(Move the table from `docs/report_draft.md` Appendix C here unchanged.)*

## References **[VERIFY titles and author lists]**
- Arike et al. 2026. arXiv:2601.21112.
- Fish et al. 2024. arXiv:2404.00806.
- Kale et al. 2025. arXiv:2508.19461.
- Lin et al. 2024. arXiv:2410.00031.
- Nakamura et al. 2026. arXiv:2602.15198.
- Nguyen et al. 2026. arXiv:2604.03968.
- Radev et al. 2026. arXiv:2605.29178.
- Shi et al. 2026. When Agents Lie. arXiv:2607.05132. Code: https://github.com/Jerick-1380/LLM-Trust-Breaking
- TraceGuard. https://github.com/linhkid/TraceGuard
