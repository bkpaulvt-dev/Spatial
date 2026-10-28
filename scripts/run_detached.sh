#!/bin/bash
# Start the DeepMed2 pipeline detached from the terminal: it survives closing the SSH connection or the laptop, and the death of a
# Claude session. Safe to run again at any time (it refuses to start a second copy; stages already done are skipped).
#   bash scripts/run_detached.sh [cuda|cpu]        # default cuda = GraphST/DeepST on GPU 1, rest on CPU
#   NTFY_TOPIC=<your-secret-topic> bash scripts/run_detached.sh cuda    # also send phone notifications (ntfy.sh app)
#   bash scripts/run_detached.sh status            # what is happening now
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
cd "$BASE/Spatial" 2>/dev/null || cd "$(dirname "$0")/.."
if [ "$1" = "status" ]; then
  echo "--- $BASE/status.txt (last 15 lines)"; tail -15 "$BASE/status.txt" 2>/dev/null
  P=$(cat "$BASE/pipeline.pid" 2>/dev/null); if [ -n "$P" ] && kill -0 "$P" 2>/dev/null; then echo "pipeline RUNNING (pid $P)"; else echo "pipeline NOT running"; fi
  echo "--- running jobs:"; ps -eo pid,etime,rss,args | grep -E "bench_run|bench_queue|setup_deepmed2" | grep -v grep | cut -c1-150
  echo "--- RAM:"; free -g | sed -n '1,2p'; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
  exit 0
fi
[ -n "$NTFY_TOPIC" ] && echo "$NTFY_TOPIC" > "$BASE/ntfy_topic"      # phone notifications through ntfy.sh (optional)
P=$(cat "$BASE/pipeline.pid" 2>/dev/null)
if [ -n "$P" ] && kill -0 "$P" 2>/dev/null; then echo "already running (pid $P); use: bash scripts/run_detached.sh status"; exit 0; fi
setsid nohup bash scripts/deepmed2_pipeline.sh "${1:-cuda}" > "$BASE/pipeline.log" 2>&1 < /dev/null &
echo $! > "$BASE/pipeline.pid"
echo "started pipeline (pid $!), detached. Check:  bash scripts/run_detached.sh status"
