#!/bin/bash
# Slurm job: DLPFC benchmark on one TinkerCliffs GPU (VT ARC).
# 1. Fill in --account (see: sacctmgr show assoc user=$USER format=account%30).
# 2. Check GPU partitions with: sinfo -o "%P %G %l" | grep -i gpu   (e.g. a100_normal_q, h200_normal_q)
# 3. sbatch scripts/tinkercliffs_gpu_job.sh
#SBATCH --job-name=hicast-dlpfc-gpu
#SBATCH --account=CHANGE_ME
#SBATCH --partition=a100_normal_q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$HOME/Spatial}"
mkdir -p logs results

module load Miniconda3 2>/dev/null || module load Anaconda3
source activate spatial 2>/dev/null || conda activate spatial

export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
nvidia-smi

# Several small runs share the one GPU; raise --workers if GPU use stays low.
python scripts/benchmark_dlpfc.py \
    --data data/DLPFC \
    --out results/dlpfc_gpu.jsonl \
    --seeds 0 1 2 \
    --methods histar histar_deterministic hicast \
    --device cuda \
    --workers 4
