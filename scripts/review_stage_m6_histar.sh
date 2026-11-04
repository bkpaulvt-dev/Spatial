#!/bin/bash
# M6 (i): official HiSTaR code (envs/histar, pinned commit 0039a3b, tutorial settings) on the 12 DLPFC sections x 3 seeds, CPU, compared with our PyTorch port (scripts/review_m6_report.py).
# dry run (151673, seed 0, scratch) -> real run (24 h / 30 GB per job).
set -e
source "$(dirname "$0")/review_stage_common.sh"
[ -x "$BASE/envs/histar/bin/python" ] || { echo "environment envs/histar missing (review_logs/build_env_histar.sh)"; exit 1; }
rm -f "$SCRATCH/m6h_dry.jsonl"; rm -rf "$SCRATCH/m6h_runs"
python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/m6h_dry.jsonl" --runs-dir "$SCRATCH/m6h_runs" --job dlpfc:151673:histar_official:0
dry_ok "$SCRATCH/m6h_dry.jsonl"
echo "dry run passed; real run"
python scripts/review_jobs.py --methods histar_official --groups original --datasets dlpfc > "$SCRATCH/m6h_jobs.txt"
python -W ignore scripts/review_queue.py --workers 1 --jobs-file "$SCRATCH/m6h_jobs.txt" | tee "$SCRATCH/m6h_real.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/m6h_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/m6h_real.log"
python scripts/review_m6_report.py || true
