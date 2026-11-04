#!/bin/bash
# BayesSpace with platform "ST" on the three Stereo-seq sections x 3 seeds (scripts/review_methods.py: bayesspace_st; same settings as the Visium run except the platform).
# 0 (added) version check of the installed BayesSpace against the paper's 1.5.1 on a Visium section. 1 install check (BayesSpace into $BASE/Rlib) -> 2 dry run (job list + one scratch job with 1,500 MCMC iterations on the smallest section; never recorded as a result)
# -> 3 real run (50,000 iterations, 24 h and 30 GB per job; a job over a limit is recorded as such and never retried or changed).
set -e
source "$(dirname "$0")/review_stage_common.sh"
rlib_ok BayesSpace || { Rscript "$BASE/review_logs/install_bayesspace.R" || true; }
rlib_ok BayesSpace || { echo "BayesSpace could not be installed (see review_logs/install_bayesspace.log)"; exit 1; }
rm -f "$SCRATCH/bsst_dry.jsonl"; rm -rf "$SCRATCH/bsst_runs"
python -W ignore scripts/review_queue.py --dry-run --job stereo:E9.5_E1S1:bayesspace_st:0
REVIEW_DRY_NREP=1500 python -W ignore scripts/review_queue.py --workers 1 --timeout 7200 --out "$SCRATCH/bsst_dry.jsonl" --runs-dir "$SCRATCH/bsst_runs" --job stereo:E9.5_E1S1:bayesspace_st:0
dry_ok "$SCRATCH/bsst_dry.jsonl"
echo "dry run passed; version check: BayesSpace here vs the paper's 1.5.1 on DLPFC 151673 (Visium, paper settings, seed 0)"
python -W ignore scripts/review_queue.py --workers 1 --job dlpfc:151673:bayesspace:0 | tee "$SCRATCH/bsst_vcheck.log"
python scripts/review_bayesspace_version_report.py || true
echo "real run: Stereo-seq with the paper's settings (50,000 iterations, burn-in 1,000, 15 PCs, gamma 3, t model); the 1,500 iterations were for the dry run only"
J=""; for s in 0 1 2; do for sec in E9.5_E1S1 E10.5_E2S1 E10.5_E1S1; do J="$J --job stereo:$sec:bayesspace_st:$s"; done; done
python -W ignore scripts/review_queue.py --workers 1 $J | tee "$SCRATCH/bsst_real.log"
grep -q REVIEW_QUEUE_DONE "$SCRATCH/bsst_real.log" || grep -q "0 of 9 jobs to run" "$SCRATCH/bsst_real.log"
