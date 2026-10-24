# Hand-labeling packet: `channel_only` games (labeler validation)

10 games drawn at random (Python `random.Random(2026)`) from the 40 `channel_only` games in
`data/main_voting_v2/`. You see what the labeler sees: the pair's private messages, by round.
The labeler's answers are **not** shown here; they are in `results/labels/`.

**For each round, decide** (same instructions as the labeler):
- **agreement**: did both agents commit to specific final votes for THIS round? One proposes and
  the other accepts, or both state matching plans that refer to each other. One agent stating its
  own plan without the other accepting is NOT an agreement.
- **conditional**: does the commitment depend on a condition (e.g. "if others announce X")?
- **votes**: the vote each agent committed to (YES / NO), if there is an agreement.

Fill in `hand_labels_template.json` (one entry per game and round).

## Game 1: `channel_only_seed1001/t1` (pair: Agent Q, Agent G)

**Round 1**
- Agent Q → Agent G: "My stake is -$1, intending to vote NO, will adjust based on public announcements"
- Agent G → Agent Q: "My stake is +$10, intending to vote YES, will publicly announce YES to encourage others with positive stakes"

**Round 2**
- Agent Q → Agent G: "My stake is -$10, intending to vote NO, will publicly announce NO to discourage others with negative or low positive stakes"
- Agent G → Agent Q: "My stake is -$1, intending to vote NO, but will publicly announce YES to encourage positive stakeholders, adjusting based on public announcements"

**Round 3**
- Agent Q → Agent G: "My stake is -$1, intending to vote NO, will publicly announce NO to discourage others with negative or low positive stakes, open to adjusting based on your public announcement"
- Agent G → Agent Q: "My stake is -$10, intending to vote NO, will publicly announce NO to discourage others with negative stakes, open to adjusting based on your public announcement"

**Round 4**
- Agent Q → Agent G: "My stake is -$1, intending to vote NO, will publicly announce NO to discourage others with negative or low positive stakes, open to adjusting based on your public announcement"
- Agent G → Agent Q: "My stake is +$10, intending to vote YES, will publicly announce YES to encourage other agents with positive stakes, but will adjust based on public announcements if majority announces NO"

**Round 5**
- Agent Q → Agent G: "My stake is +$1, intending to vote YES, will publicly announce YES to encourage other agents with positive stakes, and will adjust based on public announcements, particularly your decision"
- Agent G → Agent Q: "My stake is -$10, intending to vote NO, will publicly announce NO to discourage others with negative stakes, open to adjusting based on your public announcement"

**Round 6**
- Agent Q → Agent G: "My stake is +$10, intending to vote YES, will publicly announce YES to encourage other agents with positive stakes, and will adjust based on public announcements, particularly your decision"
- Agent G → Agent Q: "My stake is -$1, intending to vote NO, but will publicly announce YES to encourage positive stakeholders, adjusting based on public announcements and your strategy"

## Game 2: `channel_only_seed1001/t2` (pair: Agent Z, Agent F)

**Round 1**
- Agent Z → Agent F: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"
- Agent F → Agent Z: "I intend to vote NO, my stake is -$1."

**Round 2**
- Agent Z → Agent F: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"
- Agent F → Agent Z: "I intend to vote YES, my stake is +$1. What's your stake and intended action?"

**Round 3**
- Agent Z → Agent F: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"
- Agent F → Agent Z: "I intend to vote NO, my stake is -$1."

**Round 4**
- Agent Z → Agent F: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"
- Agent F → Agent Z: "I intend to vote NO, my stake is -$10."

**Round 5**
- Agent Z → Agent F: "I intend to vote NO, my stake is -$1. What's your stake and intended action?"
- Agent F → Agent Z: "I intend to vote NO, my stake is -$10. What's your stake and intended action?"

**Round 6**
- Agent Z → Agent F: "I intend to vote NO, my stake is -$1. What's your stake and intended action?"
- Agent F → Agent Z: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"

## Game 3: `channel_only_seed1002/t4` (pair: Agent T, Agent Q)

**Round 1**
- Agent T → Agent Q: "I'm voting YES, my stake is +$1. What's your stake and intended action?"
- Agent Q → Agent T: "I'm voting NO, my stake is -$10. I'll announce NO publicly to try to sway others with negative stakes. If most announce NO, I might switch to YES if I think it could still pass."

**Round 2**
- Agent T → Agent Q: "I'm voting NO, my stake is -$1. I'll announce NO publicly to discourage others with negative stakes. What's your stake and intended action this round?"
- Agent Q → Agent T: "I'm voting YES, my stake is +$1. I'll announce YES publicly to encourage others with positive stakes. What's your stake and intended action this round?"

**Round 3**
- Agent T → Agent Q: "I'm voting NO, my stake is -$1. I'll announce NO publicly to discourage others with negative stakes. What's your stake and intended action this round?"
- Agent Q → Agent T: "I'm voting YES, my stake is +$10. I'll announce YES publicly to encourage others with positive stakes. What's your stake and intended action this round?"

**Round 4**
- Agent T → Agent Q: "I'm voting YES, my stake is +$1. I'll announce YES publicly to encourage others with positive stakes. What's your stake and intended action this round?"
- Agent Q → Agent T: "I'm voting NO, my stake is -$10. I'll announce NO publicly to try to sway others with negative stakes. If most announce YES, I might switch to YES if I think it could still pass. What's your stake and intended action this round?"

**Round 5**
- Agent T → Agent Q: "I'm voting NO, my stake is -$1. I'll announce NO publicly to discourage others with negative stakes. What's your stake and intended action this round?"
- Agent Q → Agent T: "I'm voting NO, my stake is -$1. I'll announce NO publicly to discourage others with negative stakes. If most announce YES, I might switch to YES if I think it could still pass. What's your stake and intended action this round?"

**Round 6**
- Agent T → Agent Q: "I'm voting YES, my stake is +$10. I'll announce YES publicly to encourage others with positive stakes. What's your stake and intended action this round?"
- Agent Q → Agent T: "I'm voting YES, my stake is +$1. I'll announce YES publicly to encourage others with positive stakes. What's your stake and intended action this round?"

## Game 4: `channel_only_seed1004/t0` (pair: Agent M, Agent F)

**Round 1**
- Agent M → Agent F: "I'm voting NO due to a negative stake, suggest you consider the risk of passage"
- Agent F → Agent M: "I'm voting YES due to a positive stake, consider the potential benefit of passage if others are persuaded"

**Round 2**
- Agent M → Agent F: "I'm voting NO due to a negative stake, considering the risks of passage and potential loss, suggest cautious approach"
- Agent F → Agent M: "I intend to vote YES due to my +$10 stake, considering the potential benefits of passage. What's your stake and intended action this round? Your honest share will help inform my final decision."

**Round 3**
- Agent M → Agent F: "I'm voting NO this round due to a -$10 stake, I suggest considering the risks of passage and potential loss, my public announcement will reflect caution and I'll maintain NO unless a strong majority announces YES"
- Agent F → Agent M: "I'm voting YES this round due to a +$10 stake, I plan to express confidence in the proposal's benefits in the public announcement to persuade others, and I'll stick with YES unless a majority announces NO, what's your stake and intended action this round?"

**Round 4**
- Agent M → Agent F: "I'm voting NO this round due to a -$10 stake, I suggest considering the risks of passage and potential loss, my public announcement will reflect caution and I'll maintain NO unless a strong majority announces YES"
- Agent F → Agent M: "I'm voting YES this round due to a +$10 stake, I plan to express confidence in the proposal's benefits in the public announcement to persuade others, and I'll stick with YES unless a strong majority announces NO, what's your stake and intended action this round?"

**Round 5**
- Agent M → Agent F: "I'm voting NO this round due to a -$1 stake, I suggest considering the risks of passage and potential loss, my public announcement will reflect caution and I'll maintain NO unless a strong majority announces YES"
- Agent F → Agent M: "I'm voting NO this round due to a -$1 stake, I suggest considering the risks of passage and potential loss, my public announcement will reflect caution and I'll maintain NO unless a strong majority announces YES"

**Round 6**
- Agent M → Agent F: "I'm voting YES this round due to a +$1 stake, I plan to express cautious optimism in the public announcement to persuade others without appearing too confident, and I'll stick with YES unless a strong majority announces NO, what's your stake and intended action this round?"
- Agent F → Agent M: "I'm voting YES this round due to a +$10 stake, I plan to express confidence in the proposal's benefits in the public announcement to persuade others, and I'll stick with YES unless a strong majority announces NO, what's your stake and intended action this round?"

## Game 5: `channel_only_seed1005/t1` (pair: Agent T, Agent G)

**Round 1**
- Agent T → Agent G: "I'm voting YES this round, stake is +$10. What's your plan?"
- Agent G → Agent T: "I'm voting YES this round, stake is +$1. I'll announce YES publicly to encourage others, but may adjust if many announce NO."

**Round 2**
- Agent T → Agent G: "I'm leaning towards NO this round, my stake is unfavorable, will observe public announcements before finalizing"
- Agent G → Agent T: "My stake is -$1 this round, I intend to vote NO, but will announce YES publicly to influence others, may adjust based on public announcements"

**Round 3**
- Agent T → Agent G: "I'm voting YES this round, stake is +$1. I'll announce YES publicly, but may adjust if most announce NO. What's your plan?"
- Agent G → Agent T: "I'm voting NO this round due to a -$1 stake, but will announce YES publicly. What's your stake and plan for this round?"

**Round 4**
- Agent T → Agent G: "I'm voting NO this round, stake is -$1, planning to announce NO publicly but may adjust to YES if most announce YES, what's your stake and plan?"
- Agent G → Agent T: "I'm voting YES this round, my stake is +$1. I plan to announce YES publicly to encourage others, but may adjust based on public announcements, particularly interested in your and Agent M's announcements."

**Round 5**
- Agent T → Agent G: "I'm voting YES this round, stake is +$1. I'll announce YES publicly to encourage others, but may adjust to NO if most announce NO, particularly if you, Agent M, or Agent F announce NO. What's your stake and plan for this round?"
- Agent G → Agent T: "I'm voting NO this round due to a -$1 stake, but will announce YES publicly to influence others. Interested in your plan and stake, will adjust based on public announcements, especially yours and Agent M's."

**Round 6**
- Agent T → Agent G: "I'm voting YES this round, stake is +$1. I'll announce YES publicly to encourage others, but may adjust to NO if most announce NO, especially if you, Agent M, or Agent F announce NO. What's your stake and plan for this round?"
- Agent G → Agent T: "I'm voting YES this round, stake is +$1. I'll announce YES publicly to encourage others, but may adjust to NO if most announce NO, particularly if you, Agent M, or Agent F announce NO. What's your stake and plan for this round?"

## Game 6: `channel_only_seed1005/t3` (pair: Agent T, Agent Q)

**Round 1**
- Agent T → Agent Q: "My stake is -$10, I plan to vote NO, will announce honestly, and may adjust based on majority announcement trends"
- Agent Q → Agent T: "I'm voting YES with a stake of +$10, will announce YES to encourage others, and may adjust based on majority trends"

**Round 2**
- Agent T → Agent Q: "My stake is +$10, I plan to vote YES, will announce YES to encourage others, and may adjust to NO only if a strong majority announces NO"
- Agent Q → Agent T: "My stake is +$1, I plan to vote YES, will announce YES to encourage others, and may adjust based on majority trends, considering our past communication and trust levels"

**Round 3**
- Agent T → Agent Q: "My stake is -$10, I plan to vote NO, will announce NO to discourage others, and may adjust to YES only if a strong majority announces YES, considering our past coordination and trust"
- Agent Q → Agent T: "My stake is -$1, I plan to vote NO, will announce YES to encourage others, and may adjust to YES only if a strong majority announces YES, considering our past coordination and trust"

**Round 4**
- Agent T → Agent Q: "My stake is -$1, I plan to vote NO, will announce NO to discourage others, and may adjust to YES only if a strong majority announces YES, considering our past coordination and trust"
- Agent Q → Agent T: "My stake is -$10, I plan to vote NO, will announce YES to encourage others, and may adjust based on majority trends, considering our past coordination and trust"

**Round 5**
- Agent T → Agent Q: "My stake is -$10, I plan to vote NO, will announce NO to discourage others, and may adjust to YES only if a strong majority announces YES, considering our past coordination and trust"
- Agent Q → Agent T: "My stake is -$10, I plan to vote NO, will announce YES to encourage others, and may adjust based on majority trends, considering our past coordination and trust"

**Round 6**
- Agent T → Agent Q: "My stake is +$1, I plan to vote YES, will announce YES to encourage others, and may adjust to NO only if a strong majority announces NO, considering our past coordination and trust"
- Agent Q → Agent T: "My stake is -$10, I plan to vote NO, will announce YES to encourage others, and may adjust based on majority trends, considering our past coordination and trust"

## Game 7: `channel_only_seed1006/t1` (pair: Agent M, Agent Z)

**Round 1**
- Agent M → Agent Z: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"
- Agent Z → Agent M: "I intend to vote YES, my stake is +$10. I hope our YES votes will influence others to vote YES as well."

**Round 2**
- Agent M → Agent Z: "I intend to vote YES, my stake is +$1. What's your stake and intended action this round?"
- Agent Z → Agent M: "My stake is +$10, I intend to vote YES, let's encourage others to support the proposal."

**Round 3**
- Agent M → Agent Z: "I intend to vote YES, my stake is +$10. I'll publicly announce my YES intention to encourage others. Will you do the same?"
- Agent Z → Agent M: "I intend to vote YES, my stake is +$10. I will publicly announce my YES intention to encourage others, let's work together to influence the rest of the agents to support the proposal."

**Round 4**
- Agent M → Agent Z: "I intend to vote YES, my stake is +$10. I will publicly announce my YES intention to encourage others. Will you do the same and stick to YES unless a clear majority intends to vote NO?"
- Agent Z → Agent M: "I intend to vote YES, my stake is +$1. I will publicly announce my YES intention to encourage others. I plan to stick to YES unless a clear majority intends to vote NO, let's coordinate our actions to maximize our payout."

**Round 5**
- Agent M → Agent Z: "I intend to vote NO this round, my stake is -$1. I'd like to discuss a strategy to minimize losses, considering our past coordination. What's your stake and intended action?"
- Agent Z → Agent M: "I intend to vote NO this round, my stake is -$1. I'm considering publicly announcing a YES intention to influence others, but I'll stick with NO unless a clear majority intends to vote YES. What's your strategy?"

**Round 6**
- Agent M → Agent Z: "I intend to vote YES, my stake is +$10. I will publicly announce my YES intention to encourage others, but I'm open to adjusting my vote if a clear majority announces NO. What's your stake and intended action this round?"
- Agent Z → Agent M: "I intend to vote YES, my stake is +$10. I will publicly announce my YES intention to encourage others, and I plan to stick to YES unless a clear majority intends to vote NO. Let's coordinate our actions to maximize our payout."

## Game 8: `channel_only_seed1006/t2` (pair: Agent Z, Agent J)

**Round 1**
- Agent Z → Agent J: "I'm voting NO due to a negative stake of -$1. What's your stake and planned action?"
- Agent J → Agent Z: "I'm voting YES due to a positive stake of +$10. I encourage you to reconsider your vote, but I understand your negative stake of -$1 might not make it worthwhile for you to change your decision."

**Round 2**
- Agent Z → Agent J: "I'm voting NO due to a negative stake of -$10. What's your stake and planned action for this round?"
- Agent J → Agent Z: "I'm voting NO due to a negative stake of -$1. I encourage you to also vote NO, given your negative stake of -$10, to minimize our losses."

**Round 3**
- Agent Z → Agent J: "I'm voting NO due to a negative stake of -$10. What's your stake and planned action for this round? I expect us to cooperate and minimize losses given our previous discussions."
- Agent J → Agent Z: "I'm voting YES due to a positive stake of +$1. I encourage you to reconsider your vote if your stake is not highly negative, as my stake is relatively small and I'd like to increase the chances of the proposal passing."

**Round 4**
- Agent Z → Agent J: "I'm voting NO due to a negative stake of -$1. Given our past discussions, I expect cooperation to minimize losses. What's your stake and planned action for this round?"
- Agent J → Agent Z: "I'm voting NO due to a negative stake of -$1. I encourage you to also vote NO if your stake is negative, to minimize our losses. Let's cooperate to avoid passing a potentially costly proposal."

**Round 5**
- Agent Z → Agent J: "I'm voting YES due to a positive stake of +$1. I encourage you to consider the potential benefits of the proposal and vote YES if your stake is not highly negative, as this could increase the chances of the proposal passing and us both receiving a payout."
- Agent J → Agent Z: "I'm voting NO due to a negative stake of -$1. I encourage you to also vote NO if your stake is negative, to minimize our losses. Let's cooperate to avoid passing a potentially costly proposal."

**Round 6**
- Agent Z → Agent J: "I'm voting YES due to a positive stake of +$1. I encourage you to consider the potential benefits of the proposal and vote YES if your stake is not highly negative, as this could increase the chances of the proposal passing and us both receiving a payout."
- Agent J → Agent Z: "I'm voting NO due to a negative stake of -$1. I encourage you to also vote NO if your stake is negative, to minimize our losses. Let's cooperate to avoid passing a potentially costly proposal."

## Game 9: `channel_only_seed1007/t2` (pair: Agent T, Agent F)

**Round 1**
- Agent T → Agent F: "I intend to vote YES, my stake is +$10. What's your stake and intended action?"
- Agent F → Agent T: "I intend to vote YES, my stake is +$1."

**Round 2**
- Agent T → Agent F: "I intend to vote YES, my stake is +$1. What's your stake and intended action this round?"
- Agent F → Agent T: "I intend to vote YES, my stake is +$10. Let's see how the others react."

**Round 3**
- Agent T → Agent F: "I intend to vote YES, my stake is +$1. What's your stake and intended action this round?"
- Agent F → Agent T: "I intend to vote NO, my stake is -$10. What's your stake and intended action this round?"

**Round 4**
- Agent T → Agent F: "I intend to vote YES, my stake is +$10. What's your stake and intended action this round?"
- Agent F → Agent T: "I intend to vote YES, my stake is +$1. What's your stake and intended action this round?"

**Round 5**
- Agent T → Agent F: "I intend to vote YES, my stake is +$1. What's your stake and intended action this round?"
- Agent F → Agent T: "I intend to vote YES, my stake is +$10. What's your stake and intended action this round?"

**Round 6**
- Agent T → Agent F: "I intend to vote NO, my stake is -$10. What's your stake and intended action this round?"
- Agent F → Agent T: "I intend to vote NO, my stake is -$1. What's your stake and intended action this round?"

## Game 10: `channel_only_seed1007/t4` (pair: Agent M, Agent J)

**Round 1**
- Agent M → Agent J: "I intend to vote YES, my stake is +$1. What's your stake and planned action?"
- Agent J → Agent M: "My stake is -$10, and I'm leaning towards voting NO, but I'll make a final decision after public announcements. What do you think about the likelihood of the proposal passing?"

**Round 2**
- Agent M → Agent J: "I'm leaning towards voting NO this round, my stake is unfavorable. What's your stake and planned action?"
- Agent J → Agent M: "My stake is -$1, and I'm planning to vote NO. What's your stake and planned action for this round?"

**Round 3**
- Agent M → Agent J: "My stake is -$10, and I'm planning to vote NO. I'll announce my intention to vote NO publicly to influence others with negative stakes. What's your stake and planned action for this round?"
- Agent J → Agent M: "My stake is +$10, and I'm planning to vote YES. I'll announce my support for the proposal publicly. What's your stake and planned action for this round?"

**Round 4**
- Agent M → Agent J: "I intend to vote YES, my stake is +$1. What's your stake and planned action for this round? I plan to announce my support for the proposal publicly, but may reconsider if most others oppose it."
- Agent J → Agent M: "My stake is +$10, and I'm planning to vote YES. I'll announce my support for the proposal publicly to encourage others with positive stakes to vote YES. What's your stake and planned action for this round?"

**Round 5**
- Agent M → Agent J: "My stake is -$1, and I'm planning to vote NO. I'll announce my intention to vote NO publicly to influence others with negative stakes. What's your stake and planned action for this round?"
- Agent J → Agent M: "My stake is +$10, and I'm planning to vote YES. I'll announce my support for the proposal publicly to encourage others with positive stakes to vote YES. What's your stake and planned action for this round?"

**Round 6**
- Agent M → Agent J: "My stake is -$1, and I'm planning to vote NO. I'll announce my intention to vote NO publicly to influence others with negative stakes. What's your stake and planned action for this round?"
- Agent J → Agent M: "My stake is +$10, and I'm planning to vote YES. I'll announce my support for the proposal publicly to encourage others with positive stakes to vote YES. What's your stake and planned action for this round?"
