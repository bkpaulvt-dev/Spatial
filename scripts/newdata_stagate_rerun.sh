#!/bin/bash
# One-shot: rerun the 6 STAGATE Allen jobs (ABCA1-085/103, seeds 0-2) with the owner-approved mclust wrapper, settings unchanged.
# Waits until the Allen queue (PID given as $1) has ended so that at most 2 heavy jobs run.
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
. "$(dirname "$(readlink -f "$0")")/deepmed2_env.sh"
export SPATIALBENCH_MAX_RSS_GB=30 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$BASE/Spatial" || exit 1
. scripts/spatialbench_path.sh
export R_LIBS="$BASE/Rlib"
while kill -0 "$1" 2>/dev/null; do sleep 120; done
disk_guard 100 || exit 6
echo "$(date '+%F %T') [stagate-rerun] start (6 jobs, wrapper)" >> "$BASE/newdata_status.txt"
python -W ignore scripts/newdata_queue.py --datasets allenmerfish --methods stagate --sections ABCA1-085 ABCA1-103 --max-attempts 9 --workers 1 --ignore-hold
echo "$(date '+%F %T') [stagate-rerun] end" >> "$BASE/newdata_status.txt"
