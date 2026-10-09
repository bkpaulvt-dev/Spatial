"""Per-section quality control and dataset-difficulty indices (plan section 1).

Every threshold used for flags is fixed here, before any method is run, and is identical for all
methods (rule 15.8). QC never edits the data: it reports, and flags sections for exclusion rules
that are decided in the protocol, not per method.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.spatial import ConvexHull, cKDTree
from sklearn.decomposition import PCA
from sklearn import metrics as skm

from . import metrics as M

FLAG_RULES = {
    "few_spots": "n_obs < 500",
    "low_annotation": "annotated_fraction < 0.5",
    "tiny_domain": "smallest_domain_fraction < 0.01",
    "duplicate_coordinates": "duplicate_coordinate_fraction > 0.01",
    "few_genes": "n_vars < 100",
    "single_domain": "n_domains < 2",
}


def _log_pca(X, n_pcs=30, n_hvg=2000, seed=0):
    """Uniform expression embedding for QC: library-size normalise, log1p, (top-variance genes if > n_hvg), scale, PCA."""
    X = sp.csr_matrix(X).astype(np.float64)
    lib = np.asarray(X.sum(1)).ravel()
    lib[lib == 0] = 1
    X = sp.diags(1e4 / lib) @ X
    X.data = np.log1p(X.data)
    X = X.toarray()
    if X.shape[1] > n_hvg:
        X = X[:, np.argsort(-X.var(0))[:n_hvg]]
    sd = X.std(0)
    X = (X - X.mean(0)) / np.where(sd > 0, sd, 1)
    X = np.clip(X, -10, 10)
    return PCA(n_components=min(n_pcs, X.shape[1] - 1, X.shape[0] - 1), random_state=seed).fit_transform(X)


def section_qc(adata, name: str = "", k_graph: int = 6, k_expr: int = 15, seed: int = 0) -> dict:
    """QC record for one section (raw counts in .X, .obsm['spatial'], .obs['ground_truth'])."""
    X = sp.csr_matrix(adata.X)
    n, g = X.shape
    coords = np.asarray(adata.obsm["spatial"], float)
    truth = adata.obs["ground_truth"].to_numpy(dtype=object)
    ok = M.valid_mask(truth)
    umi = np.asarray(X.sum(1)).ravel()
    det = np.asarray((X > 0).sum(1)).ravel()
    sp_ = M.spacing(coords)
    try:
        hull_area = ConvexHull(coords / sp_).volume
    except Exception:
        hull_area = float("nan")
    dup = 1 - len({tuple(r) for r in np.round(coords, 6)}) / n
    rec = {"section": name, "n_obs": int(n), "n_vars": int(g), "median_umi": float(np.median(umi)),
           "median_genes_detected": float(np.median(det)), "sparsity": float(1 - X.nnz / (n * g)),
           "spacing_native_units": sp_, "hull_area_spacing2": float(hull_area),
           "spots_per_spacing2": float(n / hull_area) if hull_area == hull_area and hull_area > 0 else float("nan"),
           "duplicate_coordinate_fraction": float(dup), "annotated_fraction": float(ok.mean())}
    t = truth[ok]
    dom, cnt = np.unique(t.astype(str), return_counts=True)
    p = cnt / cnt.sum()
    rec.update(n_domains=int(len(dom)), smallest_domain_fraction=float(p.min()), largest_domain_fraction=float(p.max()),
               domain_size_entropy_norm=float(-(p * np.log(p)).sum() / np.log(len(p))) if len(p) > 1 else 0.0,
               domain_imbalance_ratio=float(p.max() / p.min()), chance_purity=float((p ** 2).sum()))
    # label coherence in space (truth treated as a prediction): high fragmentation => noisy or very fine labels
    sq = M.spatial_quality(truth, coords, truth, k=k_graph)
    rec.update(truth_edge_homophily=sq["edge_homophily"], truth_morans_I=sq["morans_I"],
               truth_mean_components=sq["mean_components_per_cluster"],
               truth_main_component_fraction=sq["main_component_fraction"], truth_boundary_fraction=sq["boundary_fraction"])
    # difficulty: how separable are the domains from expression alone, and how much does space add?
    pcs = _log_pca(X[ok], seed=seed)
    idx = cKDTree(pcs).query(pcs, k=k_expr + 1)[1][:, 1:]
    tc = pd.factorize(pd.Series(t))[0]
    expr_purity = float((tc[idx] == tc[:, None]).mean())
    sil = float(skm.silhouette_score(pcs[:3000] if len(pcs) > 3000 else pcs, tc[:3000] if len(pcs) > 3000 else tc)) if len(dom) > 1 else float("nan")
    rec.update(expression_knn_purity=expr_purity, expression_silhouette=sil,
               spatial_gain=float(sq["edge_homophily"] - expr_purity),
               expression_purity_above_chance=float(expr_purity - rec["chance_purity"]))
    rec["flags"] = ";".join(f for f, rule in FLAG_RULES.items() if eval(rule, {}, rec))
    return rec
