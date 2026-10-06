"""Benchmark HiSTaR vs HiCAST (and ablations) on the 12 DLPFC slices.

Example
-------
python scripts/benchmark_dlpfc.py --data data/DLPFC --out results/dlpfc.jsonl \
    --methods histar hicast --seeds 0 1 2 --workers 4

``--config NAME=JSON`` adds a HiCAST variant, e.g.
    --config no_lg='{"local_global": false}'
Every (method, slice, seed) run appends one JSON line, and finished runs are
skipped on restart, so the script can be interrupted and resumed.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from hicast.data import DLPFC_SLICES, DLPFC_N_CLUSTERS, SpatialData, load_dlpfc  # noqa: E402


def cached_slice(data_root: str, cache: str, slice_id: str) -> SpatialData:
    path = os.path.join(cache, f"{slice_id}.npz")
    if not os.path.exists(path):
        d = load_dlpfc(data_root, slice_id)
        np.savez_compressed(path, X=d.X, coords=d.coords, labels=d.labels.astype(object))
    z = np.load(path, allow_pickle=True)
    return SpatialData(X=z["X"], coords=z["coords"], labels=z["labels"],
                       meta={"slice": slice_id, "n_clusters": DLPFC_N_CLUSTERS[slice_id]})


def run_one(job):
    warnings.filterwarnings("ignore")
    import torch
    torch.set_num_threads(1)
    from hicast.cluster import evaluate, gmm_eee, spatial_refine
    from hicast.histar import HiSTaR
    from hicast.model import HiCAST

    method, cfg, slice_id, seed, data_root, cache = job
    d = cached_slice(data_root, cache, slice_id)
    k = d.meta["n_clusters"]
    torch.manual_seed(seed)
    np.random.seed(seed)
    t0 = time.time()
    if method.startswith("histar"):
        model = HiSTaR(d.X, d.coords, k, seed=seed, **cfg).fit()
    else:
        model = HiCAST(d.X, d.coords, seed=seed, **cfg).fit()
    Z = model.embed()
    train_time = time.time() - t0
    pred = gmm_eee(Z, k)
    res = {"method": method, "slice": slice_id, "seed": seed, "time": train_time}
    res.update(evaluate(pred, d.labels))
    ref = evaluate(spatial_refine(pred, d.coords), d.labels)
    res.update({f"{m}_refined": v for m, v in ref.items()})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="results/dlpfc.jsonl")
    ap.add_argument("--cache", default=None)
    ap.add_argument("--slices", nargs="+", default=DLPFC_SLICES)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--methods", nargs="*", default=["histar", "hicast"])
    ap.add_argument("--config", nargs="*", default=[], help="NAME=JSON HiCAST/HiSTaR variants")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    configs = {"histar": {}, "histar_deterministic": {"deterministic_eval": True}, "hicast": {}}
    for c in args.config:
        name, js = c.split("=", 1)
        configs[name] = json.loads(js)
        if name not in args.methods:
            args.methods.append(name)

    cache = args.cache or os.path.join(os.path.dirname(os.path.abspath(args.out)), "cache")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    for s in args.slices:                       # preprocess once, serially
        cached_slice(args.data, cache, s)

    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                r = json.loads(line)
                done.add((r["method"], r["slice"], r["seed"]))
    jobs = [(m, configs[m], s, sd, args.data, cache)
            for sd in args.seeds for s in args.slices for m in args.methods
            if (m, s, sd) not in done]
    print(f"{len(jobs)} runs to do ({len(done)} already done)", flush=True)
    with ProcessPoolExecutor(args.workers, mp_context=mp.get_context("spawn")) as ex, open(args.out, "a") as f:
        futs = {ex.submit(run_one, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"{r['method']:<24} {r['slice']} seed={r['seed']} ARI={r['ARI']:.3f} "
                  f"ARI_ref={r['ARI_refined']:.3f} t={r['time']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
