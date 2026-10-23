"""Breast cancer: score at the 4 coarse classes (annot_type: Healthy, Tumor, Invasive, Surrounding tumor) instead of the
20 numbered regions (fine_annot_type). Each fine region belongs to exactly one coarse class. Every seed-0 embedding is
clustered with matched clustering (tied Gaussian mixture, 20 starts, best likelihood) at K = 4.

python scripts/brca_coarse.py -> results/brca_coarse.json
"""
import glob, json, os
import numpy as np, pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
meta = pd.read_csv(os.path.join(ROOT, "data", "BRCA", "block_a_1", "metadata.tsv"), sep="\t", index_col=0)
fine2coarse = meta.groupby("fine_annot_type").annot_type.first().to_dict()
y = np.load(os.path.join(ROOT, "results", "cache", "brca_block_a_1.npz"), allow_pickle=True)["labels"]
yc = np.array([fine2coarse[v] for v in y])
out = {}
for f in sorted(glob.glob(os.path.join(ROOT, "results", "emb", "brca_block_a_1_*.npy"))):
    m = os.path.basename(f)[len("brca_block_a_1_"):-4]
    Z = np.load(f).astype(np.float64)
    r = {}
    for k, lab in ((4, yc), (20, y)):
        p = GaussianMixture(k, covariance_type="tied", n_init=20, reg_covar=1e-5, random_state=0).fit(Z).predict(Z)
        r[f"ARI_k{k}"] = float(adjusted_rand_score(lab, p))
    out[m] = r
    print(f"{m:<18} coarse K=4 {r['ARI_k4']:.3f}   fine K=20 {r['ARI_k20']:.3f}", flush=True)
json.dump(out, open(os.path.join(ROOT, "results", "brca_coarse.json"), "w"), indent=1)
