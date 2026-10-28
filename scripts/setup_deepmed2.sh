#!/bin/bash
# Set up the project on DeepMed2 for the rerun of the memory-capped jobs. Everything (code, conda environment, caches, data,
# results) goes under ONE folder, /mnt/disk/bikashkumar/SpatialBench; nothing is installed system-wide and no sudo is used.
# Re-running the script is safe (finished steps are skipped).
#
#   bash setup_deepmed2.sh 2>&1 | tee setup_deepmed2.log
#
# Needs: conda (miniconda/anaconda), git, internet access (GitHub, CRAN, conda-forge, 10x/CNGB for the data),
# about 30 GB free disk, and (for the rerun) >= 64 GB available RAM.
set -e
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}
REPO=${REPO:-https://github.com/bkpaulvt-dev/Spatial}
BRANCH=${BRANCH:-claude/great-cori-opzfx7}
step() { printf '\n=== %s ===\n' "$*"; }

step "0. checks"
mkdir -p "$BASE" && [ -w "$BASE" ] || { echo "cannot write to $BASE"; exit 1; }
echo "host: $(hostname)   user: $(whoami)"
echo "CPU : $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2)  ($(nproc) threads)"
free -g | sed -n '1,2p'
FREE_GB=$(df -BG --output=avail "$BASE" | tail -1 | tr -dc '0-9')
echo "free disk under $BASE: ${FREE_GB} GB"
[ "$FREE_GB" -ge 30 ] || { echo "need at least 30 GB free disk"; exit 1; }
AVAIL_RAM=$(free -g | awk 'NR==2{print $7}')
[ "$AVAIL_RAM" -ge 64 ] || echo "WARNING: only ${AVAIL_RAM} GB RAM available now (the rerun wants >= 64 GB); check again before starting it"
command -v git >/dev/null || { echo "git not found"; exit 1; }
command -v conda >/dev/null || { echo "conda not found (install miniconda in $BASE/miniconda if needed)"; exit 1; }
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv 2>/dev/null || echo "(no nvidia-smi: CPU only)"

# keep every cache inside the project folder
export CONDA_PKGS_DIRS="$BASE/.conda_pkgs" PIP_CACHE_DIR="$BASE/.pip_cache" TMPDIR="$BASE/tmp"
mkdir -p "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR" "$TMPDIR"

step "1. code (GitHub $BRANCH)"
if [ -d "$BASE/Spatial/.git" ]; then
  git -C "$BASE/Spatial" fetch origin "$BRANCH" && git -C "$BASE/Spatial" checkout "$BRANCH" && git -C "$BASE/Spatial" pull --ff-only origin "$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO" "$BASE/Spatial"   # a private repository asks for your GitHub login; it is not stored
fi
cd "$BASE/Spatial"
git log --oneline -1

step "2. conda environment (python 3.13 + R 4.3.3 + pinned packages) in $BASE/env"
if [ ! -x "$BASE/env/bin/python" ]; then
  # environment/environment.deepmed2.yml = environment.yml with series pins for the R/Bioconductor conda packages, no TeX Live
  (cd environment && conda env create -p "$BASE/env" -f environment.deepmed2.yml) || {
    echo "---- conda could not solve the environment; missing packages:"; exit 1; }
fi
set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$BASE/env"
python --version; R --version | head -1
if ! command -v g++ >/dev/null || ! command -v gfortran >/dev/null; then
  echo "compilers missing: installing them into the project environment"
  conda install -y -p "$BASE/env" -c conda-forge compilers
fi

step "3. R package BASS (needs a compiler)"
Rscript -e 'if (!requireNamespace("BASS", quietly = TRUE)) remotes::install_github("zhengli09/BASS@5c2690fddcdeb12461a69106ff4681777d0a8822", upgrade = "never") else cat("BASS already installed\n")'
Rscript -e 'library(BASS); library(mclust); cat("BASS and mclust load\n")'

step "4. method code that is used from a clone"
mkdir -p data/ext/methods
[ -d data/ext/methods/DeepST ] || git clone https://github.com/JiangBioLab/DeepST data/ext/methods/DeepST
git -C data/ext/methods/DeepST checkout -q e37997f
[ -d data/ext/methods/Spatial-MGCN ] || git clone https://github.com/cs-wangbo/Spatial-MGCN data/ext/methods/Spatial-MGCN
git -C data/ext/methods/Spatial-MGCN checkout -q cf4412d

step "5. Stereo-seq data (MOSTA E9.5_E1S1, E10.5_E2S1, E10.5_E1S1; several GB, resumable) + SHA-256 check"
python scripts/download_new_datasets.py --datasets stereo
python scripts/download_new_datasets.py --datasets stereo --verify-only

step "6. preflight"
python - <<'PY'
import importlib, os
for m in ("torch", "scanpy", "GraphST", "nichepca", "sklearn", "rpy2"):
    mod = importlib.import_module(m); print(f"{m:10s} {getattr(mod, '__version__', 'ok')}")
import torch; print("CUDA available to torch:", torch.cuda.is_available(), (torch.cuda.device_count() if torch.cuda.is_available() else ""))
PY
python scripts/bench_queue.py --dry-run --datasets stereo --sections E10.5_E1S1 --seeds 0 1 2 \
    --methods bass graphst nichepca spatial_mgcn deepst --out "$TMPDIR/dry_run.jsonl" --retry-errors | tail -3

step "done"
cat <<EOF
Project: $BASE/Spatial        environment: conda activate $BASE/env
Check again that >= 64 GB RAM is available (free -g), then start the rerun:

  cd $BASE/Spatial && source "\$(conda info --base)/etc/profile.d/conda.sh" && conda activate $BASE/env
  # CPU (recommended):
  nohup sh scripts/rerun_memory_failures.sh > bigmem.log 2>&1 &
  # or with GraphST/DeepST on the second GPU:
  DEVICE=cuda GPU=1 nohup sh scripts/rerun_memory_failures.sh > bigmem_gpu.log 2>&1 &
  tail -f bigmem.log        # ends with BIGMEM_DONE
EOF
