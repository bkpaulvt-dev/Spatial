"""Data loading and preprocessing for spatial transcriptomics slices.

The preprocessing follows the pipeline described in the HiSTaR paper
(log-normalisation -> highly variable genes -> PCA), using the SEDR-style
settings that the HiSTaR code base is derived from. Every method in the
benchmark consumes exactly the same matrix, so differences in results come
from the models, not from preprocessing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


DLPFC_SLICES = [
    "151507", "151508", "151509", "151510",   # donor Br5292
    "151669", "151670", "151671", "151672",   # donor Br5595
    "151673", "151674", "151675", "151676",   # donor Br8100
]

DLPFC_N_CLUSTERS = {s: (5 if s in {"151669", "151670", "151671", "151672"} else 7)
                    for s in DLPFC_SLICES}


@dataclass
class SpatialData:
    """Minimal container passed to every model."""
    X: np.ndarray                      # (N, d) model input (PCA of HVGs)
    coords: np.ndarray                 # (N, 2) spatial coordinates
    labels: np.ndarray | None = None   # (N,) ground-truth domain labels (str), may contain NaN
    batch: np.ndarray | None = None    # (N,) integer batch / slice id
    obs_names: np.ndarray | None = None
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return self.X.shape[0]


def load_dlpfc_adata(root: str, slice_id: str):
    """Read one DLPFC slice (10x h5 + spatialLIBD metadata) into an AnnData."""
    import scanpy as sc

    path = os.path.join(root, slice_id)
    adata = sc.read_10x_h5(os.path.join(path, "filtered_feature_bc_matrix.h5"))
    adata.var_names_make_unique()
    meta = pd.read_csv(os.path.join(path, "metadata.tsv"), sep="\t", index_col=0)
    meta = meta.loc[adata.obs_names]
    adata.obs["ground_truth"] = meta["layer_guess_reordered"].astype(object).values
    adata.obs["array_row"] = meta["row"].values
    adata.obs["array_col"] = meta["col"].values
    adata.obsm["spatial"] = meta[["imagecol", "imagerow"]].to_numpy(dtype=np.float64)
    adata.obs["slice"] = slice_id
    return adata


def preprocess(adata, n_top_genes: int = 2000, n_pcs: int = 200, seed: int = 0):
    """Count QC -> HVG (seurat_v3 on counts) -> normalise -> log1p -> scale -> PCA."""
    import scanpy as sc
    from sklearn.decomposition import PCA

    adata = adata.copy()
    adata.layers["counts"] = adata.X.copy()
    sc.pp.filter_genes(adata, min_cells=50)
    sc.pp.filter_genes(adata, min_counts=10)
    sc.pp.highly_variable_genes(adata, flavor="seurat_v3", layer="counts",
                                n_top_genes=n_top_genes)
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    adata = adata[:, adata.var["highly_variable"]].copy()
    sc.pp.scale(adata, max_value=10)
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    pcs = PCA(n_components=n_pcs, random_state=seed).fit_transform(X)
    return adata, pcs.astype(np.float32)


def load_dlpfc(root: str, slice_id: str, n_pcs: int = 200, seed: int = 0) -> SpatialData:
    adata = load_dlpfc_adata(root, slice_id)
    adata, pcs = preprocess(adata, n_pcs=n_pcs, seed=seed)
    return SpatialData(
        X=pcs,
        coords=adata.obsm["spatial"].astype(np.float32),
        labels=adata.obs["ground_truth"].to_numpy(),
        batch=np.zeros(adata.n_obs, dtype=np.int64),
        obs_names=adata.obs_names.to_numpy(),
        meta={"slice": slice_id, "n_clusters": DLPFC_N_CLUSTERS[slice_id]},
    )


def load_dlpfc_multi(root: str, slice_ids: list[str], n_pcs: int = 200,
                     seed: int = 0, offset: float | None = None) -> SpatialData:
    """Load several slices into one SpatialData for joint (batch-corrected) analysis.

    Genes are intersected, preprocessing is done jointly, and each slice is
    shifted along x so that spatial KNN graphs never connect different slices.
    """
    import anndata as ad

    adatas = [load_dlpfc_adata(root, s) for s in slice_ids]
    joint = ad.concat(adatas, join="inner", label="batch_key", keys=slice_ids,
                      index_unique="-")
    joint, pcs = preprocess(joint, n_pcs=n_pcs, seed=seed)
    coords = joint.obsm["spatial"].astype(np.float32).copy()
    batch = pd.Categorical(joint.obs["batch_key"], categories=slice_ids).codes.astype(np.int64)
    span = np.ptp(coords[:, 0]) if offset is None else offset
    coords[:, 0] += batch * (span * 1.5)
    return SpatialData(
        X=pcs, coords=coords,
        labels=joint.obs["ground_truth"].to_numpy(),
        batch=batch, obs_names=joint.obs_names.to_numpy(),
        meta={"slices": slice_ids, "n_clusters": DLPFC_N_CLUSTERS[slice_ids[0]]},
    )
