"""How much does ARI depend on the GMM initialisation alone, on a *fixed* embedding?

For every DLPFC slice, one embedding is computed (seed 0) for HiSTaR (official-code port,
published defaults) and AnisoST. The mclust-EEE-equivalent GMM is then fitted 20 times
with a single random start each (random_state 0..19). We record ARI and the per-spot
log-likelihood of every fit, the ARI of the best-likelihood fit (= 20-start robust GMM),
and the ARI of the 3-start fit used by the standard pipeline (hicast.cluster.gmm_eee).

python scripts/clustering_lottery.py      -> results/clustering_lottery.jsonl
"""
import json, os, sys, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from benchmark_anisost import DLPFC_SLICES, N_CLUSTERS  # noqa: E402

N_FITS = 20


def run(job):
    warnings.filterwarnings("ignore")
    import torch
    torch.set_num_threads(1)
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import adjusted_rand_score
    from hicast.cluster import gmm_eee
    from hicast.histar import HiSTaR
    from anisost import AnisoST
    method, s = job
    z = np.load(os.path.join(ROOT, "results", "cache", f"{s}.npz"), allow_pickle=True)
    X, C, y = z["X"], z["coords"], z["labels"]
    k = N_CLUSTERS[s]
    keep = np.array([isinstance(v, str) for v in y])
    if method == "histar":
        torch.manual_seed(0); np.random.seed(0)
        Z = HiSTaR(X, C, k, seed=0).fit().embed()
    else:
        Z = AnisoST(seed=0).embed(X, C)
    Z = np.asarray(Z, dtype=np.float64)
    fits = []
    for r in range(N_FITS):
        g = GaussianMixture(k, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=r).fit(Z)
        p = g.predict(Z)
        fits.append({"rs": r, "ll": float(g.score(Z)), "ARI": float(adjusted_rand_score(y[keep], p[keep]))})
    std3 = gmm_eee(Z, k)
    return {"method": method, "slice": s, "fits": fits,
            "ARI_standard3": float(adjusted_rand_score(y[keep], std3[keep])),
            "ARI_bestll": max(fits, key=lambda f: f["ll"])["ARI"]}


if __name__ == "__main__":
    out = os.path.join(ROOT, "results", "clustering_lottery.jsonl")
    jobs = [(m, s) for m in ("histar", "anisost") for s in DLPFC_SLICES]
    with ProcessPoolExecutor(4, mp_context=mp.get_context("spawn")) as ex, open(out, "w") as f:
        for fut in as_completed([ex.submit(run, j) for j in jobs]):
            r = fut.result()
            f.write(json.dumps(r) + "\n"); f.flush()
            a = [x["ARI"] for x in r["fits"]]
            print(f"{r['method']:<8} {r['slice']} single-start ARI {min(a):.3f}-{max(a):.3f}  best-LL {r['ARI_bestll']:.3f}", flush=True)
