#!/bin/bash
# A9: Spatial-MGCN with the three pre-registered label-free stopping rules (docs/PREREGISTERED_A9.md; scripts/review_methods.py::spatial_mgcn_a9) on the 24 original sections x 3 seeds.
# dry run (smallest STARmap section, seed 0, scratch; its rule-F ARI is compared with the existing label-free record) -> real run (24 h / 30 GB per job) -> report.
set -e
source "$(dirname "$0")/review_stage_common.sh"
rm -f "$SCRATCH/a9_dry.jsonl"; rm -rf "$SCRATCH/a9_runs"
python -W ignore scripts/review_queue.py --workers 1 --timeout 10800 --out "$SCRATCH/a9_dry.jsonl" --runs-dir "$SCRATCH/a9_runs" --job starmap:20180417_BZ5_control:spatial_mgcn_a9:0
dry_ok "$SCRATCH/a9_dry.jsonl"
python - "$SCRATCH/a9_dry.jsonl" <<'PY'
import json, sys
r = [json.loads(l) for l in open(sys.argv[1])][-1]; e = r["extra"]
o = [json.loads(l) for l in open("results/benchmark_runs.jsonl")]
o = [x for x in o if x["method"] == "spatial_mgcn" and x["dataset"] == r["dataset"] and x["section"] == r["section"] and x["seed"] == 0 and x["status"] == "ok"]
print("dry run A9: ARI F %.3f P %.3f L %.3f plateau epoch %d; existing label-free value %s" % (e["ARI_rule_F"], e["ARI_rule_P"], e["ARI_rule_L"], e["plateau_epoch"], o[-1]["metrics"]["ARI"] if o else "n/a"))
PY
echo "dry run passed; real run"
python scripts/review_jobs.py --methods spatial_mgcn_a9 --groups original > "$SCRATCH/a9_jobs.txt"
python -W ignore scripts/review_queue.py --workers 1 --jobs-file "$SCRATCH/a9_jobs.txt" | tee "$SCRATCH/a9_real.log"
python scripts/review_a9_report.py || true
grep -q REVIEW_QUEUE_DONE "$SCRATCH/a9_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/a9_real.log"
