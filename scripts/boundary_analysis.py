"""Accuracy at domain boundaries vs. interiors: anisotropic vs. linear diffusion.

A spot is a *boundary* spot if any of its spatial KNN neighbours (k = 6) has a
different ground-truth layer. Predicted clusters are matched to layers with the
Hungarian algorithm, and accuracy is reported separately on boundary and
interior spots (seeds 0-2, all 12 slices).
"""
import os, sys, json, warnings
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import wilcoxon
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, ".."), HERE]
from anisost import AnisoST, spatial_knn
from benchmark_anisost import DLPFC_SLICES, N_CLUSTERS

warnings.filterwarnings("ignore")
cache = sys.argv[1] if len(sys.argv) > 1 else "results/cache"
rows = []
for s in DLPFC_SLICES:
    z = np.load(f"{cache}/{s}.npz", allow_pickle=True)
    X, C, y = z["X"], z["coords"], z["labels"]
    keep = np.array([isinstance(v, str) for v in y])
    A = spatial_knn(C, 6).tolil()
    yl = np.array([v if isinstance(v, str) else "" for v in y])
    bnd = np.array([keep[i] and any(yl[j] != yl[i] and keep[j] for j in A.rows[i]) for i in range(len(y))])
    for seed in (0, 1, 2):
        for diff in ("anisotropic", "linear"):
            p = AnisoST(diffusion=diff, seed=seed).fit_predict(X, C, N_CLUSTERS[s])
            labs = np.unique(yl[keep])
            M = np.array([[np.sum((p[keep] == c) & (yl[keep] == l)) for l in labs] for c in range(N_CLUSTERS[s])])
            r, c = linear_sum_assignment(-M)
            mp = dict(zip(r, labs[c]))
            hit = np.array([mp.get(v, "") for v in p]) == yl
            rows.append({"slice": s, "seed": seed, "diffusion": diff,
                         "acc_boundary": hit[bnd].mean(), "acc_interior": hit[keep & ~bnd].mean(),
                         "frac_boundary": bnd[keep].mean()})
    print(s, flush=True)
with open(os.path.join(HERE, "..", "results", "anisost_boundary.jsonl"), "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
import pandas as pd
d = pd.DataFrame(rows).groupby(["slice", "diffusion"])[["acc_boundary", "acc_interior"]].mean().unstack()
print(d.round(3))
for m in ("acc_boundary", "acc_interior"):
    diff = d[m]["anisotropic"] - d[m]["linear"]
    print(m, "aniso - linear: mean %.3f, wins %d/12, p=%.3f" % (diff.mean(), (diff > 0).sum(), wilcoxon(diff).pvalue))
