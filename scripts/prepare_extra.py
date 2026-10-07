"""Prepare the STARmap (mouse mPFC) and MERFISH (mouse hypothalamus) sections with domain labels.

Source: the BASS-Analysis repository (Li & Zhou, Nat. Biotechnol. 2022), which packages
STARmap (Wang et al., Science 2018; 3 sections, 166 genes, layers L1, L2/3, L5, L6) and
MERFISH animal 1 (Moffitt et al., Science 2018; Bregma -0.04 to -0.24, 155 genes,
8 annotated regions). Fetch and convert (needs R):

  git clone --depth 1 https://github.com/zhengli09/BASS-Analysis data/ext/BASS-Analysis
  Rscript scripts/export_bass_data.R data/ext/BASS-Analysis/data data/ext/csv
  python scripts/prepare_extra.py

Targeted panels have no HVG step: all genes are kept, counts are library-size normalised,
log-transformed, scaled, and reduced to 50 PCs. Output: results/cache/<dataset>_<section>.npz
with X (PCs), G (log-normalised genes, for BANKSY/SpaGCN), coords, labels, genes.
"""
import glob, os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "ext", "csv")
OUT = os.path.join(ROOT, "results", "cache")

EXTRA = {
    "starmap": {"sections": ["20180417_BZ5_control", "20180419_BZ9_control", "20180424_BZ14_control"], "n_clusters": 4},
    "merfish": {"sections": ["-0.04", "-0.09", "-0.14", "-0.19", "-0.24"], "n_clusters": 8},
}


def prepare(ds, sec):
    from sklearn.decomposition import PCA
    cnt = pd.read_csv(os.path.join(SRC, f"{ds}_{sec}_counts.csv"), index_col=0)
    info = pd.read_csv(os.path.join(SRC, f"{ds}_{sec}_info.csv"), index_col=0).loc[cnt.index]
    C = cnt.to_numpy(np.float64)
    keep = C.sum(1) > 0
    C, info = C[keep], info[keep]
    G = np.log1p(C / C.sum(1, keepdims=True) * 1e4)
    S = (G - G.mean(0)) / (G.std(0) + 1e-8)
    S = np.clip(S, -10, 10)
    X = PCA(50, random_state=0).fit_transform(S).astype(np.float32)
    labels = info["z"].astype(str).to_numpy().astype(object)
    np.savez_compressed(os.path.join(OUT, f"{ds}_{sec}.npz"), X=X, G=G.astype(np.float32),
                        coords=info[["x", "y"]].to_numpy(np.float32), labels=labels,
                        genes=np.array(cnt.columns, dtype=object))
    return C.shape, pd.Series(labels).value_counts().to_dict()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for ds, m in EXTRA.items():
        for sec in m["sections"]:
            print(ds, sec, *prepare(ds, sec))
