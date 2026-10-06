"""Clustering and evaluation helpers shared by all methods."""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, normalized_mutual_info_score,
                             fowlkes_mallows_score, silhouette_score)
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import NearestNeighbors


def gmm_eee(Z: np.ndarray, n_clusters: int, seed: int = 2023, n_pcs: int | None = None) -> np.ndarray:
    """Gaussian mixture with one shared full covariance.

    This is mclust's ``EEE`` model (equal volume, shape and orientation), which
    HiSTaR, SEDR and STAGATE call through rpy2; scikit-learn's ``tied``
    covariance is the same model, so no R installation is needed.
    """
    Z = np.asarray(Z, dtype=np.float64)
    if n_pcs is not None and Z.shape[1] > n_pcs:
        Z = PCA(n_components=n_pcs, random_state=seed).fit_transform(Z)
    gm = GaussianMixture(n_components=n_clusters, covariance_type="tied",
                         n_init=3, reg_covar=1e-5, random_state=seed)
    return gm.fit_predict(Z)


def spatial_refine(labels: np.ndarray, coords: np.ndarray, k: int = 6) -> np.ndarray:
    """Majority vote over each spot and its k spatial neighbours (post-processing)."""
    _, idx = NearestNeighbors(n_neighbors=k + 1).fit(coords).kneighbors(coords)
    out = labels.copy()
    for i in range(len(labels)):
        vals, cnt = np.unique(labels[idx[i]], return_counts=True)
        if cnt.max() > (k + 1) // 2:
            out[i] = vals[cnt.argmax()]
    return out


def evaluate(pred: np.ndarray, truth: np.ndarray | None, Z: np.ndarray | None = None) -> dict:
    res = {}
    if truth is not None:
        keep = np.array([isinstance(t, str) for t in truth])
        p, t = pred[keep], truth[keep]
        res.update(ARI=adjusted_rand_score(t, p), NMI=normalized_mutual_info_score(t, p),
                   FMS=fowlkes_mallows_score(t, p))
    if Z is not None and len(np.unique(pred)) > 1:
        res["SC"] = float(silhouette_score(Z, pred, sample_size=min(5000, len(pred)), random_state=0))
    return res


def ilisi(Z: np.ndarray, batch: np.ndarray, k: int = 30) -> np.ndarray:
    """Per-spot inverse Simpson index of batch labels among k nearest neighbours.

    Simplified (unweighted kNN) version of the integration LISI. Ranges from
    1 (no mixing) to the number of batches (perfect mixing).
    """
    _, idx = NearestNeighbors(n_neighbors=k).fit(Z).kneighbors(Z)
    nb = batch[idx]
    out = np.empty(len(Z))
    for i in range(len(Z)):
        _, c = np.unique(nb[i], return_counts=True)
        p = c / c.sum()
        out[i] = 1.0 / np.sum(p ** 2)
    return out
