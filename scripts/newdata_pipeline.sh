#!/bin/bash
# New-datasets extension in one resumable script (model: scripts/deepmed2_pipeline.sh). Start it only through scripts/run_newdata_detached.sh.
#   P1 simulation:  generate the tissues -> wait for RAM -> queue in tiers (cheapest methods first) -> analysis after each tier -> commit
# Every stage skips what is finished. Progress: $BASE/newdata_status.txt (one line per stage and per failed job); log: $BASE/newdata_pipeline.log.
# Ends with PIPELINE_DONE or STOP: <reason>. Not included here (no code that passed the dry run yet): osmFISH, BaristaSeq, HER2+, prostate,
# Allen MERFISH; see docs/NEWDATA_DEEPMED2.md. Visium HD / Xenium are deliberately skipped (docs/NEWDATA_REPORT.md).
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
MIN_RAM=${MIN_RAM:-64}               # GB available before a tier may start
export SPATIALBENCH_MAX_RSS_GB=${CAP_GB:-30}     # per-job cap (deviation from 12 GB, see docs/PREREGISTERED_SIM.md)
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$BASE/Spatial" || exit 1
STATUS="$BASE/newdata_status.txt"
# phone notifications (optional): topic only from $BASE/ntfy_topic or NTFY_TOPIC; the topic is never printed or committed
NTFY_TOPIC=${NTFY_TOPIC:-$(cat "$BASE/ntfy_topic" 2>/dev/null)}
notify() { [ -n "$NTFY_TOPIC" ] && curl -fsS -m 10 -H "Title: SpatialBench newdata" -d "$*" "https://ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1; return 0; }
say() { echo "$(date '+%F %T') $*" | tee -a "$STATUS"; case "$*" in *STOP*|*PIPELINE_DONE*|*"tier"*|*failed*|*"stage"*) notify "$*";; esac; }
trap 'notify "newdata pipeline ended (exit code $?); see newdata_status.txt"' EXIT
say "pipeline start (pid $$, host $(hostname), cap ${SPATIALBENCH_MAX_RSS_GB} GB per job)"

# 0. preflight: only the project environment, never the shared base
source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env"
[ "$(python -c 'import sys;print(sys.prefix)')" = "$BASE/env" ] || { say "STOP: python is not the project environment"; exit 2; }
export R_LIBS_USER="$BASE/Rlib"
python -m pytest -q tests/test_dataset_groups.py >/dev/null 2>&1 || { say "STOP: dataset-group test failed (existing datasets would resolve differently)"; exit 2; }

# 1. simulated tissues (resumable: existing files are skipped)
say "stage 1: simulated tissues"
for try in 1 2 3; do
  python -W ignore scripts/simulate_domains.py --examples >> "$BASE/newdata_sim.log" 2>&1
  [ "$(ls data/Sim/sim_bands data/Sim/sim_blocks 2>/dev/null | grep -c h5ad)" -eq 45 ] && break
  say "simulation incomplete (attempt $try)"; sleep 30
done
[ "$(ls data/Sim/sim_bands data/Sim/sim_blocks 2>/dev/null | grep -c h5ad)" -eq 45 ] || { say "STOP: simulation did not produce 45 tissues"; exit 3; }
say "stage 1: 45 tissues done"

# 2. tiers of methods, cheapest first (scripts/newdata_queue.py orders them): 5 = baselines + BANKSY, 9 = + NichePCA/SpaGCN/SEDR/HiSTaR, 17 = all
commit_small() {
  git add results/newdata_runs_*.jsonl results/newdata_sim_manifest.json results/newdata_stats*.json results/newdata_stats*.csv \
          results/newdata_*.md docs/figures/newdata_*.png docs/NEWDATA_REPORT.md 2>/dev/null
  git -c user.name="Bikash Kumar Paul" -c user.email="bkpaul.vt@gmail.com" commit -qm "newdata: results after $1 (small files only)" 2>/dev/null
  # push only the branch new-datasets, no force; a failed push (no credentials) is fine, the files stay in place
  git -c credential.helper= -c credential.helper="!$BASE/bin/gh auth git-credential" push origin new-datasets 2>&1 | tail -1 | tee -a "$STATUS"
}
for N in 5 9 17; do
  say "tier (cheapest $N methods): waiting for >= ${MIN_RAM} GB available RAM"
  for i in $(seq 1 36); do
    A=$(free -g | awk 'NR==2{print $7}'); [ "$A" -ge "$MIN_RAM" ] && break
    say "only ${A} GB available; waiting 10 min"; sleep 600
  done
  A=$(free -g | awk 'NR==2{print $7}'); [ "$A" -ge "$MIN_RAM" ] || { say "STOP: RAM stayed below ${MIN_RAM} GB (${A} GB)"; exit 4; }
  say "tier (cheapest $N methods): running with ${A} GB available"
  for try in 1 2 3; do
    python -W ignore scripts/newdata_queue.py --datasets sim_bands sim_blocks --workers 2 --max-methods $N >> "$BASE/newdata_queue.log" 2>&1
    tail -1 "$BASE/newdata_queue.log" | grep -q NEWDATA_QUEUE_DONE && break
    say "queue ended without NEWDATA_QUEUE_DONE (attempt $try); restarting (resumable)"; sleep 60
  done
  tail -1 "$BASE/newdata_queue.log" | grep -q NEWDATA_QUEUE_DONE || { say "STOP: queue did not finish for tier $N; see newdata_queue.log"; exit 5; }
  python - <<'PY' >> "$STATUS"
import json, glob, collections
c = collections.Counter(); err = []
last = {}
for f in glob.glob("results/newdata_runs_*.jsonl"):
    for l in open(f):
        r = json.loads(l); last[r["id"]] = r
for r in last.values():
    c[r["status"]] += 1
    if r["status"] != "ok": err.append(f"  {r['id']} {str(r.get('error',''))[:70]}")
print(f"  records: {dict(c)}"); [print(e) for e in err[:15]]
PY
  if [ -f scripts/newdata_stats.py ]; then python -W ignore scripts/newdata_stats.py >> "$BASE/newdata_stats.log" 2>&1 || say "stats failed (see newdata_stats.log); continuing"; fi
  commit_small "tier $N"
  say "tier (cheapest $N methods) done"
done
say "PIPELINE_DONE"
