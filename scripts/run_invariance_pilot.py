"""Invariance pilot on training-free methods (fast enough to repeat many times).

Inputs are the first 30 PCs of the QC/benchmark preprocessing, so permuting feature columns and
rescaling the matrix are meaningful tests. -> results/invariance_pilot.json
"""
import json, os, sys, warnings
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT); warnings.filterwarnings("ignore")
from anisost import AnisoST  # noqa: E402
from spatialbench.invariance import run_invariance  # noqa: E402
from benchmark_anisost import N_CLUSTERS  # noqa: E402  (scripts/ on path via sys.path[0])


def make(diffusion, n_init=20):
    def fn(X, coords, k, seed):
        m = AnisoST(n_pcs=X.shape[1], diffusion=diffusion, n_init=n_init, seed=seed)
        return m.fit_predict(X, coords, k)
    return fn


CASES = [("dlpfc", "151673"), ("merfish", "-0.14")]
out = {}
for ds, sec in CASES:
    if ds == "dlpfc":
        z = np.load(os.path.join(ROOT, "results", "cache", f"{sec}.npz"), allow_pickle=True)
        X, coords, k = z["X"][:, :30], z["coords"].astype(float), N_CLUSTERS[sec]
    else:
        z = np.load(os.path.join(ROOT, "results", "cache", f"{ds}_{sec}.npz"), allow_pickle=True)
        X, coords, k = z["X"][:, :30], z["coords"].astype(float), 8
    for name, fn in [("pca_gmm", make("none")), ("linear_diffusion", make("linear")), ("anisost", make("anisotropic"))]:
        r = run_invariance(fn, X, coords, k, n_seeds=3, repeats=2)
        out[f"{ds}/{sec}/{name}"] = r
        worst = max(r["violation"].items(), key=lambda kv: kv[1])
        print(f"{ds}/{sec} {name:<17} seed-baseline ARI {r['seed_baseline']:.3f}  worst violation {worst[1]:.3f} ({worst[0]})", flush=True)
        json.dump(out, open(os.path.join(ROOT, "results", "invariance_pilot.json"), "w"), indent=1)
