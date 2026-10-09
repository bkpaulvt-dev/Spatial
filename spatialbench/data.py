"""Dataset registry access and uniform section loading (raw counts + coordinates + annotation)."""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


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
    csv = os.path.join(root, "data", "ext", "csv")
    cnt = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_counts.csv"), index_col=0)
    info = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_info.csv"), index_col=0).loc[cnt.index]
    keep = cnt.sum(1).to_numpy() > 0
    a = anndata.AnnData(cnt[keep].to_numpy(np.float32), obs=pd.DataFrame(index=cnt.index[keep].astype(str)),
                        var=pd.DataFrame(index=cnt.columns.astype(str)))
    a.obs["ground_truth"] = info.loc[keep, "z"].astype(str).to_numpy()
    a.obsm["spatial"] = info.loc[keep, ["x", "y"]].to_numpy(np.float64)
    return a
