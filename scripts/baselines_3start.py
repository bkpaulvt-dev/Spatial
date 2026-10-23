"""Linear diffusion and PCA with the 3-start GMM used as the standard clustering of AnisoST, HiSTaR and BANKSY.

Until now the two baselines were only clustered with the 20-start best-likelihood GMM, so in the
"standard" comparison they had a stronger clustering step than the methods they were compared with.
This gives them the same 3-start GMM (seeds 0-2, all 20 sections).

python scripts/baselines_3start.py   -> results/baselines_3start.jsonl
"""
import json, os, sys, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from benchmark_anisost import DLPFC_SLICES, N_CLUSTERS  # noqa: E402
from prepare_extra import EXTRA, n_clusters  # noqa: E402

OUT = os.path.join(ROOT, "results", "baselines_3start.jsonl")
METHODS = {"linear_diffusion_single_gmm": "linear", "pca_gmm_single_gmm": "none", "anisost_single_gmm": "anisotropic"}
# AnisoST's 3-start fit on the first three datasets is in anisost_main.jsonl; here only for the datasets run later
ONLY_NEW = {"anisost_single_gmm": ("brca", "stereo")}


def jobs():
    secs = [("dlpfc", s, N_CLUSTERS[s], f"{s}.npz") for s in DLPFC_SLICES]
    for ds, m in EXTRA.items():
        secs += [(ds, s, n_clusters(ds, s), f"{ds}_{s}.npz") for s in m["sections"]]
    return [(m, ds, s, k, f, seed) for m in METHODS for ds, s, k, f in secs for seed in (0, 1, 2)
            if m not in ONLY_NEW or ds in ONLY_NEW[m]]


def run(job):
    warnings.filterwarnings("ignore")
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    from anisost import AnisoST
    method, ds, s, k, fname, seed = job
    z = np.load(os.path.join(ROOT, "results", "cache", fname), allow_pickle=True)
    X, C, y = z["X"], z["coords"], z["labels"]
    keep = np.array([isinstance(v, str) for v in y])
    t0 = time.time()
    p = AnisoST(diffusion=METHODS[method], n_init=3, seed=seed).fit_predict(X, C, k)
    return {"method": method, "dataset": ds, "slice": s, "seed": seed, "time": time.time() - t0,
            "ARI": float(adjusted_rand_score(y[keep], p[keep])), "NMI": float(normalized_mutual_info_score(y[keep], p[keep]))}


if __name__ == "__main__":
    done = set()
    if os.path.exists(OUT):
        done = {(r["method"], r["dataset"], str(r["slice"]), r["seed"]) for r in map(json.loads, open(OUT))}
    todo = [j for j in jobs() if (j[0], j[1], str(j[2]), j[5]) not in done]
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", 3)), mp_context=mp.get_context("spawn")) as ex, open(OUT, "a") as f:
        for fut in as_completed([ex.submit(run, j) for j in todo]):
            r = fut.result(); f.write(json.dumps(r) + "\n"); f.flush()
    print(f"{len(todo)} runs written to {OUT}")
