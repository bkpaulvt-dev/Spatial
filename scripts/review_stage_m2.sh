#!/bin/bash
# M2: CellCharter (envs/m2) and MENDER (envs/mender, official PyPI SOMENDER 1.1) on the 24 original sections and the real new sections (Allen MERFISH, plus any real dataset registered at this time), 3 seeds.
# Datasets registered later (osmFISH, BaristaSeq, HER2+, prostate) get these methods from their own stage (scripts/review_catchup.sh).
# dry run (one small section per method, scratch records, never counted) -> real run (24 h and 30 GB per job).
set -e
source "$(dirname "$0")/review_stage_common.sh"
for e in m2 mender; do [ -x "$BASE/envs/$e/bin/python" ] || { echo "environment envs/$e missing (see review_logs/build_env_*.sh)"; exit 1; }; done
rm -f "$SCRATCH/m2_dry.jsonl"; rm -rf "$SCRATCH/m2_runs"
python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/m2_dry.jsonl" --runs-dir "$SCRATCH/m2_runs" --job dlpfc:151673:mender:0 --job dlpfc:151673:cellcharter:0
python - "$SCRATCH/m2_dry.jsonl" <<'PY'
import json, math, sys
rs = [json.loads(l) for l in open(sys.argv[1])]
bad = [r for r in rs if r["status"] != "ok" or not math.isfinite(r["metrics"]["ARI"])]
for r in rs: print(r["id"], r["status"], r.get("metrics", {}).get("ARI"), str(r.get("error", ""))[:500])
sys.exit(1 if bad or len(rs) < 2 else 0)
PY
echo "dry run passed; real run"
python scripts/review_jobs.py --methods mender cellcharter > "$SCRATCH/m2_jobs.txt"
python -W ignore scripts/review_queue.py --workers 1 --jobs-file "$SCRATCH/m2_jobs.txt" | tee "$SCRATCH/m2_real.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/m2_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/m2_real.log"
