"""Numbers, tables and figures for the multi-dataset manuscript (paper/main.tex).

Inputs : results/{anisost_main,dlpfc_main,baselines,extra,graphst,clustering_lottery}.jsonl,
         results/mclust_lottery_*.csv
Outputs: results/paper_numbers_v2.json, results/table_main.tex, docs/figures/v2_*.png
"""
import glob, json, os, sys, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon, spearmanr

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
R = lambda f: os.path.join(ROOT, "results", f)
FIG = os.path.join(ROOT, "docs", "figures")
INK, INK2, GRID, GRAY = "#0b0b0b", "#52514e", "#e4e3df", "#a3a29c"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "savefig.dpi": 300,
                     "savefig.bbox": "tight", "font.family": "DejaVu Sans"})
DS = ["dlpfc", "starmap", "merfish"]
DSN = {"dlpfc": "DLPFC (Visium)", "starmap": "STARmap mPFC", "merfish": "MERFISH hypothalamus"}
out = {}

# ------------------------------------------------------------------ benchmark table
def rd(f):
    return pd.read_json(R(f), lines=True) if os.path.exists(R(f)) else pd.DataFrame()
a = rd("anisost_main.jsonl").assign(dataset="dlpfc")
b = rd("baselines.jsonl").assign(dataset="dlpfc")
e = rd("extra.jsonl"); g = rd("graphst.jsonl")
d = pd.concat([a, b, e, g], ignore_index=True)
d["slice"] = d["slice"].astype(str)
d = d[[c for c in ["dataset", "method", "slice", "seed", "ARI", "NMI", "time"] if c in d]]
d.loc[d.method == "histar_rerun", "method"] = "histar"
P = d.groupby(["dataset", "method", "slice"]).ARI.mean()
NAMES = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "anisost_single_gmm": "AnisoST",
         "pca_gmm": "PCA (non-spatial)", "histar": "HiSTaR", "histar+robust": "HiSTaR",
         "graphst": "GraphST", "graphst+robust": "GraphST", "graphst_refined": "GraphST (refined)",
         "banksy_l0.8": "BANKSY λ=0.8", "banksy_l0.8+robust": "BANKSY λ=0.8",
         "banksy_l0.2": "BANKSY λ=0.2", "banksy_l0.2+robust": "BANKSY λ=0.2", "spagcn": "SpaGCN"}
# (label, standard-clustering method, robust-clustering method)
ROWS = [("Linear diffusion$^\\dagger$", None, "linear_diffusion"), ("AnisoST$^\\dagger$", "anisost_single_gmm", "anisost"),
        ("PCA, non-spatial$^\\dagger$", None, "pca_gmm"), ("BANKSY $\\lambda=0.8$", "banksy_l0.8", "banksy_l0.8+robust"),
        ("BANKSY $\\lambda=0.2$", "banksy_l0.2", "banksy_l0.2+robust"), ("HiSTaR", "histar", "histar+robust"),
        ("GraphST", "graphst", "graphst+robust"), ("SpaGCN", "spagcn", None)]
def mean(ds, m):
    try: return float(P.loc[(ds, m)].mean())
    except KeyError: return np.nan
tab = ["\\begin{tabular}{l" + "cc" * len(DS) + "}", "\\toprule",
       " & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{DSN[x]}}}" for x in DS) + " \\\\",
       " & " + " & ".join(["Standard & Robust"] * len(DS)) + " \\\\", "\\midrule"]
for lab, m0, m1 in ROWS:
    cells = []
    for ds in DS:
        for m in (m0, m1):
            v = mean(ds, m) if m else np.nan
            cells.append("--" if np.isnan(v) else f"{v:.3f}")
    tab.append(lab + " & " + " & ".join(cells) + " \\\\")
tab += ["\\bottomrule", "\\end{tabular}"]
open(R("table_main.tex"), "w").write("\n".join(tab) + "\n")
out["means"] = {ds: {m: round(mean(ds, m), 3) for m in sorted(d[d.dataset == ds].method.unique())} for ds in DS}
out["seed_sd"] = {ds: {m: round(float(v), 3) for m, v in d[d.dataset == ds].groupby(["method", "slice"]).ARI.std()
                                                     .groupby("method").mean().items()} for ds in DS}
out["time_median_s"] = {ds: {m: round(float(v), 1) for m, v in d[d.dataset == ds].groupby("method").time.median().items()} for ds in DS}

# pooled section-level comparisons (20 sections), Holm-corrected
S = P.unstack("method")
pairs = [("linear_diffusion", "histar+robust"), ("linear_diffusion", "histar"), ("linear_diffusion", "graphst"),
         ("linear_diffusion", "graphst+robust"), ("linear_diffusion", "banksy_l0.8+robust"), ("linear_diffusion", "banksy_l0.8"),
         ("linear_diffusion", "spagcn"), ("linear_diffusion", "anisost"), ("linear_diffusion", "pca_gmm")]
pv = {}
for x, y in pairs:
    if x in S and y in S:
        s2 = S[[x, y]].dropna()
        pv[(x, y)] = (wilcoxon(s2[x], s2[y]).pvalue, float((s2[x] - s2[y]).mean()), int((s2[x] > s2[y]).sum()), len(s2))
order = sorted(pv, key=lambda k: pv[k][0]); run = 0; holm = {}
for i, k in enumerate(order):
    run = max(run, min(1, (len(pv) - i) * pv[k][0])); holm[k] = run
out["pooled"] = {f"{x}_vs_{y}": {"delta": round(v[1], 3), "wins": v[2], "n": v[3], "p": round(v[0], 4),
                                 "p_holm": round(holm[(x, y)], 4)} for (x, y), v in pv.items()}
# robust-vs-standard clustering, per method pooled
out["clustering_gain"] = {}
for m0, m1 in [("histar", "histar+robust"), ("graphst", "graphst+robust"), ("anisost_single_gmm", "anisost"),
               ("banksy_l0.8", "banksy_l0.8+robust"), ("banksy_l0.2", "banksy_l0.2+robust")]:
    if m0 in S and m1 in S:
        s2 = S[[m0, m1]].dropna(); diff = s2[m1] - s2[m0]
        out["clustering_gain"][m0] = {"delta": round(float(diff.mean()), 3), "wins": int((diff > 0).sum()), "n": len(s2),
                                      "p": round(float(wilcoxon(s2[m1], s2[m0]).pvalue), 4),
                                      "per_dataset": {ds: round(float(diff.loc[ds].mean()), 3) for ds in DS if ds in diff.index.get_level_values(0)}}

# ------------------------------------------------------------------ sklearn lottery
L = [json.loads(l) for l in open(R("clustering_lottery.jsonl"))]
lr = []
for r in L:
    x = np.array([f["ARI"] for f in r["fits"]]); ll = np.array([f["ll"] for f in r["fits"]])
    lr.append({"dataset": r.get("dataset", "dlpfc"), "method": r["method"], "slice": r["slice"], "range": x.max() - x.min(),
               "mean": x.mean(), "max": x.max(), "min": x.min(), "best_ll": r["ARI_bestll"], "best_ll_value": ll.max(),
               "rho": spearmanr(ll, x).statistic})
LT = pd.DataFrame(lr)
out["lottery"] = {f"{ds}/{m}": {k: round(float(v), 3) for k, v in {
    "mean_range": gg["range"].mean(), "max_range": gg["range"].max(), "mean_single": gg["mean"].mean(),
    "mean_oracle": gg["max"].mean(), "mean_best_ll": gg.best_ll.mean(), "median_rho": gg.rho.median(),
    "n": len(gg)}.items()} for (ds, m), gg in LT.groupby(["dataset", "method"])}
out["lottery_all"] = {"mean_range": round(float(LT["range"].mean()), 3), "max_range": round(float(LT["range"].max()), 3),
                      "oracle_minus_single": round(float((LT["max"] - LT["mean"]).mean()), 3),
                      "n_embeddings": len(LT)}

# ------------------------------------------------------------------ mclust perturbations
mf = [f for f in glob.glob(R("mclust_lottery_*.csv"))]
if mf:
    M = pd.concat([pd.read_csv(f) for f in mf]); M["slice"] = M["slice"].astype(str)
    base = M[M.kind == "base"].set_index(["dataset", "method", "slice"])
    pert = M[M.kind != "base"].dropna(subset=["ARI"])
    pert = pert.join(base[["ARI", "loglik_per_obs"]].rename(columns={"ARI": "base_ARI", "loglik_per_obs": "base_ll"}),
                     on=["dataset", "method", "slice"])
    pert["dARI"] = pert.ARI - pert.base_ARI
    agg = pert.groupby(["dataset", "method", "slice", "kind"]).agg(rng=("ARI", lambda v: v.max() - v.min()),
                                                                 maxabs=("dARI", lambda v: v.abs().max()),
                                                                 changed=("dARI", lambda v: (v.abs() > 0.05).mean()))
    out["mclust"] = {f"{ds}/{m}/{k}": {"mean_range": round(float(gg.rng.mean()), 3), "max_range": round(float(gg.rng.max()), 3),
                                        "frac_runs_dARI_gt_0.05": round(float(gg.changed.mean()), 3), "n_sections": len(gg)}
                     for (ds, m, k), gg in agg.reset_index().groupby(["dataset", "method", "kind"])}
    j = base.reset_index().merge(LT, on=["dataset", "method", "slice"])
    out["mclust_vs_sklearn"] = {"frac_mclust_ll_ge_best20": round(float((j.loglik_per_obs >= j.best_ll_value - 1e-3).mean()), 3),
                                "mean_ARI_mclust": round(float(j.ARI.mean()), 3), "mean_ARI_best20": round(float(j.best_ll.mean()), 3),
                                "n": len(j)}
    pert.to_csv(R("mclust_perturbations_long.csv"), index=False)
json.dump(out, open(R("paper_numbers_v2.json"), "w"), indent=1)

# ------------------------------------------------------------------ figures
slices = {ds: sorted(LT[LT.dataset == ds].slice.unique(), key=lambda s: float(s) if ds == "merfish" else s) for ds in DS}
methods = [m for m in ["histar", "graphst", "anisost"] if m in LT.method.unique()]
MN = {"histar": "HiSTaR", "graphst": "GraphST", "anisost": "AnisoST"}
mb = base.reset_index() if mf else None
fig, axs = plt.subplots(len(methods), 3, figsize=(7.4, 1.9 * len(methods) + 0.4), sharey=True,
                        gridspec_kw={"width_ratios": [len(slices[x]) + 1 for x in DS]}, squeeze=False)
for i, m in enumerate(methods):
    for jx, ds in enumerate(DS):
        ax = axs[i, jx]
        for r in L:
            if r["method"] != m or r.get("dataset", "dlpfc") != ds: continue
            k = slices[ds].index(r["slice"]); v = [f["ARI"] for f in r["fits"]]
            ax.plot([k, k], [min(v), max(v)], color=GRID, lw=5, solid_capstyle="round", zorder=1)
            ax.scatter(np.full(len(v), k), v, s=6, color=GRAY, zorder=2, linewidths=0)
            ax.scatter(k, r["ARI_bestll"], s=30, color=BLUE, edgecolor="white", lw=0.8, zorder=3)
            if mb is not None:
                q = mb[(mb.dataset == ds) & (mb.method == m) & (mb.slice == r["slice"])]
                if len(q): ax.scatter(k, q.ARI.iloc[0], s=30, facecolor="none", edgecolor=INK, lw=1.1, zorder=4)
        ax.set_xticks(range(len(slices[ds])), [s.replace("_control", "").replace("2018", "") for s in slices[ds]] if i == len(methods) - 1 else [],
                      rotation=60, fontsize=6.5)
        ax.set_xlim(-0.7, len(slices[ds]) - 0.3)
        if i == 0: ax.set_title(DSN[ds], fontsize=8.5, color=INK)
        if jx == 0: ax.set_ylabel(f"{MN[m]}\nARI")
h = [plt.Line2D([], [], marker="o", ls="", color=GRAY, ms=3.5, label="Single-start GMM (20 per section)"),
     plt.Line2D([], [], marker="o", ls="", color=BLUE, ms=5, label="Best log-likelihood of the 20"),
     plt.Line2D([], [], marker="o", ls="", mfc="none", mec=INK, ms=5, label="R mclust EEE (default)")]
fig.legend(handles=h, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.02), fontsize=7.5)
fig.subplots_adjust(hspace=0.25, wspace=0.08)
fig.savefig(f"{FIG}/v2_fig1_lottery.png"); plt.close(fig)

if mf:
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.4), sharey=True)
    for ax, ds in zip(axs, DS):
        for k_, m in enumerate(methods):
            for off, kind, c in [(-0.15, "jitter1pct", BLUE), (0.15, "permute", ORANGE)]:
                q = pert[(pert.dataset == ds) & (pert.method == m) & (pert.kind == kind)]
                if len(q):
                    jit = np.random.default_rng(0).uniform(-0.07, 0.07, len(q))
                    ax.scatter(k_ + off + jit, q.dARI, s=5, color=c, alpha=0.5, linewidths=0)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(range(len(methods)), [MN[m] for m in methods]); ax.set_title(DSN[ds], fontsize=8.5, color=INK)
        ax.grid(axis="x", visible=False)
    axs[0].set_ylabel("ARI change vs. unperturbed mclust")
    h = [plt.Line2D([], [], marker="o", ls="", color=BLUE, ms=4, label="Gaussian noise, 1% of feature SD"),
         plt.Line2D([], [], marker="o", ls="", color=ORANGE, ms=4, label="Row order permuted")]
    fig.legend(handles=h, ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.06), fontsize=7.5)
    fig.savefig(f"{FIG}/v2_fig2_mclust.png"); plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.9), sharex=False)
for ax, ds in zip(axs, DS):
    rows = [r for r in ROWS if not np.isnan(mean(ds, r[2] or r[1]))]
    for i, (lab, m0, m1) in enumerate(rows):
        v1 = mean(ds, m1) if m1 else np.nan; v0 = mean(ds, m0) if m0 else np.nan
        if m0 and m1: ax.plot([v0, v1], [i, i], color=GRAY, lw=1.4)
        if m0: ax.scatter(v0, i, color=GRAY, s=28, zorder=3)
        if m1: ax.scatter(v1, i, color=BLUE, s=28, zorder=3)
    ax.set_yticks(range(len(rows)), [r[0].replace("$^\\dagger$", "").replace("$\\lambda=", "λ=").replace("$", "") for r in rows] if ds == "dlpfc" else [])
    ax.set_title(DSN[ds], fontsize=8.5, color=INK); ax.set_xlabel("Mean ARI"); ax.grid(axis="y", visible=False)
    ax.invert_yaxis()
h = [plt.Line2D([], [], marker="o", ls="", color=GRAY, ms=5, label="Standard clustering (single mclust-style fit / method's own)"),
     plt.Line2D([], [], marker="o", ls="", color=BLUE, ms=5, label="20-start GMM, best likelihood")]
fig.legend(handles=h, ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.07), fontsize=7.5)
fig.savefig(f"{FIG}/v2_fig3_matched.png"); plt.close(fig)
print(json.dumps(out, indent=1)[:6000])
