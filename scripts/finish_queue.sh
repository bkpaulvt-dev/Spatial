#!/bin/sh
# Remaining computations, in order (memory: never more than two heavy jobs):
#  1. wait for the two running R mclust workers on the 18,408-bin Stereo-seq section to finish their current embedding
#  2. the other embeddings of that section without the noise repetitions (MCLUST_NO_JIT=1), two workers
#  3. DeepST seeds 1-2 on breast cancer and Stereo-seq   4. GraphST Stereo-seq reruns + re-analysis
#  5. R mclust for the Stereo-seq E9.5 Spatial-MGCN embedding
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
OUT=results/mclust_seed_g6.csv
while ps -eo args | grep -v grep | grep -q "mclust_seed.R"; do sleep 30; done
# release the fences (lock dirs of embeddings not yet in the output)
for d in $OUT.lock_*; do [ -d "$d" ] && rmdir "$d"; done
MCLUST_NO_JIT=1 Rscript scripts/mclust_seed.R results/emb/csv $OUT "stereo__E10.5_E1S1__" &
sleep 20
MCLUST_NO_JIT=1 Rscript scripts/mclust_seed.R results/emb/csv $OUT "stereo__E10.5_E1S1__"
wait
echo MCLUST6_DONE
sh scripts/run_deepst_seeds.sh
sh scripts/rerun_graphst_stereo.sh
Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g5.csv "stereo__E9.5_E1S1__spatial_mgcn__"
echo ALL_DONE
