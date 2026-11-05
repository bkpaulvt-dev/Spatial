#!/bin/bash
# M5: multi-sample BASS (record name bass_multisample; never replaces the single-section BASS records): MERFISH (5 sections jointly) first, then DLPFC (3 donor groups of 4 sections), 3 seeds.
# SETTINGS: exactly the BASS authors' documented multi-sample settings (BASS-Analysis analysis/DLPFC.Rmd: C 20, R 7, nsample 10000, sparkx 3000 genes, 20 PCs; analysis/MERFISH.Rmd: C 20, R 8, package defaults
# burn-in 2000 / nsample 5000, scaled PCA, Harmony). They are identical to the single-section settings of configs/methods.yaml, so there is NO deviation from them. The shortened burn-in (100) and nsample (200) apply to the DRY RUN only.
# RULE (owner, 2026-11-04): the joint fits are not run beyond the 24 h cap. The first MERFISH job (the joint fit, seed 0) runs alone first; if it hits a limit, ONE time-limit record stands for the group, the rest of
# M5 (other MERFISH jobs and the DLPFC groups) is skipped and the reason is written to results/review_m5_group_skipped.json.
set -e
source "$(dirname "$0")/review_stage_common.sh"
rlib_ok BASS || { echo "R package BASS missing"; exit 1; }
rm -f "$SCRATCH/m5_dry.jsonl"; rm -rf "$SCRATCH/m5_runs" "$SCRATCH/bassms_dry"
python -W ignore scripts/review_queue.py --dry-run --job merfish:-0.04:bass_multisample:0
REVIEW_DRY_NREP=200 python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/m5_dry.jsonl" --runs-dir "$SCRATCH/m5_runs" --job merfish:-0.04:bass_multisample:0
dry_ok "$SCRATCH/m5_dry.jsonl"
echo "dry run passed; real run: the MERFISH joint fit first"
python -W ignore scripts/review_queue.py --workers 1 --job merfish:-0.04:bass_multisample:0 | tee "$SCRATCH/m5_first.log"
if python - <<'PY'
import json, sys
last = None
for l in open("results/review_runs_deepmed2.jsonl"):
    r = json.loads(l)
    if r["id"] == "merfish__-0.04__bass_multisample__s0": last = r
if last and last["status"] != "ok" and last.get("outcome") in ("time limit", "memory limit"):
    json.dump({"reason": last["outcome"], "id": last["id"], "error": str(last.get("error", ""))[:300],
               "note": "ONE group-level record: the MERFISH joint fit hit its limit; the other MERFISH jobs and the DLPFC groups were skipped by rule (owner decision 2026-11-04)"},
              open("results/review_m5_group_skipped.json", "w"), indent=1)
    sys.exit(7)
PY
then
  J=""; for s in 0 1 2; do
    for sec in -0.04 -0.09 -0.14 -0.19 -0.24; do J="$J --job merfish:$sec:bass_multisample:$s"; done
    for sec in 151507 151508 151509 151510 151669 151670 151671 151672 151673 151674 151675 151676; do J="$J --job dlpfc:$sec:bass_multisample:$s"; done
  done
  python -W ignore scripts/review_queue.py --workers 1 $J | tee "$SCRATCH/m5_real.log"
  grep -q REVIEW_QUEUE_DONE "$SCRATCH/m5_real.log" || grep -q " 0 of .* jobs to run" "$SCRATCH/m5_real.log"
else
  echo "M5 group skipped (see results/review_m5_group_skipped.json)"
fi
