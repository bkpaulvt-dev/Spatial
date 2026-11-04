# DeepMed2: where files go. SOURCE this file at the top of every script and from ~/.bashrc.
#   . /mnt/disk/bikashkumar/SpatialBench/Spatial/scripts/deepmed2_env.sh
# Why: the root disk (/) of DeepMed2 is shared and was 100% full (5.3 GB free) while /mnt/disk had about 6 TB free.
# Nothing of ours may write temporary files, caches, installs or results to / (including /tmp and the home folder).
export BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
export TMPDIR="$BASE/tmp" TEMP="$BASE/tmp" TMP="$BASE/tmp"
export PIP_CACHE_DIR="$BASE/.pip_cache" CONDA_PKGS_DIRS="$BASE/.conda_pkgs" XDG_CACHE_HOME="$BASE/.cache"
export HF_HOME="$BASE/.cache/huggingface" TORCH_HOME="$BASE/.cache/torch" MPLCONFIGDIR="$BASE/.cache/matplotlib"
export NUMBA_CACHE_DIR="$BASE/.cache/numba" CUDA_CACHE_PATH="$BASE/.cache/nv" TRITON_CACHE_DIR="$BASE/.cache/triton"
export R_LIBS_USER="${R_LIBS_USER:-$BASE/Rlib}"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR" "$CONDA_PKGS_DIRS" "$XDG_CACHE_HOME" "$HF_HOME" "$TORCH_HOME" "$MPLCONFIGDIR" \
         "$NUMBA_CACHE_DIR" "$CUDA_CACHE_PATH" "$TRITON_CACHE_DIR" 2>/dev/null

# disk_guard [min_free_GB_on_BASE, default 100]: call it before every stage; returns 1 (stage must not start) if BASE has too little room or a
# temp variable points outside BASE. It only reads; it deletes nothing. A full root disk is reported as a warning (we cannot fix it).
disk_guard() {
  local need=${1:-100} free
  case "$TMPDIR" in "$BASE"/*) ;; *) echo "disk_guard: TMPDIR=$TMPDIR is not under $BASE" >&2; return 1;; esac
  free=$(df -BG --output=avail "$BASE" 2>/dev/null | tail -1 | tr -dc '0-9')
  if [ -z "$free" ] || [ "$free" -lt "$need" ]; then echo "disk_guard: only ${free:-?} GB free under $BASE (need $need)" >&2; return 1; fi
  local rfree; rfree=$(df -BG --output=avail / 2>/dev/null | tail -1 | tr -dc '0-9')
  [ -n "$rfree" ] && [ "$rfree" -lt 2 ] && echo "disk_guard: WARNING root disk has only ${rfree} GB free (not ours to fix; keep all writes under $BASE)" >&2
  return 0
}
