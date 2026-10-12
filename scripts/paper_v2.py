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
nm = rd("new_methods.jsonl")
nm["slice"] = nm["slice"].astype(str)
nm = nm[nm.status == "ok"].drop_duplicates(["method", "dataset", "slice", "seed"], keep="last")
nm_std = nm[["dataset", "method", "slice", "seed", "ARI", "NMI", "time"]]
nm_rob = nm[["dataset", "method", "slice", "seed", "ARI_robust", "NMI_robust", "time"]].rename(
    columns={"ARI_robust": "ARI", "NMI_robust": "NMI"}).assign(method=lambda x: x.method + "+robust").dropna(subset=["ARI"])
d = pd.concat([a, b, e, g, nm_std, nm_rob], ignore_index=True)
d["slice"] = d["slice"].astype(str)
d = d[[c for c in ["dataset", "method", "slice", "seed", "ARI", "NMI", "time"] if c in d]]
d.loc[d.method == "histar_rerun", "method"] = "histar"
P = d.groupby(["dataset", "method", "slice"]).ARI.mean()
NAMES = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "anisost_single_gmm": "AnisoST",
         "pca_gmm": "PCA (non-spatial)", "histar": "HiSTaR", "histar+robust": "HiSTaR",
         "graphst": "GraphST", "graphst+robust": "GraphST", "graphst_refined": "GraphST (refined)",
         "banksy_l0.8": "BANKSY λ=0.8", "banksy_l0.8+robust": "BANKSY λ=0.8",
         "banksy_l0.2": "BANKSY λ=0.2", "banksy_l0.2+robust": "BANKSY λ=0.2", "spagcn": "SpaGCN"}
NEW = [("STAGATE", "stagate"), ("SEDR", "sedr"), ("SpaceFlow", "spaceflow"), ("NichePCA", "nichepca"), ("CCST", "ccst"),
       ("Spatial-MGCN", "spatial_mgcn"), ("DeepST", "deepst"), ("BASS", "bass"), ("BayesSpace", "bayesspace")]
# (label, standard-clustering method, robust-clustering method)
ROWS = [("Linear diffusion$^\\dagger$", None, "linear_diffusion"), ("AnisoST$^\\dagger$", "anisost_single_gmm", "anisost"),
        ("PCA, non-spatial$^\\dagger$", None, "pca_gmm"), ("BANKSY $\\lambda=0.8$", "banksy_l0.8", "banksy_l0.8+robust"),
        ("BANKSY $\\lambda=0.2$", "banksy_l0.2", "banksy_l0.2+robust"), ("HiSTaR", "histar", "histar+robust"),
        ("GraphST", "graphst", "graphst+robust"), ("SpaGCN", "spagcn", None)] + \
       [(lab, m, m + "+robust") for lab, m in NEW]
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
         ("linear_diffusion", "spagcn"), ("linear_diffusion", "anisost"), ("linear_diffusion", "pca_gmm")] + \
         [("linear_diffusion", m) for _, m in NEW if m not in ("bass", "bayesspace")] + \
         [("linear_diffusion", m + "+robust") for _, m in NEW if m not in ("bass", "bayesspace")] + \
         [("linear_diffusion", "bass")]
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

fig, axs = plt.subplots(1, 3, figsize=(7.4, 4.8), sharex=False)
for ax, ds in zip(axs, DS):
    rows = [r for r in ROWS if not (np.isnan(mean(ds, r[2])) and np.isnan(mean(ds, r[1])))]
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

# ---- lottery range per method (all methods with embeddings)
MN2 = {"histar": "HiSTaR", "graphst": "GraphST", "anisost": "AnisoST", **{m: l for l, m in NEW}}
lm = LT.groupby("method")["range"].agg(["mean", "max"]).sort_values("mean")
fig, ax = plt.subplots(figsize=(3.6, 0.28 * len(lm) + 0.8))
yy = np.arange(len(lm))
ax.barh(yy, lm["mean"], color=BLUE, height=0.55, label="mean over sections")
ax.scatter(lm["max"], yy, color=ORANGE, s=18, zorder=3, label="worst section")
ax.set_yticks(yy, [MN2.get(m, m) for m in lm.index]); ax.set_xlabel("ARI range over 20 single-start GMM fits")
ax.grid(axis="y", visible=False); ax.legend(frameon=False, fontsize=7, loc="lower right")
fig.savefig(f"{FIG}/v2_fig4_lottery_methods.png"); plt.close(fig)
out["lottery_by_method"] = {m: {"mean_range": round(float(r["mean"]), 3), "max_range": round(float(r["max"]), 3)} for m, r in lm.iterrows()}
json.dump(out, open(R("paper_numbers_v2.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ("pooled", "lottery_by_method")}, indent=1)[:5000])

# ------------------------------------------------------------------ LaTeX macros (every number in the text)
# results/paper_macros.tex is \input by paper/main.tex, so quoted numbers cannot be mistyped.
MAC = {}
def mac(name, val, dec=3):
    v = val if isinstance(val, str) else f"{val:.{dec}f}"
    v = v.replace("<", "\\ensuremath{<}")
    if v.startswith("-"): v = "\\ensuremath{-}" + v[1:]
    MAC[name] = v
MCN = {"linear_diffusion": "Lin", "anisost": "Aniso", "pca_gmm": "Pca", "histar": "Histar", "graphst": "Graphst",
       "graphst_refined": "GraphstRef", "banksy_l0.8": "BanksyHi", "banksy_l0.2": "BanksyLo", "spagcn": "Spagcn",
       "stagate": "Stagate", "sedr": "Sedr", "spaceflow": "Spaceflow", "nichepca": "Nichepca", "ccst": "Ccst",
       "spatial_mgcn": "Mgcn", "deepst": "Deepst", "bass": "Bass", "bayesspace": "Bayesspace"}
DSM = {"dlpfc": "Dlpfc", "starmap": "Starmap", "merfish": "Merfish"}
for ds in DS:
    for m, nme in MCN.items():
        v = out["means"][ds].get(m)
        if v is not None and not np.isnan(v):
            mac(f"mean{nme}{DSM[ds]}", v)
            rb = out["means"][ds].get(m + "+robust")
            if rb is not None and not np.isnan(rb): mac(f"robust{nme}{DSM[ds]}", rb)
# macro-average over the three datasets (equal weight per dataset)
for m, nme in MCN.items():
    vs = [out["means"][ds].get(m) for ds in DS]
    if all(v is not None and not np.isnan(v) for v in vs): mac(f"overall{nme}", float(np.mean(vs)))
# pooled linear-diffusion comparisons
pn = {"histar": "Histar", "histar+robust": "HistarRob", "graphst": "Graphst", "graphst+robust": "GraphstRob",
      "banksy_l0.8": "BanksyHi", "banksy_l0.8+robust": "BanksyHiRob", "spagcn": "Spagcn", "anisost": "Aniso", "pca_gmm": "Pca",
      "bass": "Bass", **{m: MCN[m] for _, m in NEW}, **{m + "+robust": MCN[m] + "Rob" for _, m in NEW}}
for k, v in out["pooled"].items():
    y = k.split("_vs_", 1)[1]
    if y in pn:
        mac(f"dLin{pn[y]}", v["delta"]); mac(f"winsLin{pn[y]}", str(v["wins"])); mac(f"pLin{pn[y]}", v["p_holm"] if v["p_holm"] >= 0.001 else "<0.001", 3) \
            if isinstance(v["p_holm"], str) else mac(f"pLin{pn[y]}", ("%.3f" % v["p_holm"]) if v["p_holm"] >= 0.001 else "<0.001")
sig = [k for k, v in out["pooled"].items() if v["p_holm"] < 0.05 and v["delta"] > 0]
mac("nPooled", str(len(out["pooled"]))); mac("nPooledSig", str(len(sig)))
mac("nPooledNotSig", str(len(out["pooled"]) - len(sig)))
# robust-vs-standard clustering gain for every method that has both
Gx = {}
for m0 in ["histar", "graphst", "anisost_single_gmm", "banksy_l0.8", "banksy_l0.2"] + [m for _, m in NEW]:
    m1 = {"anisost_single_gmm": "anisost"}.get(m0, m0 + ("" if m0 in ("histar", "graphst") and False else "+robust"))
    if m0 in S and m1 in S:
        s2 = S[[m0, m1]].dropna(); diff = s2[m1] - s2[m0]
        Gx[m0] = (float(diff.mean()), int((diff > 0).sum()), len(s2), float(wilcoxon(s2[m1], s2[m0]).pvalue))
out["clustering_gain_all"] = {k: {"delta": round(v[0], 3), "wins": v[1], "n": v[2], "p": round(v[3], 4)} for k, v in Gx.items()}
GN = {"histar": "Histar", "graphst": "Graphst", "anisost_single_gmm": "Aniso", "banksy_l0.8": "BanksyHi", "banksy_l0.2": "BanksyLo",
      **{m: MCN[m] for _, m in NEW}}
for k, v in Gx.items():
    mac(f"gain{GN[k]}", f"{v[0]:+.3f}"); mac(f"gainWins{GN[k]}", str(v[1])); mac(f"gainN{GN[k]}", str(v[2]))
    mac(f"gainP{GN[k]}", f"{v[3]:.3f}" if v[3] >= 0.001 else "<0.001")
mac("nGainPos", str(sum(v[0] > 0.005 for v in Gx.values()))); mac("nGainNeg", str(sum(v[0] < -0.005 for v in Gx.values())))
mac("nGainTot", str(len(Gx)))
# sklearn lottery
mac("lotN", str(len(LT))); mac("lotNMethods", str(LT.method.nunique()))
mac("lotMean", float(LT["range"].mean()), 2); mac("lotMax", float(LT["range"].max()), 2)
mac("lotOracle", float((LT["max"] - LT["mean"]).mean()), 2)
bm = LT.groupby("method")["range"].mean()
mac("lotLo", float(bm.min()), 2); mac("lotHi", float(bm.max()), 2)
mac("lotLoName", MN2[bm.idxmin()]); mac("lotHiName", MN2[bm.idxmax()])
wr = LT.loc[LT["range"].idxmax()]
mac("lotWorstMethod", MN2[wr.method]); mac("lotWorstSection", f"{wr.dataset} {wr.slice}")
for m in MN2:
    if m in bm.index:
        mac(f"lotMean{MCN.get(m, m)}", float(bm[m]), 2); mac(f"lotMax{MCN.get(m, m)}", float(LT[LT.method == m]["range"].max()), 2)
        mac(f"lotBestLL{MCN.get(m, m)}", float(LT[LT.method == m].best_ll.mean()), 3)
        mac(f"lotSingle{MCN.get(m, m)}", float(LT[LT.method == m]["mean"].mean()), 3)
bl = LT.assign(g=LT.best_ll - LT["mean"]).groupby("method").g.mean()
mac("lotBLUp", str(int((bl > 0.005).sum()))); mac("lotBLDown", str(int((bl < -0.005).sum())))
for ds in DS:
    gd = LT[LT.dataset == ds]
    mac(f"rho{DSM[ds]}Lo", float(gd.groupby("method").rho.median().min()), 2)
    mac(f"rho{DSM[ds]}Hi", float(gd.groupby("method").rho.median().max()), 2)
    mac(f"rho{DSM[ds]}Med", float(gd.rho.median()), 2)
    mac(f"rhoNeg{DSM[ds]}", str(int((gd.groupby("method").rho.median() < 0).sum())))
# mclust
if mf:
    mac("mcN", str(base.reset_index().groupby(["dataset", "method", "slice"]).ngroups))
    mac("mcNMethods", str(base.reset_index().method.nunique()))
    for kind, kn in [("permute", "Perm"), ("jitter1pct", "Jit")]:
        q = agg.reset_index(); q = q[q.kind == kind]
        mac(f"mc{kn}Mean", float(q.rng.mean()), 2); mac(f"mc{kn}Max", float(q.rng.max()), 2)
        mac(f"mc{kn}Frac", str(round(100 * float(q.changed.mean()))))
        for ds in DS:
            qd = q[q.dataset == ds]; mac(f"mc{kn}Mean{DSM[ds]}", float(qd.rng.mean()), 2)
        # share of embeddings whose range exceeds 0.1
        mac(f"mc{kn}Gt", str(round(100 * float((q.rng > 0.1).mean()))))
    j2 = base.reset_index().merge(LT, on=["dataset", "method", "slice"], suffixes=("", "_lt"))
    mac("mcDefault", float(j2.ARI.mean()), 2); mac("mcBest", float(j2.best_ll.mean()), 2)
    mac("mcLLfrac", str(round(100 * float((j2.loglik_per_obs >= j2.best_ll_value - 1e-3).mean()))))
    mac("mcWorse", str(round(100 * float((j2.ARI < j2.best_ll - 0.02).mean()))))
    mac("mcBetter", str(round(100 * float((j2.ARI > j2.best_ll + 0.02).mean()))))
    mac("mcNJ", str(len(j2)))
# Spatial-MGCN label-selected epoch
sm = nm[nm.method == "spatial_mgcn"].assign(g=lambda x: x.ARI_label_selected_epoch - x.ARI)
mac("mgcnLeak", float(sm.g.mean()), 3)
for ds in DS:
    mac(f"mgcnLeak{DSM[ds]}", float(sm[sm.dataset == ds].g.mean()), 2)
    mac(f"mgcnOracle{DSM[ds]}", float(sm[sm.dataset == ds].ARI_label_selected_epoch.mean()), 3)
    mac(f"mgcnFinal{DSM[ds]}", float(sm[sm.dataset == ds].ARI.mean()), 3)
mac("mgcnLeakN", str(len(sm)))
# runtime / memory from the unified runner
ur = [json.loads(l) for l in open(R("benchmark_runs.jsonl"))]
ur = {x["id"]: x for x in ur}.values()
RS = pd.DataFrame([dict(method=x["method"], dataset=x["dataset"], t=x["resources"].get("wall_s"), mem=x["resources"].get("peak_rss_gb"),
                        kwh=x["resources"].get("energy_kwh")) for x in ur if x["status"] == "ok"])
rsm = RS.groupby("method").agg(t=("t", "median"), mem=("mem", "max"), kwh=("kwh", "sum"))
for m, r_ in rsm.iterrows():
    nme = MCN.get(m, m)
    mac(f"timeMed{nme}", f"{r_.t:.0f}"); mac(f"memMax{nme}", f"{r_.mem:.1f}")
tm = nm.groupby("method").time.median()
for m, v in tm.items(): mac(f"timePilot{MCN.get(m, m)}", f"{v:.0f}")
out["resources"] = {"unified": {m: {"median_s": round(float(r_.t), 1), "max_mem_gb": round(float(r_.mem), 2), "kwh_total": float(r_.kwh)} for m, r_ in rsm.iterrows()},
                    "pilot_median_s": {m: round(float(v), 1) for m, v in tm.items()}}

# resource table: median wall-clock per section (all runs, one CPU thread unless noted) and peak memory (standardised runner)
RN = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "banksy_l0.8": "BANKSY", "histar": "HiSTaR",
      "graphst": "GraphST", "spagcn": "SpaGCN", **{m: l for l, m in NEW}}
tt = RS.groupby("method").t.median()
mem_m = RS.groupby("method").mem.max()
rows_ = ["\\begin{tabular}{lrr}", "\\toprule", "Method & Median time per section (s) & Peak memory (GB) \\\\", "\\midrule"]
for m, lab in RN.items():
    t_ = tt.get(m, np.nan); me_ = mem_m.get(m, np.nan)
    if np.isnan(t_): continue
    rows_.append(f"{lab} & {'--' if np.isnan(t_) else f'{t_:.0f}'} & {'--' if np.isnan(me_) else f'{me_:.1f}'} \\\\")
rows_ += ["\\bottomrule", "\\end{tabular}"]
open(R("table_resources.tex"), "w").write("\n".join(rows_) + "\n")

# best method per dataset over both protocols
LAB = {"linear_diffusion": "linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "graphst": "GraphST",
       "banksy_l0.8": "BANKSY $\\lambda=0.8$", "banksy_l0.2": "BANKSY $\\lambda=0.2$", "spagcn": "SpaGCN", "graphst_refined": "GraphST (refined)",
       **{m: l for l, m in NEW}}
for ds in DS:
    cand = {k: v for k, v in out["means"][ds].items() if not np.isnan(v)}
    k = max(cand, key=cand.get); base_k = k.replace("+robust", "").replace("anisost_single_gmm", "anisost")
    mac(f"best{DSM[ds]}", LAB.get(base_k, base_k)); mac(f"best{DSM[ds]}Val", cand[k])
    top = sorted(cand, key=cand.get, reverse=True)[:3]
# counts
mac("nSections", str(P.reset_index()[["dataset", "slice"]].drop_duplicates().shape[0]))
mac("nMethodsPub", "13")
open(R("paper_macros.tex"), "w").write("% generated by scripts/paper_v2.py: do not edit\n" +
    "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(MAC.items())))
json.dump(out, open(R("paper_numbers_v2.json"), "w"), indent=1)
print(len(MAC), "macros written")
