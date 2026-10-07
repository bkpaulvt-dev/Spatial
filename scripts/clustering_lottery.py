"""How much does ARI depend on the GMM initialisation alone, on a *fixed* embedding?

For every section of the three datasets (DLPFC, STARmap, MERFISH), one embedding is computed
(seed 0) for HiSTaR (official-code port, published defaults) and AnisoST, and saved to
results/emb/ (STARmap/MERFISH embeddings are written by benchmark_extra.py). The tied-covariance
GMM is then fitted 20 times with a single random start each (random_state 0..19). We record
ARI and per-spot log-likelihood of every fit, the ARI of the best-likelihood fit (= 20-start
robust GMM) and of the 3-start fit used by the standard pipeline. Embeddings and labels are
also exported as CSV for the R mclust experiment (scripts/mclust_lottery.R).

python scripts/clustering_lottery.py      -> results/clustering_lottery.jsonl
"""
import json, os, sys, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from benchmark_anisost import DLPFC_SLICES, N_CLUSTERS  # noqa: E402
from prepare_extra import EXTRA  # noqa: E402

N_FITS = 20
EMB = os.path.join(ROOT, "results", "emb")


def sections():
    out = [("dlpfc", s, N_CLUSTERS[s], f"{s}.npz") for s in DLPFC_SLICES]
    for ds, m in EXTRA.items():
        out += [(ds, s, m["n_clusters"], f"{ds}_{s}.npz") for s in m["sections"]]
    return out


def run(job):
    warnings.filterwarnings("ignore")
    import torch; torch.set_num_threads(1)
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import adjusted_rand_score
    from hicast.cluster import gmm_eee
    from hicast.histar import HiSTaR
    from anisost import AnisoST
    method, ds, s, k, fname = job
    z = np.load(os.path.join(ROOT, "results", "cache", fname), allow_pickle=True)
    X, C, y = z["X"], z["coords"], z["labels"]
    keep = np.array([isinstance(v, str) for v in y])
    path = os.path.join(EMB, f"{ds}_{s}_{method}.npy")
    if os.path.exists(path):
        Z = np.load(path)
    elif method == "graphst":                       # written by benchmark_graphst.py only
        return None
    else:
        if method == "histar":
            torch.manual_seed(0); np.random.seed(0)
            Z = HiSTaR(X, C, k, seed=0).fit().embed()
        else:
            Z = AnisoST(seed=0).embed(X, C)
        np.save(path, Z)
    Z = np.asarray(Z, dtype=np.float64)
    os.makedirs(os.path.join(EMB, "csv"), exist_ok=True)
    np.savetxt(os.path.join(EMB, "csv", f"{ds}__{s}__{method}__k{k}.csv"), Z, delimiter=",")
    np.savetxt(os.path.join(EMB, "csv", f"{ds}__{s}__labels.csv"),
               np.array([v if isinstance(v, str) else "NA" for v in y]), fmt="%s")
    fits = []
    for r in range(N_FITS):
        g = GaussianMixture(k, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=r).fit(Z)
        p = g.predict(Z)
        fits.append({"rs": r, "ll": float(g.score(Z)), "ARI": float(adjusted_rand_score(y[keep], p[keep]))})
    std3 = gmm_eee(Z, k)
    return {"method": method, "dataset": ds, "slice": s, "fits": fits,
            "ARI_standard3": float(adjusted_rand_score(y[keep], std3[keep])),
            "ARI_bestll": max(fits, key=lambda f: f["ll"])["ARI"]}


if __name__ == "__main__":
    os.makedirs(EMB, exist_ok=True)
    out = os.path.join(ROOT, "results", "clustering_lottery.jsonl")
    methods = os.environ.get("METHODS", "histar anisost graphst").split()
    done = set()
    if os.path.exists(out):
        done = {(r["method"], r.get("dataset", "dlpfc"), r["slice"]) for r in map(json.loads, open(out))}
    jobs = [(m, ds, s, k, f) for m in methods for ds, s, k, f in sections() if (m, ds, s) not in done]
    workers = int(os.environ.get("WORKERS", 4))
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn")) as ex, open(out, "a") as f:
        for fut in as_completed([ex.submit(run, j) for j in jobs]):
            r = fut.result()
            if r is None:
                continue
            f.write(json.dumps(r) + "\n"); f.flush()
            a = [x["ARI"] for x in r["fits"]]
            print(f"{r['method']:<8} {r['dataset']:<8} {r['slice']} single-start ARI {min(a):.3f}-{max(a):.3f}  best-LL {r['ARI_bestll']:.3f}", flush=True)
