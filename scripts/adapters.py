"""One interface for every benchmarked method.

    ADAPTERS[name](adata, k, seed, ds) -> dict(labels=<official clustering of the method>,
                                               emb=<embedding or None>, extra={...})

``adata``: raw counts in .X, coordinates in .obsm['spatial'], labels in .obs['ground_truth'] (the
adapters never read the labels, except Spatial-MGCN's documented label-selected epoch which is
recorded in ``extra`` and never used for the returned labels).
The runner additionally clusters every non-None embedding with the matched 20-start GMM.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]


def _pcs(a, seed):
    from spatialbench.preprocess import uniform_pcs
    return uniform_pcs(a, seed)[0]


def _train_free(diffusion):
    def f(a, k, seed, ds):
        from anisost import AnisoST, robust_gmm
        X, C = _pcs(a, seed), np.asarray(a.obsm["spatial"], float)
        m = AnisoST(diffusion=diffusion, seed=seed)
        Z = m.embed(X, C)
        return {"labels": robust_gmm(Z, k, seed=seed), "emb": Z, "extra": {}}
    return f


def histar(a, k, seed, ds):
    import torch
    from hicast.cluster import gmm_eee
    from hicast.histar import HiSTaR
    X, C = _pcs(a, seed), np.asarray(a.obsm["spatial"], float)
    torch.manual_seed(seed); np.random.seed(seed)
    Z = HiSTaR(X, C, k, seed=seed).fit().embed()
    return {"labels": gmm_eee(Z, k), "emb": Z, "extra": {}}


def banksy(lam):
    def f(a, k, seed, ds):
        import scanpy as sc
        from hicast.cluster import gmm_eee
        from benchmark_extra import banksy_embed
        b = a.copy()
        if b.n_vars > 2000:
            sc.pp.filter_genes(b, min_cells=50); sc.pp.filter_genes(b, min_counts=10)
            sc.pp.highly_variable_genes(b, flavor="seurat_v3", n_top_genes=2000)
            sc.pp.normalize_total(b, target_sum=1e4); sc.pp.log1p(b)
            b = b[:, b.var["highly_variable"]].copy()
        else:
            sc.pp.normalize_total(b, target_sum=1e4); sc.pp.log1p(b)
        G = b.X.toarray() if hasattr(b.X, "toarray") else np.asarray(b.X)
        Z = banksy_embed(G, np.asarray(a.obsm["spatial"], float), list(b.var_names), lam, seed)
        return {"labels": gmm_eee(Z, k, seed=seed), "emb": Z, "extra": {}}
    return f


def spagcn(a, k, seed, ds):
    import random, scanpy as sc, torch, SpaGCN as spg
    b = a.copy()
    spg.prefilter_genes(b, min_cells=3); spg.prefilter_specialgenes(b)
    sc.pp.normalize_total(b); sc.pp.log1p(b)
    b.X = np.asarray(b.X.toarray() if hasattr(b.X, "toarray") else b.X, dtype=np.float32)
    C = np.asarray(a.obsm["spatial"], float)
    adj = spg.calculate_adj_matrix(x=C[:, 1] if ds == "dlpfc" else C[:, 0], y=C[:, 0] if ds == "dlpfc" else C[:, 1], histology=False)
    l = spg.search_l(0.5, adj, start=0.01, end=1000, tol=0.01, max_run=100)
    res = spg.search_res(b, adj, l, k, start=0.7, step=0.1, tol=5e-3, lr=0.05, max_epochs=20, r_seed=seed, t_seed=seed, n_seed=seed)
    random.seed(seed); torch.manual_seed(seed); np.random.seed(seed)
    clf = spg.SpaGCN(); clf.set_l(l)
    clf.train(b, adj, init_spa=True, init="louvain", res=res, tol=5e-3, lr=0.05, max_epochs=200)
    pred, _ = clf.predict()
    return {"labels": pred, "emb": None, "extra": {"resolution": float(res)}}


def graphst(a, k, seed, ds):
    import torch, scanpy as sc
    from GraphST import GraphST
    from GraphST.utils import clustering
    b = a.copy()
    if b.n_vars <= 3000:                       # targeted panel: keep every gene, GraphST's remaining preprocessing
        b.var["highly_variable"] = True
        sc.pp.normalize_total(b, target_sum=1e4); sc.pp.log1p(b); sc.pp.scale(b, zero_center=False, max_value=10)
    m = GraphST.GraphST(b, device=torch.device("cpu"), random_seed=41 + seed)
    b = m.train()
    clustering(b, k, radius=50, method="mclust", refinement=False)
    Z = np.asarray(b.obsm["emb_pca"])
    return {"labels": b.obs["domain"].astype(int).to_numpy(), "emb": Z, "extra": {}}


def _from_new(name):
    def f(a, k, seed, ds):
        import new_methods
        lab, Z = new_methods.METHODS[name](a, k, seed, ds)
        extra = dict(new_methods.LAST_ORACLE) if name == "spatial_mgcn" else {}
        return {"labels": np.asarray(lab), "emb": None if Z is None else np.asarray(Z), "extra": extra}
    return f


ADAPTERS = {"linear_diffusion": _train_free("linear"), "anisost": _train_free("anisotropic"), "pca_gmm": _train_free("none"),
            "histar": histar, "graphst": graphst, "banksy_l0.2": banksy(0.2), "banksy_l0.8": banksy(0.8), "spagcn": spagcn}
for _m in ("stagate", "sedr", "spaceflow", "nichepca", "ccst", "spatial_mgcn", "deepst", "bass", "bayesspace"):
    ADAPTERS[_m] = _from_new(_m)

# methods that must run alone (memory) and that are Visium-only
SERIAL = {"deepst"}
VISIUM_ONLY = {"bayesspace"}
