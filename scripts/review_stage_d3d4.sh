#!/bin/bash
# D3 osmFISH + D4 BaristaSeq (SDMBench release; "labels from SDMBench, derivation not fully documented", a separate labelled group). Gated by INCLUDE_SDMBENCH in review_config.env (0 -> exit 99, skipped).
# download + md5 check + export + registry -> dry run (linear diffusion seed 0 on each dataset, scratch) -> all original methods x 3 seeds (24 h / 30 GB) -> R2 methods built so far -> G3 (a-e).
set -e
source "$(dirname "$0")/review_stage_common.sh"
[ "${INCLUDE_SDMBENCH:-0}" = "1" ] || { echo "INCLUDE_SDMBENCH is not 1: D3/D4 skipped by decision"; exit 99; }
python scripts/review_sdmbench.py
rm -f "$SCRATCH/d3d4_dry.jsonl"; rm -rf "$SCRATCH/d3d4_runs"
python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/d3d4_dry.jsonl" --runs-dir "$SCRATCH/d3d4_runs" --job osmfish:osmFISH:linear_diffusion:0 --job baristaseq:Slice_1:linear_diffusion:0
python - "$SCRATCH/d3d4_dry.jsonl" <<'PY'
import json, math, sys
rs = [json.loads(l) for l in open(sys.argv[1])]
for r in rs: print(r["id"], r["status"], r.get("K"), r.get("metrics", {}).get("ARI"), str(r.get("error", ""))[:300])
sys.exit(0 if len(rs) == 2 and all(r["status"] == "ok" and math.isfinite(r["metrics"]["ARI"]) for r in rs) else 1)
PY
echo "dry run passed; real run: all methods x 3 seeds"
python -W ignore scripts/newdata_queue.py --datasets osmfish baristaseq --workers 1 --ignore-hold --out results/review_runs_d3d4_deepmed2.jsonl | tee "$SCRATCH/d3d4_real.log"
tail -1 "$SCRATCH/d3d4_real.log" | grep -q NEWDATA_QUEUE_DONE
bash scripts/review_catchup.sh osmfish baristaseq || true
mkdir -p results/review_g3_d3d4
python -W ignore scripts/newdata_g3.py --datasets osmfish baristaseq --stage all --workers 1 --records "results/review_runs_d3d4_deepmed2.jsonl" --outdir results/review_g3_d3d4 || echo "G3 failed (see log)"
