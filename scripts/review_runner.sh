#!/bin/bash
# Review runner (docs/DEEPMED2_NEXT.md): runs the stages of scripts/review_stages.txt in order, unattended. Start it only through scripts/run_review_detached.sh.
#  * stage list and decisions are re-read all the time: a stage built later is picked up; edit $BASE/review_config.env to change a decision
#  * prep stages run now (one at a time); heavy stages wait for the end of the current plan (PHASE2_DONE) and for >= 64 GB free RAM; at most 2 jobs at a time (inside the stages)
#  * a stage that fails is retried up to 3 times with unchanged settings, then recorded as failed and the runner goes on; exit code 99 of a stage = skipped by decision
#  * after each stage: local commit of small result files on branch new-datasets and a push of that branch only (no force; failed push is fine)
#  Progress: $BASE/review_status.txt, ending in PIPELINE_DONE or STOP: <reason>. Logs: $BASE/review_logs/<stage>.log. Phone alerts: topic file, never printed or committed.
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
. "$(dirname "$(readlink -f "${BASH_SOURCE[0]:-$0}")")/deepmed2_env.sh"   # disk rule: nothing is written to / (CLAUDE.md)
export SPATIALBENCH_MAX_RSS_GB=${CAP_GB:-30} OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$BASE/Spatial" || exit 1
RSTATE=${RSTATE:-$BASE}; GATE_FILE=${GATE_FILE:-$BASE/newdata_status.txt}      # RSTATE/GATE_FILE/STAGES/RETRY_SLEEP/REVIEW_NO_GIT: overridable for tests only
STATUS="$RSTATE/review_status.txt"; CONF="$RSTATE/review_config.env"; DONE="$RSTATE/review_done"; LOGS="$RSTATE/review_logs"; mkdir -p "$DONE" "$LOGS"
if [ ! -f "$CONF" ]; then cat > "$CONF" <<'E'
# Decisions of the review runner (defaults = the answers proposed in docs/REVIEW_QUESTIONS.md). Edit and save: the runner re-reads this file before every stage.
APPROVE_R5=0              # 1 = run the equal-tuning arm (needs your approval of the budget in docs/REVIEW_QUESTIONS.md)
HER2_UNPACKED=0           # 1 once the unpacked HER2+ files are in data/HER2ST/ (the encrypted Zenodo zips are not used)
INCLUDE_SDMBENCH=0        # 1 = also run osmFISH and BaristaSeq from SDMBench (labels anatomical by name, derivation undocumented)
PROSTATE_LABELS_CONFIRMED=0   # 1 once the per-spot pathologist labels of the prostate deposit are in data/PROSTATE/
ALLOW_VISIUMHD_XENIUM=1   # scalability-only runs at the very end
E
fi
NTFY_TOPIC=${NTFY_TOPIC:-$(cat "$BASE/ntfy_topic" 2>/dev/null)}
notify() { [ -n "$NTFY_TOPIC" ] && curl -fsS -m 10 -H "Title: SpatialBench review" -d "$*" "https://ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1; return 0; }
say() { echo "$(date '+%F %T') $*" | tee -a "$STATUS"; case "$*" in *STOP*|*PIPELINE_DONE*|*done*|*FAILED*|*skipped*) notify "[review] $*";; esac; }
trap 'notify "review runner ended (exit code $?); see review_status.txt"' EXIT
say "review runner start (pid $$, host $(hostname), cap ${SPATIALBENCH_MAX_RSS_GB} GB per job)"
source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env"
[ "$(python -c 'import sys;print(sys.prefix)')" = "$BASE/env" ] || { say "STOP: python is not the project environment"; exit 2; }
export R_LIBS_USER="$BASE/Rlib"

# Amendment 2 (docs/PREREGISTERED_SIM.md): the gate is open from the start (the simulation pipeline uses 1 heavy slot, the review stages the other); GATE_REQUIRE=1 restores the old gate
gate_open() { [ -z "$GATE_REQUIRE" ] || grep -q "PHASE2_DONE" "$GATE_FILE" 2>/dev/null; }
STAGES=${STAGES:-scripts/review_stages.txt}; RETRY_SLEEP=${RETRY_SLEEP:-120}      # overridable for tests only (REVIEW_NO_GIT=1 also skips commit and push)
commit_small() {
  [ -z "$REVIEW_NO_GIT" ] || return 0
  [ "$(git branch --show-current)" = "new-datasets" ] || return 0
  git add data/CHECKSUMS.sha256 results/review_*.jsonl results/review_*.json results/review_*.csv results/review_*.md results/review_report configs/methods_extra.yaml configs/datasets_newdata.yaml docs/REVIEW_*.md docs/PREREGISTERED_*.md 2>/dev/null
  git -c user.name="Bikash Kumar Paul" -c user.email="bkpaul.vt@gmail.com" commit -qm "review: $1 (small files only)" 2>/dev/null
  git -c credential.helper= -c credential.helper="!$BASE/bin/gh auth git-credential" push origin new-datasets 2>&1 | tail -1 | tee -a "$STATUS"
}
wait_ram() { for i in $(seq 1 36); do A=$(free -g | awk 'NR==2{print $7}'); [ "$A" -ge 64 ] && return 0; say "only ${A} GB available; waiting 10 min"; sleep 600; done; return 1; }
run_stage() {   # name script
  for try in 1 2 3; do
    bash "$2" >> "$LOGS/$1.log" 2>&1 < /dev/null; rc=$?
    [ $rc -eq 0 ] && { touch "$DONE/$1"; say "stage $1 done"; commit_small "stage $1"; return 0; }
    [ $rc -eq 99 ] && { touch "$DONE/$1.skipped"; say "stage $1 skipped by decision ($(tail -1 "$LOGS/$1.log" | cut -c1-120))"; return 0; }
    say "stage $1 failed (attempt $try, exit $rc); see $LOGS/$1.log"; sleep "$RETRY_SLEEP"
  done
  touch "$DONE/$1.failed"; say "stage $1 FAILED after 3 attempts (recorded, the runner goes on)"; commit_small "stage $1 failed"; return 1
}
idle_since=""; last_blocked=""
while true; do
  progressed=0; blocked=""; waiting=0
  while IFS='|' read -r name phase script; do
    case "$name" in ''|\#*) continue;; esac
    [ -f "$DONE/$name" ] || [ -f "$DONE/$name.failed" ] || [ -f "$DONE/$name.skipped" ] && continue
    if [ ! -f "$script" ]; then blocked="$blocked $name"; continue; fi
    if [ "$phase" = heavy ]; then
      gate_open || { waiting=1; continue; }
      wait_ram || { say "STOP: RAM stayed below 64 GB"; exit 4; }
    fi
    disk_guard 100 || { say "disk_guard failed before stage $name; waiting 10 min"; sleep 600; continue; }
    set -a; source "$CONF"; set +a
    say "stage $name ($phase): start"
    run_stage "$name" "$script"; progressed=1
  done < <(grep -v '^[[:space:]]*#' "$STAGES")
  if [ "$blocked" != "$last_blocked" ] && [ -n "$blocked" ]; then say "blocked (script not built yet):$blocked"; last_blocked="$blocked"; fi
  if [ $progressed -eq 0 ]; then
    if [ -z "$blocked" ] && [ $waiting -eq 0 ]; then say "PIPELINE_DONE"; break; fi
    if [ $waiting -eq 0 ]; then   # only blocked stages left: wait for them to be built, at most 14 days
      [ -n "$idle_since" ] || idle_since=$(date +%s)
      [ $(( $(date +%s) - idle_since )) -gt $((14*86400)) ] && { say "STOP: stages still not built after 14 days:$blocked"; exit 5; }
    else idle_since=""; fi
    sleep 600
  else idle_since=""; fi
done
