# Spatial: HiSTaR analysis and HiCAST

Spatial-domain identification for spatial transcriptomics.

* **`docs/HiCAST.md`**: summary of the HiSTaR paper (Yu et al., *J. Transl. Med.*
  2025), its weaknesses (including bugs found in the official code), the design of
  **HiCAST**, the proposed successor, and an honest benchmark on all 12 DLPFC slices.
* **`hicast/histar.py`**: faithful PyTorch port of the official HiSTaR code (MIT).
* **`hicast/model.py`**: HiCAST: expression-aware graph, per-spot hop attention,
  hierarchical VAE with deterministic inference, local–global contrast, attention
  fusion of levels, learned loss balancing, optional batch-aware graph and decoder.
* **`scripts/benchmark_dlpfc.py`**: resumable, parallel benchmark (methods × slices × seeds).

## Headline result

On 12 DLPFC slices × 3 seeds, with identical preprocessing and clustering,
**HiCAST does not beat HiSTaR**: median ARI 0.493 vs 0.509 (p = 0.68). HiCAST
was better on the donor used for tuning but worse on the two held-out donors. The
official HiSTaR code also gives a lower median ARI here (0.509) than the paper
reports (0.65). See `docs/HiCAST.md` §5–6 for the full results and lessons.

## Usage

```bash
pip install -r requirements.txt
```

```python
from hicast.data import load_dlpfc
from hicast.model import HiCAST
from hicast.cluster import gmm_eee, evaluate

d = load_dlpfc("data/DLPFC", "151673")       # folder with filtered_feature_bc_matrix.h5 + metadata.tsv
Z = HiCAST(d.X, d.coords, seed=0).fit().embed()
labels = gmm_eee(Z, d.meta["n_clusters"])
print(evaluate(labels, d.labels))
```

Multi-slice integration: `load_dlpfc_multi(root, ["151673", "151674"])`, then pass
`batch=d.batch` to `HiCAST` (adds cross-slice MNN edges and a batch-conditional decoder).

### Data
DLPFC count matrices: `https://spatial-dlpfc.s3.us-east-2.amazonaws.com/h5/<slice>_filtered_feature_bc_matrix.h5`;
annotations (`metadata.tsv`): `JinmiaoChenLab/SEDR_analyses/data/DLPFC/<slice>/`.

### Benchmark
```bash
python scripts/benchmark_dlpfc.py --data data/DLPFC --out results/dlpfc_main.jsonl \
    --seeds 0 1 2 --methods histar histar_deterministic hicast --workers 4
# ablation variants:  --config no_lg='{"local_global": false}'
```
