#!/bin/bash
# M5: multi-sample BASS (record name bass_multisample; never replaces the single-section BASS records): DLPFC (3 donor groups of 4 sections) and MERFISH (5 sections jointly), 3 seeds.
# dry run (job list + one scratch group fit with 200 MCMC samples on MERFISH, separate cache) -> real run (authors' settings, 24 h / 30 GB per job).
set -e
source "$(dirname "$0")/review_stage_common.sh"
rlib_ok BASS || { echo "R package BASS missing"; exit 1; }
rm -f "$SCRATCH/m5_dry.jsonl"; rm -rf "$SCRATCH/m5_runs" "$SCRATCH/bassms_dry"
python -W ignore scripts/review_queue.py --dry-run --job merfish:-0.04:bass_multisample:0
REVIEW_DRY_NREP=200 python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/m5_dry.jsonl" --runs-dir "$SCRATCH/m5_runs" --job merfish:-0.04:bass_multisample:0
dry_ok "$SCRATCH/m5_dry.jsonl"
echo "dry run passed; real run"
J=""; for s in 0 1 2; do
  for sec in 151507 151508 151509 151510 151669 151670 151671 151672 151673 151674 151675 151676; do J="$J --job dlpfc:$sec:bass_multisample:$s"; done
  for sec in -0.04 -0.09 -0.14 -0.19 -0.24; do J="$J --job merfish:$sec:bass_multisample:$s"; done
done
python -W ignore scripts/review_queue.py --workers 1 $J | tee "$SCRATCH/m5_real.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/m5_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/m5_real.log"
