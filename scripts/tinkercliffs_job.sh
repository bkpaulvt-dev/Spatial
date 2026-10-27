#!/bin/bash
# Slurm job: full DLPFC benchmark on TinkerCliffs (VT ARC). CPU only.
# Fill in --account, check the partition with `sinfo`, then: sbatch scripts/tinkercliffs_job.sh
#SBATCH --job-name=hicast-dlpfc
#SBATCH --account=CHANGE_ME
#SBATCH --partition=normal_q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$HOME/Spatial}"
mkdir -p logs results

module load Miniconda3 2>/dev/null || module load Anaconda3
source activate spatial 2>/dev/null || conda activate spatial

export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

python scripts/benchmark_dlpfc.py \
    --data data/DLPFC \
    --out results/dlpfc_tc.jsonl \
    --seeds 0 1 2 \
    --methods histar histar_deterministic hicast \
    --workers "${SLURM_CPUS_PER_TASK:-8}"
