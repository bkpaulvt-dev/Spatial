#!/usr/bin/env bash
# One-time setup on a VT ARC login node (Tinker Cliffs). Run from the repo root:
#   bash cluster/arc/setup_env.sh
# Creates a conda env "spatial" with CUDA-enabled PyTorch and the repo's requirements.
set -euo pipefail

module reset
module load Miniforge3 2>/dev/null || module load Miniconda3   # module names vary by cluster; see `module spider conda`

ENV=${ENV:-spatial}
if ! conda env list | grep -qE "^${ENV}\s"; then
  conda create -y -n "$ENV" python=3.11
fi
source activate "$ENV"

# CUDA 12.1 wheels run on the A100 driver; the login node has no GPU, so the check below only confirms the build.
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python -c "import torch; print('torch', torch.__version__, 'CUDA build', torch.version.cuda)"
