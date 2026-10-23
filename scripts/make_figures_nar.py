"""Main figures 2-5 in NAR style: vector PDF + 600 dpi PNG, exactly 17.5 cm wide (fixed figsize, no tight bbox), text >= 7 pt,
uppercase bold panel letters, TrueType (Type 42) fonts.

Colour rules (one meaning per colour across the paper):
  * family colours ONLY mean method family: blue #2a78d6 training-free baselines, orange #eb6834 deep graph encoders,
    aqua #1baf7a statistical and neighbourhood methods;
  * datasets are marker shape + neutral grey (DLPFC filled circle dark grey, STARmap filled triangle mid grey,
    MERFISH hollow square);
  * protocol (default vs matched clustering) is hollow vs filled black marker;
  * magnitudes use a neutral grey ramp; signed correlations a brown-white-purple diverging ramp (CVD-checked).

Protocols: "default clustering" = each method's own pipeline; "matched clustering" = the same 20-start best-likelihood
Gaussian mixture for every embedding (keys "robust" in results/stats_cluster_aware.json).

python scripts/make_figures_nar.py -> docs/figures/nar_fig{2,3,4,5}_*.pdf|png
"""
import json, os, glob, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda f: os.path.join(ROOT, "results", f)
OUT = os.path.join(ROOT, "docs", "figures")
CM = 1 / 2.54
WIDTH = 17.5 * CM
INK, INK2, GRID, MUTE = "#0b0b0b", "#4a4a4a", "#e4e3df", "#8a8a8a"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 7, "axes.labelsize": 7.5, "axes.titlesize": 8,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                     "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK, "axes.labelcolor": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
                     "savefig.bbox": "standard"})
SEQ = LinearSegmentedColormap.from_list("seq_grey", ["#fafafa", "#d4d4d4", "#9a9a9a", "#5a5a5a", "#1f1f1f"])
DIV = LinearSegmentedColormap.from_list("div_brpu", ["#8c510a", "#d8b365", "#f5f5f5", "#b2abd2", "#5e3c99"])

LAB = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "graphst": "GraphST",
       "banksy_l0.8": "BANKSY λ = 0.8", "banksy_l0.2": "BANKSY λ = 0.2", "spagcn": "SpaGCN", "stagate": "STAGATE", "sedr": "SEDR",
       "spaceflow": "SpaceFlow", "nichepca": "NichePCA", "ccst": "CCST", "spatial_mgcn": "Spatial-MGCN", "deepst": "DeepST",
       "bass": "BASS", "bayesspace": "BayesSpace"}
RANKKEY = {"linear_diffusion": "Linear diffusion", "banksy_l0.8": "BANKSY λ=0.8", "banksy_l0.2": "BANKSY λ=0.2"}
FAMILY = {"linear_diffusion": 0, "anisost": 0, "pca_gmm": 0,
          "histar": 1, "graphst": 1, "spagcn": 1, "stagate": 1, "sedr": 1, "spaceflow": 1, "ccst": 1, "spatial_mgcn": 1, "deepst": 1,
          "banksy_l0.8": 2, "banksy_l0.2": 2, "nichepca": 2, "bass": 2, "bayesspace": 2}
INTERNAL = ("spagcn", "bass", "bayesspace")  # cluster internally: identical under both protocols
FCOL = [BLUE, ORANGE, AQUA]
FNAME = ["Training-free baselines", "Deep graph encoders", "Statistical and neighbourhood methods"]
DSN = {"dlpfc": "DLPFC", "starmap": "STARmap", "merfish": "MERFISH", "brca": "Breast", "stereo": "Stereo-seq"}
NSEC = {"dlpfc": 12, "starmap": 3, "merfish": 5, "brca": 1, "stereo": 3}
ND = len(DSN)
# dataset encoding: shape + neutral grey
DMK = {"dlpfc": dict(marker="o", mfc="#3a3a3a", mec="#3a3a3a"), "starmap": dict(marker="^", mfc="#8a8a8a", mec="#8a8a8a"),
       "merfish": dict(marker="s", mfc="white", mec="#6a6a6a"), "brca": dict(marker="D", mfc="#bdbdbd", mec="#5a5a5a"),
       "stereo": dict(marker="v", mfc="white", mec="#3a3a3a")}
# methods stopped at the per-job memory cap on the largest Stereo-seq section: their Stereo-seq mean covers the other sections
_runs = {}
if os.path.exists(R("benchmark_runs.jsonl")):
    for l in open(R("benchmark_runs.jsonl")):
        r_ = json.loads(l); _runs[r_["id"]] = r_
OOM = {r_["method"] for r_ in _runs.values() if r_.get("status") != "ok" and "out of memory" in str(r_.get("error", ""))}

cs = json.load(open(R("stats_cluster_aware.json")))
comp_m = {k.split("/", 1)[1]: v for k, v in cs["comparisons"].items() if k.startswith("robust/")}
mean_d = cs["means_standard"]; mean_m = cs["means_robust"]; rank = cs["ranking"]


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"))
    plt.close(fig)


def letter(fig, x, y, s):
    """Panel letter at figure coordinates (top-left of the panel)."""
    fig.text(x, y, s, fontsize=10, fontweight="bold", ha="left", va="top")


def family_handles(ms=5):
    return [Line2D([], [], marker="o", ls="", color=FCOL[i], ms=ms, label=FNAME[i]) for i in range(3)]


def dataset_handles(ms=4.5):
    return [Line2D([], [], ls="", ms=ms, mew=0.8, label=f"{DSN[d]} (n = {NSEC[d]})", **DMK[d]) for d in DSN]


# ---------------------------------------------------------------- Figure 2: accuracy under matched clustering
def fig_accuracy():
    ms = [m for m in LAB if m in mean_m and len(mean_m[m]) == ND]
    ms.sort(key=lambda m: -np.mean([mean_m[m][d] for d in DSN]))
    ms.append("bayesspace")  # Visium only (DLPFC and breast cancer)
    n = len(ms); y = np.arange(n)[::-1]
    fig = plt.figure(figsize=(WIDTH, 11.4 * CM))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.45, 1.15, 0.85], wspace=0.08, left=0.135, right=0.985, top=0.885, bottom=0.27)
    ax0, ax1, ax2 = [fig.add_subplot(gs[0, i]) for i in range(3)]
    # A: heatmap of mean ARI (matched clustering)
    A = np.array([[mean_m[m].get(d, np.nan) for d in DSN] for m in ms], float)
    im = ax0.imshow(np.ma.masked_invalid(A), cmap=SEQ, vmin=0, vmax=0.8, aspect="auto", extent=[-0.5, ND - 0.5, -0.5, n - 0.5])
    for i, m in enumerate(ms):
        for j, d in enumerate(DSN):
            v = A[i, j]
            if np.isnan(v):
                ax0.text(j, n - 1 - i, "–", ha="center", va="center", fontsize=7, color=INK2)
            else:
                star = "*" if (d == "stereo" and m in OOM) else ""
                ax0.text(j, n - 1 - i, f"{v:.2f}{star}", ha="center", va="center", fontsize=7, color="white" if v > 0.45 else INK)
    ax0.set_xticks(range(ND), [DSN[d].replace("Stereo-seq", "Stereo") for d in DSN]); ax0.xaxis.tick_top(); ax0.tick_params(length=0)
    ax0.set_yticks(y, [LAB[m] for m in ms]); ax0.tick_params(axis="y", pad=9)
    for s in ax0.spines.values(): s.set_visible(False)
    for yy, m in zip(y, ms):
        ax0.plot(-0.62, yy, "o", color=FCOL[FAMILY[m]], ms=4.3, clip_on=False, zorder=5)
    ax0.set_xlim(-0.5, ND - 0.5); ax0.set_ylim(-0.5, n - 0.5)
    ax0.set_title("Mean ARI, matched clustering", pad=16)
    p0 = ax0.get_position()
    cax = fig.add_axes([p0.x0 + 0.1 * p0.width, 0.075, 0.8 * p0.width, 0.018])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[0, 0.2, 0.4, 0.6, 0.8])
    cb.outline.set_linewidth(0.4); cb.ax.tick_params(labelsize=7, length=2)
    cb.set_label("Mean ARI", fontsize=7, labelpad=1)
    # B: forest plot, linear diffusion minus method (matched clustering)
    ax1.axvspan(-0.03, 0.03, color="#e9e9e6", zorder=0, lw=0)
    ax1.axvline(0, color=INK2, lw=0.6, zorder=1)
    for yy, m in zip(y, ms):
        if m == "linear_diffusion":
            ax1.text(0.0, yy, "reference", ha="center", va="center", fontsize=7, color=INK2, style="italic"); continue
        v = comp_m[m]; lo, hi = v["ci95"]; col = FCOL[FAMILY[m]]
        ax1.plot([lo, hi], [yy, yy], color=col, lw=1.3, solid_capstyle="butt", zorder=2)
        filled = lo > 0
        ax1.plot(v["delta"], yy, "o", ms=4.8, mfc=col if filled else "white", mec=col, mew=1.1, zorder=3)
        if m == "bayesspace":
            ax1.text(hi + 0.012, yy, "(Visium only)", ha="left", va="center", fontsize=7, color=INK2)
    ax1.set_yticks(y, []); ax1.tick_params(axis="y", length=0)
    ax1.set_ylim(-0.5, n - 0.5)
    ax1.set_xlim(-0.1, 0.45); ax1.set_xticks([-0.1, 0, 0.1, 0.2, 0.3, 0.4])
    ax1.set_xlabel("ARI difference")
    ax1.grid(axis="x", color=GRID, lw=0.5); ax1.set_axisbelow(True)
    ax1.set_title("Linear diffusion minus method\n(95% bootstrap interval)", pad=5)
    h = [Line2D([], [], marker="o", ls="", mfc=INK2, mec=INK2, ms=4.5, label="interval above zero"),
         Line2D([], [], marker="o", ls="", mfc="white", mec=INK2, ms=4.5, label="unresolved"),
         Patch(color="#e9e9e6", label="±0.03 equivalence margin")]
    p2_ = ax2.get_position()
    fig.legend(handles=h, loc="lower left", ncol=1, frameon=False, bbox_to_anchor=(p2_.x0 - 0.035, 0.0),
               handletextpad=0.3, labelspacing=0.3)
    # C: rank intervals (matched clustering)
    NR = cs["ranking_methods"]; XP = NR + 3.6
    for yy, m in zip(y, ms):
        key = RANKKEY.get(m, LAB[m])
        if key not in rank:
            why = "Visium only" if m == "bayesspace" else "memory cap"
            ax2.text((NR + 1) / 2, yy, f"not ranked: {why}", ha="center", va="center", fontsize=7, color=INK2, style="italic"); continue
        rk = rank[key]; col = FCOL[FAMILY[m]]
        ax2.plot(rk["rank95"], [yy, yy], color=col, lw=1.3, solid_capstyle="butt")
        ax2.plot(rk["median_rank"], yy, "o", ms=4.8, color=col)
        if rk["p_best"] >= 0.01:
            ax2.text(XP, yy, f"{rk['p_best']:.2f}", ha="right", va="center", fontsize=7, color=INK)
    ax2.set_yticks(y, []); ax2.tick_params(axis="y", length=0); ax2.set_ylim(-0.5, n - 0.5)
    ax2.set_xlim(0.3, XP + 0.2); ax2.set_xticks([1, *range(4, NR - 1, 3), NR])
    ax2.spines["bottom"].set_bounds(0.3, NR + 0.7)
    ax2.set_xlabel("Rank (1 = best)\nP(best) shown when ≥ 0.01"); ax2.grid(axis="x", color=GRID, lw=0.5); ax2.set_axisbelow(True)
    ax2.set_title("Rank, median and\n95% interval", pad=5)
    ax2.text(XP, n - 0.45, "P(best)", ha="right", va="bottom", fontsize=7, color=INK2)
    # letters
    for ax, s, dx in ((ax0, "A", -0.12), (ax1, "B", -0.02), (ax2, "C", -0.02)):
        p = ax.get_position(); letter(fig, p.x0 + dx if s != "A" else 0.005, 0.995, s)
    p1 = ax1.get_position()
    fig.legend(handles=family_handles(), loc="lower left", ncol=1, frameon=False, bbox_to_anchor=(p1.x0 - 0.02, 0.0),
               handletextpad=0.2, labelspacing=0.3)
    save(fig, "nar_fig2_accuracy")


# ---------------------------------------------------------------- Figure 3: robustness (random starts, R mclust seeds, likelihood)
def load_mclust_seed():
    fs = sorted(glob.glob(R("mclust_seed_g*.csv")))
    parts = []
    for f in fs:
        try:
            d = pd.read_csv(f, on_bad_lines="skip")
            if {"dataset", "slice", "method", "kind", "ARI"} <= set(d.columns): parts.append(d)
        except Exception:
            pass
    if not parts: return pd.DataFrame(columns=["dataset", "slice", "method", "kind", "ARI"])
    d = pd.concat(parts, ignore_index=True)
    d["ARI"] = pd.to_numeric(d["ARI"], errors="coerce"); d = d.dropna(subset=["ARI"])
    d["slice"] = d["slice"].astype(str)
    return d


def ranges(d, kind, min_n):
    g = d[d.kind == kind].groupby(["dataset", "method", "slice"]).ARI
    r = g.agg(lambda v: v.max() - v.min()).rename("rng").to_frame(); r["n"] = g.size()
    return r[r.n >= min_n].reset_index()


def fig_robustness():
    L = [json.loads(l) for l in open(R("clustering_lottery.jsonl"))]
    rows = []
    for r in L:
        a = np.array([f["ARI"] for f in r["fits"]]); ll = np.array([f["ll"] for f in r["fits"]])
        rows.append(dict(dataset=r.get("dataset", "dlpfc"), method=r["method"], slice=str(r["slice"]), rng=a.max() - a.min(),
                         rho=spearmanr(ll, a).statistic))
    LT = pd.DataFrame(rows)
    order = LT.groupby("method").rng.median().sort_values().index.tolist()[::-1]  # largest median range at top
    n = len(order); yrow = {m: n - 1 - i for i, m in enumerate(order)}
    MS = load_mclust_seed()
    SR = ranges(MS, "seed", 2); FJ = ranges(MS, "full_jit", 2)
    rg = np.random.default_rng(1)
    fig = plt.figure(figsize=(WIDTH, 10.4 * CM))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.1], wspace=0.07, left=0.125, right=0.985, top=0.80, bottom=0.27)
    axs = [fig.add_subplot(gs[0, i]) for i in range(3)]
    jit = {"dlpfc": -0.24, "starmap": -0.12, "merfish": 0.0, "brca": 0.12, "stereo": 0.24}

    def dots(ax, df, col, dy=0.0, sz=3.6):
        for m in order:
            g = df[df.method == m]
            for ds in DSN:
                v = g[g.dataset == ds][col].dropna().values
                if not len(v): continue
                yy = yrow[m] + dy + jit[ds] * (0.6 if dy else 1.0) + rg.uniform(-0.06, 0.06, len(v))
                ax.plot(v, yy, ls="", ms=sz, mew=0.6, alpha=0.9, zorder=2, **DMK[ds])

    def iqr(ax, df, col):
        for m in order:
            g = df[df.method == m][col].dropna()
            if not len(g): continue
            q1, q3 = g.quantile([0.25, 0.75]); yy = yrow[m]
            ax.plot([q1, q3], [yy, yy], color=INK, lw=1.8, solid_capstyle="butt", zorder=3, alpha=0.8)
            ax.plot(g.median(), yy, "o", mfc="white", mec=INK, ms=4.0, mew=1.0, zorder=4)

    # A: 20 single-start fits
    ax = axs[0]
    dots(ax, LT, "rng"); iqr(ax, LT, "rng")
    ax.set_yticks([yrow[m] for m in order], [LAB[m] for m in order])
    ax.set_xlabel("ARI range (max − min)"); ax.set_title("Range over 20 single-start\nGaussian-mixture fits", pad=5)
    # B: R mclust seeds
    ax = axs[1]
    xmax_b = 0.65
    if len(SR):
        dots(ax, SR, "rng", dy=-0.12); iqr(ax, SR, "rng")
        xmax_b = max(xmax_b, SR.rng.max() + 0.03)
    if len(FJ):
        for _, r_ in FJ.iterrows():
            if r_.method not in yrow: continue
            ax.plot(r_.rng, yrow[r_.method] + 0.3 + rg.uniform(-0.05, 0.05), marker="x", ls="", color=INK, ms=3.6, mew=0.8, zorder=5)
        xmax_b = max(xmax_b, FJ.rng.max() + 0.03)
    done = set(SR.method) if len(SR) else set()
    for m in order:
        if m not in done:
            ax.text(0.01, yrow[m], "not yet run" if len(MS) else "", ha="left", va="center", fontsize=7, color=MUTE, style="italic")
    if not len(MS):
        ax.text(0.5, 0.5, "R mclust runs not available", transform=ax.transAxes, ha="center", va="center", fontsize=7, color=INK2)
    ax.set_yticks([yrow[m] for m in order], [])
    ax.set_xlabel("ARI range (max − min)"); ax.set_title("R mclust: range over 10 random seeds\n(default initialisation)", pad=5)
    for a in axs[:2]:
        a.set_ylim(-0.6, n - 0.4); a.set_xlim(-0.01, max(0.65, xmax_b)); a.grid(axis="x", color=GRID, lw=0.5); a.set_axisbelow(True)
    # C: Spearman rho heatmap
    H = np.array([[LT[(LT.method == m) & (LT.dataset == d)].rho.median() for d in DSN] for m in order[::-1]])
    ax = axs[2]
    im = ax.imshow(np.ma.masked_invalid(H), cmap=DIV, vmin=-1, vmax=1, aspect="auto", extent=[-0.5, ND - 0.5, -0.5, n - 0.5], origin="lower")
    for i in range(n):
        for j in range(ND):
            v = H[i, j]
            if np.isnan(v):
                ax.text(j, i, "–", ha="center", va="center", fontsize=7, color=INK2); continue
            ax.text(j, i, f"{v:+.1f}".replace("-", "−"), ha="center", va="center", fontsize=7, color="white" if abs(v) > 0.6 else INK)
    SPLIT = {"starmap": "STAR-\nmap", "merfish": "MER-\nFISH", "stereo": "Stereo-\nseq", "dlpfc": "DLPFC\n", "brca": "Breast\n"}
    ax.set_xticks(range(ND), [f"{SPLIT[d]}\nn = {NSEC[d]}" for d in DSN]); ax.xaxis.tick_top()
    ax.set_yticks(range(n), []); ax.set_ylim(-0.6, n - 0.4); ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title("Log-likelihood vs ARI,\nmedian Spearman ρ", pad=36)
    p2 = ax.get_position()
    cax = fig.add_axes([p2.x0 + 0.08 * p2.width, 0.12, 0.84 * p2.width, 0.02])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[-1, -0.5, 0, 0.5, 1])
    cb.ax.set_xticklabels(["−1", "−0.5", "0", "0.5", "1"]); cb.outline.set_linewidth(0.4); cb.ax.tick_params(labelsize=7, length=2)
    cb.set_label("Spearman ρ", fontsize=7, labelpad=1)
    # letters + legend
    letter(fig, 0.005, 0.995, "A")
    for a, s in ((axs[1], "B"), (axs[2], "C")):
        letter(fig, a.get_position().x0 - 0.015, 0.995, s)
    h = dataset_handles() + [Line2D([], [], color=INK, lw=1.8, marker="o", mfc="white", mec=INK, ms=4, label="median and IQR"),
                             Line2D([], [], marker="x", ls="", color=INK, ms=4, mew=0.8, label="R mclust, full-data initialisation + 1% noise (5 runs)")]
    p0 = axs[0].get_position()
    fig.legend(handles=h, loc="lower left", ncol=3, frameon=False, bbox_to_anchor=(p0.x0 - 0.115, 0.0), handletextpad=0.4, handlelength=1.8,
               columnspacing=1.2, labelspacing=0.35)
    save(fig, "nar_fig3_robustness")
    return LT


# ---------------------------------------------------------------- Figure 4: default vs matched clustering
def fig_protocol():
    ms = [m for m in LAB if m in mean_m and m in mean_d and len(mean_m[m]) == ND and len(mean_d[m]) == ND and m not in INTERNAL]
    ms.sort(key=lambda m: -np.mean([mean_m[m][d] for d in DSN]))
    n = len(ms); y = np.arange(n)[::-1]
    fig, axs = plt.subplots(1, ND, figsize=(WIDTH, 8.6 * CM), sharey=True,
                            gridspec_kw={"wspace": 0.1, "left": 0.135, "right": 0.985, "top": 0.9, "bottom": 0.255})
    for ax, ds in zip(axs, DSN):
        for yy, m in zip(y, ms):
            a, b = mean_d[m][ds], mean_m[m][ds]
            ax.plot([a, b], [yy, yy], color=FCOL[FAMILY[m]], lw=2.0, solid_capstyle="butt", zorder=2)
            ax.plot(a, yy, "o", ms=4.8, mfc="white", mec=INK, mew=0.9, zorder=3)
            ax.plot(b, yy, "o", ms=4.0, mfc=INK, mec=INK, zorder=4)
        ax.set_xlim(0.0, 0.8); ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
        ax.set_xticklabels(["", "0.2", "", "0.6", ""])
        ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True); ax.set_xlabel("Mean ARI")
        ax.set_title(f"{DSN[ds]} (n = {NSEC[ds]})", pad=4)
    axs[0].set_yticks(y, [LAB[m] for m in ms]); axs[0].set_ylim(-0.6, n - 0.4)
    axs[0].tick_params(axis="y", pad=9)
    for yy, m in zip(y, ms):
        axs[0].plot(-0.035, yy, "o", color=FCOL[FAMILY[m]], ms=4.3, clip_on=False, zorder=5, transform=axs[0].get_yaxis_transform())
    letter(fig, 0.005, 0.995, "A")
    for a, s in zip(axs[1:], "BCDE"):
        letter(fig, a.get_position().x0 - 0.012, 0.995, s)
    h = [Line2D([], [], marker="o", ls="", mfc="white", mec=INK, ms=4.8, label="Default clustering (method's own pipeline)"),
         Line2D([], [], marker="o", ls="", mfc=INK, mec=INK, ms=4.2, label="Matched clustering (20-start Gaussian mixture)")]
    fig.legend(handles=h, loc="lower left", ncol=2, frameon=False, bbox_to_anchor=(0.12, 0.055), columnspacing=1.6, handletextpad=0.3)
    fig.legend(handles=family_handles(), loc="lower left", ncol=3, frameon=False, bbox_to_anchor=(0.12, 0.0), columnspacing=1.6,
               handletextpad=0.3, title=None)
    save(fig, "nar_fig4_protocol")


# ---------------------------------------------------------------- Figure 5: domain maps, DLPFC 151673 (default clustering)
def fig_maps(section="151673"):
    from sklearn.metrics import adjusted_rand_score
    z = np.load(os.path.join(ROOT, "results", "cache", f"{section}.npz"), allow_pickle=True)
    C, y_true = z["coords"], z["labels"]
    keep = np.array([isinstance(v, str) for v in y_true])
    names = sorted({v for v in y_true if isinstance(v, str)})
    code = {n_: i for i, n_ in enumerate(names)}
    t = np.array([code.get(v, -1) if isinstance(v, str) else -1 for v in y_true])
    # L1..L6, WM. L6 brown (was purple, confusable with L1 blue under deuteranopia); WM dark grey.
    pal = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8c510a", "#3a3a3a"]
    short = [s.replace("Layer", "L") for s in names]
    meths = ["linear_diffusion", "banksy_l0.8", "bass", "sedr", "stagate", "histar", "graphst", "spagcn", "nichepca"]
    fig, axs = plt.subplots(2, 5, figsize=(WIDTH, 8.4 * CM),
                            gridspec_kw={"wspace": 0.02, "hspace": 0.17, "left": 0.005, "right": 0.995, "top": 0.885, "bottom": 0.085})
    axs = axs.ravel()

    def draw(ax, lab, title):
        ax.scatter(C[:, 0], -C[:, 1], c=[pal[v] if v >= 0 else "#e4e3df" for v in lab], s=1.6, lw=0, rasterized=True)
        ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=7, pad=1.5)
    draw(axs[0], t, "Annotation")
    for ax, m in zip(axs[1:], meths):
        f = os.path.join(ROOT, "results", "runs", f"dlpfc__{section}__{m}__s0.npz")
        if not os.path.exists(f): ax.axis("off"); continue
        p = np.load(f)["labels"]; K = len(names)
        pu = np.unique(p[keep]); M = np.zeros((len(pu), K))
        for i, c in enumerate(pu):
            for k in range(K): M[i, k] = np.sum((p == c) & (t == k))
        r, c_ = linear_sum_assignment(-M); mp = {pu[i]: c_[j] for j, i in enumerate(r)}
        mm = np.array([mp.get(v, K - 1) for v in p])
        ari = adjusted_rand_score(t[keep], p[keep])
        draw(ax, np.where(keep, mm, -1), f"{LAB[m]} (ARI {ari:.2f})")
    fig.text(0.5, 0.985, f"DLPFC section {section}, default clustering (each method's own pipeline), seed 0",
             ha="center", va="top", fontsize=8)
    fig.legend(handles=[Patch(color=pal[i], label=s) for i, s in enumerate(short)], loc="lower center", ncol=len(names),
               frameon=False, bbox_to_anchor=(0.5, 0.0), handlelength=1.1, columnspacing=1.4, handletextpad=0.4, fontsize=7)
    save(fig, "nar_fig5_maps")


if __name__ == "__main__":
    import sys
    todo = sys.argv[1:] or ["accuracy", "robustness", "protocol", "maps"]
    for name in todo: globals()[f"fig_{name}"]()
    print("figures written:", sorted(os.path.basename(f) for f in glob.glob(os.path.join(OUT, "nar_fig*.pdf"))))
