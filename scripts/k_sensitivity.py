"""Sensitivity to the number of domains K, and a label-free choice of K.

Every method was given the true number of domains. Here each seed-0 embedding (results/emb/<dataset>_<section>_<method>.npy)
is clustered with the matched protocol (tied-covariance Gaussian mixture, 20 random starts, best likelihood) for
K = K_true - 2 ... K_true + 2, recording ARI and BIC. The label-free choice is the K with the lowest BIC.

python scripts/k_sensitivity.py   -> results/k_sensitivity.jsonl
"""
import glob, json, os, sys, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
OUT = os.path.join(ROOT, "results", "k_sensitivity.jsonl")
EMB = os.path.join(ROOT, "results", "emb")
DELTAS = (-2, -1, 0, 1, 2)


def cache_file(ds, s):
    return os.path.join(ROOT, "results", "cache", f"{s}.npz" if ds == "dlpfc" else f"{ds}_{s}.npz")


def run(job):
    warnings.filterwarnings("ignore")
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import adjusted_rand_score
    ds, s, m, path = job
    y = np.load(cache_file(ds, s), allow_pickle=True)["labels"]
    keep = np.array([isinstance(v, str) for v in y])
    k0 = len(set(y[keep]))
    Z = np.asarray(np.load(path), dtype=np.float64)
    fits = []
    for dk in DELTAS:
        k = k0 + dk
        if k < 2: continue
        g = GaussianMixture(k, covariance_type="tied", n_init=20, reg_covar=1e-5, random_state=0).fit(Z)
        p = g.predict(Z)
        fits.append({"k": k, "dk": dk, "ARI": float(adjusted_rand_score(y[keep], p[keep])), "bic": float(g.bic(Z))})
    return {"dataset": ds, "slice": s, "method": m, "k_true": k0, "fits": fits}


def jobs():
    out = []
    for path in sorted(glob.glob(os.path.join(EMB, "*.npy"))):
        base = os.path.basename(path)[:-4]
        ds, rest = base.split("_", 1)
        for m in ("linear_diffusion", "anisost", "pca_gmm", "banksy_l0.2", "banksy_l0.8", "histar", "graphst", "stagate", "sedr",
                  "spaceflow", "nichepca", "ccst", "spatial_mgcn", "deepst", "mgcn"):
            if rest.endswith("_" + m):
                s = rest[: -len(m) - 1]
                if os.path.exists(cache_file(ds, s)):
                    out.append((ds, s, "spatial_mgcn" if m == "mgcn" else m, path))
                break
    return out


if __name__ == "__main__":
    done = set()
    if os.path.exists(OUT):
        done = {(r["dataset"], r["slice"], r["method"]) for r in map(json.loads, open(OUT))}
    todo = [j for j in jobs() if (j[0], j[1], j[2]) not in done]
    print(f"{len(todo)} embeddings", flush=True)
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", 1)), mp_context=mp.get_context("spawn")) as ex, open(OUT, "a") as f:
        for fut in as_completed([ex.submit(run, j) for j in todo]):
            r = fut.result(); f.write(json.dumps(r) + "\n"); f.flush()
