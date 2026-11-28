"""Figure 3C/D of manuscript V3: domains on the held-out Allen MERFISH section ABCA1-085 (selection rule: the middle of the three sections chosen by
the fixed anterior-posterior rule; seed 0; each method's own clustering; the nine original methods that finished all three sections).
Reads results/newdata_runs/allenmerfish__ABCA1-085__<method>__s0.npz. Writes docs/figures/nar_fig3_allen_v3.pdf/.png"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT, HERE]
from spatialbench.data import load_section
CM = 1 / 2.54; WIDTH = 17.5 * CM
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 7, "pdf.fonttype": 42, "savefig.dpi": 450})
LAB = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "banksy_l0.8": "BANKSY λ = 0.8",
       "stagate": "STAGATE", "spaceflow": "SpaceFlow", "nichepca": "NichePCA", "bass": "BASS"}
SEC = "ABCA1-085"
a = load_section("allenmerfish", SEC); y = a.obs["ground_truth"].to_numpy(dtype=object); C = np.asarray(a.obsm["spatial"], float)
keep = np.array([isinstance(v, str) and v not in ("nan", "") for v in y]); names = sorted({v for v in y[keep]}); code = {n: i for i, n in enumerate(names)}
t = np.array([code.get(v, -1) if k else -1 for v, k in zip(y, keep)]); K = len(names)
pal = plt.get_cmap("tab20")(np.linspace(0, 1, 20))[[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 1, 3, 5]][:K]
res = []
for m in LAB:
    f = os.path.join(ROOT, "results", "newdata_runs", f"allenmerfish__{SEC}__{m}__s0.npz")
    if not os.path.exists(f):
        continue
    p = np.load(f)["labels"]; pu = np.unique(p[keep]); M = np.array([[np.sum((p == c) & (t == k)) for k in range(K)] for c in pu])
    r, c_ = linear_sum_assignment(-M); mp = {pu[i]: c_[j] for j, i in enumerate(r)}
    res.append((m, np.array([mp.get(v, -1) for v in p]), adjusted_rand_score(t[keep], p[keep])))
res.sort(key=lambda r_: -r_[2])
ERR, OK, NONE = "#d7301f", "#c9c9c6", "#f1f0ec"
fig = plt.figure(figsize=(WIDTH, 12.0 * CM)); gs = fig.add_gridspec(4, 5, wspace=0.02, hspace=0.22, left=0.005, right=0.995, top=0.915, bottom=0.1)
ax = [fig.add_subplot(gs[r, c]) for r in range(4) for c in range(5)]
def draw(a_, col, title):
    a_.scatter(C[:, 0], -C[:, 1], c=col, s=0.15, lw=0, rasterized=True); a_.set_aspect("equal"); a_.axis("off"); a_.set_title(title, fontsize=7, pad=1.5)
draw(ax[0], [pal[v] if v >= 0 else "#e4e3df" for v in t], "Annotation (CCF divisions)")
for a_, ae, (m, mm, ari) in zip(ax[1:5] + ax[5:10], ax[11:15] + ax[15:20], res):
    draw(a_, [pal[v] if k and v >= 0 else "#e4e3df" for v, k in zip(mm, keep)], f"{LAB[m]} (ARI {ari:.2f})")
    wrong = keep & (mm != t); draw(ae, [(ERR if w else OK) if k else NONE for w, k in zip(wrong, keep)], f"{100 * wrong.sum() / keep.sum():.0f}% misassigned")
ax[10].axis("off")
ax[10].legend(handles=[Patch(color=ERR, label="Misassigned"), Patch(color=OK, label="Correct"), Patch(color=NONE, label="No annotation")], loc="center", frameon=False, title="Cell status (D)", fontsize=7, title_fontsize=7)
fig.legend(handles=[Patch(color=pal[i], label=n) for i, n in enumerate(names)], loc="lower center", ncol=6, frameon=False, fontsize=6.5, title="CCF division (C)", title_fontsize=7, bbox_to_anchor=(0.5, 0.0))
fig.text(0.5, 0.995, f"Allen MERFISH section {SEC} (held out; middle section by the fixed selection rule), own clustering, seed 0; ordered by ARI", ha="center", va="top", fontsize=8)
fig.text(0.003, 0.955, "C", fontsize=10, fontweight="bold"); fig.text(0.003, 0.50, "D", fontsize=10, fontweight="bold")
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(ROOT, "docs", "figures", f"nar_fig3_allen_v3.{ext}"))
print([(m, round(a_, 3)) for m, _, a_ in res])
