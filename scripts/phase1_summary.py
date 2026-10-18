"""Summarise Phase 1: medians, means, bootstrap CIs, paired Wilcoxon tests with BH correction."""
import glob, json, sys
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HIGHER = ["pearson_de20", "pearson_all", "dir_acc_de20", "systema_pearson_de20", "resid_corr_top20"]
LOWER = ["mse_de20", "mse_all", "resid_mse_top20", "resid_mse_all"]


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[o] = np.minimum(q, 1)
    return out


def main(outdir="results/phase1", ours="cipher_selected"):
    r = pd.concat([pd.read_json(f, lines=True) for f in sorted(glob.glob(f"{outdir}/fold*.jsonl"))])
    mets = HIGHER + LOWER
    rng = np.random.default_rng(0)
    rows = []
    for m, g in r.groupby("method"):
        row = {"method": m, "n": len(g)}
        for k in mets:
            v = g[k].values
            bs = [np.mean(rng.choice(v, len(v))) for _ in range(1000)]
            row[k] = f"{np.median(v):.3f} / {np.mean(v):.3f} [{np.percentile(bs, 2.5):.3f}, {np.percentile(bs, 97.5):.3f}]"
        rows.append(row)
    summ = pd.DataFrame(rows).set_index("method")
    print("median / mean [95% bootstrap CI of mean]\n")
    print(summ.T.to_string())
    # paired tests: ours vs each baseline
    piv = {k: r.pivot_table(index=["fold", "cond"], columns="method", values=k) for k in mets}
    tests = []
    for b in sorted(r.method.unique()):
        if b.startswith("cipher"):
            continue
        for k in mets:
            x, y = piv[k][ours], piv[k][b]
            d = (x - y) if k in HIGHER else (y - x)       # positive = ours better
            if np.allclose(d, 0):
                continue
            p = wilcoxon(d, alternative="greater").pvalue
            tests.append({"baseline": b, "metric": k, "median_gain": float(np.median(d)),
                          "win_rate": float(np.mean(d > 0)), "p": p})
    t = pd.DataFrame(tests)
    t["q_BH"] = bh(t["p"])
    print(f"\nPaired one-sided Wilcoxon, {ours} better than baseline (positive gain = better)\n")
    print(t.round(4).to_string(index=False))
    sel = r[r.method == ours].groupby("fold")["selected"].first()
    print("\nconfig selected on validation per fold:", sel.to_dict())
    summ.to_csv(f"{outdir}/summary.csv")
    t.to_csv(f"{outdir}/tests.csv", index=False)


if __name__ == "__main__":
    main(*sys.argv[1:])
