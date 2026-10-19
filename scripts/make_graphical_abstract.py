"""NAR graphical abstract: one landscape 5:2 panel (25.4 x 10.16 cm), vector PDF + 600 dpi PNG/TIFF.

Three columns read left to right: inputs (tissue thumbnails), two findings (mini forest plot under matched clustering;
one embedding, two random starts), take-home checklist. Not a copy of any main figure. Family colours mean method family only.

Data: results/stats_cluster_aware.json ("robust/*" = matched clustering), results/clustering_lottery.jsonl (HiSTaR, DLPFC
151669: the single-start fits with the lowest and highest ARI are refitted here with the same settings to draw the maps),
results/cache/*.npz, results/emb/dlpfc_151669_histar.npy.

python scripts/make_graphical_abstract.py -> docs/figures/nar_graphical_abstract.pdf|png|tif
"""
import json, os, warnings
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture
from PIL import Image

warnings.filterwarnings("ignore")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "docs", "figures")
INK, INK2, LINE = "#0b0b0b", "#4a4a4a", "#c9c8c2"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
DOM = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8c510a", "#3a3a3a", "#6250d6"]
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "pdf.fonttype": 42, "ps.fonttype": 42,
                     "savefig.dpi": 600, "savefig.bbox": "standard"})
W, H = 254.0, 101.6
fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")


def T(x, y, s, size=11, color=INK, weight="normal", ha="left", va="center", **kw):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, **kw)


def cache(ds, s):
    f = os.path.join(ROOT, "results", "cache", f"{s}.npz" if ds == "dlpfc" else f"{ds}_{s}.npz")
    z = np.load(f, allow_pickle=True)
    lab = z["labels"]; names = sorted({v for v in lab if isinstance(v, str)})
    code = np.array([names.index(v) if isinstance(v, str) else -1 for v in lab])
    C = z["coords"].astype(float); C[:, 1] = -C[:, 1]
    return C, code, names


def tissue(C, code, x, y, size, ms):
    c = C - C.min(0); c = c * (size / c.max()); off = (np.array([size, size]) - c.max(0)) / 2
    P = np.c_[x + off[0] + c[:, 0], y + off[1] + c[:, 1]]
    ax.scatter(P[:, 0], P[:, 1], s=ms, c=[DOM[k] if k >= 0 else "#e4e3df" for k in code], lw=0, rasterized=True, zorder=3)


def flow_arrow(x0, x1, y=H / 2):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=14, color=INK2, lw=1.6, zorder=2))


# ---------------------------------------------------------------- column 1: inputs
T(36.0, 92.0, "Benchmark", 14, INK, "bold", ha="center")
for i, (ds, s, lab, ms) in enumerate((("dlpfc", "151673", "Visium", 1.1), ("starmap", "20180417_BZ5_control", "STARmap", 0.9),
                                       ("merfish", "-0.14", "MERFISH", 0.45))):
    C, code, _ = cache(ds, s)
    tissue(C, code, 3.0 + i * 22.5, 50.0, 20.0, ms)
    T(13.0 + i * 22.5, 45.0, lab, 10.5, INK2, ha="center")
T(36.0, 33.0, "20 sections", 13, INK, ha="center")
T(36.0, 25.5, "3 technologies", 13, INK, ha="center")
T(36.0, 18.0, "16 methods", 13, INK, ha="center")
flow_arrow(72.5, 81.0)

# ---------------------------------------------------------------- column 2a: mini forest plot (matched clustering)
cs = json.load(open(os.path.join(ROOT, "results", "stats_cluster_aware.json")))
comp = {k.split("/", 1)[1]: v for k, v in cs["comparisons"].items() if k.startswith("robust/")}
rows = [("linear_diffusion", "Linear diffusion", BLUE), ("bass", "BASS", AQUA), ("banksy_l0.8", "BANKSY λ = 0.8", AQUA),
        ("histar", "HiSTaR", ORANGE), ("graphst", "GraphST", ORANGE)]
T(133.0, 95.0, "Training-free smoothing is among the best", 13, INK, "bold", ha="center")
fx0, fx1 = 120.0, 176.0              # x extent of the forest
xr = (-0.25, 0.08)                   # method minus linear diffusion (ARI)
X = lambda v: fx0 + (v - xr[0]) / (xr[1] - xr[0]) * (fx1 - fx0)
ytop, dy = 86.5, 6.4
ax.add_patch(Rectangle((X(-0.03), ytop - 4 * dy - 3.2), X(0.03) - X(-0.03), 4 * dy + 6.4, fc="#ecebe7", ec="none", zorder=1))
ax.plot([X(0), X(0)], [ytop - 4 * dy - 3.2, ytop + 3.2], color=INK2, lw=0.9, zorder=2)
for i, (m, lab, col) in enumerate(rows):
    yy = ytop - i * dy
    T(fx0 - 3.0, yy, lab, 11, INK, ha="right")
    if m == "linear_diffusion":
        ax.plot(X(0), yy, "D", ms=7, color=col, zorder=4)
        T(X(0) + 3.0, yy, "reference", 10.5, INK2, style="italic"); continue
    v = comp[m]; lo, hi = -v["ci95"][1], -v["ci95"][0]; d = -v["delta"]
    ax.plot([X(lo), X(hi)], [yy, yy], color=col, lw=2.4, solid_capstyle="butt", zorder=3)
    filled = v["ci95"][0] > 0
    ax.plot(X(d), yy, "o", ms=8, mfc=col if filled else "white", mec=col, mew=1.8, zorder=4)
T(X(-0.25), ytop - 4 * dy - 6.6, "← worse", 10, INK2, ha="left")
T(X(0.08), ytop - 4 * dy - 6.6, "better →", 10, INK2, ha="right")

# ---------------------------------------------------------------- column 2b: one embedding, two random starts
T(133.0, 44.5, "Same embedding, different random start", 13, INK, "bold", ha="center")
fits = None
for l in open(os.path.join(ROOT, "results", "clustering_lottery.jsonl")):
    r = json.loads(l)
    if r["method"] == "histar" and r.get("dataset", "dlpfc") == "dlpfc" and str(r["slice"]) == "151669":
        fits = r["fits"]; break
lo_fit, hi_fit = min(fits, key=lambda f: f["ARI"]), max(fits, key=lambda f: f["ARI"])
Zh = np.load(os.path.join(ROOT, "results", "emb", "dlpfc_151669_histar.npy")).astype(np.float64)
Ch, ch, nmh = cache("dlpfc", "151669"); ok = ch >= 0; K = len(nmh)


def refit(f):
    p = GaussianMixture(K, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=f["rs"]).fit(Zh).predict(Zh)
    ari = adjusted_rand_score(ch[ok], p[ok])
    assert abs(ari - f["ARI"]) < 0.01, (ari, f["ARI"])
    pu = np.unique(p[ok]); M = np.array([[np.sum((p == c) & (ch == k)) for k in range(K)] for c in pu])
    r_, c_ = linear_sum_assignment(-M); mp = {pu[i]: c_[j] for j, i in enumerate(r_)}
    return np.where(ok, np.array([mp.get(v, -1) for v in p]), -1)


for (f, x) in ((lo_fit, 101.0), (hi_fit, 143.0)):
    tissue(Ch, refit(f), x, 10.0, 26.0, 1.6)
    T(x + 13.5, 6.0, f"ARI {f['ARI']:.2f}", 13, INK, "bold", ha="center")
# dice between the maps
dx, dyc = 133.6, 24.0
for o in (0.0, 4.2):
    ax.add_patch(FancyBboxPatch((dx - 3.6 + o, dyc - 3.0 + o * 0.35), 5.6, 5.6, boxstyle="round,pad=0,rounding_size=1.0",
                                fc="white", ec=INK2, lw=1.0, zorder=3 + o))
for px, py in ((-2.2, 1.6), (-0.8, 0.0), (0.6, -1.6)): ax.add_patch(Circle((dx + px, dyc + py), 0.45, fc=INK2, zorder=4))
for px, py in ((2.0, 3.4), (4.6, 1.4)): ax.add_patch(Circle((dx + px, dyc + py), 0.45, fc=INK2, zorder=8))
flow_arrow(184.0, 192.5)

# ---------------------------------------------------------------- column 3: take-home checklist
T(222.0, 92.0, "Take-home", 14, INK, "bold", ha="center")
items = ["Report the clustering\nprotocol and its variance", "Never select runs\nwith labels", "Include training-free\nbaselines"]
for i, s in enumerate(items):
    yy = 74.0 - i * 23.0
    ax.add_patch(FancyBboxPatch((197.0, yy - 3.2), 6.4, 6.4, boxstyle="round,pad=0,rounding_size=0.8", fc="white", ec=INK, lw=1.2, zorder=3))
    ax.plot([198.3, 200.0, 204.6], [yy + 0.1, yy - 1.8, yy + 3.6], color=INK, lw=2.0, solid_capstyle="round", zorder=4)
    T(206.5, yy, s, 12, INK, linespacing=1.25)

for ext in ("pdf", "png"):
    fig.savefig(os.path.join(FIG, f"nar_graphical_abstract.{ext}"), facecolor="white")
Image.open(os.path.join(FIG, "nar_graphical_abstract.png")).convert("RGB").save(
    os.path.join(FIG, "nar_graphical_abstract.tif"), compression="tiff_lzw", dpi=(600, 600))
print("written nar_graphical_abstract; HiSTaR 151669 ARI range", round(lo_fit["ARI"], 2), round(hi_fit["ARI"], 2))
