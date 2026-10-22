"""Fig. 4: do predicted double-perturbation profiles recover Norman et al.'s genetic-interaction
measures and categories for held-out pairs?

For each pair AB the double effect is fitted as  dAB = c1*dA + c2*dB  (Theil-Sen-like robust fit via
least squares on informative genes, as in Norman et al. 2019). Measures:
  magnitude  sqrt(c1^2 + c2^2)        > 1 synergy, < 1 suppression / buffering
  equality   min(|c1|,|c2|)/max(...)  low = one gene dominates (epistasis)
  fit        R^2 of the fit            low = neomorphic behaviour
Categories use thresholds set on the TRUE profiles (tertiles over all 131 pairs), and are
scored with AUROC of each method's predicted measure. Additive predictions give magnitude ~
sqrt(2)/... by construction, so they cannot separate categories: that is the point of the test.
"""
import glob, json, sys
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr


def gi(dA, dB, dAB, mask):
    X = np.stack([dA[mask], dB[mask]], 1)
    y = dAB[mask]
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ c
    r2 = 1 - np.sum((y - fit) ** 2) / max(np.sum((y - y.mean()) ** 2), 1e-12)
    a, b = np.abs(c)
    return {"c1": c[0], "c2": c[1], "magnitude": float(np.hypot(*c)),
            "equality": float(min(a, b) / max(max(a, b), 1e-9)), "fit": float(r2)}


def main(indir="results/phase1_preds", out="results/fig4"):
    import os
    os.makedirs(out, exist_ok=True)
    rows = []
    for f in sorted(glob.glob(f"{indir}/fold*_preds.npz")):
        z = np.load(f, allow_pickle=True)
        ctrl = z["ctrl"]
        methods = sorted({k.split("|")[1] for k in z.files if k.startswith("pred|")})
        for c in z["test"]:
            a, b = c.split("+")
            dA, dB, dT = z[f"true|{a}"] - ctrl, z[f"true|{b}"] - ctrl, z[f"true|{c}"] - ctrl
            # informative genes: changed by either single or by the double (fixed from truth)
            mask = (np.abs(dA) > 0.1) | (np.abs(dB) > 0.1) | (np.abs(dT) > 0.1)
            if mask.sum() < 10:
                continue
            rows.append({"cond": c, "method": "truth", **gi(dA, dB, dT, mask)})
            for m in methods:
                dP = z[f"pred|{m}|{c}"] - ctrl
                rows.append({"cond": c, "method": m, **gi(dA, dB, dP, mask)})
    r = pd.DataFrame(rows)
    r.to_csv(f"{out}/gi_measures.csv", index=False)
    t = r[r.method == "truth"].set_index("cond")
    lo, hi = t["magnitude"].quantile([1 / 3, 2 / 3])
    cats = {"synergy (high magnitude)": (t["magnitude"] >= hi, "magnitude", 1),
            "suppression (low magnitude)": (t["magnitude"] <= lo, "magnitude", -1),
            "epistasis (low equality)": (t["equality"] <= t["equality"].quantile(1 / 3), "equality", -1),
            "neomorphic (poor fit)": (t["fit"] <= t["fit"].quantile(1 / 3), "fit", -1)}
    res = []
    for m, g in r[r.method != "truth"].groupby("method"):
        g = g.set_index("cond").loc[t.index]
        row = {"method": m}
        for k in ["magnitude", "equality", "fit"]:
            row[f"spearman_{k}"] = spearmanr(g[k], t[k]).correlation
        for name, (lab, k, sign) in cats.items():
            row[f"AUROC {name}"] = roc_auc_score(lab.astype(int), sign * g[k]) if np.std(g[k]) > 1e-9 else 0.5
        res.append(row)
    res = pd.DataFrame(res).set_index("method").round(3)
    pd.set_option("display.width", 250)
    print(f"{len(t)} test pairs; truth magnitude tertiles {lo:.2f} / {hi:.2f}\n")
    print(res.to_string())
    res.to_csv(f"{out}/gi_scores.csv")


if __name__ == "__main__":
    main(*sys.argv[1:])
