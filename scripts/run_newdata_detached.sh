#!/bin/bash
# Start the new-datasets pipeline detached from the terminal (survives closing the laptop, SSH or a Claude session).
#   bash scripts/run_newdata_detached.sh            start (refuses to start a second copy, or while another benchmark job runs)
#   bash scripts/run_newdata_detached.sh status     plain-language status
# Phone alerts (optional): the topic file $BASE/ntfy_topic is used if it exists; it is never printed or committed.
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
cd "$BASE/Spatial" 2>/dev/null || cd "$(dirname "$0")/.."
PIDF="$BASE/newdata_pipeline.pid"; STATUS="$BASE/newdata_status.txt"
running() { P=$(cat "$PIDF" 2>/dev/null); [ -n "$P" ] && kill -0 "$P" 2>/dev/null; }
if [ "$1" = "status" ]; then
  if running; then echo "The new-datasets pipeline is RUNNING (pid $(cat $PIDF))."; else echo "The new-datasets pipeline is NOT running."; fi
  echo; echo "--- last 15 lines of $STATUS"; tail -15 "$STATUS" 2>/dev/null || echo "(no status file yet)"
  echo; echo "--- jobs running now:"; ps -eo pid,etime,rss,args | grep -E "bench_run|newdata_queue|simulate_domains" | grep -v grep | cut -c1-140 || true
  echo; echo "--- records so far (newest per job):"
  source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env" 2>/dev/null
  python - <<'PY'
import json, glob, collections
last = {}
for f in glob.glob("results/newdata_runs_*.jsonl"):
    for l in open(f):
        r = json.loads(l); last[r["id"]] = r
c = collections.Counter(r["status"] for r in last.values())
print(f"  {len(last)} jobs recorded: {dict(c)}" if last else "  none yet")
PY
  echo; echo "--- RAM (GB) and disk:"; free -g | sed -n '1,2p'; df -h /mnt/disk | tail -1
  [ -f "$BASE/ntfy_topic" ] && echo "phone alerts: topic file present (content not shown)" || echo "phone alerts: off"
  exit 0
fi
if running; then echo "already running (pid $(cat $PIDF)); use: bash scripts/run_newdata_detached.sh status"; exit 0; fi
# one heavy thing at a time on the shared server: never start next to another benchmark, setup or download of ours
OTHER=$(ps -u "$USER" -o pid,args | grep -E "bench_queue|bench_run|deepmed2_pipeline|setup_deepmed2|download_new_datasets|mclust_seed" | grep -v grep | head -3)
if [ -n "$OTHER" ]; then echo "NOT started: another job of yours is running:"; echo "$OTHER"; exit 1; fi
setsid nohup bash scripts/newdata_pipeline.sh > "$BASE/newdata_pipeline.log" 2>&1 < /dev/null &
echo $! > "$PIDF"
echo "started pipeline (pid $!), detached. Check:  bash scripts/run_newdata_detached.sh status"
