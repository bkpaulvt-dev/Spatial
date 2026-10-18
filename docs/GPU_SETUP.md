# Continuing CIPHER on a lab GPU

## 1. Environment (once)

```bash
git clone https://github.com/bkpaulvt-dev/Spatial && cd Spatial
git checkout claude/new-session-u8luyj
python -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu121   # match your CUDA driver
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## 2. Data (about 13 GB for everything; Norman + Dixit alone are 1 GB)

```bash
mkdir -p data/perturb && cd data/perturb
for f in NormanWeissman2019_filtered DixitRegev2016 ReplogleWeissman2022_K562_essential ReplogleWeissman2022_rpe1; do
  curl -L -o $f.h5ad https://zenodo.org/api/records/7041849/files/$f.h5ad/content
done
cd ../..
python -c "from cipher.data import load_norman; import pickle; pickle.dump(load_norman('data/perturb/NormanWeissman2019_filtered.h5ad'), open('data/perturb/norman_prep.pkl','wb'))"
```

CAT-ATAC multiome data: GEO GSE288996.

## 3. State of the project (as of this commit)

* Model: `cipher/model.py`. Tuned design on the dev split (seed 100):
  `{"basal": false, "adversary": false, "direct": true}` (see `results/cipher_tuning/`).
* Dev-split result: overall accuracy ties the additive baseline (Pearson top-20 DE 0.892 vs 0.894),
  interaction prediction better (residual Pearson 0.68 vs 0.45 for scaled additive).
* Test splits 0-2 were run once (2026-10-17, TITAN RTX, 30 epochs): `results/norman_test.jsonl`.
  Median over 195 test doubles: Pearson top-20 DE 0.878 vs 0.905 for additive / scaled additive
  (a small loss); residual Pearson 0.71 vs 0.51 for scaled additive (a win). Do not re-tune on these.
* The code runs on CPU by default; pass `device="cuda"` to `CIPHER(...)` or `--device cuda` to
  `scripts/benchmark_norman.py` / `scripts/sim_escape.py` to use the GPU.

## 4. Planned analyses (Cell Press methods paper)

| Fig | Analysis | Data |
|---|---|---|
| 1 | Simulation: guide efficacy, escape AUROC, no spurious interactions, power | `scripts/sim_escape.py` |
| 2 | Unseen-pair prediction, GEARS-style 0/2, 1/2, 2/2 splits; baselines additive, linear, CPA, GEARS | Norman 2019 |
| 3 | Genetic-interaction discovery vs Norman's GI map | Norman 2019 |
| 4 | Guide failure on real data, guide concordance | Dixit 2016, Gasperini 2019 |
| 5 | Network and modules vs ChIP-seq / TF-target databases / GO | Replogle 2022 K562 |
| 6 | RNA + ATAC extension; HIC2 -> ZFPM2 -> TCF4 | CAT-ATAC GSE288996 |
| S | Ablations, hyperparameter robustness, seeds, runtime, RPE1 | all |

Rules kept so far: tune only on the dev split, report test splits once, report losses honestly.
