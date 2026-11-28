"""Figure 6 of manuscript V2: pre-registered domain-size simulation. Reads results/newdata_sim_ari_table.csv, newdata_sim_delta.csv and
results/paper_review_numbers.json (tier-3 reduced design). Writes docs/figures/nar_fig6_simulation.pdf/.png. Same style as make_figures_nar.py."""
import csv, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); OUT = os.path.join(ROOT, "docs", "figures")
CM = 1 / 2.54; INK, INK2, GRID = "#0b0b0b", "#4a4a4a", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 7, "axes.labelsize": 7.5, "axes.titlesize": 8,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5, "axes.linewidth": 0.6, "axes.edgecolor": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "savefig.dpi": 600})
LAB = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "banksy_l0.8": "BANKSY 0.8",
       "banksy_l0.2": "BANKSY 0.2", "spagcn": "SpaGCN", "nichepca": "NichePCA", "bass": "BASS", "ccst": "CCST", "deepst": "DeepST",
       "graphst": "GraphST", "spaceflow": "SpaceFlow", "spatial_mgcn": "Spatial-MGCN", "stagate": "STAGATE"}
FAM = {"linear_diffusion": BLUE, "anisost": BLUE, "pca_gmm": BLUE, "histar": ORANGE, "spagcn": ORANGE, "banksy_l0.8": AQUA, "banksy_l0.2": AQUA, "nichepca": AQUA}
STY = {"linear_diffusion": dict(lw=2.0, ls="-", marker="o"), "pca_gmm": dict(lw=1.6, ls="--", marker="o", color="#4a4a4a"), "anisost": dict(lw=1, ls=":", marker="o"),
       "histar": dict(lw=1, ls="-", marker="s"), "spagcn": dict(lw=1, ls=":", marker="s"), "banksy_l0.8": dict(lw=1, ls="-", marker="^"),
       "banksy_l0.2": dict(lw=1, ls=":", marker="^"), "nichepca": dict(lw=1, ls="--", marker="D")}
A_P, B_P = [1, 2, 4, 7], [3, 5, 8, 12, 20]

rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "newdata_sim_ari_table.csv"))))
ari = {(r["method"], r["geometry"], int(r["param"])): float(r["ari_mean"]) for r in rows if r["design"].startswith("full")}
delta = list(csv.DictReader(open(os.path.join(ROOT, "results", "newdata_sim_delta.csv"))))
red = json.load(open(os.path.join(ROOT, "results", "paper_review_numbers.json")))["D_reduced"]

fig = plt.figure(figsize=(17.5 * CM, 12.5 * CM))
gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.05], hspace=0.55, wspace=0.42, left=0.105, right=0.985, top=0.93, bottom=0.10)
for col, (geo, ps, xl, ttl) in enumerate([("A", A_P, "repeats m (larger m = narrower bands)", "Layered bands"),
                                         ("B", B_P, "block side w (spot spacings)", "Random blocks")]):
    ax = fig.add_subplot(gs[0, col]); x = np.arange(len(ps))
    for m in STY:
        y = [ari.get((m, geo, p), np.nan) for p in ps]
        st = dict(STY[m]); c = st.pop("color", FAM[m])
        ax.plot(x, y, color=c, ms=3, label=LAB[m], **st, zorder=3 if m == "linear_diffusion" else 2)
    ax.set_xticks(x, [str(p) for p in ps]); ax.set_xlabel(xl); ax.set_ylim(0, 1.02); ax.set_ylabel("Mean ARI" if col == 0 else "")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.set_title(f"{'AB'[col]}  {ttl}: full design (8 methods)", loc="left", fontsize=7.5)
    if col == 1:
        HANDLES = ax.get_legend_handles_labels()
ax = fig.add_subplot(gs[0, 2]); lab = [f"{d['geometry']}{'m' if d['geometry']=='A' else 'w'}={d['param']}" for d in delta]
y = np.array([float(d["delta"]) for d in delta]); lo = np.array([float(d["ci_low"]) for d in delta]); hi = np.array([float(d["ci_high"]) for d in delta])
xx = np.arange(len(delta)); ax.axhline(0, color=INK, lw=0.6)
ax.errorbar(xx, y, yerr=[y - lo, hi - y], fmt="none", ecolor=INK2, lw=0.9, capsize=1.5)
ax.scatter(xx, y, c=[BLUE if v > 0 else "#8c510a" for v in y], s=14, zorder=3)
ax.set_xticks(xx, [l.replace("A", "").replace("B", "") for l in lab], rotation=60); ax.axvline(3.5, color=GRID, lw=0.8)
ax.text(1.5, 0.27, "bands", ha="center", fontsize=6.5); ax.text(6, 0.27, "blocks", ha="center", fontsize=6.5)
ax.set_ylabel("Δ ARI (95% interval)"); ax.set_ylim(-0.65, 0.32); ax.grid(axis="y", color=GRID, lw=0.5)
ax.set_title("C  Linear diffusion − PCA", loc="left", fontsize=7.5)

ax = fig.add_subplot(gs[1, :2]); ms = ["bass", "stagate", "graphst", "deepst", "ccst", "spatial_mgcn", "spaceflow"]
cols = [f"m={p}" for p in A_P] + [f"w={p}" for p in B_P]
M = np.array([red[m] for m in ms]); im = ax.imshow(M, cmap="Greys", vmin=0, vmax=1, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6, color="white" if M[i, j] > 0.6 else INK)
ax.set_xticks(range(len(cols)), cols); ax.set_yticks(range(len(ms)), [LAB[m] for m in ms]); ax.axvline(3.5, color="white", lw=2)
ax.set_title("D  Deep and Bayesian methods, reduced design (one tissue per setting, seed 0; no interval)", loc="left", fontsize=7.5)
ax.spines[:].set_visible(False); ax.tick_params(length=0)
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01); cb.set_label("ARI"); cb.outline.set_visible(False)
ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
ax.legend(*HANDLES, loc="upper left", bbox_to_anchor=(-0.02, 1.08), frameon=False, ncol=2, handlelength=1.8, columnspacing=0.6, title="Panels A, B (BANKSY: λ)", title_fontsize=6.5, alignment="left")
ax.text(0, 0.42, "Simulation design", fontweight="bold", va="top", fontsize=7)
ax.text(0, 0.33, "120 × 120 spots, 6 domains;\nprofiles of DLPFC 151507 L1–L6;\n"
        "negative binomial (φ = 0.5).\nA: m repeats of the six layers.\nB: square blocks of side w.\n"
        "Full design: 5 tissues × 3 seeds.", va="top", fontsize=6.5, linespacing=1.35)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, f"nar_fig6_simulation.{ext}"))
print("written", os.path.join(OUT, "nar_fig6_simulation.pdf"))
