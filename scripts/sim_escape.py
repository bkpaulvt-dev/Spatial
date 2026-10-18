"""Simulation with known guide efficacy (GLiMMIRS-sim style).

Counts follow a negative binomial whose log mean is basal state + the sum of effects of
the guides that actually worked (multiplicative, no interactions). Each guide works in a
cell with probability rho_k drawn from U(0.2, 1). 30% of perturbed cells carry two guides.

Compared:
  indicator   mean log-fold change of cells carrying the guide (standard analysis)
  cipher_noescape / cipher   CIPHER without / with the efficacy mixture
Reported: recovery of full-effect profiles, efficacy estimates, per-cell escape AUROC,
and spurious interaction magnitude on double-guide cells (truth: none).
"""
import argparse, json, os, sys
import numpy as np
import scipy.sparse as sp
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cipher.data import PerturbData  # noqa: E402
from cipher.model import CIPHER  # noqa: E402


def softmax(a):
    a = a - a.max(-1, keepdims=True)
    e = np.exp(a)
    return e / e.sum(-1, keepdims=True)


def simulate(seed, G=1000, K=24, n_per=300, n_ctrl=3000, frac_double=0.3, d_basal=5):
    rng = np.random.default_rng(seed)
    b = rng.normal(0, 1.5, G)
    load = rng.normal(0, 0.3, (d_basal, G))
    beta = np.zeros((K, G))
    for k in range(K):
        idx = rng.choice(G, 40, replace=False)
        beta[k, idx] = rng.normal(0, 1.0, 40) + np.sign(rng.normal(size=40)) * 0.5
    rho = rng.uniform(0.2, 1.0, K)
    cells_P, onmask = [], []
    for _ in range(n_ctrl):
        cells_P.append([-1, -1]); onmask.append([0, 0])
    for k in range(K):
        for _ in range(n_per):
            if rng.random() < frac_double:
                j = rng.choice([x for x in range(K) if x != k])
                P = [k, j]
            else:
                P = [k, -1]
            on = [int(p >= 0 and rng.random() < rho[p]) for p in P]
            cells_P.append(P); onmask.append(on)
    P = np.array(cells_P); on = np.array(onmask)
    N = len(P)
    zb = rng.normal(size=(N, d_basal))
    eta = b + zb @ load
    for s in range(2):
        m = (P[:, s] >= 0) & (on[:, s] == 1)
        eta[m] += beta[P[m, s]]
    lib = rng.lognormal(np.log(3000), 0.3, N)
    mu = softmax(eta) * lib[:, None]
    theta = 5.0
    X = rng.negative_binomial(theta, theta / (theta + mu)).astype(np.float32)
    conds = np.array(["control" if p[0] < 0 else "+".join(sorted(f"g{q}" for q in p if q >= 0)) for p in P])
    # ground-truth full-effect profiles, averaged over control basal states
    ctrl = P[:, 0] < 0
    eta_c = b + zb[ctrl] @ load
    truth = {k: np.log(softmax(eta_c + beta[k]).mean(0) * 1e4) for k in range(K)}
    truth["ctrl"] = np.log(softmax(eta_c).mean(0) * 1e4)
    d = PerturbData(sp.csr_matrix(X), np.array([f"gene{i}" for i in range(G)]), conds,
                    [f"g{k}" for k in range(K)], P, np.zeros(N, dtype=np.int64), {})
    return d, rho, on, truth, beta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--out", default="results/sim_escape.jsonl")
    ap.add_argument("--device", default="cpu", help='e.g. "cpu", "cuda", "cuda:1"')
    args = ap.parse_args()
    for seed in args.seeds:
        d, rho, on, truth, beta = simulate(seed)
        K = len(d.targets)
        ctrl_idx = np.where(d.conds == "control")[0]
        Xn = d.log_norm()
        L = d.lib
        def lmean(idx):
            return np.log(np.asarray(d.X[idx].multiply(1e4 / L[idx][:, None]).mean(0)).ravel() + 1e-3)
        base = lmean(ctrl_idx)
        single = (d.P[:, 1] < 0)
        est = {"indicator": {}}
        for k in range(K):
            idx = np.where((d.P[:, 0] == k) & single)[0]
            est["indicator"][k] = lmean(idx) - base
        effs = {}
        resid = {}
        for name, kw in [("cipher_noescape", {"escape": False}), ("cipher", {})]:
            m = CIPHER(d, seed=seed, epochs=args.epochs, verbose=False, device=args.device, **kw).fit()
            c0 = np.log(m.predict_mean([], ctrl_idx) + 1e-3)
            est[name] = {k: np.log(m.predict_mean([f"g{k}"], ctrl_idx, mixture=False) + 1e-3) - c0
                         for k in range(K)}
            effs[name] = m.efficacy()
            # spurious interaction on 10 pairs: full double vs sum of full singles
            rs = []
            for k in range(0, K, 2):
                dd = np.log(m.predict_mean([f"g{k}", f"g{k+1}"], ctrl_idx, mixture=False) + 1e-3) - c0
                top = np.argsort(-np.abs(est[name][k] + est[name][k + 1]))[:40]
                rs.append(np.mean(np.abs(dd - est[name][k] - est[name][k + 1])[top]) /
                          np.mean(np.abs(est[name][k] + est[name][k + 1])[top]))
            resid[name] = float(np.mean(rs))
            if name == "cipher":
                pp = m.escape_posterior(np.arange(len(d.conds)))
                has = d.P >= 0
                auroc = float(roc_auc_score(on[has], pp[has]))
        for name, e in est.items():
            sl, cr = [], []
            for k in range(K):
                t = truth[k] - truth["ctrl"]
                top = np.argsort(-np.abs(t))[:40]
                cr.append(np.corrcoef(e[k][top], t[top])[0, 1])
                sl.append(np.polyfit(t[top], e[k][top], 1)[0])
            row = {"seed": seed, "method": name, "effect_corr": float(np.mean(cr)),
                   "effect_slope": float(np.mean(sl))}
            if name in effs:
                ev = np.array([effs[name][f"g{k}"] for k in range(K)])
                row["efficacy_corr"] = float(np.corrcoef(ev, rho)[0, 1]) if name == "cipher" else None
                row["efficacy_mae"] = float(np.mean(np.abs(ev - rho))) if name == "cipher" else None
                row["spurious_interaction"] = resid[name]
            if name == "cipher":
                row["escape_auroc"] = auroc
            # attenuation of the slope as a function of true efficacy
            row["slope_vs_rho_corr"] = float(np.corrcoef(sl, rho)[0, 1])
            print(row, flush=True)
            with open(args.out, "a") as f:
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
