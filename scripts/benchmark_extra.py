"""All methods on the STARmap and MERFISH sections (prepared by scripts/prepare_extra.py).

Same methods, settings and clustering protocols as the DLPFC benchmark; nothing was tuned
on these data. SpaGCN is run without its hexagonal refinement (single-cell data, not a
Visium grid). Seed-0 embeddings of HiSTaR and AnisoST are saved to results/emb/ for the
clustering-lottery experiments.

python scripts/benchmark_extra.py --out results/extra.jsonl
"""
import argparse, json, os, sys, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from prepare_extra import EXTRA  # noqa: E402

EMB = os.path.join(ROOT, "results", "emb")


def load(ds, sec):
    return np.load(os.path.join(ROOT, "results", "cache", f"{ds}_{sec}.npz"), allow_pickle=True)


def scores(y, p):
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    return {"ARI": adjusted_rand_score(y, p), "NMI": normalized_mutual_info_score(y, p)}


def banksy_embed(G, coords, genes, lam, seed):
    import contextlib, io, anndata, pandas as pd
    from sklearn.decomposition import PCA
    from banksy.initialize_banksy import initialize_banksy
    from banksy.embed_banksy import generate_banksy_matrix
    a = anndata.AnnData(np.asarray(G, np.float64), var=pd.DataFrame(index=[str(g) for g in genes]))
    a.obs["x"], a.obs["y"] = coords[:, 0], coords[:, 1]
    a.obsm["coord_xy"] = np.asarray(coords, np.float64)
    with contextlib.redirect_stdout(io.StringIO()):
        bd = initialize_banksy(a, ("x", "y", "coord_xy"), num_neighbours=18, nbr_weight_decay="scaled_gaussian",
                               max_m=1, plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False, plt_theta=False)
        _, bm = generate_banksy_matrix(a, bd, [lam], max_m=1, verbose=False)
    return PCA(20, random_state=seed).fit_transform(np.asarray(bm.X))


def spagcn_predict(G, coords, k, seed):
    import contextlib, io, random, torch, anndata, SpaGCN as spg
    a = anndata.AnnData(np.asarray(G, np.float32))
    with contextlib.redirect_stdout(io.StringIO()):
        adj = spg.calculate_adj_matrix(x=coords[:, 0], y=coords[:, 1], histology=False)
        l = spg.search_l(0.5, adj, start=0.01, end=1000, tol=0.01, max_run=100)
        res = spg.search_res(a, adj, l, k, start=0.7, step=0.1, tol=5e-3, lr=0.05, max_epochs=20,
                             r_seed=seed, t_seed=seed, n_seed=seed)
        random.seed(seed); torch.manual_seed(seed); np.random.seed(seed)
        clf = spg.SpaGCN(); clf.set_l(l)
        clf.train(a, adj, init_spa=True, init="louvain", res=res, tol=5e-3, lr=0.05, max_epochs=200)
        pred, _ = clf.predict()
    return pred


def run(job):
    warnings.filterwarnings("ignore")
    import torch; torch.set_num_threads(1)
    from hicast.cluster import gmm_eee
    from hicast.histar import HiSTaR
    from anisost import AnisoST, robust_gmm
    method, ds, sec, seed = job
    z = load(ds, sec); X, G, C, y = z["X"], z["G"], z["coords"], z["labels"]
    k = EXTRA[ds]["n_clusters"]; base = {"dataset": ds, "slice": sec, "seed": seed}
    t0 = time.time(); out = []
    if method == "anisost":
        m = AnisoST(seed=seed); Z = m.embed(X, C); t = time.time() - t0
        out += [{**base, "method": "anisost", "time": t, **scores(y, robust_gmm(Z, k, seed=seed))},
                {**base, "method": "anisost_single_gmm", "time": t, **scores(y, robust_gmm(Z, k, n_init=3, seed=seed))}]
        if seed == 0: np.save(os.path.join(EMB, f"{ds}_{sec}_anisost.npy"), Z)
    elif method in ("linear_diffusion", "pca_gmm"):
        d = "linear" if method == "linear_diffusion" else "none"
        p = AnisoST(diffusion=d, seed=seed).fit_predict(X, C, k)
        out.append({**base, "method": method, "time": time.time() - t0, **scores(y, p)})
    elif method == "histar":
        torch.manual_seed(seed); np.random.seed(seed)
        Z = HiSTaR(X, C, k, seed=seed).fit().embed(); t = time.time() - t0
        out += [{**base, "method": "histar_rerun", "time": t, **scores(y, gmm_eee(Z, k))},
                {**base, "method": "histar+robust", "time": t, **scores(y, robust_gmm(Z, k, seed=seed))}]
        if seed == 0: np.save(os.path.join(EMB, f"{ds}_{sec}_histar.npy"), Z)
    elif method.startswith("banksy"):
        lam = float(method.split("_l")[1]); Z = banksy_embed(G, C, z["genes"], lam, seed); t = time.time() - t0
        out += [{**base, "method": method, "time": t, **scores(y, gmm_eee(Z, k, seed=seed))},
                {**base, "method": method + "+robust", "time": t, **scores(y, robust_gmm(Z, k, seed=seed))}]
    elif method == "spagcn":
        p = spagcn_predict(G, C, k, seed)
        out.append({**base, "method": "spagcn", "time": time.time() - t0, **scores(y, p)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "extra.jsonl"))
    ap.add_argument("--methods", nargs="+", default=["anisost", "linear_diffusion", "pca_gmm", "histar",
                                                     "banksy_l0.2", "banksy_l0.8", "spagcn"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(EMB, exist_ok=True)
    done = set()
    if os.path.exists(a.out):
        done = {(r["job"], r["dataset"], r["slice"], r["seed"]) for r in map(json.loads, open(a.out))}
    jobs = [(m, ds, sec, sd) for sd in a.seeds for ds, info in EXTRA.items() for sec in info["sections"]
            for m in a.methods if (m, ds, sec, sd) not in done]
    print(f"{len(jobs)} jobs", flush=True)
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("spawn")) as ex, open(a.out, "a") as f:
        futs = {ex.submit(run, j): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                rows = fut.result()
            except Exception as e:
                print(f"FAILED {j}: {type(e).__name__}: {e}", flush=True); continue
            for r in rows:
                r["job"] = j[0]; f.write(json.dumps(r) + "\n")
                print(f"{r['method']:<20} {r['dataset']} {r['slice']} s{r['seed']} ARI={r['ARI']:.3f} t={r['time']:.0f}s", flush=True)
            f.flush()


if __name__ == "__main__":
    main()
