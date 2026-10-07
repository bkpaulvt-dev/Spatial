"""Extra baselines on the 12 DLPFC slices, same splits/metrics as benchmark_anisost.py.

* ``banksy_l0.2`` / ``banksy_l0.8`` - official pybanksy package (Singhal et al., Nat. Genet. 2024):
  BANKSY matrix (k_geom = 18, max_m = 1, scaled-Gaussian decay) on the same 2000 seurat_v3
  HVGs (log-normalised), PCA(20), then the mclust-EEE-equivalent GMM. Both recommended
  lambdas are run (0.2: cell typing, 0.8: domain segmentation).
* ``spagcn`` / ``spagcn_refined`` - official SpaGCN package (Hu et al., Nat. Methods 2021),
  official tutorial pipeline without histology: p = 0.5, Louvain resolution search to the
  true number of domains (``search_res``), lr = 0.05, 200 epochs, hexagonal refinement.
  (On Python 3.13 the ``louvain`` package needs ``setuptools<81`` for ``pkg_resources``.)
* ``histar_robust`` - HiSTaR embedding (port of the official code, published defaults)
  clustered with the same 20-restart GMM as AnisoST: controls for the clustering step.

Every BANKSY / HiSTaR result is reported with both the standard 3-start GMM
(``hicast.cluster.gmm_eee``, as used for HiSTaR/HiCAST) and the 20-start GMM
(suffix ``+robust``), so the comparison with AnisoST is clustering-matched.

python scripts/benchmark_baselines.py --data data/DLPFC --out results/baselines.jsonl
"""
from __future__ import annotations

import argparse, json, os, sys, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, ".."), HERE]
from benchmark_anisost import DLPFC_SLICES, N_CLUSTERS  # noqa: E402


def load_lognorm(root, s):
    """Raw slice -> same HVGs as hicast.data.preprocess, log-normalised (not scaled)."""
    import scanpy as sc
    from hicast.data import load_dlpfc_adata
    a = load_dlpfc_adata(root, s)
    a.layers["counts"] = a.X.copy()
    sc.pp.filter_genes(a, min_cells=50)
    sc.pp.filter_genes(a, min_counts=10)
    sc.pp.highly_variable_genes(a, flavor="seurat_v3", layer="counts", n_top_genes=2000)
    sc.pp.normalize_total(a, target_sum=1e4)
    sc.pp.log1p(a)
    return a[:, a.var["highly_variable"]].copy()


def scores(y, pred):
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, fowlkes_mallows_score
    keep = np.array([isinstance(v, str) for v in y])
    return {"ARI": adjusted_rand_score(y[keep], pred[keep]),
            "NMI": normalized_mutual_info_score(y[keep], pred[keep]),
            "FMS": fowlkes_mallows_score(y[keep], pred[keep])}


def run_banksy(root, s, seed, lam):
    import contextlib, io
    from sklearn.decomposition import PCA
    from banksy.initialize_banksy import initialize_banksy
    from banksy.embed_banksy import generate_banksy_matrix
    a = load_lognorm(root, s)
    a.obs["x"], a.obs["y"] = a.obsm["spatial"][:, 0], a.obsm["spatial"][:, 1]
    a.obsm["coord_xy"] = a.obsm["spatial"]
    a.X = a.X.toarray() if hasattr(a.X, "toarray") else a.X
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        bd = initialize_banksy(a, ("x", "y", "coord_xy"), num_neighbours=18, nbr_weight_decay="scaled_gaussian",
                               max_m=1, plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False,
                               plt_theta=False)
        _, bm = generate_banksy_matrix(a, bd, [lam], max_m=1, verbose=False)
    Z = PCA(20, random_state=seed).fit_transform(np.asarray(bm.X))
    return a.obs["ground_truth"].to_numpy(), Z, time.time() - t0


def run_spagcn(root, s, seed):
    import random, torch, scanpy as sc, SpaGCN as spg
    from hicast.data import load_dlpfc_adata
    a = load_dlpfc_adata(root, s)
    a.var_names_make_unique()
    spg.prefilter_genes(a, min_cells=3)
    spg.prefilter_specialgenes(a)
    sc.pp.normalize_total(a)                   # = tutorial's normalize_per_cell (median depth)
    sc.pp.log1p(a)
    a.X = np.asarray(a.X.toarray(), dtype=np.float32)
    t0 = time.time()
    xp, yp = a.obsm["spatial"][:, 1], a.obsm["spatial"][:, 0]          # imagerow, imagecol
    adj = spg.calculate_adj_matrix(x=xp, y=yp, histology=False)
    l = spg.search_l(0.5, adj, start=0.01, end=1000, tol=0.01, max_run=100)
    res = spg.search_res(a, adj, l, N_CLUSTERS[s], start=0.7, step=0.1, tol=5e-3, lr=0.05, max_epochs=20,
                         r_seed=seed, t_seed=seed, n_seed=seed)
    random.seed(seed); torch.manual_seed(seed); np.random.seed(seed)
    clf = spg.SpaGCN(); clf.set_l(l)
    clf.train(a, adj, init_spa=True, init="louvain", res=res, tol=5e-3, lr=0.05, max_epochs=200)
    pred, _ = clf.predict()
    adj2 = spg.calculate_adj_matrix(x=a.obs["array_row"].values, y=a.obs["array_col"].values, histology=False)
    ref = np.array(spg.refine(sample_id=a.obs.index.tolist(), pred=pred.tolist(), dis=adj2, shape="hexagon"))
    return a.obs["ground_truth"].to_numpy(), pred, ref, time.time() - t0


def run_one(job):
    warnings.filterwarnings("ignore")
    import contextlib, io, torch
    torch.set_num_threads(1)
    from hicast.cluster import gmm_eee
    from anisost import robust_gmm
    method, s, seed, root, cache = job
    k = N_CLUSTERS[s]
    out = []
    base = {"slice": s, "seed": seed}
    if method.startswith("banksy"):
        y, Z, t = run_banksy(root, s, seed, float(method.split("_l")[1]))
        out.append({**base, "method": method, "time": t, **scores(y, gmm_eee(Z, k, seed=seed))})
        out.append({**base, "method": method + "+robust", "time": t, **scores(y, robust_gmm(Z, k, seed=seed))})
    elif method == "spagcn":
        with contextlib.redirect_stdout(io.StringIO()):
            y, p, r, t = run_spagcn(root, s, seed)
        out.append({**base, "method": "spagcn", "time": t, **scores(y, p)})
        out.append({**base, "method": "spagcn_refined", "time": t, **scores(y, r)})
    elif method == "histar":
        from hicast.histar import HiSTaR
        z = np.load(os.path.join(cache, f"{s}.npz"), allow_pickle=True)
        torch.manual_seed(seed); np.random.seed(seed)
        t0 = time.time()
        Z = HiSTaR(z["X"], z["coords"], k, seed=seed).fit().embed()
        t = time.time() - t0
        out.append({**base, "method": "histar_rerun", "time": t, **scores(z["labels"], gmm_eee(Z, k))})
        out.append({**base, "method": "histar+robust", "time": t, **scores(z["labels"], robust_gmm(Z, k, seed=seed))})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/DLPFC")
    ap.add_argument("--cache", default="results/cache")
    ap.add_argument("--out", default="results/baselines.jsonl")
    ap.add_argument("--methods", nargs="+", default=["banksy_l0.2", "banksy_l0.8", "spagcn", "histar"])
    ap.add_argument("--slices", nargs="+", default=DLPFC_SLICES)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {(r["job"], r["slice"], r["seed"]) for r in map(json.loads, f)}
    jobs = [(m, s, sd, args.data, args.cache) for sd in args.seeds for s in args.slices
            for m in args.methods if (m, s, sd) not in done]
    print(f"{len(jobs)} jobs ({len(done)} done)", flush=True)
    with ProcessPoolExecutor(args.workers, mp_context=mp.get_context("spawn")) as ex, open(args.out, "a") as f:
        futs = {ex.submit(run_one, j): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                rows = fut.result()
            except Exception as e:  # keep going, report at the end
                print(f"FAILED {j[:3]}: {type(e).__name__}: {e}", flush=True)
                continue
            for r in rows:
                r["job"] = j[0]
                f.write(json.dumps(r) + "\n")
                print(f"{r['method']:<20} {r['slice']} seed={r['seed']} ARI={r['ARI']:.3f} t={r['time']:.0f}s", flush=True)
            f.flush()


if __name__ == "__main__":
    main()
