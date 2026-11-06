#!/bin/bash
# M4: Novae (spatial foundation model, zero-shot with the published pretrained weights from Hugging Face; scripts/review_workers/novae_worker.py, envs/novae) on the 24 original sections and the real new sections, 3 seeds.
# If the weights cannot be downloaded (network blocked) the dry run fails and the stage is recorded as failed (the runner retries 3 times, then goes on). Datasets with Ensembl-id var_names (Allen MERFISH) fail per job by design (Novae needs symbols).
set -e
source "$(dirname "$0")/review_stage_common.sh"
[ -x "$BASE/envs/novae/bin/python" ] || { echo "environment envs/novae missing (review_logs/build_env_novae.sh)"; exit 1; }
rm -f "$SCRATCH/m4_dry.jsonl"; rm -rf "$SCRATCH/m4_runs"
python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/m4_dry.jsonl" --runs-dir "$SCRATCH/m4_runs" --job dlpfc:151673:novae:0
dry_ok "$SCRATCH/m4_dry.jsonl"
echo "dry run passed; real run"
python scripts/review_jobs.py --methods novae > "$SCRATCH/m4_jobs.txt"
python -W ignore scripts/review_queue.py --workers 1 --jobs-file "$SCRATCH/m4_jobs.txt" | tee "$SCRATCH/m4_real.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/m4_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/m4_real.log"
