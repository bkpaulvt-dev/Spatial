#!/bin/bash
# Real-data phase of the new-datasets extension, unattended (start through scripts/run_newdata_detached.sh phase2).
#   waits for tier 1 of the simulation pipeline to finish and push -> Allen MERFISH: dry run, all methods x 3 seeds (24 h / 30 GB per job), G3 (a-e)
#   -> releases the hold file so the pipeline continues with tiers 2 and 3 -> waits for PIPELINE_DONE -> final analysis, G3 on the simulation, handoff, commit, push.
# One heavy thing at a time (the queue and the G3 workers never overlap with another queue). Resumable: start it again after a crash.
# Datasets decided as NOT runnable (reasons in docs/NEWDATA_REPORT.md): osmFISH (region labels not documented as anatomical), HER2+ (data files encrypted),
# prostate (spot annotations not confirmed in the deposit), Visium HD / Xenium (no domain labels; too large).
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
export SPATIALBENCH_MAX_RSS_GB=${CAP_GB:-30} OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$BASE/Spatial" || exit 1
STATUS="$BASE/newdata_status.txt"
NTFY_TOPIC=${NTFY_TOPIC:-$(cat "$BASE/ntfy_topic" 2>/dev/null)}
notify() { [ -n "$NTFY_TOPIC" ] && curl -fsS -m 10 -H "Title: SpatialBench newdata" -d "$*" "https://ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1; return 0; }
say() { echo "$(date '+%F %T') [phase2] $*" | tee -a "$STATUS"; case "$*" in *STOP*|*DONE*|*"dataset"*|*failed*) notify "[phase2] $*";; esac; }
trap 'notify "phase2 ended (exit code $?); see newdata_status.txt"' EXIT
say "phase 2 start (pid $$)"
source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env"
[ "$(python -c 'import sys;print(sys.prefix)')" = "$BASE/env" ] || { say "STOP: python is not the project environment"; exit 2; }
export R_LIBS_USER="$BASE/Rlib"
commit_small() {   # small files only, branch new-datasets only, no force; a failed push is fine
  git add results/newdata_*.jsonl results/newdata_*.csv results/newdata_*.json results/newdata_*.md docs/figures/newdata_*.png docs/NEWDATA_*.md configs/datasets_newdata.yaml 2>/dev/null
  git -c user.name="Bikash Kumar Paul" -c user.email="bkpaul.vt@gmail.com" commit -qm "newdata: $1 (small files only)" 2>/dev/null
  git -c credential.helper= -c credential.helper="!$BASE/bin/gh auth git-credential" push origin new-datasets 2>&1 | tail -1 | tee -a "$STATUS"
}
pipe_running() { P=$(cat "$BASE/newdata_pipeline.pid" 2>/dev/null); [ -n "$P" ] && kill -0 "$P" 2>/dev/null; }

# 0. wait for tier 1 (and its push attempt, which is written before the "done" line)
say "waiting for tier 1 (5 cheapest methods) to finish and push"
until grep -q "tier (cheapest 5 methods) done" "$STATUS"; do
  pipe_running || { grep -q "tier (cheapest 5 methods) done" "$STATUS" || { say "STOP: the simulation pipeline is not running and tier 1 is not done"; exit 3; }; }
  sleep 300
done
say "tier 1 done and pushed (or push skipped); starting the real-data phase with the hold file in place"

dataset_outcome() { echo "$(date '+%F %T') $1: $2" >> results/newdata_dataset_outcomes.txt; }

# 1. Allen MERFISH (the only real dataset that passed the label and licence checks)
DS=allenmerfish
say "dataset $DS: dry run (job listing + one real small job, linear diffusion seed 0 on ABCA1-103, scratch file)"
rm -f "$BASE/newdata_dry_allen.jsonl"
python -W ignore scripts/newdata_queue.py --datasets $DS --dry-run --out "$BASE/newdata_dry_allen.jsonl" >> "$BASE/newdata_queue_allen.log" 2>&1
python -W ignore scripts/newdata_queue.py --datasets $DS --sections ABCA1-103 --methods linear_diffusion --seeds 0 --workers 1 --ignore-hold --out "$BASE/newdata_dry_allen.jsonl" >> "$BASE/newdata_queue_allen.log" 2>&1
if python - <<'PY'
import json, math, sys
rs = [json.loads(l) for l in open("/mnt/disk/bikashkumar/SpatialBench/newdata_dry_allen.jsonl")]
ok = bool(rs) and rs[-1]["status"] == "ok" and math.isfinite(rs[-1]["metrics"]["ARI"]) and rs[-1]["K"] == 7
sys.exit(0 if ok else 1)
PY
then
  say "dataset $DS: dry run ok; real run: all methods x 3 seeds (24 h and 30 GB per job)"
  for try in 1 2 3; do
    python -W ignore scripts/newdata_queue.py --datasets $DS --workers 2 --ignore-hold >> "$BASE/newdata_queue_allen.log" 2>&1
    tail -1 "$BASE/newdata_queue_allen.log" | grep -q NEWDATA_QUEUE_DONE && break
    say "dataset $DS: queue ended without NEWDATA_QUEUE_DONE (attempt $try); restarting (resumable)"; sleep 60
  done
  if tail -1 "$BASE/newdata_queue_allen.log" | grep -q NEWDATA_QUEUE_DONE; then
    say "dataset $DS: benchmark done; G3 (a-e)"
    python -W ignore scripts/newdata_g3.py --datasets $DS --stage all --workers 2 >> "$BASE/newdata_g3.log" 2>&1 || say "dataset $DS: G3 failed (see newdata_g3.log)"
    dataset_outcome $DS "ran: see results/newdata_runs_*.jsonl and results/newdata_g3_summary.md"
  else
    say "dataset $DS: failed after 3 attempts (see newdata_queue_allen.log)"; dataset_outcome $DS "queue did not finish after 3 attempts"
  fi
else
  say "dataset $DS: dry run FAILED (see newdata_queue_allen.log); skipped"; dataset_outcome $DS "dry run failed; skipped"
fi
commit_small "real data: $DS"

# 2. release the hold: the pipeline continues with tiers 2 and 3
rm -f "$BASE/newdata_hold"; say "hold file removed: the simulation pipeline continues with tiers 2 and 3"
until grep -q "PIPELINE_DONE" "$STATUS" || grep -q "STOP:" <(tail -3 "$STATUS" | grep -v phase2); do
  pipe_running || { say "the simulation pipeline is no longer running without PIPELINE_DONE; continuing with the final analysis"; break; }
  sleep 600
done

# 3. final: primary analysis, G3 on the simulation (full-design methods), handoff
say "final analysis"
python -W ignore scripts/newdata_stats.py >> "$BASE/newdata_stats.log" 2>&1 || say "stats failed (see newdata_stats.log)"
python -W ignore scripts/newdata_g3.py --datasets sim_bands sim_blocks --stage all --workers 2 >> "$BASE/newdata_g3.log" 2>&1 || say "G3 on the simulation failed (see newdata_g3.log)"
python -W ignore scripts/newdata_handoff.py >> "$BASE/newdata_stats.log" 2>&1 || say "handoff generation failed (see newdata_stats.log)"
commit_small "final results and handoff"
say "PHASE2_DONE"
