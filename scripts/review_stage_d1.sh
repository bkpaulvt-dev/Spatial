#!/bin/bash
# D1 HER2+ breast cancer (Andersson et al. 2021): skipped (exit 99) until the owner sets HER2_UNPACKED=1 in review_config.env after placing the unpacked, licensed files in data/HER2ST/.
# When it is set, this stage still needs the loader/registration step (sections with pathologist labels only): until that is written the stage fails with a clear reason instead of guessing.
# To re-run after a skip: delete $BASE/review_done/d1_her2.skipped (the runner picks the stage up again).
source "$(dirname "$0")/review_stage_common.sh"
[ "${HER2_UNPACKED:-0}" = "1" ] || { echo "HER2_UNPACKED is not 1: D1 skipped by decision"; exit 99; }
echo "HER2_UNPACKED=1 but the HER2+ loader is not written yet (needs the real file layout in data/HER2ST/); stage cannot run"; exit 1
