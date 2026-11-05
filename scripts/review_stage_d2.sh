#!/bin/bash
# D2 prostate cancer (Erickson et al. 2022): dropped unless the owner provides per-spot pathologist region labels (PROSTATE_LABELS_CONFIRMED=1, files in data/PROSTATE/). Skipped (exit 99) otherwise.
# To re-run after a skip: delete $BASE/review_done/d2_prostate.skipped.
source "$(dirname "$0")/review_stage_common.sh"
[ "${PROSTATE_LABELS_CONFIRMED:-0}" = "1" ] || { echo "PROSTATE_LABELS_CONFIRMED is not 1: D2 dropped (no confirmed per-spot labels), as decided"; exit 99; }
echo "PROSTATE_LABELS_CONFIRMED=1 but the prostate loader is not written yet; stage cannot run"; exit 1
