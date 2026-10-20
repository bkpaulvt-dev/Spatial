"""Preprocess the held-out BRCA (Visium) and Stereo-seq (MOSTA) sections into results/cache/<dataset>_<section>.npz.

Same keys as scripts/prepare_extra.py (X = PCs, G = log-normalised genes for BANKSY/SpaGCN, coords, labels, genes),
with the DLPFC preprocessing of hicast.data.preprocess (genes in >= 50 spots and >= 10 counts, 2000 Seurat-v3 HVGs on
counts, library-size normalisation, log1p, scaling, 200 PCs, seed 0); G holds the log-normalised 2000 HVGs.
Raw data: python scripts/download_new_datasets.py. Sections are registered in prepare_extra.EXTRA and
configs/datasets.yaml (all split "test").

    python scripts/prepare_new_datasets.py                    # every new section
    python scripts/prepare_new_datasets.py --datasets brca
"""
import argparse, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from prepare_extra import EXTRA, NEW, n_clusters  # noqa: E402

OUT = os.path.join(ROOT, "results", "cache")


def prepare(ds, sec):
    import scanpy as sc
    from hicast.data import preprocess
    from spatialbench.data import load_section
    a = load_section(ds, sec)
    hvg, X = preprocess(a, n_top_genes=2000, n_pcs=200, seed=0)
    b = a[:, hvg.var_names].copy()
    sc.pp.normalize_total(b, target_sum=1e4); sc.pp.log1p(b)
    G = b.X.toarray() if hasattr(b.X, "toarray") else np.asarray(b.X)
    labels = a.obs["ground_truth"].to_numpy(dtype=object)
    np.savez_compressed(os.path.join(OUT, f"{ds}_{sec}.npz"), X=X, G=G.astype(np.float32),
                        coords=np.asarray(a.obsm["spatial"], np.float32), labels=labels,
                        genes=np.array(hvg.var_names, dtype=object))
    return a.shape, pd.Series(labels).value_counts().size


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=list(NEW), choices=list(NEW))
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for ds in args.datasets:
        for sec in EXTRA[ds]["sections"]:
            (n, g), k = prepare(ds, sec)
            print(f"{ds} {sec}: {n} spots x {g} genes, {k} domains (n_clusters {n_clusters(ds, sec)})", flush=True)
