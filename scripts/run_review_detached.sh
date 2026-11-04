#!/bin/bash
# Start / inspect the review runner (docs/DEEPMED2_NEXT.md), detached from the terminal (survives closing the laptop, SSH or a Claude session).
#   bash scripts/run_review_detached.sh            start (refuses a second copy)
#   bash scripts/run_review_detached.sh status     plain-language status: runner, gate, stage table, last lines, decisions file
# Phone alerts: the topic file $BASE/ntfy_topic is used if it exists (never printed or committed). Decisions: edit $BASE/review_config.env.
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
export TMPDIR=/mnt/disk/bikashkumar/SpatialBench/tmp PIP_CACHE_DIR=/mnt/disk/bikashkumar/SpatialBench/.pip_cache CONDA_PKGS_DIRS=/mnt/disk/bikashkumar/SpatialBench/.conda_pkgs XDG_CACHE_HOME=/mnt/disk/bikashkumar/SpatialBench/.cache   # root (/) is full: temporary and cache files on /mnt/disk
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR" "$CONDA_PKGS_DIRS" "$XDG_CACHE_HOME"
cd "$BASE/Spatial" 2>/dev/null || cd "$(dirname "$0")/.."
PIDF="$BASE/review_pipeline.pid"; STATUS="$BASE/review_status.txt"; DONE="$BASE/review_done"
running() { P=$(cat "$PIDF" 2>/dev/null); [ -n "$P" ] && kill -0 "$P" 2>/dev/null; }
if [ "$1" = "status" ]; then
  if running; then echo "The review runner is RUNNING (pid $(cat $PIDF))."; else echo "The review runner is NOT running."; fi
  if grep -q PHASE2_DONE "$BASE/newdata_status.txt" 2>/dev/null; then echo "Gate: OPEN (the current plan has finished; heavy stages may run)."; else echo "Gate: CLOSED (heavy stages wait for the current plan to finish: PHASE2_DONE in newdata_status.txt); prep stages run now."; fi
  echo; echo "--- stages (name | phase | state)"
  grep -v '^[[:space:]]*#' scripts/review_stages.txt | grep -v '^$' | while IFS='|' read -r n ph sc; do
    if [ -f "$DONE/$n" ]; then st=done; elif [ -f "$DONE/$n.failed" ]; then st=FAILED; elif [ -f "$DONE/$n.skipped" ]; then st="skipped by decision"; elif [ ! -f "$sc" ]; then st="blocked: script not built yet"; else st="pending"; fi
    printf "  %-28s %-6s %s\n" "$n" "$ph" "$st"; done
  echo; echo "--- last 12 lines of $STATUS"; tail -12 "$STATUS" 2>/dev/null || echo "(no status file yet)"
  echo; echo "--- jobs running now:"; ps -eo pid,etime,rss,args | grep -E "review_queue|bench_run|review_stage" | grep -v grep | cut -c1-140 || true
  echo; echo "--- decisions ($BASE/review_config.env):"; grep -v '^#' "$BASE/review_config.env" 2>/dev/null | grep -v '^$'
  [ -f "$BASE/ntfy_topic" ] && echo "phone alerts: topic file present (content not shown)" || echo "phone alerts: off"
  exit 0
fi
if running; then echo "already running (pid $(cat $PIDF)); use: bash scripts/run_review_detached.sh status"; exit 0; fi
setsid nohup bash scripts/review_runner.sh > "$BASE/review_runner.log" 2>&1 < /dev/null &
echo $! > "$PIDF"
echo "started the review runner (pid $!), detached. Check:  bash scripts/run_review_detached.sh status"
