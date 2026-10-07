"""Benchmark AnisoST (+ ablations and a hyper-parameter sweep) on the 12 DLPFC slices.

Uses the same preprocessed inputs (results/cache/<slice>.npz, written by
scripts/benchmark_dlpfc.py / hicast.data.preprocess) and the same evaluation as
the HiSTaR / HiCAST benchmark, so the results are directly comparable with
results/dlpfc_main.jsonl.

python scripts/benchmark_anisost.py --cache results/cache --out results/anisost_main.jsonl
python scripts/benchmark_anisost.py --cache results/cache --out results/anisost_sweep.jsonl --sweep
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

DLPFC_SLICES = ["151507", "151508", "151509", "151510", "151669", "151670",
                "151671", "151672", "151673", "151674", "151675", "151676"]
N_CLUSTERS = {s: 5 if s in {"151669", "151670", "151671", "151672"} else 7 for s in DLPFC_SLICES}

# name -> AnisoST kwargs. "anisost" is the full method, the rest are ablations.
METHODS = {
    "anisost": {},
    "anisost_single_gmm": {"n_init": 3},          # usual single-run mclust-style clustering
    "linear_diffusion": {"diffusion": "linear"},  # no edge preservation
    "pca_gmm": {"diffusion": "none"},             # non-spatial
}


def sweep_configs():
    cfg = {}
    for T in [2, 5, 10, 15, 20, 30, 50]:
        cfg[f"steps={T}"] = {"steps": T}
    for q in [0.2, 0.35, 0.5, 0.65, 0.8]:
        cfg[f"q={q}"] = {"q": q}
    for k in [4, 6, 8, 12]:
        cfg[f"k={k}"] = {"k": k}
    for p in [15, 20, 30, 50]:
        cfg[f"n_pcs={p}"] = {"n_pcs": p}
    for a in [0.25, 0.5, 0.75]:
        cfg[f"alpha={a}"] = {"alpha": a}
    return cfg


def run_one(job):
    warnings.filterwarnings("ignore")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from sklearn.metrics import adjusted_rand_score, fowlkes_mallows_score, normalized_mutual_info_score
    from anisost import AnisoST

    name, cfg, s, seed, cache = job
    z = np.load(os.path.join(cache, f"{s}.npz"), allow_pickle=True)
    X, coords, y = z["X"], z["coords"], z["labels"]
    t0 = time.time()
    pred = AnisoST(seed=seed, **cfg).fit_predict(X, coords, N_CLUSTERS[s])
    t = time.time() - t0
    keep = np.array([isinstance(v, str) for v in y])
    return {"method": name, "slice": s, "seed": seed, "time": t,
            "ARI": adjusted_rand_score(y[keep], pred[keep]),
            "NMI": normalized_mutual_info_score(y[keep], pred[keep]),
            "FMS": fowlkes_mallows_score(y[keep], pred[keep]),
            "pred": pred.tolist() if (name == "anisost" and seed == 0) else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/cache")
    ap.add_argument("--out", default="results/anisost_main.jsonl")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--slices", nargs="+", default=DLPFC_SLICES)
    ap.add_argument("--sweep", action="store_true", help="one-factor-at-a-time sensitivity sweep")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    methods = sweep_configs() if args.sweep else METHODS
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {(r["method"], r["slice"], r["seed"]) for r in map(json.loads, f)}
    jobs = [(m, c, s, sd, args.cache) for sd in args.seeds for s in args.slices
            for m, c in methods.items() if (m, s, sd) not in done]
    print(f"{len(jobs)} runs ({len(done)} done)", flush=True)
    with ProcessPoolExecutor(args.workers) as ex, open(args.out, "a") as f:
        for fut in as_completed([ex.submit(run_one, j) for j in jobs]):
            r = fut.result()
            if r["pred"] is None:
                del r["pred"]
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"{r['method']:<20} {r['slice']} seed={r['seed']} ARI={r['ARI']:.3f} t={r['time']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
