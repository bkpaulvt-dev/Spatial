"""AnisoST: Anisotropic (edge-preserving) diffusion on the Spatial Transcriptomics graph.

Spatial-domain methods smooth each spot's expression with its neighbours. Linear
smoothing (GCN layers, neighbour averaging) blurs domain boundaries. AnisoST
instead runs a Perona-Malik-style diffusion on the spatial KNN graph: at every
step each edge is re-weighted by the similarity of the *current* (already
smoothed) features of its endpoints, so smoothing is strong inside a domain and
is stopped at boundaries, where neighbouring spots differ.

    H^(0) = X                                      (top PCs of log-normalised HVGs)
    w_ij^(t) = exp(-||h_i^(t) - h_j^(t)||^2 / kappa^(t)),   (i, j) in E_knn
    kappa^(t) = q-quantile of the squared edge differences   (scale free)
    H^(t+1) = (1 - alpha) H^(t) + alpha * D^-1 W^(t) H^(t)

Domains are then found with a tied-covariance Gaussian mixture (mclust EEE). The
mixture is fitted from many random starts and the highest-likelihood fit is kept,
which is label free and removes most of the run-to-run variance of the usual
single-start mclust step.

No training, no GPU, deterministic for a given seed, and a few seconds per slice.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import NearestNeighbors


def spatial_knn(coords: np.ndarray, k: int = 6) -> sp.csr_matrix:
    """Binary symmetric spatial KNN adjacency without self loops."""
    n = coords.shape[0]
    idx = NearestNeighbors(n_neighbors=k + 1).fit(coords).kneighbors(coords)[1]
    A = sp.csr_matrix((np.ones(n * k, np.float32), (np.repeat(np.arange(n), k), idx[:, 1:].ravel())),
                      shape=(n, n))
    A = ((A + A.T) > 0).astype(np.float32)
    A.setdiag(0)
    A.eliminate_zeros()
    return A.tocsr()


def _row_normalize(W: sp.spmatrix) -> sp.csr_matrix:
    d = np.asarray(W.sum(1)).ravel()
    return (sp.diags(1.0 / np.maximum(d, 1e-12)) @ W).tocsr()


def linear_diffusion(X: np.ndarray, A: sp.spmatrix, steps: int = 10, alpha: float = 0.5) -> np.ndarray:
    """Isotropic (lazy random-walk) diffusion: the ablation without edge preservation."""
    P = _row_normalize(A)
    H = X.astype(np.float64).copy()
    for _ in range(steps):
        H = (1 - alpha) * H + alpha * (P @ H)
    return H


def anisotropic_diffusion(X: np.ndarray, A: sp.spmatrix, steps: int = 10, alpha: float = 0.5,
                          q: float = 0.5, return_weights: bool = False):
    """Edge-preserving diffusion of the rows of X over the edges of A (see module docstring)."""
    A = A.tocoo()
    r, c, n = A.row, A.col, A.shape[0]
    H = X.astype(np.float64).copy()
    w = np.ones(len(r))
    for _ in range(steps):
        d = np.sum((H[r] - H[c]) ** 2, axis=1)
        w = np.exp(-d / (np.quantile(d, q) + 1e-12))
        H = (1 - alpha) * H + alpha * (_row_normalize(sp.csr_matrix((w, (r, c)), shape=(n, n))) @ H)
    if return_weights:
        return H, sp.csr_matrix((w, (r, c)), shape=(n, n))
    return H


def robust_gmm(Z: np.ndarray, n_clusters: int, n_init: int = 20, seed: int = 0) -> np.ndarray:
    """mclust-EEE-equivalent GMM; best log-likelihood over ``n_init`` random starts."""
    gm = GaussianMixture(n_components=n_clusters, covariance_type="tied", n_init=n_init,
                         reg_covar=1e-5, random_state=seed)
    return gm.fit_predict(np.asarray(Z, dtype=np.float64))


class AnisoST:
    """Training-free spatial domain identification.

    Parameters were fixed on donor 1 of the DLPFC data only (see docs/AnisoST.md).
    """

    def __init__(self, n_pcs: int = 30, k: int = 6, steps: int = 10, alpha: float = 0.5,
                 q: float = 0.5, n_init: int = 20, diffusion: str = "anisotropic", seed: int = 0):
        self.n_pcs, self.k, self.steps, self.alpha, self.q = n_pcs, k, steps, alpha, q
        self.n_init, self.diffusion, self.seed = n_init, diffusion, seed

    def embed(self, X: np.ndarray, coords: np.ndarray) -> np.ndarray:
        X = X[:, : self.n_pcs]
        A = spatial_knn(coords, self.k)
        if self.diffusion == "anisotropic":
            H, self.edge_weights_ = anisotropic_diffusion(X, A, self.steps, self.alpha, self.q,
                                                          return_weights=True)
        elif self.diffusion == "linear":
            H = linear_diffusion(X, A, self.steps, self.alpha)
        elif self.diffusion == "none":
            H = X.astype(np.float64)
        else:
            raise ValueError(self.diffusion)
        self.A_, self.embedding_ = A, H
        return H

    def fit_predict(self, X: np.ndarray, coords: np.ndarray, n_clusters: int) -> np.ndarray:
        H = self.embed(X, coords)
        self.labels_ = robust_gmm(H, n_clusters, self.n_init, self.seed)
        return self.labels_
