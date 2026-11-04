# Sourced after deepmed2_env.sh by our scripts. Rule (CLAUDE.md): never use ~/shared_disk. This drops it from PATH, never uses a conda that lives there, uses a clean conda config
# that points only under $BASE, and activates the project environment $BASE/env directly (PATH, CONDA_PREFIX and the env's own activate.d scripts) without any conda binary.
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
PATH=$(printf '%s' "$PATH" | tr ':' '\n' | grep -v '/shared_disk' | paste -sd:); export PATH
unset CONDA_EXE _CONDA_EXE _CONDA_ROOT CONDA_PYTHON_EXE CONDA_DEFAULT_ENV CONDA_SHLVL CONDA_PROMPT_MODIFIER VIRTUAL_ENV
export CONDARC="$BASE/condarc"
[ -f "$CONDARC" ] || printf 'envs_dirs:\n  - %s/envs\npkgs_dirs:\n  - %s/.conda_pkgs\nauto_activate: false\n' "$BASE" "$BASE" > "$CONDARC"
export PIP_CACHE_DIR="$BASE/.pip_cache" CONDA_PKGS_DIRS="$BASE/.conda_pkgs" MAMBA_ROOT_PREFIX="$BASE/mamba"
export CONDA_PREFIX="$BASE/env" PATH="$BASE/env/bin:$BASE/bin:$PATH"
for _f in "$BASE"/env/etc/conda/activate.d/*.sh; do [ -f "$_f" ] && . "$_f"; done 2>/dev/null
