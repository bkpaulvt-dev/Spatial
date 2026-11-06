#!/bin/bash
# Retry of tier-1 simulation jobs that were recorded as "memory limit" although their own memory was small (25 pca_gmm jobs on sim_blocks, peak 1.3-1.6 GB): they were killed by the machine-wide memory
# guard while other users filled the shared RAM, i.e. an infrastructure failure, not a result. Same queue, unchanged settings; the queue now retries such records (see real_oom in newdata_queue.py).
# Runs in the review slot (the simulation slot belongs to the real-data phase); --ignore-hold because this is tier 1 (hold only delays tiers 2-3).
set -e
source "$(dirname "$0")/review_stage_common.sh"
python -W ignore scripts/newdata_queue.py --datasets sim_bands sim_blocks --max-methods 5 --workers 1 --ignore-hold | tee "$SCRATCH/retry_sim_tier1.log"
tail -1 "$SCRATCH/retry_sim_tier1.log" | grep -q NEWDATA_QUEUE_DONE
