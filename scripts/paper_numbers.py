"""All numbers quoted in paper/main.tex, computed from results/*.jsonl -> results/paper_numbers.json."""
import json, os
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, spearmanr

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda f: os.path.join(ROOT, "results", f)
out = {}

# ---- clustering lottery ----
L = [json.loads(l) for l in open(R("clustering_lottery.jsonl"))]
rows = []
for r in L:
    a = np.array([f["ARI"] for f in r["fits"]]); ll = np.array([f["ll"] for f in r["fits"]])
    rows.append({"method": r["method"], "slice": r["slice"], "min": a.min(), "max": a.max(), "range": a.max() - a.min(),
                 "sd": a.std(ddof=1), "mean": a.mean(), "median": np.median(a), "best_ll": r["ARI_bestll"],
                 "std3": r["ARI_standard3"], "rho": spearmanr(ll, a).statistic,
                 "pct_best_ll": (a <= r["ARI_bestll"]).mean()})
lt = pd.DataFrame(rows)
for m, g in lt.groupby("method"):
    out[f"lottery_{m}"] = {k: round(float(v), 3) for k, v in {
        "mean_range": g["range"].mean(), "max_range": g["range"].max(), "min_range": g["range"].min(),
        "mean_sd": g.sd.mean(), "mean_single": g["mean"].mean(), "mean_oracle_max": g["max"].mean(),
        "mean_best_ll": g.best_ll.mean(), "mean_std3": g.std3.mean(), "median_rho": g.rho.median(),
        "frac_rho_pos": (g.rho > 0).mean(), "oracle_minus_single": (g["max"] - g["mean"]).mean()}.items()}
lt.round(3).to_csv(R("clustering_lottery_summary.csv"), index=False)

# ---- main benchmark: per-slice means ----
d = pd.concat([pd.read_json(R(f), lines=True) for f in ("anisost_main.jsonl", "dlpfc_main.jsonl", "baselines.jsonl")])
d["slice"] = d.slice.astype(str)
P = d.groupby(["method", "slice"]).ARI.mean().unstack(0)
held = [s for s in P.index if s > "151600"]
for m in P.columns:
    x = d[d.method == m]
    rng = np.random.default_rng(0); v = P[m].values
    bs = [rng.choice(v, len(v)).mean() for _ in range(5000)]
    out[f"bench_{m}"] = {"mean": round(float(v.mean()), 3), "median_slice": round(float(np.median(v)), 3),
                         "ci_lo": round(float(np.percentile(bs, 2.5)), 3), "ci_hi": round(float(np.percentile(bs, 97.5)), 3),
                         "held_out_mean": round(float(P.loc[held, m].mean()), 3),
                         "seed_sd": round(float(x.groupby("slice").ARI.std().mean()), 3),
                         "time_median_s": round(float(x.time.median()), 1)}
# primary comparisons vs AnisoST, Holm-corrected
comps = ["histar", "histar+robust", "banksy_l0.2+robust", "banksy_l0.8+robust", "linear_diffusion", "spagcn_refined", "hicast", "pca_gmm"]
pv = {m: wilcoxon(P["anisost"], P[m]).pvalue for m in comps}
order = sorted(comps, key=lambda m: pv[m]); holm = {}; run = 0
for i, m in enumerate(order):
    run = max(run, min(1, (len(comps) - i) * pv[m])); holm[m] = run
for m in comps:
    out[f"cmp_anisost_vs_{m}"] = {"delta": round(float((P["anisost"] - P[m]).mean()), 3), "wins": int((P["anisost"] > P[m]).sum()),
                                  "p": round(float(pv[m]), 4), "p_holm": round(float(holm[m]), 4)}
# clustering gain per method (paired over slices)
for a_, b_ in [("histar_rerun", "histar+robust"), ("anisost_single_gmm", "anisost"), ("banksy_l0.8", "banksy_l0.8+robust"), ("banksy_l0.2", "banksy_l0.2+robust")]:
    diff = P[b_] - P[a_]
    out[f"gain_{a_}"] = {"delta": round(float(diff.mean()), 3), "wins": int((diff > 0).sum()), "p": round(float(wilcoxon(P[b_], P[a_]).pvalue), 4)}
# boundary
bd = pd.read_json(R("anisost_boundary.jsonl"), lines=True)
g = bd.groupby(["slice", "diffusion"])[["acc_boundary", "acc_interior"]].mean().unstack()
for c in ("acc_boundary", "acc_interior"):
    diff = g[(c, "anisotropic")] - g[(c, "linear")]
    out[f"boundary_{c}"] = {"delta": round(float(diff.mean()), 3), "wins": int((diff > 0).sum()), "p": round(float(wilcoxon(diff).pvalue), 3)}
out["boundary_frac"] = [round(float(bd.frac_boundary.min()), 3), round(float(bd.frac_boundary.max()), 3)]
# sweep
w = pd.read_json(R("anisost_sweep.jsonl"), lines=True)
gm = w.groupby("method").ARI.mean()
out["sweep"] = {"n_settings": int(len(gm)), "min": round(float(gm.min()), 3), "max": round(float(gm.max()), 3)}
json.dump(out, open(R("paper_numbers.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
