#!/bin/sh
# Resume every pending computation after a container restart (all steps skip finished work).
#   nohup sh scripts/run_pending.sh > <log> 2>&1 &
# Memory: the machine has 15 GB; the largest Stereo-seq section runs one job at a time.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
LOG=${LOG:-/tmp}

# R mclust seed experiment on the 280 original embeddings: two R processes, two method groups each
( for g in 1 3; do
    case $g in 1) pat="linear_diffusion|anisost|pca_gmm|histar";; 3) pat="stagate|sedr|spaceflow";; esac
    Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g$g.csv "__(${pat})__k" >> "$LOG/mcseed_$g.log" 2>&1
  done ) &
( for g in 2 4; do
    case $g in 2) pat="banksy_l0.2|banksy_l0.8|graphst|ccst";; 4) pat="nichepca|spatial_mgcn|deepst";; esac
    Rscript scripts/mclust_seed.R results/emb/csv results/mclust_seed_g$g.csv "__(${pat})__k" >> "$LOG/mcseed_$g.log" 2>&1
  done ) &

# New datasets in the standardised runner: seed 0 first, small sections two at a time, the 18k-bin section alone
SMALL="block_a_1 E9.5_E1S1 E10.5_E2S1"
python scripts/bench_queue.py --datasets brca stereo --sections $SMALL --seeds 0 --workers 2
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 0 --workers 1
python scripts/bench_queue.py --datasets brca stereo --sections $SMALL --seeds 1 2 --workers 2 \
       --methods linear_diffusion anisost pca_gmm banksy_l0.2 banksy_l0.8 histar graphst spagcn stagate sedr spaceflow nichepca ccst spatial_mgcn bass
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 1 2 --workers 1 \
       --methods linear_diffusion anisost pca_gmm banksy_l0.2 banksy_l0.8 histar graphst spagcn stagate sedr spaceflow nichepca ccst spatial_mgcn bass
# baselines with the 3-start mixture on the new sections
python scripts/baselines_3start.py
wait
echo PENDING_DONE
