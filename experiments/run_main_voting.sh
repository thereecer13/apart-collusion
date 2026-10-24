#!/usr/bin/env bash
# Main voting batch (see SPRINT_LOG.md): seeds 1000-1007 x 3 conditions x 5 trials, 6 rounds.
# Runs 12 jobs at a time. Logs to $OUT (default outputs/main_voting/), request dumps gzipped afterwards.
# v1: defaults. v2 (after the stake-reminder fix): OUT=outputs/main_voting_v2 CONDS="instructed channel_only"
set -u
cd "$(dirname "$0")/.."
source .venv/bin/activate
OUT=${OUT:-outputs/main_voting}
CONDS=${CONDS:-"instructed channel_only none"}
mkdir -p "$OUT/logs" "$OUT/dumps"
for seed in 1000 1001 1002 1003 1004 1005 1006 1007; do
  for cond in $CONDS; do
    echo "$seed $cond"
  done
done | xargs -P 12 -L 1 bash -c '
  seed=$0; cond=$1; tag=main_${cond}_seed${seed}
  python experiments/run_endogenous.py --game voting --agents 7 --trials 5 --rounds 6 \
    --model meta-llama/llama-3.3-70b-instruct --round-robin --no-judge \
    --private-channel $cond --seed $seed --output-dir '"$OUT"' --run-suffix $tag \
    --dump-requests '"$OUT"'/dumps/$tag.jsonl > '"$OUT"'/logs/$tag.out 2>&1
  echo "finished $tag exit=$?"
'
gzip -f "$OUT"/dumps/*.jsonl
