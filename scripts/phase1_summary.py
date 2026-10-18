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
    seed_spread = None
    if "seed" in r and r["seed"].notna().any():
        # learned methods have one row per seed: spread of the per-seed median, then average seeds
        s = r[r["seed"].notna()]
        seed_spread = s.groupby(["method", "seed"])[mets].median().groupby("method").std()
        sel_counts = s[s.method == ours].groupby(["fold", "seed"])["selected"].first().value_counts()
        r = r.groupby(["method", "fold", "cond"], as_index=False)[mets].mean()
        r["selected"] = None
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
            both = x.notna() & y.notna()          # e.g. GEARS cannot score pairs outside its graph
            x, y = x[both], y[both]
            d = (x - y) if k in HIGHER else (y - x)       # positive = ours better
            if np.allclose(d, 0):
                continue
            p = wilcoxon(d, alternative="greater").pvalue
            tests.append({"baseline": b, "metric": k, "n": int(both.sum()), "median_gain": float(np.median(d)),
                          "win_rate": float(np.mean(d > 0)), "p": p})
    t = pd.DataFrame(tests)
    t["q_BH"] = bh(t["p"])
    print(f"\nPaired one-sided Wilcoxon, {ours} better than baseline (positive gain = better)\n")
    print(t.round(4).to_string(index=False))
    if seed_spread is not None:
        print("\nSD across seeds of the per-seed median\n")
        print(seed_spread.round(4).to_string())
        seed_spread.to_csv(f"{outdir}/seed_sd.csv")
        print("\nconfig selected on validation, (fold, seed) counts:", sel_counts.to_dict())
    else:
        sel = r[r.method == ours].groupby("fold")["selected"].first()
        print("\nconfig selected on validation per fold:", sel.to_dict())
    summ.to_csv(f"{outdir}/summary.csv")
    t.to_csv(f"{outdir}/tests.csv", index=False)


if __name__ == "__main__":
    main(*sys.argv[1:])
