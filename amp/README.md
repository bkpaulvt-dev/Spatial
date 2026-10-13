# Multi-task ESM-2 baseline for antimicrobial peptides

Fine-tunes ESM-2 with three heads (activity, toxicity, hemolysis) on a homology-aware split, and
reports a logistic-regression baseline on composition/physico-chemical features next to it.
(This directory is independent of the HiCAST code elsewhere in the repo.)

## Data format
CSV with `sequence` and any of `activity`, `toxicity`, `hemolysis` (0/1; **blank = unknown**, masked out of the loss).
Optional `cluster` column (e.g. from `mmseqs easy-cluster --min-seq-id 0.4`) overrides the built-in clustering.
Collect data yourself from APD3 / DBAASP / DRAMP / HemoPI etc.; take **experimentally tested** negatives where you can.
Duplicate sequences are merged; conflicting labels become unknown.

## Run (one process per GPU)
```bash
pip install -r amp/requirements.txt
CUDA_VISIBLE_DEVICES=0 python -m amp.train --data peptides.csv --out runs/650M_s0 --seed 0 \
    --model facebook/esm2_t33_650M_UR50D --bs 32 --epochs 10
CUDA_VISIBLE_DEVICES=1 python -m amp.train --data peptides.csv --out runs/650M_s1 --seed 1   # second GPU
```
Useful ablations: `--freeze-layers -1` (linear probe), `--model facebook/esm2_t12_35M_UR50D`, `--identity 0.3`.
Outputs in `--out`: `metrics.json` (val history, test AUROC/AUPRC/MCC per task for ESM-2 and the logreg baseline),
`test_predictions.csv`, `best.pt`, and the exact `train/val/test.csv`.

## Notes / limits
- Built-in clustering is an edit-distance proxy for identity. For a publishable benchmark use MMseqs2 clusters.
- The seed changes both the cluster->split assignment and initialisation; report mean±sd over seeds.
- Thresholds (for MCC) are tuned on validation only; AUROC/AUPRC are threshold-free.
- `--synthetic` / `--tiny` are smoke tests of the code path only; their metrics are meaningless.
- The local tokenizer is checked against the Hugging Face tokenizer at start-up for real models.

Tests: `python -m pytest tests_amp -q`
