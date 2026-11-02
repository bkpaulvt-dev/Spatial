#!/bin/bash
# Analyses of the embeddings of the memory-capped methods on Stereo-seq E10.5_E1S1 (after the rerun was merged):
# initialisation test, K sensitivity, R mclust seed experiment (without the noise repetitions on this 18,408-bin section).
# One R mclust worker at a time (about 5 GB each) next to the K-sensitivity job, so a 15 GB machine is enough.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
python scripts/export_runner_emb.py
METHODS="graphst nichepca spatial_mgcn deepst" WORKERS=1 python scripts/clustering_lottery.py      # writes the CSVs for R
WORKERS=1 python scripts/k_sensitivity.py > /tmp/ksens_bigmem.log 2>&1 &
MCLUST_NO_JIT=1 Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g6.csv "stereo__E10.5_E1S1__(graphst|nichepca)__"
MCLUST_NO_JIT=1 Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g6.csv "stereo__E10.5_E1S1__(spatial_mgcn|deepst)__"
wait
echo BIGMEM_ANALYSES_DONE
