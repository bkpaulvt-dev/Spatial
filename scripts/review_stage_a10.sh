#!/bin/bash
# A10 cross-host checks: DeepST seed 0 on Stereo-seq E10.5_E2S1 here (its seeds 1 and 2 were run here, seed 0 on the original machine: host confound), and one
# same-seed rerun of one cheap method (linear diffusion, seed 0, same section) to measure the host difference in ARI directly.
set -e
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}; cd "$BASE/Spatial"
source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env"; export R_LIBS_USER="$BASE/Rlib"
[ "$(python -c 'import sys;print(sys.prefix)')" = "$BASE/env" ]
python -W ignore scripts/review_queue.py --workers 1 --job stereo:E10.5_E2S1:linear_diffusion:0 --job stereo:E10.5_E2S1:deepst:0
tail -1 "$BASE/review_logs/a10_cross_host.log" | grep -q REVIEW_QUEUE_DONE || true
python scripts/review_a10_report.py
