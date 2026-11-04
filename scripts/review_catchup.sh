#!/bin/bash
# Run the already built R2 methods on newly registered real datasets: bash scripts/review_catchup.sh <dataset> [<dataset> ...]
source "$(dirname "$0")/review_stage_common.sh"
M="mender cellcharter"; for f in "$SCRATCH"/catchup_methods.txt; do [ -f "$f" ] && M=$(cat "$f"); done    # the list grows as more methods are built
python scripts/review_jobs.py --methods $M --groups newreal --datasets "$@" > "$SCRATCH/catchup_jobs.txt"
python -W ignore scripts/review_queue.py --workers 1 --jobs-file "$SCRATCH/catchup_jobs.txt" | tee "$SCRATCH/catchup.log"
