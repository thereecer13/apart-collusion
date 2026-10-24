# Sprint data

## `main_voting_v1/`
Main Committee Vote Game batch (2026-10-23/24): seeds 1000–1007 × 5 trials × {instructed,
channel_only, none}, 7 agents, 6 rounds, Llama 3.3 70B, `--no-judge`, round-robin.
`<condition>_seed<S>.json` are the results logs, `dumps/` the gzipped request dumps, and
`checks/` the plumbing and behaviour outputs. See SPRINT_LOG.md, including the stake-confusion
issue found in this batch.
