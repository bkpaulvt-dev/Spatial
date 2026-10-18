"""Loading and preprocessing of single-cell CRISPR screens (scPerturb .h5ad files)."""
from dataclasses import dataclass, field
import numpy as np
import scipy.sparse as sp


@dataclass
class PerturbData:
    X: sp.csr_matrix            # raw counts, cells x genes
    genes: np.ndarray           # gene names
    conds: np.ndarray           # condition label per cell, e.g. "control", "KLF1", "CEBPE+RUNX1T1"
    targets: list               # sorted list of perturbation units (genes or guides)
    P: np.ndarray               # cells x max_k int index into targets, -1 = padding
    batch: np.ndarray           # integer batch per cell
    target_of: dict = field(default_factory=dict)   # unit -> targeted gene (for guides)

    @property
    def lib(self):
        return np.asarray(self.X.sum(1)).ravel()

    def log_norm(self, idx=None):
        X = self.X if idx is None else self.X[idx]
        L = np.asarray(X.sum(1)).ravel()
        Y = sp.diags(1e4 / L) @ X
        Y.data = np.log1p(Y.data)
        return Y


def _select(adata, cells, n_hvg, must_have, seed):
    import scanpy as sc
    a = adata[cells].to_memory()
    a.X = sp.csr_matrix(a.X)
    sc.pp.filter_genes(a, min_cells=max(20, int(0.005 * a.n_obs)))
    sc.pp.highly_variable_genes(a, n_top_genes=n_hvg, flavor="seurat_v3", batch_key=None)
    keep = a.var.highly_variable.values | np.isin(a.var_names, list(must_have))
    return a[:, keep].copy()


def load_norman(path, n_hvg=2000, max_cells_per_cond=400, n_ctrl=4000, seed=0):
    """Norman et al. 2019 CRISPRa screen: 105 single and 131 double perturbations in K562."""
    import anndata as ad
    rng = np.random.default_rng(seed)
    adata = ad.read_h5ad(path, backed="r")
    pert = adata.obs["perturbation"].astype(str).values
    cells = []
    for c in np.unique(pert):
        idx = np.where(pert == c)[0]
        m = n_ctrl if c == "control" else max_cells_per_cond
        if len(idx) > m:
            idx = rng.choice(idx, m, replace=False)
        cells.append(np.sort(idx))
    cells = np.sort(np.concatenate(cells))
    units = sorted({g for c in np.unique(pert) if c != "control" for g in c.split("_")})
    a = _select(adata, cells, n_hvg, units, seed)
    conds = np.array(["+".join(sorted(c.split("_"))) if c != "control" else "control"
                      for c in a.obs["perturbation"].astype(str)])
    ix = {u: i for i, u in enumerate(units)}
    P = -np.ones((a.n_obs, 2), dtype=np.int64)
    for n, c in enumerate(conds):
        if c != "control":
            for j, g in enumerate(c.split("+")):
                P[n, j] = ix[g]
    batch = a.obs["gemgroup"].astype(int).values - 1
    return PerturbData(sp.csr_matrix(a.X, dtype=np.float32), np.asarray(a.var_names), conds,
                       units, P, batch, {u: u for u in units})


def load_dixit(path, n_hvg=2000, max_guides=3, seed=0):
    """Dixit et al. 2016 K562 TF knockout screen (high MOI). Perturbation units are guides."""
    import anndata as ad
    adata = ad.read_h5ad(path, backed="r")
    pert = adata.obs["perturbation"].astype(str).values
    guides = [p.split("_") if p != "control" else [] for p in pert]
    # intergenic guides are controls; units are the targeting guides
    def is_ctrl(g):
        return "INTERGENIC" in g or g == "control"
    tg = [[g for g in gs if not is_ctrl(g)] for gs in guides]
    ok = np.array([len(t) <= max_guides for t in tg])
    cells = np.where(ok)[0]
    units = sorted({g for t in tg for g in t})
    target_of = {u: u.replace("p-sg", "").split("-")[0] for u in units}
    a = _select(adata, cells, n_hvg, set(target_of.values()), seed)
    ix = {u: i for i, u in enumerate(units)}
    tg = [tg[i] for i in cells]
    P = -np.ones((a.n_obs, max_guides), dtype=np.int64)
    for n, t in enumerate(tg):
        for j, g in enumerate(t):
            P[n, j] = ix[g]
    conds = np.array(["+".join(sorted(t)) if t else "control" for t in tg])
    batch = np.zeros(a.n_obs, dtype=np.int64)
    return PerturbData(sp.csr_matrix(a.X, dtype=np.float32), np.asarray(a.var_names), conds,
                       units, P, batch, target_of)
