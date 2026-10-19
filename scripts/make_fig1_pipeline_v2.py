"""Figure 1, version 2: illustrative study design with few boxes. Biology shown from the real data (tissue sections, segmented
cells with RNA dots, Visium spot grid, spot graph, domain maps); icons from Bioicons (docs/figures/icons/LICENSES.md).

python scripts/make_fig1_pipeline_v2.py -> docs/figures/nar_fig1_pipeline_v2.pdf|png
"""
import io, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Rectangle, Polygon, FancyBboxPatch, RegularPolygon
import cairosvg
from PIL import Image
from scipy.spatial import cKDTree, Voronoi
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "docs", "figures"); ICON = os.path.join(FIG, "icons")
INK, INK2, MUTE, LINE = "#0b0b0b", "#52514e", "#8a8984", "#d6d5cf"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
DOM = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#52514e", "#e34948"]
RNA = ["#e34948", "#eda100", "#1baf7a", "#2a78d6", "#6250d6"]
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "pdf.fonttype": 42, "savefig.dpi": 600})
W, H = 175.0, 104.0
Y0 = 6.0
fig = plt.figure(figsize=(W / 25.4, (H - Y0) / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(Y0, H); ax.axis("off")
rng = np.random.default_rng(7)


TXT2 = "#4a4a4a"  # secondary text: darker than before for contrast


def T(x, y, s, size=6.5, color=INK, weight="normal", ha="left", va="center", style="normal", **kw):
    size = max(size, 6.5)  # nothing below 6.5 pt at final size (figure is printed at 100%)
    if color in (MUTE, INK2): color = TXT2
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, style=style, **kw)


def icon(name, x, y, h, w=None, z=3):
    png = cairosvg.svg2png(url=os.path.join(ICON, name), output_height=700)
    im = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    ar = im.shape[1] / im.shape[0]; w = w or h * ar
    if w / h > ar: w = h * ar
    else: h = w / ar
    ax.imshow(im, extent=[x, x + w, y, y + h], zorder=z, interpolation="lanczos")
    return w, h


def arrow(x0, y0, x1, y1, color=MUTE, lw=1.0, ms=6, rad=0.0, z=2, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=z,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


def header(x, n, title):
    T(x + 0.4, 99.6, n, 10, INK, "bold", zorder=5)
    T(x + 4.6, 99.5, title, 7.5, INK, zorder=5)


def cache(ds, s):
    f = os.path.join(ROOT, "results", "cache", f"{s}.npz" if ds == "dlpfc" else f"{ds}_{s}.npz")
    z = np.load(f, allow_pickle=True)
    lab = z["labels"]; names = sorted({v for v in lab if isinstance(v, str)})
    code = np.array([names.index(v) if isinstance(v, str) else -1 for v in lab])
    C = z["coords"].astype(float); C[:, 1] = -C[:, 1]
    return C, code, names


def place(C, x, y, size):
    c = C - C.min(0); sc = size / c.max(); c = c * sc
    off = (np.array([size, size]) - c.max(0)) / 2
    return np.c_[x + off[0] + c[:, 0], y + off[1] + c[:, 1]], sc


def tissue(C, code, x, y, size, ms, alpha=1.0, z=3):
    P, sc = place(C, x, y, size)
    ax.scatter(P[:, 0], P[:, 1], s=ms, c=[DOM[k] if k >= 0 else "#dddcd6" for k in code], lw=0, alpha=alpha, rasterized=True, zorder=z)
    return P


def zoom_cells(C, code, centre_idx, x, y, r, n_cells=26, dots=7):
    """Voronoi cells around a real cell, clipped to a circle, filled by domain colour, with RNA molecules as dots."""
    d = np.linalg.norm(C - C[centre_idx], axis=1); sel = np.argsort(d)[:n_cells * 3]
    Q = C[sel] - C[centre_idx]; Q = Q / np.sort(np.linalg.norm(Q, axis=1))[n_cells] * r
    lab = code[sel]
    clip = Circle((x, y), r, transform=ax.transData)
    vor = Voronoi(Q)
    for i, reg_i in enumerate(vor.point_region):
        reg = vor.regions[reg_i]
        if -1 in reg or not reg: continue
        poly = vor.vertices[reg] * 0.93 + Q[i] * 0.07
        p = Polygon(poly + [x, y], closed=True, fc=DOM[lab[i]] if lab[i] >= 0 else "#dddcd6", ec="white", lw=0.5, alpha=0.32, zorder=4)
        ax.add_patch(p); p.set_clip_path(clip)
        nuc = Circle((Q[i, 0] + x, Q[i, 1] + y), r * 0.07, fc="#9a98c9", ec="none", alpha=0.7, zorder=5); ax.add_patch(nuc); nuc.set_clip_path(clip)
        for _ in range(dots):
            o = rng.normal(0, r * 0.075, 2)
            dd = Circle((Q[i, 0] + o[0] + x, Q[i, 1] + o[1] + y), r * 0.022, fc=RNA[rng.integers(0, len(RNA))], ec="none", zorder=6)
            ax.add_patch(dd); dd.set_clip_path(clip)
    ax.add_patch(Circle((x, y), r, fc="none", ec=INK2, lw=0.7, zorder=7))


# ------------------------------------------------------------------ headers and flow
X = [1.0, 45.0, 75.0, 115.0, 145.0]
for x, n, t in zip(X, "ABCDE", ["Tissue and technology", "Spots and graph", "Methods", "Clustering", "Evaluation"]):
    header(x, n, t)
for x0, x1 in ((42.5, 45.5), (72.3, 75.2), (112.2, 115.2), (142.0, 144.6)):
    arrow(x0, 55.6, x1, 55.6, color=INK2, lw=1.1, ms=7)

# ------------------------------------------------------------------ 1 tissue and technology
# human DLPFC on a Visium capture area
icon("brain-1.svg", 1.5, 84.0, 9.0, w=12.5)
ax.add_patch(Ellipse((4.6, 90.0), 3.4, 2.4, fc="#c0392b", ec="none", alpha=0.75, zorder=4))
arrow(5.0, 87.6, 19.4, 82.5, color=MUTE, lw=0.7, ms=5, rad=0.25)
cap_x, cap_y, cap = 20.4, 69.5, 16.0
ax.add_patch(Rectangle((cap_x - 1.0, cap_y - 1.0), cap + 2.0, cap + 2.0, fc="#eef3f8", ec="#9db7d6", lw=0.6, zorder=2))
for i in range(28):
    for j in range(28):
        ax.add_patch(Circle((cap_x + (j + 0.5 * (i % 2)) * cap / 28, cap_y + i * cap / 28), 0.12, fc="#c5d3e3", ec="none", zorder=2.5))
C, code, names = cache("dlpfc", "151673")
tissue(C, code, cap_x, cap_y, cap, 0.42, z=3)
T(1.5, 81.0, "10x Visium", 7, INK, "bold"); T(1.5, 77.9, "human DLPFC", 6.5, INK2); T(1.5, 75.1, "12 sections", 6.5, MUTE); T(1.5, 72.3, "3 donors", 6.5, MUTE)
T(cap_x + cap / 2, cap_y - 2.6, "55 µm barcoded spots", 5.2, MUTE, ha="center")
# STARmap: mouse -> section -> zoom of cells
icon("Mouse.svg", 1.0, 53.8, 4.4, w=8.0)
T(9.6, 56.6, "STARmap", 7, INK, "bold"); T(9.6, 53.7, "mouse mPFC with 3 sections", 6.5, INK2)
Cs, cs, _ = cache("starmap", "20180417_BZ5_control")
Ps = tissue(Cs, cs, 2.5, 34.6, 22.0, 1.0)
ann = np.where(cs >= 0)[0]; ci = ann[np.argmin(np.linalg.norm(Cs[ann] - np.median(Cs[ann], 0), axis=1))]
zoom_cells(Cs, cs, ci, 35.2, 43.0, 6.4, n_cells=22, dots=6)
ax.plot([Ps[ci, 0] + 1.0, 35.2 - 6.4], [Ps[ci, 1], 43.0], color=MUTE, lw=0.5, zorder=3)
ax.add_patch(Circle(Ps[ci], 1.0, fc="none", ec=INK2, lw=0.6, zorder=6))
# MERFISH
icon("Mouse.svg", 1.0, 29.6, 4.4, w=8.0)
T(9.6, 31.6, "MERFISH", 7, INK, "bold"); T(9.6, 28.7, "mouse hypothalamus with 5 sections", 6.5, INK2)
Cm, cm, _ = cache("merfish", "-0.14")
Pm = tissue(Cm, cm, 3.0, 11.0, 15.5, 0.3)
annm = np.where(cm >= 0)[0]
tgt = np.median(Cm[annm], 0)
cand = annm[np.argsort(np.linalg.norm(Cm[annm] - tgt, axis=1))[:400]]
def ann_frac(i):
    d = np.linalg.norm(Cm - Cm[i], axis=1); nb = np.argsort(d)[:40]; return (cm[nb] >= 0).mean() + 0.2 * (len(set(cm[nb][cm[nb] >= 0])) > 1)
cim = max(cand[::20], key=ann_frac)
zoom_cells(Cm, cm, cim, 33.0, 19.0, 6.0, n_cells=22, dots=6)
ax.plot([Pm[cim, 0] + 1.0, 33.0 - 6.0], [Pm[cim, 1], 19.0], color=MUTE, lw=0.5, zorder=3)
ax.add_patch(Circle(Pm[cim], 1.0, fc="none", ec=INK2, lw=0.6, zorder=6))
T(33.0, 11.0, "Cells and RNA molecules", 6.5, MUTE, ha="center")
T(1.0, 7.9, "Colours show the expert annotation used only for scoring", 6.5, MUTE, style="italic")

# ------------------------------------------------------------------ 2 spots and graph
gx, gy, gr = 58.0, 75.0, 10.5
cen = C[np.argmin(np.linalg.norm(C - np.median(C, 0), axis=1))]
d = np.linalg.norm(C - cen, axis=1); sel = np.argsort(d)[:30]
Q = (C[sel] - cen); Q = Q / np.abs(Q).max() * (gr * 0.78) + [gx, gy]
_, nn = cKDTree(Q).query(Q, 7)
ax.add_patch(Circle((gx, gy), gr, fc="#fbfaf8", ec=INK2, lw=0.7, zorder=2))
for i in range(len(Q)):
    for j in nn[i, 1:]:
        ax.plot(Q[[i, j], 0], Q[[i, j], 1], color="#b9b8b2", lw=0.35, zorder=3)
ax.scatter(Q[:, 0], Q[:, 1], s=9, c=[DOM[k] for k in code[sel]], ec="white", lw=0.3, zorder=4)
# expression profile of one spot
k0 = 0; px, py = Q[k0]
for b in range(6):
    hgt = rng.uniform(0.6, 3.2)
    ax.add_patch(Rectangle((px + 3.0 + b * 0.75, py + 2.4), 0.55, hgt, fc=RNA[b % 5], ec="none", zorder=6))
ax.plot([px, px + 2.8], [py, py + 2.4], color=INK2, lw=0.4, zorder=5)
T(gx, gy - gr - 2.8, "Expression profiles", 7, INK, ha="center")
T(gx, gy - gr - 5.8, "6-nearest-neighbour graph", 7, INK, ha="center")
T(gx, 46.5, "Normalisation and 2000 HVGs", 6.5, MUTE, ha="center"); T(gx, 43.7, "PCA with 200 or 50 PCs", 6.5, MUTE, ha="center")
T(gx, 37.5, "True number of", 6.5, MUTE, ha="center", style="italic"); T(gx, 34.7, "domains given", 6.5, MUTE, ha="center", style="italic")
T(gx, 21.0, "Baselines use this graph", 6.5, MUTE, ha="center", style="italic"); T(gx, 18.2, "other methods build their own", 6.5, MUTE, ha="center", style="italic")

# ------------------------------------------------------------------ 3 methods (no boxes)
def fam_title(y, col, t, n):
    ax.add_patch(Circle((77.0, y), 1.3, fc=col, ec="none", zorder=4))
    for k, line in enumerate(t.split("\n")):
        T(79.2, y - 2.9 * k, line, 7, INK, "bold")
    T(111.6, y, n, 7, col, "bold", ha="right")
fam_title(90.5, ORANGE, "Deep graph encoders", "9")
icon("neural-network-1.svg", 77.0, 75.5, 10.5, w=10.5)
for j, nm in enumerate(["HiSTaR", "GraphST", "STAGATE", "SEDR", "SpaceFlow", "CCST", "Spatial-MGCN", "DeepST", "SpaGCN"]):
    T(89.0 if j < 5 else 100.6, 86.8 - (j if j < 5 else j - 5) * 2.9, nm, 6.5, INK2)
fam_title(68.0, AQUA, "Statistical and\nneighbourhood methods", "4")
xs = np.linspace(-3, 3, 60)
for mu, sd, a in ((-0.9, 0.7, 0.9), (1.0, 0.9, 0.7)):
    yv = np.exp(-0.5 * ((xs - mu) / sd) ** 2)
    ax.fill_between(82.0 + xs * 1.6, 52.0, 52.0 + yv * 9 * a, color=AQUA, alpha=0.35, lw=0, zorder=2)
    ax.plot(82.0 + xs * 1.6, 52.0 + yv * 9 * a, color=AQUA, lw=0.9, zorder=3)
ax.plot([77.0, 87.5], [52.0, 52.0], color=INK2, lw=0.6, zorder=3)
for j, nm in enumerate(["BANKSY (λ = 0.2, 0.8)", "NichePCA", "BASS", "BayesSpace"]):
    T(89.0, 61.2 - j * 2.9, nm, 6.5, INK2)
fam_title(41.5, BLUE, "Training-free baselines", "3")
# heat diffusion over a real tissue patch
sel2 = np.argsort(np.linalg.norm(C - cen, axis=1))[:160]
Qd = C[sel2] - cen; Qd = Qd / np.abs(Qd).max() * 6.0 + [83.0, 29.0]
seed = Qd[np.argmin(Qd[:, 0] + Qd[:, 1])]
val = np.exp(-np.linalg.norm(Qd - seed, axis=1) / 3.5)
ax.scatter(Qd[:, 0], Qd[:, 1], s=3.2, c=[plt.cm.Blues(0.15 + 0.8 * v) for v in val], lw=0, zorder=3)
for j, nm in enumerate(["Linear diffusion", "AnisoST", "PCA"]):
    T(91.0, 37.4 - j * 2.9, nm, 6.5, INK2)
T(93.5, 15.0, "Official code with published settings", 6.5, MUTE, ha="center", style="italic")
T(93.5, 12.2, "Output is an embedding or domain labels", 6.5, MUTE, ha="center", style="italic")

# ------------------------------------------------------------------ 4 clustering
z = np.load(os.path.join(ROOT, "results", "runs", "dlpfc__151673__linear_diffusion__s0.npz"))
E2 = PCA(2, random_state=0).fit_transform(z["emb"].astype(float))
E2 = E2[np.random.default_rng(0).choice(len(E2), 900, replace=False)]
E2 = (E2 - E2.min(0)) / (E2.max(0) - E2.min(0))
Pe = np.c_[116.5 + E2[:, 0] * 25.0, 73.5 + E2[:, 1] * 17.0]
gm = GaussianMixture(5, covariance_type="full", random_state=2, n_init=3).fit(Pe); l2 = gm.predict(Pe)
ax.scatter(Pe[:, 0], Pe[:, 1], s=0.8, c=[DOM[l] for l in l2], lw=0, alpha=0.8, rasterized=True, zorder=3)
for k_ in range(5):
    w_, v_ = np.linalg.eigh(gm.covariances_[k_]); ang = np.degrees(np.arctan2(v_[1, 1], v_[0, 1]))
    ax.add_patch(Ellipse(gm.means_[k_], 3.2 * np.sqrt(w_[1]), 3.2 * np.sqrt(w_[0]), angle=ang, fc="none", ec=INK, lw=0.55, zorder=4))
T(129.0, 70.4, "Gaussian mixture", 6.5, INK2, ha="center"); T(129.0, 67.6, "on the embedding", 6.5, INK2, ha="center")
rows = [("dice", "Random starts", "Same embedding"), ("perm", "R random seeds", "R mclust default fit"), ("best", "Matched clustering", "Versus default clustering")]
for i, (g, t1, t2) in enumerate(rows):
    y0 = (61.5, 50.6, 41.0)[i]; gx_ = 116.8
    if g == "dice":
        for o, a_ in ((0, 10), (2.4, -12)):
            ax.add_patch(FancyBboxPatch((gx_ - 2.0 + o, y0 - 2.0 + o * 0.3), 3.6, 3.6, boxstyle="round,pad=0,rounding_size=0.6", fc="white", ec=INK, lw=0.6, zorder=3 + o))
        for px_, py_ in ((-1.0, 0.9), (0.4, -0.5), (-0.3, 0.2)): ax.add_patch(Circle((gx_ + px_ + 0.1, y0 + py_ - 0.1), 0.28, fc=INK, zorder=4))
        for px_, py_ in ((1.6, 1.8), (2.9, 0.5)): ax.add_patch(Circle((gx_ + px_, y0 + py_), 0.28, fc=INK, zorder=6))
    elif g == "perm":
        ax.add_patch(FancyArrowPatch((gx_ - 2.2, y0 + 1.2), (gx_ + 3.0, y0 - 1.2), arrowstyle="-|>", mutation_scale=4.5, color=INK, lw=0.7, zorder=3, connectionstyle="arc3,rad=-0.3"))
        ax.add_patch(FancyArrowPatch((gx_ - 2.2, y0 - 1.2), (gx_ + 3.0, y0 + 1.2), arrowstyle="-|>", mutation_scale=4.5, color=INK, lw=0.7, zorder=3, connectionstyle="arc3,rad=0.3"))
    else:
        for k_ in range(3): ax.add_patch(Ellipse((gx_ + 0.4 + k_ * 0.45, y0 + 0.2 - k_ * 0.25), 4.4, 2.4, angle=25, fc="none", ec=MUTE if k_ < 2 else INK, lw=0.7, zorder=3))
        T(gx_ + 3.0, y0 + 2.0, "★", 6.5, INK, ha="center")
    T(122.3, y0 + 1.5, t1, 7, INK); T(122.3, y0 - 1.6, t2, 6.5, MUTE)


# ------------------------------------------------------------------ 4b one embedding, 20 random starts (real data)
from sklearn.metrics import adjusted_rand_score
Zh = np.load(os.path.join(ROOT, "results", "emb", "dlpfc_151669_histar.npy")).astype(float)
Ch, ch, nmh = cache("dlpfc", "151669"); okh = ch >= 0; Kh = len(nmh)
fits = []
for r in range(20):
    g_ = GaussianMixture(Kh, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=r).fit(Zh)
    p_ = g_.predict(Zh); fits.append((adjusted_rand_score(ch[okh], p_[okh]), p_))
aris = np.array([f[0] for f in fits])
T(129.0, 34.0, "ARI of 20 random starts", 7, INK, ha="center")
sx0, sx1, sy = 120.5, 137.5, 30.0
lo, hi = aris.min(), aris.max()
ax.plot([sx0, sx1], [sy, sy], color=LINE, lw=0.6, zorder=2)
sxv = lambda v: sx0 + (v - lo) / (hi - lo) * (sx1 - sx0)
for v in aris:
    ax.add_patch(Circle((sxv(v), sy + rng.uniform(-0.3, 0.3)), 0.5, fc=INK2, ec="white", lw=0.2, alpha=0.85, zorder=3))
ax.plot([sx0, 122.6], [sy - 0.9, 27.0], color=MUTE, lw=0.5, zorder=2); ax.plot([sx1, 135.8], [sy - 0.9, 27.0], color=MUTE, lw=0.5, zorder=2)
def matched(pred):
    pu = np.unique(pred[okh]); Mx = np.zeros((len(pu), Kh))
    for i, c_ in enumerate(pu):
        for k_ in range(Kh): Mx[i, k_] = np.sum((pred == c_) & (ch == k_))
    r_, c2 = linear_sum_assignment(-Mx); mp = {pu[i]: c2[j] for j, i in enumerate(r_)}
    return np.where(okh, np.array([mp.get(v, -1) for v in pred]), -1)
iw, ib = int(np.argmin(aris)), int(np.argmax(aris))
tissue(Ch, matched(fits[iw][1]), 116.6, 13.6, 12.0, 0.32)
tissue(Ch, matched(fits[ib][1]), 129.8, 13.6, 12.0, 0.32)
T(122.6, 11.8, f"ARI {aris[iw]:.2f}", 7, INK, ha="center"); T(135.8, 11.8, f"ARI {aris[ib]:.2f}", 7, INK, ha="center")
T(129.0, 8.6, "HiSTaR on DLPFC section 151669", 6.5, MUTE, ha="center")

# ------------------------------------------------------------------ 5 evaluation
Ct, ct, nm_t = cache("dlpfc", "151673")
pred = np.load(os.path.join(ROOT, "results", "runs", "dlpfc__151673__linear_diffusion__s0.npz"))["labels"]
keep = ct >= 0; K = len(nm_t); pu = np.unique(pred[keep]); Mx = np.zeros((len(pu), K))
for i, c_ in enumerate(pu):
    for k_ in range(K): Mx[i, k_] = np.sum((pred == c_) & (ct == k_))
r_, c2 = linear_sum_assignment(-Mx); mp = {pu[i]: c2[j] for j, i in enumerate(r_)}
pm = np.array([mp.get(v, -1) for v in pred])
tissue(Ct, ct, 146.0, 76.0, 12.5, 0.3)
tissue(Ct, np.where(keep, pm, -1), 160.5, 76.0, 12.5, 0.3)
T(152.2, 74.2, "Annotation", 6.5, MUTE, ha="center"); T(166.7, 74.2, "Prediction", 6.5, MUTE, ha="center")
T(159.0, 82.2, "vs", 6.0, INK2, ha="center")
for j, (t1, t2) in enumerate((("Agreement", "ARI, NMI and AMI"), ("Domain and spatial quality", "macro-F1, CHAOS and PAS"), ("Cost", "run time and memory"))):
    T(145.6, 68.2 - j * 6.3, t1, 6.8, INK); T(145.6, 65.4 - j * 6.3, t2, 6.5, MUTE)
tx, ty = 159.5, 44.5
T(tx, 47.6, "Bootstrap over donors", 6.8, INK, ha="center"); T(tx, 44.8, "and datasets", 6.8, INK, ha="center")
ax.add_patch(Circle((tx, ty - 3.2), 0.9, fc=INK2, zorder=3))
for i, xx in enumerate([tx - 8.0, tx - 4.0, tx, tx + 4.0, tx + 8.0]):
    ax.plot([tx, xx], [ty - 3.2, ty - 7.6], color=MUTE, lw=0.5, zorder=2)
    ax.add_patch(Circle((xx, ty - 7.6), 0.75, fc=INK2, zorder=3))
    for d_ in ((-0.9, 0, 0.9) if i < 3 else (-0.9, 0.9)):
        ax.plot([xx, xx + d_], [ty - 7.6, ty - 10.8], color=MUTE, lw=0.4, zorder=2); ax.add_patch(Circle((xx + d_, ty - 10.8), 0.32, fc=MUTE, zorder=3))
ry = 24.5
ax.add_patch(Rectangle((tx - 1.3, ry - 4.4), 2.6, 9.0, fc="#e7e6e1", ec="none", zorder=1.5))
for i, (c0, c1, m) in enumerate(((0.4, 3.0, 1.6), (2.0, 6.4, 4.0), (5.0, 9.6, 7.2))):
    yy = ry + 3.0 - i * 3.0
    ax.plot([148.5 + c0 * 2.2, 148.5 + c1 * 2.2], [yy, yy], color=[BLUE, AQUA, ORANGE][i], lw=1.2, solid_capstyle="round", zorder=3)
    ax.add_patch(Circle((148.5 + m * 2.2, yy), 0.6, fc=[BLUE, AQUA, ORANGE][i], zorder=4))
T(tx, 16.2, "Differences and ranks", 6.5, MUTE, ha="center"); T(tx, 13.4, "with an equivalence margin", 6.5, MUTE, ha="center")

for ext in ("pdf", "png"):
    fig.savefig(os.path.join(FIG, f"nar_fig1_pipeline_v2.{ext}"))
print("written nar_fig1_pipeline_v2")
