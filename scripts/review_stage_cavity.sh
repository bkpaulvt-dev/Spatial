#!/bin/bash
# Revision V3 item 3b (docs/V3_REVISION_WORKPLAN.md): rerun the 16 original methods with seed 0 on the three Stereo-seq sections (unchanged
# settings) so that each prediction can be scored with and without the MOSTA 'Cavity' bins (scripts/v3_cavity.py).
set -e
source "$(dirname "$0")/review_stage_common.sh"
J="$SCRATCH/cavity_jobs.txt"; : > "$J"
for sec in E9.5_E1S1 E10.5_E2S1 E10.5_E1S1; do
  for m in linear_diffusion anisost pca_gmm histar graphst banksy_l0.8 banksy_l0.2 spagcn stagate sedr spaceflow nichepca ccst spatial_mgcn deepst bass; do
    echo "stereo:$sec:$m:0" >> "$J"; done; done
python -W ignore scripts/review_queue.py --workers 2 --jobs-file "$J" --out results/cavity_runs_deepmed2.jsonl --runs-dir results/cavity_runs | tee "$SCRATCH/cavity_real.log"
python -W ignore scripts/v3_cavity.py | tee "$SCRATCH/cavity_analysis.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/cavity_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/cavity_real.log"
