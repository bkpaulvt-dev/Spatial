#!/bin/bash
# The whole DeepMed2 job in one resumable script: setup -> wait for RAM -> rerun -> commit results. Meant to be started
# detached by scripts/run_detached.sh, so it keeps running when the SSH connection, the laptop or a Claude session goes away.
# Every stage is skipped when already done, so after a crash or a reboot simply start run_detached.sh again.
#   progress: $BASE/status.txt (one line per stage)   log: $BASE/pipeline.log
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
DEV=${1:-cuda}                       # cuda: GraphST and DeepST on GPU index $GPU (default 1); cpu: everything on CPU
export GPU=${GPU:-1}
MIN_RAM=${MIN_RAM:-64}               # GB available before the rerun may start
cd "$BASE/Spatial" || exit 1
say() { echo "$(date '+%F %T') $*" | tee -a "$BASE/status.txt"; }
say "pipeline start (device=$DEV, pid $$, host $(hostname))"

# 1. setup (creates the environment, installs BASS, downloads the data; resumable)
if [ ! -f "$BASE/.setup_done" ]; then
  say "stage 1/4: setup"
  for try in 1 2 3; do
    if bash scripts/setup_deepmed2.sh >> "$BASE/setup_deepmed2.log" 2>&1; then touch "$BASE/.setup_done"; break; fi
    say "setup failed (attempt $try); see $BASE/setup_deepmed2.log"; sleep 120
  done
  [ -f "$BASE/.setup_done" ] || { say "STOP: setup failed three times"; exit 2; }
fi
say "stage 1/4: setup done"
source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env"

# 2. wait for enough free RAM (the server is shared); up to 6 h
say "stage 2/4: waiting for >= ${MIN_RAM} GB available RAM"
for i in $(seq 1 36); do
  A=$(free -g | awk 'NR==2{print $7}')
  [ "$A" -ge "$MIN_RAM" ] && break
  say "only ${A} GB available; waiting 10 min"; sleep 600
done
A=$(free -g | awk 'NR==2{print $7}'); [ "$A" -ge "$MIN_RAM" ] || { say "STOP: RAM stayed below ${MIN_RAM} GB (${A} GB)"; exit 3; }
say "RAM available: ${A} GB"

# 3. the rerun; GPU variant only if torch can use the GPU, else CPU. Restarted up to 5 times (resumable).
if [ "$DEV" = "cuda" ] && ! CUDA_VISIBLE_DEVICES=$GPU python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)"; then
  say "CUDA not available to torch -> running the CPU variant"; DEV=cpu
fi
say "stage 3/4: rerun (device=$DEV)"
for try in 1 2 3 4 5; do
  if [ "$DEV" = "cuda" ]; then DEVICE=cuda GPU=$GPU sh scripts/rerun_memory_failures.sh >> "$BASE/rerun.log" 2>&1
  else sh scripts/rerun_memory_failures.sh >> "$BASE/rerun.log" 2>&1; fi
  grep -q BIGMEM_DONE "$BASE/rerun.log" && break
  say "rerun ended without BIGMEM_DONE (attempt $try); restarting (resumable)"; sleep 60
done
grep -q BIGMEM_DONE "$BASE/rerun.log" || { say "STOP: rerun did not finish after 5 attempts; see $BASE/rerun.log"; exit 4; }
say "stage 3/4: rerun done"

# 4. results: summary, commit, push (a failed push is fine: the files stay in place)
say "stage 4/4: collecting results"
python - <<'PY' >> "$BASE/status.txt"
import json, glob
for f in sorted(glob.glob("results/benchmark_runs_bigmem*.jsonl")):
    for l in open(f):
        r = json.loads(l); m = r.get("metrics", {})
        print(f"  {r['id']:<55} {r['status']:<5} ARI={m.get('ARI', float('nan')):.3f} peak={r['resources'].get('peak_rss_gb', 0):.1f}GB device={r.get('device', 'cpu')}")
PY
git add results/benchmark_runs_bigmem*.jsonl 2>/dev/null
git -c user.name="DeepMed2 run" -c user.email="deepmed2@localhost" commit -qm "Rerun of the memory-capped jobs on DeepMed2 (CPU/GPU, 125 GB RAM)" 2>/dev/null
git push origin HEAD 2>&1 | tail -2 | tee -a "$BASE/status.txt" || true
ls results/runs/stereo__E10.5_E1S1__* results/runs/stereo__E10.5_E2S1__deepst__* 2>/dev/null | wc -l | xargs -I{} echo "  {} result files in results/runs (git-ignored; copy them back)" | tee -a "$BASE/status.txt"
say "PIPELINE_DONE"
