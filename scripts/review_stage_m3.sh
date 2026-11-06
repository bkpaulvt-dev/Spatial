#!/bin/bash
# M3: DR-SC (CRAN DR.SC, scripts/review_drsc.R) and GraphBG (github CamiLQDTULab/GraphBG, needs Python 3.8.20 -> own environment envs/graphbg), on the 24 original sections and the real new sections, 3 seeds.
# GraphBG part: runs only if envs/graphbg exists; otherwise "environment build failed (needs conda for Python 3.8; no allowed conda)" is written to results/review_m3_graphbg_status.json and the stage goes on with DR-SC.
set -e
source "$(dirname "$0")/review_stage_common.sh"
rlib_ok DR.SC || { echo "DR.SC missing (review_logs/install_m1.R)"; exit 1; }
rm -f "$SCRATCH/m3_dry.jsonl"; rm -rf "$SCRATCH/m3_runs"
python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/m3_dry.jsonl" --runs-dir "$SCRATCH/m3_runs" --job dlpfc:151673:drsc:0
dry_ok "$SCRATCH/m3_dry.jsonl"
echo "dry run passed; real run (DR-SC)"
python scripts/review_jobs.py --methods drsc > "$SCRATCH/m3_jobs.txt"
python -W ignore scripts/review_queue.py --workers 1 --jobs-file "$SCRATCH/m3_jobs.txt" | tee "$SCRATCH/m3_real.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/m3_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/m3_real.log"
if [ -x "$BASE/envs/graphbg/bin/python" ] && grep -q graphbg "$SCRATCH/catchup_methods.txt" 2>/dev/null; then echo "GraphBG: environment present (stage extension: see scripts/review_stage_m3b.sh)"; 
else
  python - <<'PY'
import json
json.dump({"method": "GraphBG", "status": "environment build failed",
           "reason": "GraphBG requires Python 3.8.20 (conda create python=3.8.20); the only Python 3.8 route is a conda, and no conda outside ~/shared_disk was cleared for use by the owner; not run, nothing was recorded as a result",
           "source": "https://github.com/CamiLQDTULab/GraphBG (commit 9114759)"}, open("results/review_m3_graphbg_status.json", "w"), indent=1)
PY
fi
