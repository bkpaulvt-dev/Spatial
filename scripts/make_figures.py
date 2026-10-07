"""Figures and tables for docs/AnisoST.md (reads results/*.jsonl and results/cache)."""
import json, os, sys, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
warnings.filterwarnings("ignore")
R = lambda f: os.path.join(ROOT, "results", f)
FIG = os.path.join(ROOT, "docs", "figures"); os.makedirs(FIG, exist_ok=True)

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#a3a29c"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "savefig.dpi": 300, "savefig.bbox": "tight", "font.family": "DejaVu Sans"})

a = pd.read_json(R("anisost_main.jsonl"), lines=True); b = pd.read_json(R("dlpfc_main.jsonl"), lines=True)
d = pd.concat([a, b], ignore_index=True); d["slice"] = d["slice"].astype(str)
NAMES = {"anisost": "AnisoST (ours)", "linear_diffusion": "Linear diffusion + robust GMM",
         "anisost_single_gmm": "AnisoST, single-start GMM", "histar": "HiSTaR",
         "histar_deterministic": "HiSTaR (deterministic eval)", "hicast": "HiCAST", "pca_gmm": "PCA + GMM (non-spatial)"}
donor = lambda s: 1 if s < "151600" else (2 if s < "151673" else 3)
slices = sorted(d.slice.unique())
P = d.groupby(["method", "slice"]).ARI.mean().unstack(0)

# ---- Table 1 (markdown) ----
lines = ["| Method | Median ARI | Mean ARI | Mean ARI donor 1 (tuning) | Mean ARI donors 2+3 (held out) | Median NMI | Seed SD | Δ vs AnisoST (Wilcoxon p) | Time / slice |",
         "|---|---|---|---|---|---|---|---|---|"]
for m in ["anisost", "linear_diffusion", "anisost_single_gmm", "histar", "histar_deterministic", "hicast", "pca_gmm"]:
    x = d[d.method == m]; held = x[x.slice.map(donor) > 1]; tun = x[x.slice.map(donor) == 1]
    sd = x.groupby("slice").ARI.std().mean()
    if m == "anisost": cmp = "—"
    else:
        diff = P[m] - P["anisost"]; cmp = f"{diff.mean():+.3f} (p = {wilcoxon(P['anisost'], P[m]).pvalue:.3f})"
    lines.append(f"| {NAMES[m]} | {x.ARI.median():.3f} | {x.ARI.mean():.3f} | {tun.ARI.mean():.3f} | {held.ARI.mean():.3f} | "
                 f"{x.NMI.median():.3f} | {sd:.3f} | {cmp} | {x.time.median():.1f} s |")
per = ["| Slice | Donor | AnisoST | Linear diff. | HiSTaR | HiCAST | PCA+GMM |", "|---|---|---|---|---|---|---|"]
S = d.groupby(["method", "slice"]).ARI.agg(["mean", "std"])
for s in slices:
    row = [s, str(donor(s))]
    best = max(P.loc[s, m] for m in ["anisost", "linear_diffusion", "histar", "hicast", "pca_gmm"])
    for m in ["anisost", "linear_diffusion", "histar", "hicast", "pca_gmm"]:
        mu, sd = S.loc[(m, s)]; t = f"{mu:.3f} ± {sd:.3f}"
        row.append(f"**{t}**" if np.isclose(mu, best) else t)
    per.append("| " + " | ".join(row) + " |")
open(R("anisost_tables.md"), "w").write("\n".join(lines) + "\n\n" + "\n".join(per) + "\n")
print("\n".join(lines)); print("\n".join(per))

# ---- Fig 1: per-slice ARI, AnisoST vs HiSTaR vs HiCAST ----
fig, ax = plt.subplots(figsize=(7.2, 3.0))
x = np.arange(len(slices))
for off, m, c in [(-0.22, "anisost", BLUE), (0, "histar", ORANGE), (0.22, "hicast", AQUA)]:
    sub = d[d.method == m]
    for i, s in enumerate(slices):
        v = sub[sub.slice == s].ARI.values
        ax.scatter(np.full(len(v), i + off), v, s=10, color=c, alpha=0.45, linewidths=0)
    ax.scatter(x + off, P[m].loc[slices], s=36, color=c, edgecolor="white", linewidth=1.2, label=NAMES[m], zorder=3)
for xv in (3.5, 7.5): ax.axvline(xv, color=GRID, lw=1)
for i, t in enumerate(["Donor 1 (tuning)", "Donor 2 (held out)", "Donor 3 (held out)"]):
    ax.text(1.5 + 4 * i, 0.93, t, ha="center", color=INK2, fontsize=8)
ax.set_xticks(x, slices, rotation=45); ax.set_ylabel("ARI"); ax.set_ylim(0.2, 0.97)
ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.02))
fig.savefig(f"{FIG}/fig1_per_slice_ari.png"); plt.close(fig)

# ---- Fig 2: ablation (mean ARI over slices, 95% bootstrap CI) ----
order = ["pca_gmm", "hicast", "histar", "anisost_single_gmm", "linear_diffusion", "anisost"]
rng = np.random.default_rng(0)
fig, ax = plt.subplots(figsize=(5.2, 2.6))
for i, m in enumerate(order):
    v = P[m].values; bs = [rng.choice(v, len(v)).mean() for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    ax.barh(i, v.mean(), height=0.6, color=BLUE if m == "anisost" else GRAY)
    ax.plot([lo, hi], [i, i], color=INK, lw=1)
    ax.text(hi + 0.01, i, f"{v.mean():.3f}", va="center", color=INK, fontsize=8)
ax.set_yticks(range(len(order)), [NAMES[m] for m in order]); ax.set_xlabel("Mean ARI over 12 slices (95% bootstrap CI)")
ax.set_xlim(0, 0.7); ax.grid(axis="y", visible=False)
fig.savefig(f"{FIG}/fig2_ablation.png"); plt.close(fig)

# ---- Fig 3: sensitivity sweep ----
if os.path.exists(R("anisost_sweep.jsonl")):
    w = pd.read_json(R("anisost_sweep.jsonl"), lines=True)
    w["param"] = w.method.str.split("=").str[0]; w["value"] = w.method.str.split("=").str[1].astype(float)
    params = ["steps", "q", "k", "n_pcs", "alpha"]; default = {"steps": 10, "q": 0.5, "k": 6, "n_pcs": 30, "alpha": 0.5}
    labels = {"steps": "Diffusion steps T", "q": "Edge-scale quantile q", "k": "Neighbours k",
              "n_pcs": "Number of PCs", "alpha": "Step size α"}
    fig, axs = plt.subplots(1, 5, figsize=(8.6, 2.1), sharey=True)
    fig.subplots_adjust(wspace=0.35)
    hist = d[d.method == "histar"].ARI.mean()
    for ax, p in zip(axs, params):
        g = w[w.param == p].groupby("value").ARI.mean()
        ax.axhline(hist, color=ORANGE, lw=1, ls="--")
        ax.plot(g.index, g.values, color=BLUE, lw=2, marker="o", ms=4)
        ax.scatter([default[p]], [g.loc[default[p]]], s=60, facecolor="white", edgecolor=BLUE, zorder=3, lw=1.5)
        ax.set_xlabel(labels[p], fontsize=8)
        if p == "steps":
            ax.set_xscale("log"); ax.minorticks_off(); ax.set_xticks([2, 5, 10, 20, 50], ["2", "5", "10", "20", "50"])
    axs[0].set_ylabel("Mean ARI"); axs[0].set_ylim(0.38, 0.6)
    axs[0].text(2, hist + 0.005, "HiSTaR", color=ORANGE, fontsize=7)
    fig.savefig(f"{FIG}/fig3_sensitivity.png"); plt.close(fig)

# ---- Fig 4: boundary vs interior ----
if os.path.exists(R("anisost_boundary.jsonl")):
    bd = pd.read_json(R("anisost_boundary.jsonl"), lines=True)
    g = bd.groupby(["slice", "diffusion"])[["acc_boundary", "acc_interior"]].mean().unstack()
    fig, axs = plt.subplots(1, 2, figsize=(5.4, 2.6), sharey=True)
    for ax, col, t in [(axs[0], "acc_boundary", "Boundary spots"), (axs[1], "acc_interior", "Interior spots")]:
        for s in g.index:
            ax.plot([0, 1], [g.loc[s, (col, "linear")], g.loc[s, (col, "anisotropic")]], color=GRAY, lw=1)
        ax.scatter(np.zeros(len(g)), g[(col, "linear")], color=GRAY, s=14, zorder=3)
        ax.scatter(np.ones(len(g)), g[(col, "anisotropic")], color=BLUE, s=14, zorder=3)
        diff = g[(col, "anisotropic")] - g[(col, "linear")]
        ax.set_title(f"{t}\nΔ = {diff.mean():+.3f}, p = {wilcoxon(diff).pvalue:.3f}", fontsize=8.5, color=INK)
        ax.set_xticks([0, 1], ["Linear", "Anisotropic"]); ax.set_xlim(-0.3, 1.3); ax.grid(axis="x", visible=False)
    axs[0].set_ylabel("Accuracy (Hungarian-matched)")
    fig.savefig(f"{FIG}/fig4_boundary.png"); plt.close(fig)

# ---- Fig 5: spatial maps for 151673 ----
from anisost import AnisoST
from benchmark_anisost import N_CLUSTERS
from scipy.optimize import linear_sum_assignment
s = "151673"; z = np.load(R(f"cache/{s}.npz"), allow_pickle=True); X, C, y = z["X"], z["coords"], z["labels"]
LAY = ["Layer1", "Layer2", "Layer3", "Layer4", "Layer5", "Layer6", "WM"]
cmap = plt.get_cmap("viridis", 7)
keep = np.array([isinstance(v, str) for v in y])
def matched(p):
    M = np.array([[np.sum((p[keep] == c) & (y[keep] == l)) for l in LAY] for c in range(7)])
    r, c = linear_sum_assignment(-M); mp = dict(zip(r, c)); return np.array([mp[v] for v in p])
from sklearn.metrics import adjusted_rand_score
panels = [("Manual annotation", np.array([LAY.index(v) if isinstance(v, str) else -1 for v in y]), None)]
for diff, name in [("none", "PCA + GMM"), ("linear", "Linear diffusion"), ("anisotropic", "AnisoST")]:
    p = AnisoST(diffusion=diff, seed=0).fit_predict(X, C, 7)
    panels.append((name, matched(p), adjusted_rand_score(y[keep], p[keep])))
fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.3))
for ax, (t, lab, ari) in zip(axs, panels):
    m = lab >= 0
    ax.scatter(C[~m, 0], -C[~m, 1], s=1.2, color=GRID, linewidths=0)
    ax.scatter(C[m, 0], -C[m, 1], s=1.2, c=lab[m], cmap=cmap, vmin=-0.5, vmax=6.5, linewidths=0)
    ax.set_title(t if ari is None else f"{t}\nARI = {ari:.3f}", fontsize=8.5, color=INK)
    ax.set_aspect("equal"); ax.axis("off")
handles = [plt.Line2D([], [], marker="o", ls="", color=cmap(i), ms=5, label=l.replace("Layer", "L")) for i, l in enumerate(LAY)]
fig.legend(handles=handles, ncol=7, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.05), fontsize=8)
fig.savefig(f"{FIG}/fig5_spatial_151673.png"); plt.close(fig)
print("figures written")
