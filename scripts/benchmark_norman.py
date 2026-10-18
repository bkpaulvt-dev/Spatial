"""Held-out double-perturbation prediction on Norman et al. 2019.

All singles and a random half of the doubles are used for training; the other half of
the doubles are test conditions. Profiles are log1p of the mean normalised expression
(1e4 * counts / library) of a condition. Results are appended as JSON lines.

Methods
  control          predict the control profile (no effect)
  additive_lin     MIMOSCA-style additivity on the expression scale
  additive_log     multiplicative null (GLiMMIRS): delta_AB = delta_A + delta_B on log scale
  scaled_additive  additive_log scaled by one scalar fitted on training doubles
  cipher[...]      CIPHER and its ablations (see --variants)
"""
import argparse, json, os, pickle, sys, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cipher.model import CIPHER  # noqa: E402

VARIANTS = {
    "cipher": {},
    "cipher_linear": {"activation": "linear"},           # CPA-like: latent effects add
    "cipher_noescape": {"escape": False},
    "cipher_noadv": {"adversary": False},
}


def profiles(d):
    L = d.lib
    out = {}
    for c in np.unique(d.conds):
        idx = np.where(d.conds == c)[0]
        out[c] = np.asarray((d.X[idx].multiply(1e4 / L[idx][:, None])).mean(0)).ravel()
    return out


def metrics(pred, true, ctrl, sA, sB, n_de=20):
    dt, dp = true - ctrl, pred - ctrl
    de = np.argsort(-np.abs(dt))[:n_de]
    res_t = true - (sA + sB - ctrl)
    res_p = pred - (sA + sB - ctrl)
    def corr(a, b):
        if np.std(a) < 1e-9 or np.std(b) < 1e-9:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])
    top_r = np.argsort(-np.abs(res_t))[:n_de]
    return {"pearson_de20": corr(dp[de], dt[de]), "pearson_all": corr(dp, dt),
            "mse_de20": float(np.mean((dp[de] - dt[de]) ** 2)),
            "resid_corr_de20": corr(res_p[de], res_t[de]),
            "resid_corr_top20": corr(res_p[top_r], res_t[top_r]),
            "resid_mse_top20": float(np.mean((res_p[top_r] - res_t[top_r]) ** 2))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/perturb/norman_prep.pkl")
    ap.add_argument("--out", default="results/norman_doubles.jsonl")
    ap.add_argument("--splits", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--variants", nargs="*", default=list(VARIANTS))
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--config", nargs="*", default=[], help="name=JSON extra variants")
    args = ap.parse_args()
    for c in args.config:
        k, v = c.split("=", 1)
        VARIANTS[k] = json.loads(v)
        args.variants.append(k)
    d = pickle.load(open(args.data, "rb"))
    prof = {c: np.log1p(v) for c, v in profiles(d).items()}
    lin = {c: np.expm1(v) for c, v in prof.items()}
    ctrl = prof["control"]
    doubles = sorted(c for c in prof if "+" in c)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    for split in args.splits:
        rng = np.random.default_rng(split)
        test = set(rng.choice(doubles, len(doubles) // 2, replace=False))
        train_d = [c for c in doubles if c not in test]
        train_idx = np.where(~np.isin(d.conds, list(test)))[0]
        ctrl_idx = np.where(d.conds == "control")[0]
        # scalar for scaled additive, least squares on training doubles' deltas
        num = den = 0.0
        for c in train_d:
            a, b = c.split("+")
            s = prof[a] + prof[b] - 2 * ctrl
            num += s @ (prof[c] - ctrl)
            den += s @ s
        alpha = num / den
        preds = {}
        for c in sorted(test):
            a, b = c.split("+")
            preds.setdefault("control", {})[c] = ctrl
            preds.setdefault("additive_log", {})[c] = prof[a] + prof[b] - ctrl
            preds.setdefault("additive_lin", {})[c] = np.log1p(np.clip(lin[a] + lin[b] - lin["control"], 0, None))
            preds.setdefault("scaled_additive", {})[c] = ctrl + alpha * (prof[a] + prof[b] - 2 * ctrl)
        timing = {}
        for v in args.variants:
            t = time.time()
            print(f"[split {split}] fitting {v}", flush=True)
            m = CIPHER(d, seed=split, epochs=args.epochs, threads=args.threads, train_idx=train_idx,
                       **VARIANTS[v]).fit()
            for c in sorted(test):
                preds.setdefault(v, {})[c] = np.log1p(m.predict_mean(c.split("+"), ctrl_idx))
            # also score how well training singles are reconstructed (fit sanity)
            sing = [c for c in prof if "+" not in c and c != "control"]
            fit_s = np.mean([metrics(np.log1p(m.predict_mean([c], ctrl_idx)), prof[c], ctrl, ctrl, ctrl)
                             ["pearson_de20"] for c in sing[:30]])
            timing[v] = (time.time() - t, float(fit_s))
            print(f"  done in {timing[v][0]:.0f}s, train-single pearson_de20 {fit_s:.3f}", flush=True)
        with open(args.out, "a") as f:
            for meth, pm in preds.items():
                for c, p in pm.items():
                    a, b = c.split("+")
                    r = metrics(p, prof[c], ctrl, prof[a], prof[b])
                    r.update(method=meth, split=split, cond=c, alpha=float(alpha),
                             seconds=float(timing.get(meth, (0, 0))[0]), train_single_fit=float(timing.get(meth, (0, 0))[1]))
                    f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
