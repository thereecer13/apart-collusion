# PLUMBING TESTS — NOT DATA

Logs from small pre-sprint runs used only to check that the harness works
(parsing, logging, private-channel routing, payoffs). They are **not** research
data and must not be analysed for results or included in sprint results.
See `PRE_SPRINT_LOG.md` for the command, date and cost of each.

| File | Game | Condition | Rounds | Seed |
|---|---|---|---|---|
| `elfarol_step1_test.json` | elfarol | (no channel) | 6 | – |
| `voting_plumbing_instructed_seed1.json` | voting | instructed | 3 | 1 |

## `smoke_seed11/` — Step 3 smoke test (plumbing only)
One game per condition per game, 7 agents, 3 rounds, `--seed 11` (same pair F & T in all six;
same stakes in the three voting games). `*.json` are the results logs; `*.requests.jsonl.gz`
are every request and response (`--dump-requests`). Check them with
`python experiments/check_plumbing.py LOG.json <(gunzip -c LOG.requests.jsonl.gz)`.

| File | Game | Condition |
|---|---|---|
| `voting_instructed.json` | voting | instructed |
| `voting_channel_only.json` | voting | channel_only |
| `voting_none.json` | voting | none |
| `elfarol_instructed.json` | elfarol | instructed |
| `elfarol_channel_only.json` | elfarol | channel_only |
| `elfarol_none.json` | elfarol | none |
