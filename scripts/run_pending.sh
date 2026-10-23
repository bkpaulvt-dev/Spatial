#!/bin/sh
# Resume every pending computation after a container restart (all steps skip finished work).
#   nohup sh scripts/run_pending.sh > <log> 2>&1 &
# Memory: the machine has 15 GB and running out of memory restarts the whole container, so benchmark jobs run one at a
# time with a per-job cap (spatialbench/resources.py kills a job above the cap or when < 0.8 GB is left and records it as
# out of memory). R mclust on the largest Stereo-seq section (18k bins, ~5 GB, not covered by the cap) runs only after
# the benchmark, alone.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
export SPATIALBENCH_MAX_RSS_GB=${SPATIALBENCH_MAX_RSS_GB:-12}
LOG=${LOG:-/tmp}

# R mclust seed experiment on the smaller new sections (small memory), next to the benchmark
Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g5.csv "(brca__block_a_1|stereo__E9.5_E1S1|stereo__E10.5_E2S1)__" >> "$LOG/mcseed_5.log" 2>&1 &

# New datasets in the standardised runner, one job at a time
ALL15="linear_diffusion anisost pca_gmm banksy_l0.2 banksy_l0.8 histar graphst spagcn stagate sedr spaceflow nichepca ccst spatial_mgcn bass"
python scripts/bench_queue.py --datasets brca stereo --sections block_a_1 E9.5_E1S1 E10.5_E2S1 --seeds 0 --workers 1
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 0 --workers 1
python scripts/baselines_3start.py
python scripts/bench_queue.py --datasets brca stereo --sections block_a_1 E9.5_E1S1 E10.5_E2S1 --seeds 1 2 --workers 1 --methods $ALL15
# CCST takes ~5.5 h per run on this section and was cut off twice by platform restarts: it keeps seeds 0 and 1 here
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 1 2 --workers 1 --methods $(echo $ALL15 | sed "s/ ccst//")
# runs that failed for a fixed reason (e.g. Spatial-MGCN NaN on Stereo-seq) are retried once; out-of-memory stays recorded
python scripts/bench_queue.py --datasets brca stereo --seeds 0 --workers 1 --methods spatial_mgcn --retry-errors --sections E9.5_E1S1
wait
# R mclust on the largest section, alone
Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g6.csv "stereo__E10.5_E1S1__" >> "$LOG/mcseed_6.log" 2>&1
echo PENDING_DONE
