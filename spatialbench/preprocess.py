"""Uniform preprocessing shared by every method that takes an expression matrix (rule 15.8).

Whole-transcriptome sections (> 2000 genes): the DLPFC pipeline used throughout this project
(genes in >= 50 spots and >= 10 counts, 2000 Seurat-v3 HVGs, library-size normalisation, log1p, scaling,
200 PCs). Targeted panels (<= 2000 genes): all genes, same normalisation, scaling clipped at 10, <= 50 PCs.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from sklearn.decomposition import PCA


def uniform_pcs(adata, seed: int = 0):
    """Return (PCs as float32, name of the route used)."""
    if adata.n_vars > 2000:
        from hicast.data import preprocess
        _, pcs = preprocess(adata.copy(), n_top_genes=2000, n_pcs=200, seed=seed)
        return pcs.astype(np.float32), "hvg2000_pca200"
    X = sp.csr_matrix(adata.X).astype(np.float64)
    lib = np.asarray(X.sum(1)).ravel()
    lib[lib == 0] = 1
    X = sp.diags(1e4 / lib) @ X
    X.data = np.log1p(X.data)
    X = X.toarray()
    sd = X.std(0)
    X = np.clip((X - X.mean(0)) / np.where(sd > 0, sd, 1), -10, 10)
    return PCA(n_components=min(50, X.shape[1] - 1), random_state=seed).fit_transform(X).astype(np.float32), "allgenes_pca50"
