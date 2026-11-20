"""R5 equal-tuning arm (Arm B, docs/PROTOCOL.md section 5; plan 15.2), cheap methods only. Pre-registered in docs/PREREGISTERED_TUNING.md.

Every method gets the same budget: 10 configurations (configuration 0 = its Arm A setting), each run once (seed 0) on the six
development sections (DLPFC donor Br5292 x 4, STARmap 1, MERFISH 1; configs/datasets.yaml split: dev). The configuration with the
highest selection score (mean over the 3 dev datasets of the per-dataset mean ARI) is frozen in results/r5_selected.json and run as
r5__<method>__tuned on the 24 original sections x 3 seeds. Method names: r5__<method>__c<j> (tuning phase) and r5__<method>__tuned.
Existing adapters and settings are not changed; this file only adds new method names.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SELECTED = os.path.join(ROOT, "results", "r5_selected.json")

# Configuration 0 of every grid is the Arm A (as-benchmarked) setting. Grids fixed before any R5 run.
GRIDS = {
    "linear_diffusion": [dict(knn=6, alpha=0.5, steps=10, pcs=30), dict(knn=6, alpha=0.5, steps=5, pcs=30), dict(knn=6, alpha=0.5, steps=20, pcs=30),
                         dict(knn=6, alpha=0.3, steps=10, pcs=30), dict(knn=6, alpha=0.7, steps=10, pcs=30), dict(knn=4, alpha=0.5, steps=10, pcs=30),
                         dict(knn=10, alpha=0.5, steps=10, pcs=30), dict(knn=15, alpha=0.5, steps=10, pcs=30), dict(knn=10, alpha=0.5, steps=20, pcs=30),
                         dict(knn=6, alpha=0.5, steps=10, pcs=15)],
    "anisost": [dict(knn=6, alpha=0.5, steps=10, q=0.5, pcs=30), dict(knn=6, alpha=0.5, steps=5, q=0.5, pcs=30), dict(knn=6, alpha=0.5, steps=20, q=0.5, pcs=30),
                dict(knn=6, alpha=0.3, steps=10, q=0.5, pcs=30), dict(knn=6, alpha=0.7, steps=10, q=0.5, pcs=30), dict(knn=4, alpha=0.5, steps=10, q=0.5, pcs=30),
                dict(knn=10, alpha=0.5, steps=10, q=0.5, pcs=30), dict(knn=6, alpha=0.5, steps=10, q=0.25, pcs=30), dict(knn=6, alpha=0.5, steps=10, q=0.75, pcs=30),
                dict(knn=10, alpha=0.5, steps=20, q=0.5, pcs=30)],
    "pca_gmm": [dict(pcs=p) for p in (30, 5, 10, 15, 20, 25, 35, 40, 45, 50)],
    "banksy": [dict(lam=0.8, k_geom=18, pcs=20), dict(lam=0.2, k_geom=18, pcs=20), dict(lam=0.5, k_geom=18, pcs=20), dict(lam=0.8, k_geom=10, pcs=20),
               dict(lam=0.8, k_geom=30, pcs=20), dict(lam=0.5, k_geom=10, pcs=20), dict(lam=0.5, k_geom=30, pcs=20), dict(lam=0.8, k_geom=18, pcs=30),
               dict(lam=0.5, k_geom=18, pcs=30), dict(lam=0.2, k_geom=18, pcs=30)],
    "nichepca": [dict(knn=6, n_comps=30), dict(knn=4, n_comps=30), dict(knn=10, n_comps=30), dict(knn=15, n_comps=30), dict(knn=20, n_comps=30),
                 dict(knn=6, n_comps=15), dict(knn=6, n_comps=50), dict(knn=10, n_comps=15), dict(knn=10, n_comps=50), dict(knn=15, n_comps=50)],
}
ARM_A = {"linear_diffusion": "linear_diffusion", "anisost": "anisost", "pca_gmm": "pca_gmm", "banksy": "banksy_l0.8", "nichepca": "nichepca"}


def _diffusion(kind, c, a, k, seed):
    from adapters import _pcs
    from anisost import AnisoST, robust_gmm
    X, C = _pcs(a, seed), np.asarray(a.obsm["spatial"], float)
    m = AnisoST(n_pcs=c["pcs"], k=c.get("knn", 6), steps=c.get("steps", 10), alpha=c.get("alpha", 0.5), q=c.get("q", 0.5), diffusion=kind, seed=seed)
    Z = m.embed(X, C)
    return {"labels": robust_gmm(Z, k, seed=seed), "emb": Z, "extra": {}}


def _banksy(c, a, k, seed):
    """As adapters.banksy, with lambda, number of neighbours and PCA dimensions taken from the configuration."""
    import contextlib, io, anndata, pandas as pd, scanpy as sc
    from sklearn.decomposition import PCA
    from banksy.initialize_banksy import initialize_banksy
    from banksy.embed_banksy import generate_banksy_matrix
    from hicast.cluster import gmm_eee
    b = a.copy()
    if b.n_vars > 2000:
        sc.pp.filter_genes(b, min_cells=50); sc.pp.filter_genes(b, min_counts=10)
        sc.pp.highly_variable_genes(b, flavor="seurat_v3", n_top_genes=2000)
        sc.pp.normalize_total(b, target_sum=1e4); sc.pp.log1p(b)
        b = b[:, b.var["highly_variable"]].copy()
    else:
        sc.pp.normalize_total(b, target_sum=1e4); sc.pp.log1p(b)
    G = b.X.toarray() if hasattr(b.X, "toarray") else np.asarray(b.X)
    coords = np.asarray(a.obsm["spatial"], float)
    g = anndata.AnnData(np.asarray(G, np.float64), var=pd.DataFrame(index=[str(x) for x in b.var_names]))
    g.obs["x"], g.obs["y"] = coords[:, 0], coords[:, 1]; g.obsm["coord_xy"] = coords
    with contextlib.redirect_stdout(io.StringIO()):
        bd = initialize_banksy(g, ("x", "y", "coord_xy"), num_neighbours=c["k_geom"], nbr_weight_decay="scaled_gaussian",
                               max_m=1, plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False, plt_theta=False)
        _, bm = generate_banksy_matrix(g, bd, [c["lam"]], max_m=1, verbose=False)
    Z = PCA(c["pcs"], random_state=seed).fit_transform(np.asarray(bm.X))
    return {"labels": gmm_eee(Z, k, seed=seed), "emb": Z, "extra": {}}


def _nichepca(c, a, k, seed):
    """As new_methods.nichepca, with knn and the number of components taken from the configuration."""
    import contextlib, io, nichepca as npc, scanpy as sc
    a = a.copy()
    with contextlib.redirect_stdout(io.StringIO()):
        npc.workflows.nichepca(a, knn=c["knn"], n_comps=c["n_comps"])
        sc.pp.neighbors(a, use_rep="X_npca", random_state=seed)
        npc.clustering.leiden_with_nclusters(a, n_clusters=k, seed=seed)
    return {"labels": a.obs["leiden"].astype(int).to_numpy(), "emb": np.asarray(a.obsm["X_npca"]), "extra": {}}


RUN = {"linear_diffusion": lambda c, a, k, s: _diffusion("linear", c, a, k, s), "anisost": lambda c, a, k, s: _diffusion("anisotropic", c, a, k, s),
       "pca_gmm": lambda c, a, k, s: _diffusion("none", c, a, k, s), "banksy": _banksy, "nichepca": _nichepca}


def config_of(name):
    """r5__<method>__c<j> -> (method, j, config); r5__<method>__tuned -> (method, selected j, config) from results/r5_selected.json."""
    _, method, tag = name.split("__")
    if tag == "tuned":
        j = int(json.load(open(SELECTED))["selected"][method]["config"])
    else:
        j = int(tag[1:])
    return method, j, GRIDS[method][j]


def _adapter(name):
    def f(a, k, seed, ds):
        method, j, c = config_of(name)
        out = RUN[method](c, a, k, seed)
        out["extra"] = dict(out["extra"], r5_config=float(j))
        return out
    return f


ADAPTERS = {f"r5__{m}__c{j}": _adapter(f"r5__{m}__c{j}") for m, g in GRIDS.items() for j in range(len(g))}
ADAPTERS.update({f"r5__{m}__tuned": _adapter(f"r5__{m}__tuned") for m in GRIDS})


def version(name):
    method, j, c = config_of(name)
    return f"R5 {method} configuration {j}: " + json.dumps(c, sort_keys=True)


DEV = [("dlpfc", "151507"), ("dlpfc", "151508"), ("dlpfc", "151509"), ("dlpfc", "151510"), ("starmap", "20180417_BZ5_control"), ("merfish", "-0.04")]

if __name__ == "__main__":   # tuning-phase job list: 5 methods x 10 configurations x 6 dev sections x seed 0 = 300 jobs
    for ds, sec in DEV:
        for m, g in GRIDS.items():
            for j in range(len(g)):
                print(f"{ds}:{sec}:r5__{m}__c{j}:0")
