#!/bin/sh
# Resume every pending computation after a container restart (all steps skip finished work).
#   nohup sh scripts/run_pending.sh > <log> 2>&1 &
# Memory: the machine has 15 GB and running out of memory restarts the whole container, so benchmark jobs run one at a
# time with a per-job cap (spatialbench/resources.py kills a job above the cap or when < 0.8 GB is left and records it as
# out of memory), next to a single R mclust process (< 2 GB).
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
export SPATIALBENCH_MAX_RSS_GB=${SPATIALBENCH_MAX_RSS_GB:-12}
LOG=${LOG:-/tmp}

# R mclust seed experiment on the 280 original embeddings: one R process, groups in turn
( for g in 2 1 3 4; do
    case $g in 1) pat="linear_diffusion|anisost|pca_gmm|histar";; 2) pat="banksy_l0.2|banksy_l0.8|graphst|ccst";;
               3) pat="stagate|sedr|spaceflow";; 4) pat="nichepca|spatial_mgcn|deepst";; esac
    Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g$g.csv "__(${pat})__k" >> "$LOG/mcseed_$g.log" 2>&1
  done ) &

# New datasets in the standardised runner, one job at a time: seed 0 for every method, then seeds 1 and 2
ALL15="linear_diffusion anisost pca_gmm banksy_l0.2 banksy_l0.8 histar graphst spagcn stagate sedr spaceflow nichepca ccst spatial_mgcn bass"
python scripts/bench_queue.py --datasets brca stereo --sections block_a_1 E9.5_E1S1 E10.5_E2S1 --seeds 0 --workers 1
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 0 --workers 1
python scripts/baselines_3start.py
python scripts/bench_queue.py --datasets brca stereo --sections block_a_1 E9.5_E1S1 E10.5_E2S1 --seeds 1 2 --workers 1 --methods $ALL15
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 1 2 --workers 1 --methods $ALL15
wait
echo PENDING_DONE
