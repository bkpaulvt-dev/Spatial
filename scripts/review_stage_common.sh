# Sourced by the review stage scripts: project environment only, R packages and temporary files on /mnt/disk (the root file system is full), helpers.
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}; cd "$BASE/Spatial" || exit 1
. "$BASE/Spatial/scripts/deepmed2_env.sh"   # disk rule (CLAUDE.md)
# disk_guard before every stage/download; a failing guard waits (up to 6 h, as the runbook says) and then exits 99 (skipped, reason in the log)
for _i in $(seq 1 36); do disk_guard 100 && break; [ $_i -eq 36 ] && exit 99; sleep 600; done
. "$BASE/Spatial/scripts/spatialbench_path.sh"   # project env without any conda from ~/shared_disk (CLAUDE.md)
[ "$(python -c 'import sys;print(sys.prefix)')" = "$BASE/env" ] || { echo "not the project environment"; exit 2; }
export R_LIBS="$BASE/Rlib" R_LIBS_USER="$BASE/Rlib" TMPDIR="$BASE/tmp" MAKEFLAGS=-j4 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1; export PYTHONPATH="$BASE/Spatial/scripts/thread_shim:$PYTHONPATH"; mkdir -p "$TMPDIR"
export SPATIALBENCH_MAX_RSS_GB=${SPATIALBENCH_MAX_RSS_GB:-30}
SCRATCH="$BASE/review_scratch"; mkdir -p "$SCRATCH"
rlib_ok() { Rscript -e "quit(status = !requireNamespace('$1', quietly = TRUE))" >/dev/null 2>&1; }
# dry_ok <jsonl> : the last record of a dry-run file must be status ok with a finite ARI (exit 1 otherwise, reason printed)
dry_ok() { python - "$1" <<'PY'
import json, math, sys
rs = [json.loads(l) for l in open(sys.argv[1])]
r = rs[-1] if rs else None
if not r or r["status"] != "ok" or not math.isfinite(r["metrics"]["ARI"]):
    print("DRY RUN FAILED:", None if not r else (r["status"], str(r.get("error", ""))[:600])); sys.exit(1)
print("dry run ok:", r["id"], "ARI=%.3f" % r["metrics"]["ARI"], "k_found", r.get("k_found"), "of", r.get("K"))
PY
}

