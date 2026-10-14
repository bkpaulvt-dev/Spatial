"""Publication figures in NAR style (vector PDF + 600 dpi PNG; 17.5 cm double-column / 8.5 cm single-column widths).

Colours: three method families (fixed order, validated all-pairs with the dataviz validator): training-free baselines (blue),
graph / deep encoders (orange), classical statistical, neighbourhood and Bayesian methods (aqua). Single-hue sequential ramps for
magnitudes, blue-orange diverging pair with a neutral midpoint for signed quantities. Every mark is labelled (method names on the axes).

python scripts/make_figures_nar.py -> docs/figures/nar_fig*.pdf|png
"""
import json, os, glob, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda f: os.path.join(ROOT, "results", f)
OUT = os.path.join(ROOT, "docs", "figures")
CM = 1 / 2.54
INK, INK2, GRID, MUTE = "#0b0b0b", "#52514e", "#e4e3df", "#a3a29c"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.8, "legend.fontsize": 6.5, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                     "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
                     "savefig.bbox": "tight", "savefig.pad_inches": 0.03})
SEQ = LinearSegmentedColormap.from_list("seq", ["#f4f8fd", "#cfe1f6", "#8ab9ec", "#2a78d6", "#123f7a"])
DIV = LinearSegmentedColormap.from_list("div", ["#eb6834", "#f4b79e", "#eeede9", "#9dc3ee", "#2a78d6"])

LAB = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "graphst": "GraphST",
       "banksy_l0.8": "BANKSY λ=0.8", "banksy_l0.2": "BANKSY λ=0.2", "spagcn": "SpaGCN", "stagate": "STAGATE", "sedr": "SEDR",
       "spaceflow": "SpaceFlow", "nichepca": "NichePCA", "ccst": "CCST", "spatial_mgcn": "Spatial-MGCN", "deepst": "DeepST",
       "bass": "BASS", "bayesspace": "BayesSpace"}
FAMILY = {"linear_diffusion": 0, "anisost": 0, "pca_gmm": 0,
          "histar": 1, "graphst": 1, "spagcn": 1, "stagate": 1, "sedr": 1, "spaceflow": 1, "ccst": 1, "spatial_mgcn": 1, "deepst": 1,
          "banksy_l0.8": 2, "banksy_l0.2": 2, "nichepca": 2, "bass": 2, "bayesspace": 2}
FCOL = [BLUE, ORANGE, AQUA]
FNAME = ["Training-free baselines", "Graph / deep encoders", "Statistical, neighbourhood, Bayesian"]
DSN = {"dlpfc": "DLPFC (Visium)", "starmap": "STARmap", "merfish": "MERFISH"}
DCOL = {"dlpfc": BLUE, "starmap": ORANGE, "merfish": AQUA}

cs = json.load(open(R("stats_cluster_aware.json")))
comp = {k.split("/")[1]: v for k, v in cs["comparisons"].items() if k.startswith("standard/")}
means = cs["means_standard"]; meansr = cs["means_robust"]; rank = cs["ranking"]


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"))
    plt.close(fig)


def panel(ax, letter, dx=-0.0, dy=1.02):
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="right")


def family_legend(ax, loc="lower right", ncol=1, **kw):
    h = [Line2D([], [], marker="o", ls="", color=FCOL[i], ms=4.5, label=FNAME[i]) for i in range(3)]
    return ax.legend(handles=h, frameon=False, loc=loc, ncol=ncol, handletextpad=0.2, borderaxespad=0.2, **kw)


# ---------------------------------------------------------------- Figure 2: accuracy
def fig_accuracy():
    ms = [m for m in LAB if m != "bayesspace" and m in means and len(means[m]) == 3]
    overall = {m: np.mean([means[m][d] for d in DSN]) for m in ms}
    ms.sort(key=lambda m: -overall[m])
    n = len(ms); y = np.arange(n)[::-1]
    fig = plt.figure(figsize=(17.5 * CM, 8.4 * CM))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.25, 0.95], wspace=0.07, left=0.125, right=0.995, top=0.90, bottom=0.12)
    ax0, ax1, ax2 = [fig.add_subplot(gs[0, i]) for i in range(3)]
    # a: heatmap of mean ARI
    A = np.array([[means[m][d] for d in DSN] for m in ms])
    ax0.imshow(A, cmap=SEQ, vmin=0.1, vmax=0.75, aspect="auto", extent=[-0.5, 2.5, -0.5, n - 0.5])
    for i, m in enumerate(ms):
        for j, d in enumerate(DSN):
            v = A[i, j]; ax0.text(j, n - 1 - i, f"{v:.2f}", ha="center", va="center", fontsize=6.3, color="white" if v > 0.5 else INK)
    ax0.set_xticks(range(3), ["DLPFC", "STARmap", "MERFISH"]); ax0.xaxis.tick_top(); ax0.tick_params(length=0)
    ax0.set_yticks(y, [LAB[m] for m in ms]); ax0.tick_params(axis="y", pad=11)
    for t, m in zip(ax0.get_yticklabels(), ms): t.set_color(INK)
    for s in ax0.spines.values(): s.set_visible(False)
    ax0.set_title("Mean ARI", pad=14, fontsize=7.5); panel(ax0, "a", dx=-0.58, dy=1.09)
    # family dots left of labels
    for yy, m in zip(y, ms):
        ax0.plot(-0.56, yy, "o", color=FCOL[FAMILY[m]], ms=4.2, clip_on=False, zorder=5)
    ax0.set_xlim(-0.5, 2.5)
    # b: forest plot of delta (reference minus method)
    ax1.axvspan(-0.03, 0.03, color="#eeede9", zorder=0, lw=0)
    ax1.axvline(0, color=INK2, lw=0.6, zorder=1)
    for yy, m in zip(y, ms):
        if m == "linear_diffusion":
            ax1.text(0.0, yy, "reference", ha="center", va="center", fontsize=6.3, color=INK2, style="italic"); continue
        v = comp[m]; lo, hi = v["ci95"]; col = FCOL[FAMILY[m]]
        ax1.plot([lo, hi], [yy, yy], color=col, lw=1.4, solid_capstyle="round", zorder=2)
        filled = v["category"] == "baseline_better"
        ax1.plot(v["delta"], yy, "o", ms=4.6, mfc=col if filled else "white", mec=col, mew=1.1, zorder=3)
        for d, mk in (("dlpfc", "|"), ("starmap", "|"), ("merfish", "|")):
            pass
    ax1.set_yticks(y, [])
    ax1.set_ylim(-0.7, n - 0.3); ax0.set_ylim(-0.5, n - 0.5)
    ax1.set_xlim(-0.12, 0.42); ax1.set_xlabel("Linear diffusion minus method (ARI)")
    ax1.grid(axis="x", color=GRID, lw=0.5); ax1.set_axisbelow(True)
    ax1.set_title("Difference to the reference, 95% CI", pad=14, fontsize=7.5); panel(ax1, "b", dx=-0.03, dy=1.09)
    h = [Line2D([], [], marker="o", ls="", mfc=INK2, mec=INK2, ms=4.2, label="interval above zero"),
         Line2D([], [], marker="o", ls="", mfc="white", mec=INK2, ms=4.2, label="unresolved"),
         matplotlib.patches.Patch(color="#eeede9", label="±0.03 ARI margin")]
    ax1.legend(handles=h, frameon=False, loc="upper right", fontsize=6.2, handletextpad=0.3, borderaxespad=0.1, bbox_to_anchor=(1.0, 0.93))
    # c: rank intervals
    for yy, m in zip(y, ms):
        rk = rank["Linear diffusion" if m == "linear_diffusion" else LAB[m]]
        col = FCOL[FAMILY[m]]
        ax2.plot(rk["rank95"], [yy, yy], color=col, lw=1.4, solid_capstyle="round")
        ax2.plot(rk["median_rank"], yy, "o", ms=4.6, color=col)
        if rk["p_best"] >= 0.01:
            ax2.text(16.9, yy, f"{rk['p_best']:.2f}", ha="right", va="center", fontsize=6.3, color=INK)
    ax2.set_yticks(y, []); ax2.set_ylim(-0.7, n - 0.3); ax2.set_xlim(0.3, 17); ax2.set_xticks([1, 4, 8, 12, 16])
    ax2.set_xlabel("Rank (1 = best)"); ax2.grid(axis="x", color=GRID, lw=0.5); ax2.set_axisbelow(True)
    ax2.set_title("Rank, median and 95% interval", pad=14, fontsize=7.5); panel(ax2, "c", dx=-0.03, dy=1.09)
    ax2.text(16.9, n - 0.1, "P(best)", ha="right", va="bottom", fontsize=6.0, color=INK2)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=FCOL[i], ms=4.5, label=FNAME[i]) for i in range(3)], loc="lower center",
               ncol=3, frameon=False, bbox_to_anchor=(0.56, -0.03), handletextpad=0.2, columnspacing=1.6)
    save(fig, "nar_fig2_accuracy")


# ---------------------------------------------------------------- Figure 3: robustness (lottery, mclust, likelihood)
def fig_robustness():
    L = [json.loads(l) for l in open(R("clustering_lottery.jsonl"))]
    rows = []
    for r in L:
        a = np.array([f["ARI"] for f in r["fits"]]); ll = np.array([f["ll"] for f in r["fits"]])
        rows.append(dict(dataset=r.get("dataset", "dlpfc"), method=r["method"], slice=str(r["slice"]), rng=a.max() - a.min(),
                         rho=spearmanr(ll, a).statistic))
    LT = pd.DataFrame(rows)
    pm = pd.read_csv(R("mclust_perturbations_long.csv")); pm["slice"] = pm["slice"].astype(str)
    pr = pm[pm.kind == "permute"].groupby(["dataset", "method", "slice"]).ARI.agg(lambda v: v.max() - v.min()).rename("prng").reset_index()
    LT = LT.merge(pr, on=["dataset", "method", "slice"], how="left")
    order = LT.groupby("method").rng.median().sort_values().index.tolist()
    n = len(order); y = np.arange(n)
    rg = np.random.default_rng(1)
    fig = plt.figure(figsize=(17.5 * CM, 7.2 * CM))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.15, 0.8], wspace=0.09, left=0.115, right=0.995, top=0.88, bottom=0.17)
    axs = [fig.add_subplot(gs[0, i]) for i in range(3)]
    for ax, col, title, xl in ((axs[0], "rng", "Different random starts", "ARI range over 20 fits of one fixed embedding"),
                               (axs[1], "prng", "R mclust, spot order permuted", "ARI range over 10 permutations")):
        for i, m in enumerate(order):
            g = LT[LT.method == m]
            for ds in DSN:
                v = g[g.dataset == ds][col].dropna().values
                ax.scatter(v, np.full(len(v), i) + rg.uniform(-0.28, 0.28, len(v)), s=5.5, color=DCOL[ds], alpha=0.75, lw=0, zorder=2)
            med = g[col].median(); q1, q3 = g[col].quantile([0.25, 0.75])
            ax.plot([q1, q3], [i, i], color=INK, lw=2.0, solid_capstyle="butt", zorder=3, alpha=0.85)
            ax.plot(med, i, "o", mfc="white", mec=INK, ms=3.8, mew=1.0, zorder=4)
        ax.set_yticks(y, [LAB[m] if ax is axs[0] else "" for m in order]); ax.set_ylim(-0.7, n - 0.3)
        ax.set_xlim(-0.01, 0.65); ax.set_xlabel(xl); ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
        ax.set_title(title, pad=4, fontsize=7.5)
    panel(axs[0], "a", dx=-0.52); panel(axs[1], "b", dx=-0.03)
    h = [Line2D([], [], marker="o", ls="", color=DCOL[d], ms=4, label=DSN[d]) for d in DSN] + [Line2D([], [], color=INK, lw=2, marker="o", mfc="white", mec=INK, ms=3.8, label="median and IQR")]
    axs[1].legend(handles=h, frameon=False, loc="lower right", fontsize=6.2, handletextpad=0.3, borderaxespad=0.1)
    # c: rho heatmap
    H = np.array([[LT[(LT.method == m) & (LT.dataset == d)].rho.median() for d in DSN] for m in order])
    ax = axs[2]
    ax.imshow(H, cmap=DIV, vmin=-0.7, vmax=0.7, aspect="auto", extent=[-0.5, 2.5, -0.5, n - 0.5], origin="lower")
    for i in range(n):
        for j in range(3):
            v = H[i, j]; ax.text(j, i, f"{v:+.2f}".replace("-", "−"), ha="center", va="center", fontsize=6.2, color="white" if abs(v) > 0.45 else INK)
    ax.set_xticks(range(3), ["DLPFC", "STARmap", "MERFISH"], rotation=0, fontsize=6.0); ax.set_yticks(y, []); ax.set_ylim(-0.7, n - 0.3)
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title("Likelihood vs ARI (Spearman ρ)", pad=4, fontsize=7.5); panel(ax, "c", dx=-0.03)
    save(fig, "nar_fig3_robustness")
    return LT


# ---------------------------------------------------------------- Figure 4: standard vs 20-start clustering
def fig_protocol():
    ms = [m for m in LAB if m in meansr and m in means and m != "linear_diffusion" and m != "pca_gmm" and len(meansr[m]) == 3
          and m not in ("spagcn", "bass", "bayesspace")]
    ms.sort(key=lambda m: -np.mean([means[m][d] for d in DSN]))
    n = len(ms); y = np.arange(n)[::-1]
    fig, axs = plt.subplots(1, 3, figsize=(17.5 * CM, 6.6 * CM), sharey=True, gridspec_kw={"wspace": 0.07, "left": 0.115, "right": 0.995, "top": 0.88, "bottom": 0.2})
    for ax, ds in zip(axs, DSN):
        for yy, m in zip(y, ms):
            a, b = means[m][ds], meansr[m][ds]
            col = BLUE if b >= a else ORANGE
            ax.plot([a, b], [yy, yy], color=col, lw=1.5, solid_capstyle="round", zorder=2)
            ax.plot(a, yy, "o", ms=4.6, mfc="white", mec=INK2, mew=1.0, zorder=3)
            ax.plot(b, yy, "o", ms=4.6, mfc=col, mec=col, zorder=3)
        ax.set_xlim(0.05, 0.8); ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True); ax.set_xlabel("Mean ARI")
        ax.set_title(DSN[ds], pad=4, fontsize=7.5)
    axs[0].set_yticks(y, [LAB[m] for m in ms]); axs[0].set_ylim(-0.7, n - 0.3)
    panel(axs[0], "a", dx=-0.62); panel(axs[1], "b", dx=-0.03); panel(axs[2], "c", dx=-0.03)
    h = [Line2D([], [], marker="o", ls="", mfc="white", mec=INK2, ms=4.5, label="Standard clustering (method's own)"),
         Line2D([], [], marker="o", ls="", color=BLUE, ms=4.5, label="20-start clustering, higher"),
         Line2D([], [], marker="o", ls="", color=ORANGE, ms=4.5, label="20-start clustering, lower")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.56, -0.03), columnspacing=1.6, handletextpad=0.2)
    save(fig, "nar_fig4_protocol")


# ---------------------------------------------------------------- Figure 5: domain maps, DLPFC 151673
def fig_maps(section="151673"):
    z = np.load(os.path.join(ROOT, "results", "cache", f"{section}.npz"), allow_pickle=True)
    C, y_true = z["coords"], z["labels"]
    keep = np.array([isinstance(v, str) for v in y_true])
    names = sorted({v for v in y_true if isinstance(v, str)})
    code = {n_: i for i, n_ in enumerate(names)}
    t = np.array([code.get(v, -1) if isinstance(v, str) else -1 for v in y_true])
    pal = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#52514e"]
    cmap = matplotlib.colors.ListedColormap(pal[:len(names)])
    meths = ["linear_diffusion", "banksy_l0.8", "bass", "sedr", "stagate", "histar", "graphst", "spagcn", "nichepca"]
    fig, axs = plt.subplots(2, 5, figsize=(17.5 * CM, 7.6 * CM), gridspec_kw={"wspace": 0.02, "hspace": 0.16, "left": 0.005, "right": 0.995, "top": 0.93, "bottom": 0.09})
    axs = axs.ravel()
    def draw(ax, lab, title):
        ax.scatter(C[:, 0], -C[:, 1], c=[pal[v] if v >= 0 else "#e4e3df" for v in lab], s=1.6, lw=0, rasterized=True)
        ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=6.8, pad=1.5)
    draw(axs[0], t, "Annotation")
    from sklearn.metrics import adjusted_rand_score
    for ax, m in zip(axs[1:], meths):
        f = os.path.join(ROOT, "results", "runs", f"dlpfc__{section}__{m}__s0.npz")
        if not os.path.exists(f): ax.axis("off"); continue
        p = np.load(f)["labels"]; K = len(names)
        # Hungarian matching of predicted clusters to annotated layers (valid spots only)
        pu = np.unique(p[keep]); M = np.zeros((len(pu), K))
        for i, c in enumerate(pu):
            for k in range(K): M[i, k] = np.sum((p == c) & (t == k))
        r, c_ = linear_sum_assignment(-M); mp = {pu[i]: c_[j] for j, i in enumerate(r)}
        extra = [u for u in pu if u not in mp]; mm = np.array([mp.get(v, K - 1 if v in extra else -1) for v in p])
        ari = adjusted_rand_score(t[keep], p[keep])
        draw(ax, np.where(keep, mm, -1), f"{LAB[m]}  (ARI {ari:.2f})")
    fig.legend(handles=[matplotlib.patches.Patch(color=pal[i], label=n_) for i, n_ in enumerate(names)], loc="lower center", ncol=len(names),
               frameon=False, bbox_to_anchor=(0.5, -0.02), handlelength=1.1, columnspacing=1.2, handletextpad=0.4, fontsize=6.5)
    save(fig, "nar_fig5_maps")


if __name__ == "__main__":
    fig_accuracy(); LT = fig_robustness(); fig_protocol(); fig_maps()
    print("figures written:", sorted(os.path.basename(f) for f in glob.glob(os.path.join(OUT, "nar_fig*.pdf"))))
