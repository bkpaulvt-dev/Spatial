#!/bin/sh
# DeepST seeds 1-2 on the breast cancer and Stereo-seq sections (missing from the first seeds-1-2 queue).
# DeepST needs 8-11 GB here, so this waits until the R mclust workers on the largest Stereo-seq section have finished.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 SPATIALBENCH_MAX_RSS_GB=${SPATIALBENCH_MAX_RSS_GB:-12}
while ps -eo args | grep -v grep | grep -q "mclust_seed.R"; do sleep 60; done
python scripts/bench_queue.py --datasets brca stereo --sections block_a_1 E9.5_E1S1 E10.5_E2S1 --seeds 1 2 --workers 1 --methods deepst
echo DEEPST_DONE
