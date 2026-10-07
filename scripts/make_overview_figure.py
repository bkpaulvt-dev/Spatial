"""Figure 1: study design overview + a real example of the clustering lottery.

Panels (a)-(d) describe the design; panel (e) shows DLPFC section 151669, where one fixed
HiSTaR embedding (seed 0) clustered with the same tied-covariance GMM gives ARI 0.23 or 0.67
depending only on the random start (random_state 9 vs 13, from results/clustering_lottery.jsonl).
Needs results/emb/dlpfc_151669_histar.npy (written by scripts/clustering_lottery.py).
Output: docs/figures/fig0_overview.pdf (+ .png preview)
"""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "docs", "figures")
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#f4f3ef"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "savefig.dpi": 300})

# ---------------- data for panel (e)
S, K = "151669", 5
z = np.load(os.path.join(ROOT, "results", "cache", f"{S}.npz"), allow_pickle=True)
C, y = z["coords"], z["labels"]
Z = np.load(os.path.join(ROOT, "results", "emb", f"dlpfc_{S}_histar.npy")).astype(np.float64)
rec = next(r for r in map(json.loads, open(os.path.join(ROOT, "results", "clustering_lottery.jsonl")))
           if r.get("dataset", "dlpfc") == "dlpfc" and r["slice"] == S and r["method"] == "histar")
fits = sorted(rec["fits"], key=lambda f: f["ARI"])
keep = np.array([isinstance(v, str) for v in y])
LAY = sorted(set(y[keep]), key=lambda s: (s == "WM", s))           # Layer3..Layer6, WM
cmap = plt.get_cmap("viridis", len(LAY))
def run(rs):
    p = GaussianMixture(K, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=rs).fit(Z).predict(Z)
    M = np.array([[np.sum((p[keep] == c) & (y[keep] == l)) for l in LAY] for c in range(K)])
    r, c = linear_sum_assignment(-M); mp = dict(zip(r, c))
    return np.array([mp[v] for v in p]), adjusted_rand_score(y[keep], p[keep])
lo, hi = run(fits[0]["rs"]), run(fits[-1]["rs"])
truth = np.array([LAY.index(v) if isinstance(v, str) else -1 for v in y])

# ---------------- layout
fig = plt.figure(figsize=(7.2, 4.3))
ax = fig.add_axes([0, 0.44, 1, 0.56]); ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")

def box(x, w, title, lines, tag, hl=None):
    ax.add_patch(FancyBboxPatch((x, 4), w, 46, boxstyle="round,pad=0.4,rounding_size=2",
                                fc=SURF, ec=GRID, lw=0.8))
    ax.text(x + 1.2, 54, tag, fontsize=9, fontweight="bold", color=INK, va="center")
    ax.text(x + 5, 54, title, fontsize=8.2, fontweight="bold", color=INK, va="center")
    yy = 45
    for ln in lines:
        if ln == "":
            yy -= 3; continue
        col = BLUE if (hl and ln in hl) else INK2
        ax.text(x + 1.8, yy, ln, fontsize=7, color=col, va="top")
        yy -= 5.2

def arrow(x0, x1):
    ax.add_patch(FancyArrowPatch((x0, 27), (x1, 27), arrowstyle="-|>", mutation_scale=9, lw=1, color=INK2))

box(1, 21, "Data", ["3 technologies, 20 sections", "", "DLPFC, 10x Visium (12)", "STARmap mPFC (3)",
                    "MERFISH hypothalamus (5)", "", "expert domain labels", "(used only for scoring)"], "a")
arrow(22.8, 25.2)
box(26, 22, "Methods", ["Deep: HiSTaR, GraphST", "Published: BANKSY, SpaGCN",
                                       "Training-free: linear", "  diffusion, AnisoST, PCA", "",
                                       "3 training seeds each;", "one fixed embedding per", "section kept for (c)"], "b")
arrow(48.8, 51.2)
box(52, 24.5, "Clustering protocols", ["Standard: one mclust-style fit", "Robust: best likelihood of 20",
                                       "Lottery: 20 single random starts", "R mclust perturbations:",
                                       "  • permute spot order (10×)", "  • add 1% noise (10×)", "",
                                       "same mixture model (EEE)"], "c",
    hl=["Lottery: 20 single random starts"])
arrow(77.3, 79.7)
box(80.5, 18.5, "Evaluation", ["ARI vs. labels", "seed variance", "runtime", "",
                               "Wilcoxon tests,", "Holm correction", "", "matched vs. standard"], "d")

# ---------------- panel (e): real lottery example
fig.text(0.012, 0.405, "e", fontsize=9, fontweight="bold", color=INK)
fig.text(0.045, 0.405, f"Same fixed HiSTaR embedding (DLPFC {S}), same mixture model, different random start only",
         fontsize=8.2, fontweight="bold", color=INK)
panels = [("Expert annotation", truth, None), (f"Random start {fits[0]['rs']}", lo[0], lo[1]),
          (f"Random start {fits[-1]['rs']}", hi[0], hi[1])]
for i, (t, lab, ari) in enumerate(panels):
    a = fig.add_axes([0.04 + i * 0.235, 0.0, 0.21, 0.31])
    m = lab >= 0
    a.scatter(C[~m, 0], -C[~m, 1], s=0.6, color=GRID, linewidths=0)
    a.scatter(C[m, 0], -C[m, 1], s=0.6, c=lab[m], cmap=cmap, vmin=-0.5, vmax=len(LAY) - 0.5, linewidths=0)
    a.set_aspect("equal"); a.axis("off")
    a.set_title(t if ari is None else f"{t}:  ARI = {ari:.2f}", fontsize=7.5, color=INK, pad=2)
a = fig.add_axes([0.745, 0.02, 0.25, 0.32]); a.axis("off")
for j, l in enumerate(LAY):
    a.scatter([0.05], [0.88 - j * 0.12], s=22, color=cmap(j))
    a.text(0.12, 0.88 - j * 0.12, l.replace("Layer", "Layer "), va="center", fontsize=7, color=INK2)
a.text(0.0, 0.18, f"Across 20 random starts on this embedding:\nARI {fits[0]['ARI']:.2f} – {fits[-1]['ARI']:.2f}",
       fontsize=7, color=INK, va="top")
a.set_xlim(0, 1); a.set_ylim(0, 1)

os.makedirs(FIG, exist_ok=True)
fig.savefig(os.path.join(FIG, "fig0_overview.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(FIG, "fig0_overview.png"), bbox_inches="tight", dpi=200)
print("ARI low/high:", round(lo[1], 3), round(hi[1], 3))
