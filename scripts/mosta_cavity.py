"""Share of bins and median counts of the MOSTA 'Cavity' annotation class per Stereo-seq section (low-count region; Limitations).

python scripts/mosta_cavity.py   -> results/mosta_cavity.csv
"""
import os, warnings
import anndata as ad, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
rows = []
for s in ("E9.5_E1S1", "E10.5_E2S1", "E10.5_E1S1"):
    a = ad.read_h5ad(os.path.join(ROOT, "data", "Stereo", f"{s}.MOSTA.h5ad"), backed="r")
    X = a.layers["count"] if "count" in a.layers else a.X
    tot = np.asarray(X.sum(axis=1)).ravel(); ann = a.obs["annotation"].astype(str).values
    cav = ann == "Cavity"
    rows.append(dict(section=s, n_bins=len(ann), cavity_frac=cav.mean(), cavity_median_counts=float(np.median(tot[cav])),
                     other_median_counts=float(np.median(tot[~cav]))))
pd.DataFrame(rows).to_csv(os.path.join(ROOT, "results", "mosta_cavity.csv"), index=False)
print(pd.DataFrame(rows).round(2).to_string())
