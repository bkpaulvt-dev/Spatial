#!/bin/bash
# Crossed training-seed x clustering-seed experiment (docs/PREREGISTERED_CROSSED_SEED.md): 7 sections x 9 methods x 5 training seeds,
# embedding of every seed saved (REVIEW_SAVE_EMB_ALL=1), then scripts/cs_analysis.py (20 GMM + 20 k-means single starts per embedding).
set -e
source "$(dirname "$0")/review_stage_common.sh"
export REVIEW_SAVE_EMB_ALL=1
J="$SCRATCH/cs_jobs.txt"; : > "$J"
for spec in dlpfc:151507 dlpfc:151669 dlpfc:151673 starmap:20180419_BZ9_control merfish:-0.14 brca:block_a_1 stereo:E9.5_E1S1; do
  for m in linear_diffusion anisost pca_gmm banksy_l0.8 nichepca histar graphst stagate spaceflow; do
    for s in 0 1 2 3 4; do echo "$spec:$m:$s" >> "$J"; done
  done
done
python -W ignore scripts/review_queue.py --workers 2 --jobs-file "$J" --out results/cs_runs_deepmed2.jsonl --runs-dir results/cs_runs | tee "$SCRATCH/cs_real.log"
python -W ignore scripts/cs_analysis.py | tee "$SCRATCH/cs_analysis.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/cs_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/cs_real.log"
