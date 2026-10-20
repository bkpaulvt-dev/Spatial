"""Dataset registry access and uniform section loading (raw counts + coordinates + annotation)."""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Platform groups used by method adapters instead of `ds == "dlpfc"` checks (keep run_r_method.R in sync).
VISIUM = {"dlpfc", "brca"}                        # 10x Visium: hexagonal spot lattice, array_row/array_col
WHOLE_TRANSCRIPTOME = VISIUM | {"stereo"}         # spot/bin-level, whole transcriptome (HVG selection as DLPFC);
                                                  # the others (STARmap, MERFISH) are single-cell targeted panels


def load_registry(path: str | None = None) -> dict:
    with open(path or os.path.join(ROOT, "configs", "datasets.yaml")) as f:
        return yaml.safe_load(f)


def sections(reg: dict | None = None):
    """Yield (dataset, section, split) for every registered section."""
    reg = reg or load_registry()
    for ds, card in reg["datasets"].items():
        for sec, info in card["sections"].items():
            yield ds, sec, info.get("split", "test")


def load_section(ds: str, sec: str, root: str | None = None):
    """AnnData with raw counts in .X, coordinates in .obsm['spatial'] and labels in .obs['ground_truth']."""
    import anndata
    root = root or ROOT
    if ds == "dlpfc":
        import scanpy as sc
        path = os.path.join(root, "data", "DLPFC", sec)
        a = sc.read_10x_h5(os.path.join(path, "filtered_feature_bc_matrix.h5"))
        a.var_names_make_unique()
        meta = pd.read_csv(os.path.join(path, "metadata.tsv"), sep="\t", index_col=0).loc[a.obs_names]
        a.obs["ground_truth"] = meta["layer_guess_reordered"].astype(object).values
        a.obsm["spatial"] = meta[["imagecol", "imagerow"]].to_numpy(dtype=np.float64)
        a.obs["array_row"], a.obs["array_col"] = meta["row"].values, meta["col"].values
        return a
    if ds == "brca":   # 10x Visium (Space Ranger 1.1.0); scripts/download_new_datasets.py
        import scanpy as sc
        path = os.path.join(root, "data", "BRCA", sec)
        a = sc.read_10x_h5(os.path.join(path, "filtered_feature_bc_matrix.h5"))
        a.var_names_make_unique()
        pos = pd.read_csv(os.path.join(path, "spatial", "tissue_positions_list.csv"), header=None, index_col=0,
                          names=["barcode", "in_tissue", "array_row", "array_col", "pxl_row", "pxl_col"]).loc[a.obs_names]
        meta = pd.read_csv(os.path.join(path, "metadata.tsv"), sep="\t", index_col=0).reindex(a.obs_names)
        a.obs["ground_truth"] = meta["fine_annot_type"].astype(object).values   # 20 regions (configs/datasets.yaml)
        # full-resolution pixels in the (x=col, y=row) order of DLPFC (whose imagecol/imagerow are on a smaller scale:
        # spot spacing 273 vs ~6 units; method radii are expressed in measured spot spacings, so only the order matters)
        a.obsm["spatial"] = pos[["pxl_col", "pxl_row"]].to_numpy(dtype=np.float64)
        a.obs["array_row"], a.obs["array_col"] = pos["array_row"].values, pos["array_col"].values
        return a
    if ds == "stereo":   # Stereo-seq MOSTA bin50 h5ad; scripts/download_new_datasets.py
        import scipy.sparse as sp
        b = anndata.read_h5ad(os.path.join(root, "data", "Stereo", f"{sec}.MOSTA.h5ad"))
        X = sp.csr_matrix(b.layers["count"] if "count" in b.layers else b.X, dtype=np.float32)
        keep = np.asarray(X.sum(1)).ravel() > 0
        a = anndata.AnnData(X[keep], obs=pd.DataFrame(index=b.obs_names[keep].astype(str)),
                            var=pd.DataFrame(index=b.var_names.astype(str)))
        a.var_names_make_unique()
        a.obs["ground_truth"] = b.obs["annotation"].astype(str).to_numpy()[keep].astype(object)
        a.obsm["spatial"] = np.asarray(b.obsm["spatial"], dtype=np.float64)[keep]
        return a
    csv = os.path.join(root, "data", "ext", "csv")
    cnt = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_counts.csv"), index_col=0)
    info = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_info.csv"), index_col=0).loc[cnt.index]
    keep = cnt.sum(1).to_numpy() > 0
    a = anndata.AnnData(cnt[keep].to_numpy(np.float32), obs=pd.DataFrame(index=cnt.index[keep].astype(str)),
                        var=pd.DataFrame(index=cnt.columns.astype(str)))
    a.obs["ground_truth"] = info.loc[keep, "z"].astype(str).to_numpy()
    a.obsm["spatial"] = info.loc[keep, ["x", "y"]].to_numpy(np.float64)
    return a
