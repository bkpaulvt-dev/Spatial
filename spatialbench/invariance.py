"""Metamorphic (invariance) tests: transformations that must not change a method's answer (plan section 6).

A method is a callable ``fn(X, coords, k, seed) -> labels`` (X: (n, genes or PCs) matrix).
For each transformation T we compute the *consistency* ARI(original labels, labels on T(data) mapped back
to the original order). Stochastic methods never reach 1.0, so every score is compared with the
method's own *seed-to-seed* consistency ARI(seed a, seed b) on the untransformed data:

    violation = max(0, seed_baseline - consistency)

A violation clearly above zero means the transformation changes the answer by more than random
restarts do. ``pass`` uses a tolerance ``tol`` (default 0.02) on that violation, with a one-sided
bootstrap-free rule (mean over repeats); report the numbers, not only the flag.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import adjusted_rand_score as ARI

TRANSFORMS = {}


def _register(name):
    def deco(f):
        TRANSFORMS[name] = f
        return f
    return deco


@_register("permute_spots")
def permute_spots(X, coords, rs):
    p = rs.permutation(len(X))
    return X[p], coords[p], p                      # new row i is old row p[i]


@_register("rescale_coords_x100")
def rescale(X, coords, rs):
    return X, coords * 100.0, np.arange(len(X))


@_register("rescale_coords_x0.01")
def rescale_down(X, coords, rs):
    return X, coords * 0.01, np.arange(len(X))


@_register("translate_coords")
def translate(X, coords, rs):
    return X, coords + np.array([1e4, -5e3]), np.arange(len(X))


@_register("rotate_coords_37deg")
def rotate(X, coords, rs):
    a = np.deg2rad(37)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return X, coords @ R.T, np.arange(len(X))


@_register("reflect_coords")
def reflect(X, coords, rs):
    return X, coords * np.array([-1.0, 1.0]), np.arange(len(X))


@_register("permute_features")
def permute_features(X, coords, rs):
    return X[:, rs.permutation(X.shape[1])], coords, np.arange(len(X))


@_register("scale_expression_x2")
def scale_x2(X, coords, rs):
    return X * 2.0, coords, np.arange(len(X))      # only meaningful for scale-invariant inputs (e.g. PCs of standardised data)


def run_invariance(fn, X, coords, k, n_seeds: int = 3, repeats: int = 2, transforms=None, tol: float = 0.02,
                   base_seed: int = 0) -> dict:
    """Return {'seed_baseline': float, 'consistency': {T: mean ARI}, 'violation': {T: float}, 'pass': {T: bool}}."""
    names = transforms or list(TRANSFORMS)
    X, coords = np.asarray(X), np.asarray(coords, float)
    labs = [fn(X, coords, k, base_seed + s) for s in range(n_seeds)]
    pair = [ARI(labs[i], labs[j]) for i in range(n_seeds) for j in range(i + 1, n_seeds)]
    seed_base = float(np.mean(pair)) if pair else 1.0
    ref = labs[0]
    out = {"seed_baseline": seed_base, "consistency": {}, "violation": {}, "pass": {}, "n_seeds": n_seeds}
    for name in names:
        vals = []
        for r in range(repeats):
            rs = np.random.RandomState(1000 + r)
            Xt, ct, p = TRANSFORMS[name](X, coords, rs)
            lt = np.asarray(fn(Xt, ct, k, base_seed))      # same seed as ref: isolates the transformation
            back = np.empty_like(lt)
            back[p] = lt                                    # row i of the transformed data is original row p[i]
            vals.append(ARI(ref, back))
        c = float(np.mean(vals))
        out["consistency"][name] = c
        out["violation"][name] = float(max(0.0, seed_base - c)) if seed_base < 1 else float(1 - c)
        out["pass"][name] = out["violation"][name] <= tol
    return out
