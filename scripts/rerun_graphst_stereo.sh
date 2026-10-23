#!/bin/sh
# GraphST on Stereo-seq with its documented Stereo-seq setting (datatype='Stereo'), then the analyses of its seed-0 embeddings.
# Waits for the R mclust workers and the DeepST seeds (memory).
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 SPATIALBENCH_MAX_RSS_GB=${SPATIALBENCH_MAX_RSS_GB:-12}
while ps -eo args | grep -v grep | grep -qE "mclust_seed.R|run_deepst_seeds.sh"; do sleep 60; done
python scripts/bench_queue.py --datasets stereo --seeds 0 1 2 --workers 1 --methods graphst --force
python scripts/export_runner_emb.py --force graphst
# drop the analyses of the old GraphST Stereo-seq embeddings, then recompute them
python - <<'PY'
import json, glob, pandas as pd
for f in ("results/clustering_lottery.jsonl", "results/k_sensitivity.jsonl"):
    rows = [json.loads(l) for l in open(f)]
    keep = [r for r in rows if not (r.get("dataset") == "stereo" and r["method"] == "graphst")]
    open(f, "w").write("".join(json.dumps(r) + "\n" for r in keep)); print(f, len(rows) - len(keep), "removed")
for f in glob.glob("results/mclust_seed_g*.csv"):
    d = pd.read_csv(f); k = d[~((d.dataset == "stereo") & (d.method == "graphst"))]
    if len(k) < len(d): k.to_csv(f, index=False); print(f, len(d) - len(k), "removed")
PY
METHODS=graphst WORKERS=1 python scripts/clustering_lottery.py
python scripts/k_sensitivity.py
Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g5.csv "stereo__(E9.5_E1S1|E10.5_E2S1)__graphst__"
MCLUST_NO_JIT=1 Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g6.csv "stereo__E10.5_E1S1__graphst__"
echo GRAPHST_DONE
