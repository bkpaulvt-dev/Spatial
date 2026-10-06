"""Graph construction utilities.

* ``spatial_knn``          - symmetric spatial KNN graph (what HiSTaR uses).
* ``expression_weights``   - HiCAST: re-weights every spatial edge by the
  expression affinity of its two endpoints, so edges that cross a domain
  boundary (or a tear / gap in the tissue) are down-weighted instead of
  smoothing two different domains together.
* ``mnn_edges``            - HiCAST: cross-slice mutual-nearest-neighbour
  edges in expression space, used to connect slices for batch integration.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import torch
from sklearn.neighbors import NearestNeighbors


def spatial_knn(coords: np.ndarray, k: int = 6) -> sp.csr_matrix:
    """Binary symmetric KNN adjacency without self loops."""
    n = coords.shape[0]
    nn = NearestNeighbors(n_neighbors=k + 1).fit(coords)
    _, idx = nn.kneighbors(coords)
    rows = np.repeat(np.arange(n), k)
    cols = idx[:, 1:].reshape(-1)
    A = sp.csr_matrix((np.ones_like(rows, dtype=np.float32), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(np.float32)
    A.setdiag(0)
    A.eliminate_zeros()
    return A.tocsr()


def expression_weights(A: sp.csr_matrix, H: np.ndarray, tau: float | None = None,
                       floor: float = 0.05) -> sp.csr_matrix:
    """Weight each edge (i, j) of ``A`` by exp(-(1 - cos(h_i, h_j)) / tau).

    ``tau`` defaults to the median edge distance so the kernel is scale free.
    Weights are clipped below at ``floor`` so the graph never disconnects.
    """
    A = A.tocoo()
    Hn = H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-8)
    d = 1.0 - np.sum(Hn[A.row] * Hn[A.col], axis=1)
    if tau is None:
        tau = float(np.median(d)) + 1e-8
    w = np.exp(-d / tau)
    w = np.clip(w, floor, 1.0).astype(np.float32)
    return sp.csr_matrix((w, (A.row, A.col)), shape=A.shape)


def mnn_edges(H: np.ndarray, batch: np.ndarray, k: int = 3) -> sp.csr_matrix:
    """Mutual nearest neighbours between every pair of batches (cosine space)."""
    n = H.shape[0]
    Hn = H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-8)
    rows, cols = [], []
    ids = np.unique(batch)
    for a_i, a in enumerate(ids):
        for b in ids[a_i + 1:]:
            ia, ib = np.where(batch == a)[0], np.where(batch == b)[0]
            nab = NearestNeighbors(n_neighbors=k).fit(Hn[ib]).kneighbors(Hn[ia])[1]
            nba = NearestNeighbors(n_neighbors=k).fit(Hn[ia]).kneighbors(Hn[ib])[1]
            ab = {(ia[i], ib[j]) for i in range(len(ia)) for j in nab[i]}
            ba = {(ia[j], ib[i]) for i in range(len(ib)) for j in nba[i]}
            for (i, j) in ab & ba:
                rows += [i, j]
                cols += [j, i]
    vals = np.ones(len(rows), dtype=np.float32)
    return sp.csr_matrix((vals, (rows, cols)), shape=(n, n))


def normalize_adj(A: sp.spmatrix, self_loops: bool = True) -> sp.csr_matrix:
    """Symmetric normalisation D^-1/2 (A + I) D^-1/2."""
    A = A.tocsr().astype(np.float32)
    if self_loops:
        A = A + sp.eye(A.shape[0], dtype=np.float32)
    deg = np.asarray(A.sum(1)).ravel()
    dinv = sp.diags(np.power(np.maximum(deg, 1e-12), -0.5))
    return (dinv @ A @ dinv).tocsr()


def to_torch_sparse(A: sp.spmatrix, device="cpu", dtype=torch.float32) -> torch.Tensor:
    A = A.tocoo()
    idx = torch.from_numpy(np.vstack([A.row, A.col]).astype(np.int64))
    val = torch.from_numpy(A.data.astype(np.float32))
    return torch.sparse_coo_tensor(idx, val, A.shape, dtype=dtype, device=device).coalesce()
