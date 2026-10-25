#!/bin/bash
# DLPFC benchmark on one VT ARC A100. Submit from the repo root:
#   sbatch --account=<your_allocation> cluster/arc/run_a100.sbatch
# Extra benchmark arguments can follow the script name, e.g.
#   sbatch --account=<alloc> cluster/arc/run_a100.sbatch --methods hicast --seeds 0
#
# Check partition names with `sinfo -s` and your allocations with `quota` / ColdFront;
# change -p below if ARC has renamed the A100 partition.
#SBATCH -J spatial-a100
#SBATCH -p a100_normal_q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH -t 12:00:00
#SBATCH -o logs/%x-%j.out

set -euo pipefail
mkdir -p logs

module reset
module load Miniforge3 2>/dev/null || module load Miniconda3
source activate "${ENV:-spatial}"

nvidia-smi
python -c "import torch; assert torch.cuda.is_available(), 'no GPU visible'; print(torch.cuda.get_device_name(0))"

DATA=${DATA:-data/DLPFC}                       # or a path under /projects/<group>/ ...
OUT=${OUT:-results/dlpfc_a100_${SLURM_JOB_ID}.jsonl}

# Each worker is a separate process sharing the one GPU; 4 is a safe start for DLPFC-sized slices.
python scripts/benchmark_dlpfc.py --data "$DATA" --out "$OUT" \
    --device cuda --workers "${WORKERS:-4}" "$@"
