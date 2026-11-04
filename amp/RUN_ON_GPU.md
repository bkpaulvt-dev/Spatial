# Runbook: multi-task ESM-2 AMP baseline on the GPU server

> **For Claude Code running on the DeepMed2 server (2 x 24 GB NVIDIA GPUs).**
> Read this whole file, then execute the steps in order. Stop and ask the user wherever a step says **ASK**.
> Rules: never invent or simulate data; never report metrics from `--synthetic` / `--tiny` runs as results;
> if a step fails, report the exact error rather than working around it silently.

## 0. Goal
Fine-tune ESM-2 with three heads (activity, toxicity, hemolysis) on a **homology-aware split**, compare it with a
logistic-regression baseline on the same split, and report mean ± sd over seeds. The code is already written and
unit-tested (8 tests, CPU only). It has **not** yet been run on real data or real ESM-2 weights, so this run is its
first real test. Expect to fix small issues.

## 1. Get the code
```bash
git clone https://github.com/bkpaulvt-dev/Spatial.git && cd Spatial
git checkout claude/zen-noether-05q4o8
ls amp tests_amp        # train.py, build_dataset.py, tools.py, model.py, ...
```
(`amp/` is independent of the HiCAST code elsewhere in the repo.)

## 2. Environment
```bash
nvidia-smi                                   # expect 2 GPUs, ~24 GB each; note driver/CUDA version
python3 -m venv .venv-amp && source .venv-amp/bin/activate
pip install -r amp/requirements.txt          # if torch lacks CUDA, install the wheel matching the driver
python -c "import torch;print(torch.__version__, torch.cuda.device_count(), torch.cuda.is_available())"
python -m pytest tests_amp -q                # all 8 must pass before continuing
```
If `torch.cuda.is_available()` is False, fix the torch/CUDA install first (do not train on CPU).

## 3. Check model download works
```bash
python - <<'EOF'
from amp.tokenizer import check_against_hf
check_against_hf("facebook/esm2_t6_8M_UR50D", ["KKLLKWLKKLL", "GIGKFLHSAK"])
print("tokenizer matches HF; model hub reachable")
EOF
```
If the server cannot reach huggingface.co: **ASK** the user for an offline copy/mirror. Models needed:
`facebook/esm2_t33_650M_UR50D` (main), `facebook/esm2_t12_35M_UR50D` (small ablation).
`--model` accepts a local directory path.

## 4. Smoke-test the pipeline (not a result)
```bash
python -m amp.train --synthetic --tiny --out runs/smoke --epochs 3
```
Should finish in seconds. Then a short GPU test with the small real model:
```bash
python -m amp.train --synthetic --model facebook/esm2_t6_8M_UR50D --out runs/smoke_gpu --epochs 2
```
Confirm it used the GPU (`nvidia-smi` while running). Delete `runs/smoke*` afterwards.

## 5. Build the real dataset  (ASK the user for the files)
**ASK** where the database exports are. Expected sources (the user downloads them; formats vary by version):
APD3, DBAASP, DRAMP (activity); HemoPI / DBAASP / DRAMP (hemolysis); ToxinPred or similar (toxicity); and,
ideally, **experimentally tested inactive** peptides as negatives.

For each file:
```bash
python -m amp.build_dataset inspect <file>      # columns + categorical values
```
Then write `data/spec.json` (schema and example in the docstring of `amp/build_dataset.py`) and build:
```bash
mkdir -p data
python -m amp.build_dataset build --spec data/spec.json --out data/peptides.csv
cat data/peptides.csv.report.json
```
Decisions to **ASK** the user about rather than guess: the HC50 threshold for "hemolytic" (µM), which numeric field
defines activity (e.g. MIC cut-off), and whether any negatives are "assumed" (e.g. UniProt non-AMP) rather than tested.
Keep assumed negatives in a **separate source name** so they can be ablated. Show the user the report (rows kept/dropped,
label conflicts, positives per task) and confirm before training. If a task has < ~200 labelled positives, say so.

## 6. Homology-aware clusters (MMseqs2)
Without this, the built-in edit-distance clustering is only a proxy.
```bash
conda install -c bioconda mmseqs2 -y     # or: apt/brew/binary release; ASK if no install route
python -m amp.tools fasta data/peptides.csv data/peptides.fasta
mmseqs easy-cluster data/peptides.fasta data/clu data/tmp --min-seq-id 0.4 -c 0.8 --cov-mode 1 -s 7.5
python -m amp.tools add-clusters data/peptides.csv data/clu_cluster.tsv data/peptides_clustered.csv
```
Caveat: MMseqs2's k-mer prefilter is weak on very short peptides, so some similar pairs may stay unclustered. State this
in the final report. Run the whole experiment a second time with `--min-seq-id 0.3` as a sensitivity check.

## 7. Train: 2 GPUs, one process each
650M parameters, bf16, batch 32 and max length 100 should fit in 24 GB; if OOM, use `--bs 16` and report it.
```bash
mkdir -p runs logs
for seed in 0 1 2 3 4; do
  gpu=$((seed % 2))
  CUDA_VISIBLE_DEVICES=$gpu nohup python -m amp.train --data data/peptides_clustered.csv \
    --model facebook/esm2_t33_650M_UR50D --out runs/esm650_s$seed --seed $seed \
    --epochs 10 --bs 32 > logs/esm650_s$seed.log 2>&1 &
  [ $gpu -eq 1 ] && wait      # at most 2 jobs at a time
done; wait
```
Watch `tail logs/*.log`. Each run prints split sizes, the logistic-regression test AUROC, per-epoch validation AUROC,
and final test metrics. Checks while running:
- Train loss decreasing and val AUROC well above 0.5 by epoch 2-3. If val AUROC stays ~0.5, stop and diagnose
  (labels, LR, tokenizer) instead of waiting.
- `labelled per task (train)` counts match the dataset report.

Ablations (same seeds, same split): linear probe `--freeze-layers -1`; small model `--model facebook/esm2_t12_35M_UR50D`;
`--identity`/MMseqs2 0.3 clusters. Name outputs clearly, e.g. `runs/probe650_s$seed`.

## 8. Aggregate
```bash
python -m amp.tools aggregate runs/esm650_s*/metrics.json
python -m amp.tools aggregate runs/probe650_s*/metrics.json
```
Prints mean ± sd (over seeds) of AUROC / AUPRC / MCC for ESM-2 **and** the logistic-regression baseline, per task.
Seeds change both the cluster-to-split assignment and the initialisation, so the sd includes split variance.

## 9. Report back to the user
Write `runs/REPORT.md` containing: dataset report summary; MMseqs2 settings; the aggregate tables (both identity levels,
fine-tune vs linear probe vs logistic regression); per-task sample counts; GPU/time per run; and honest caveats:
negatives provenance, short-peptide clustering weakness, tasks with few positives. State clearly whether ESM-2 beats the
logistic-regression baseline **on the homology-split test set** and by how much (compare to the sd). Do not describe
results as state-of-the-art; no external benchmark comparison has been done.

## 10. Housekeeping
- Do not commit `data/`, `runs/`, `logs/` or checkpoints (`best.pt`). Add them to `.gitignore` if missing.
- If you change code to fix a bug, rerun `python -m pytest tests_amp -q` and commit the fix on a new branch off
  `claude/zen-noether-05q4o8`, then tell the user exactly what changed and why.

## Known limitations of this code
- Mean pooling + linear heads only; no LoRA, no class re-weighting, no calibration. These are deliberate (simple baseline).
- MCC thresholds are tuned on validation, applied to test.
- Sequences are limited to the 20 standard residues, length 5-100 (no D-amino acids, modifications or cyclisation).
