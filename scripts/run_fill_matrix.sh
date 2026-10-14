#!/bin/sh
# Resume the coverage-fill benchmark (all remaining methods, 3 seeds). Safe to re-run: finished jobs are skipped.
# Start with:  nohup sh scripts/run_fill_matrix.sh > fill.log 2>&1 &
# Never run deepst / bayesspace / nichepca at the same time as other jobs (memory: 15 GB container).
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
for m in spagcn bass stagate spaceflow graphst spatial_mgcn ccst; do
  python scripts/bench_queue.py --methods $m --seeds 0 1 2 --workers 3
done
python scripts/bench_queue.py --methods deepst bayesspace --seeds 0 1 2 --workers 1
python scripts/bench_queue.py --methods spagcn bass stagate spaceflow graphst spatial_mgcn ccst deepst bayesspace --seeds 0 1 2 --workers 1 --retry-errors
echo FILL_FINISHED
