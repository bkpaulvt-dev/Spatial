#!/bin/sh
# Rerun, on a machine with >= 64 GB free RAM, the jobs that exceeded the 12 GB cap on the 15 GB benchmark machine:
#   Stereo-seq E10.5_E1S1 (18,408 bins): BASS, GraphST (datatype='Stereo'), NichePCA, Spatial-MGCN, DeepST, seeds 0-2
#   Stereo-seq E10.5_E2S1:               DeepST seeds 1-2
# CPU only, one thread per job, same code as the paper. Results go to a separate file (the host differs from the benchmark
# machine, so run times are NOT comparable and are left out of the timing comparison; memory is reported):
#   results/benchmark_runs_bigmem.jsonl  and  results/runs/<id>.json|npz
# Usage (after the setup in docs/BIGMEM_RERUN.md):   nohup sh scripts/rerun_memory_failures.sh > bigmem.log 2>&1 &
# Variables: WORKERS (default 2 parallel jobs), CAP_GB (per-job memory cap, default 30; the machine is shared).
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export SPATIALBENCH_MAX_RSS_GB=${CAP_GB:-30}
OUT=results/benchmark_runs_bigmem.jsonl
W=${WORKERS:-2}
echo "host: $(hostname)  $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2)  RAM available: $(free -g | awk 'NR==2{print $7}') GB"
# --retry-errors: the earlier out-of-memory records are ignored for these ids
python scripts/bench_queue.py --datasets stereo --sections E10.5_E1S1 --seeds 0 1 2 --workers $W --retry-errors \
    --methods bass graphst nichepca spatial_mgcn deepst --out $OUT
python scripts/bench_queue.py --datasets stereo --sections E10.5_E2S1 --seeds 1 2 --workers 1 --retry-errors \
    --methods deepst --out $OUT
echo BIGMEM_DONE
