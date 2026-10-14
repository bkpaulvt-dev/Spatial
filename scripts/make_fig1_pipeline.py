"""Figure 1: study design / pipeline (NAR double column, 17.5 cm). Vector shapes and text; tissue thumbnails and the
embedding are drawn from the real data; icons from Bioicons (licences in docs/figures/icons/LICENSES.md).

python scripts/make_fig1_pipeline.py -> docs/figures/nar_fig1_pipeline.pdf|png
"""
import io, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse, Circle, FancyArrowPatch, Rectangle, Polygon
import cairosvg
from PIL import Image
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "docs", "figures"); ICON = os.path.join(FIG, "icons")
INK, INK2, MUTE, LINE, PANEL = "#0b0b0b", "#52514e", "#8a8984", "#d6d5cf", "#f6f5f2"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
DOM = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#52514e", "#e34948"]
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "pdf.fonttype": 42, "savefig.dpi": 600})
W, H = 175.0, 112.0                                   # figure in millimetres
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")


def T(x, y, s, size=6.2, color=INK, weight="normal", ha="left", va="center", style="normal", **kw):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, style=style, **kw)


def box(x, y, w, h, fc=PANEL, ec="none", lw=0.6, r=1.6, z=0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, zorder=z))


def icon(name, x, y, h, w=None, z=3):
    png = cairosvg.svg2png(url=os.path.join(ICON, name), output_height=600)
    im = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    ar = im.shape[1] / im.shape[0]; w = w or h * ar
    if w / h > ar: w = h * ar
    else: h = w / ar
    ax.imshow(im, extent=[x, x + w, y, y + h], zorder=z, interpolation="lanczos")
    return w


def arrow(x0, y0, x1, y1, color=MUTE, lw=1.1, ms=7, z=2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=ms, color=color, lw=lw, zorder=z,
                                 shrinkA=0, shrinkB=0))


def header(x, n, title, w):
    ax.add_patch(Circle((x + 2.4, 106.2), 2.3, fc=INK, ec="none", zorder=4))
    T(x + 2.4, 106.15, n, 6.5, "white", "bold", ha="center")
    T(x + 5.6, 106.2, title, 7.6, INK, "bold")


def cache(ds, s):
    f = os.path.join(ROOT, "results", "cache", f"{s}.npz" if ds == "dlpfc" else f"{ds}_{s}.npz")
    z = np.load(f, allow_pickle=True)
    return z["coords"].astype(float), z["labels"]


def thumb(ds, s, x, y, size, flip=True, ms=0.6):
    C, lab = cache(ds, s)
    names = sorted({v for v in lab if isinstance(v, str)}); code = {n: i for i, n in enumerate(names)}
    col = [DOM[code[v]] if isinstance(v, str) else "#dddcd6" for v in lab]
    c = C - C.min(0); sc = size / c.max(); c = c * sc
    if flip: c[:, 1] = c[:, 1].max() - c[:, 1]
    off = (size - c.max(0)) / 2
    ax.scatter(x + off[0] + c[:, 0], y + off[1] + c[:, 1], s=ms, c=col, lw=0, rasterized=True, zorder=3)


# ------------------------------------------------------------------ column frames
XA, WA = 1.5, 40.0; XB, WB = 43.0, 27.5; XC, WC = 72.0, 40.5; XD, WD = 114.0, 29.5; XE, WE = 145.0, 28.5
TOP, BOT = 101.5, 26.0
for x, w in ((XA, WA), (XB, WB), (XC, WC), (XD, WD), (XE, WE)):
    box(x, BOT, w, TOP - BOT, fc=PANEL, r=2.0, z=0)
def header(x, n, title):
    ax.add_patch(Circle((x + 2.4, 106.2), 2.3, fc=INK, ec="none", zorder=4))
    T(x + 2.4, 106.1, n, 6.6, "white", "bold", ha="center", zorder=5)
    T(x + 5.6, 106.2, title, 7.6, INK, "bold", zorder=5)
for x, n, t in ((XA, "1", "Data"), (XB, "2", "Preprocessing"), (XC, "3", "Methods"), (XD, "4", "Clustering"), (XE, "5", "Evaluation")):
    header(x, n, t)
for x0, x1 in ((XA + WA, XB), (XB + WB, XC), (XC + WC, XD), (XD + WD, XE)):
    arrow(x0 + 0.1, 63.5, x1 - 0.1, 63.5, color=INK2, lw=1.2, ms=8, z=6)

# ------------------------------------------------------------------ 1 Data
cards = [("dlpfc", "151673", "10x Visium", "human DLPFC", ["12 sections, 3 donors", "~4k spots, 33.5k genes", "5–7 layers"], "brain-1.svg", "glassslide-top.svg"),
         ("starmap", "20180417_BZ5_control", "STARmap", "mouse mPFC", ["3 sections", "~1.1k cells, 166 genes", "4 layers"], "Mouse.svg", "microscope-cartoon.svg"),
         ("merfish", "-0.14", "MERFISH", "mouse hypothalamus", ["5 sections", "~5.7k cells, 155 genes", "8 regions"], "Mouse.svg", "microscope-cartoon.svg")]
CH = 22.0
for i, (ds, s, tech, tissue, lines, org, inst) in enumerate(cards):
    y0 = 77.5 - i * (CH + 2.2)
    box(XA + 1.2, y0, WA - 2.4, CH, fc="white", ec=LINE, lw=0.5, r=1.4, z=1)
    thumb(ds, s, XA + 2.2, y0 + 2.0, 16.0, ms=0.5 if ds != "starmap" else 1.5)
    tx = XA + 19.6
    T(tx, y0 + 18.6, tech, 6.6, INK, "bold"); T(tx, y0 + 15.2, tissue, 6.0, INK2)
    for j, l in enumerate(lines): T(tx, y0 + 11.4 - j * 3.1, l, 5.7, INK2)
    icon(inst, XA + WA - 10.6, y0 + 0.9, 3.8, w=4.6)
    icon(org, XA + WA - 6.0, y0 + 1.0, 3.4, w=4.4)
T(XA + WA / 2, BOT + 2.0, "annotation used only for scoring", 5.6, MUTE, ha="center", style="italic")

# ------------------------------------------------------------------ 2 Preprocessing
bx = XB; cx = XB + WB / 2
rng = np.random.default_rng(3); M = rng.gamma(0.6, 1.0, (6, 8))
for i in range(6):
    for j in range(8):
        v = min(M[i, j] / 2.2, 1)
        ax.add_patch(Rectangle((bx + 2.2 + j * 1.45, 90.6 + i * 1.3), 1.3, 1.15, fc=plt.cm.Blues(0.12 + 0.75 * v), ec="none", zorder=2))
T(bx + 14.6, 95.6, "counts", 6.0, INK, "bold"); T(bx + 14.6, 92.6, "spots × genes", 5.6, MUTE)
steps = [["normalise, log1p"], ["2,000 HVGs (Visium)", "all genes (panels)"], ["PCA (200 / 50 PCs)"]]
yy = 88.4
for st in steps:
    arrow(cx, yy + 1.6, cx, yy + 0.1, color=MUTE, lw=0.8, ms=5)
    hb = 4.6 if len(st) == 1 else 7.4
    box(bx + 1.2, yy - hb, WB - 2.4, hb, fc="white", ec=LINE, lw=0.5, r=1.0, z=1)
    if len(st) == 1: T(cx, yy - hb / 2, st[0], 5.8, INK, ha="center")
    else: T(cx, yy - 2.3, st[0], 5.8, INK, ha="center"); T(cx, yy - 5.2, st[1], 5.5, MUTE, ha="center")
    yy -= hb + 2.0
C, lab = cache("dlpfc", "151673")
cen = C.mean(0); d = np.linalg.norm(C - cen, axis=1); sel = np.argsort(d)[:40]; P = C[sel]
P = (P - P.min(0)) / (P.max(0) - P.min(0)).max() * 16.0
gx, gy = cx - P[:, 0].max() / 2, 39.0
_, nn = cKDTree(P).query(P, 7)
for i in range(len(P)):
    for j in nn[i, 1:]:
        ax.plot([gx + P[i, 0], gx + P[j, 0]], [gy + P[i, 1], gy + P[j, 1]], color="#b9b8b2", lw=0.35, zorder=2)
ax.scatter(gx + P[:, 0], gy + P[:, 1], s=4.0, color=INK2, lw=0, zorder=3)
arrow(cx, yy + 1.6, cx, 56.6, color=MUTE, lw=0.8, ms=5)
T(cx, 35.6, "spatial 6-NN graph", 5.8, INK, ha="center")
T(cx, BOT + 4.6, "true number of", 5.5, MUTE, ha="center", style="italic"); T(cx, BOT + 2.0, "domains given", 5.5, MUTE, ha="center", style="italic")

# ------------------------------------------------------------------ 3 Methods
fams = [(ORANGE, "Graph / deep encoders", "9", ["HiSTaR", "GraphST", "STAGATE", "SEDR", "SpaceFlow", "CCST", "Spatial-MGCN", "DeepST", "SpaGCN"], "nn"),
        (AQUA, "Statistical / Bayesian", "4", ["BANKSY", "NichePCA", "BASS", "BayesSpace"], "bayes"),
        (BLUE, "Training-free baselines", "3", ["linear diffusion", "AnisoST", "PCA"], "diff")]
ys = [77.5, 53.3, 32.0]; hs = [22.0, 22.0, 19.0]
for (col, title, n, names, kind), y0, h in zip(fams, ys, hs):
    box(XC + 1.2, y0, WC - 2.4, h, fc="white", ec=col, lw=0.9, r=1.4, z=1)
    ax.add_patch(Rectangle((XC + 1.6, y0 + h - 4.8), WC - 3.2, 4.4, fc=col, ec="none", zorder=1.5, alpha=0.14))
    T(XC + 2.8, y0 + h - 2.6, title, 6.2, INK, "bold"); T(XC + WC - 2.6, y0 + h - 2.6, n, 6.6, col, "bold", ha="right")
    gx0, gy0 = XC + 2.8, y0 + 2.0
    if kind == "nn":
        icon("neural-network-1.svg", gx0, gy0 + 2.8, 10.0, w=10.0)
    elif kind == "bayes":
        xs = np.linspace(-3, 3, 60)
        for mu, sd, a in ((-0.9, 0.7, 0.9), (1.0, 0.9, 0.7)):
            yv = np.exp(-0.5 * ((xs - mu) / sd) ** 2)
            ax.fill_between(gx0 + 5 + xs * 1.6, gy0 + 3.5, gy0 + 3.5 + yv * 8 * a, color=AQUA, alpha=0.35, lw=0, zorder=2)
            ax.plot(gx0 + 5 + xs * 1.6, gy0 + 3.5 + yv * 8 * a, color=AQUA, lw=0.9, zorder=3)
        ax.plot([gx0, gx0 + 10.4], [gy0 + 3.5, gy0 + 3.5], color=INK2, lw=0.6, zorder=3)
    else:
        pts = np.array([[0, 0], [3, 1.6], [3, -1.6], [6, 3], [6, 0], [6, -3], [9, 1.6], [9, -1.6]], float)
        Ed = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (2, 5), (3, 6), (4, 6), (4, 7), (5, 7), (1, 2), (6, 7)]
        for a_, b_ in Ed: ax.plot(gx0 + 0.5 + pts[[a_, b_], 0], gy0 + 5.5 + pts[[a_, b_], 1], color="#b9b8b2", lw=0.6, zorder=2)
        val = np.exp(-np.linalg.norm(pts - pts[0], axis=1) / 4.0)
        ax.scatter(gx0 + 0.5 + pts[:, 0], gy0 + 5.5 + pts[:, 1], s=12, c=[plt.cm.Blues(0.25 + 0.7 * v) for v in val], ec=INK2, lw=0.3, zorder=3)
    k = (len(names) + 1) // 2 if len(names) > 4 else len(names)
    for j, nm in enumerate(names):
        cxn = XC + 15.2 if j < k else XC + 25.6
        cy = y0 + h - 7.6 - (j if j < k else j - k) * 3.0
        T(cxn, cy, nm, 5.6, INK2)
T(XC + WC / 2, BOT + 2.0, "official code, published settings", 5.6, MUTE, ha="center", style="italic")

# ------------------------------------------------------------------ 4 Clustering
z = np.load(os.path.join(ROOT, "results", "runs", "dlpfc__151673__linear_diffusion__s0.npz"))
E2 = PCA(2, random_state=0).fit_transform(z["emb"].astype(float))
sub = np.random.default_rng(0).choice(len(E2), 900, replace=False); E2 = E2[sub]
E2 = (E2 - E2.min(0)) / (E2.max(0) - E2.min(0))
ex, ey, ew, eh = XD + 2.4, 79.0, WD - 4.8, 16.0
Pm = np.c_[ex + E2[:, 0] * ew, ey + E2[:, 1] * eh]
gm = GaussianMixture(5, covariance_type="full", random_state=2, n_init=3).fit(Pm); lab2 = gm.predict(Pm)
ax.scatter(Pm[:, 0], Pm[:, 1], s=0.8, c=[DOM[l] for l in lab2], lw=0, alpha=0.8, rasterized=True, zorder=3)
for k_ in range(5):
    w_, v_ = np.linalg.eigh(gm.covariances_[k_]); ang = np.degrees(np.arctan2(v_[1, 1], v_[0, 1]))
    ax.add_patch(Ellipse(gm.means_[k_], 2 * 1.6 * np.sqrt(w_[1]), 2 * 1.6 * np.sqrt(w_[0]), angle=ang, fc="none", ec=INK, lw=0.55, zorder=4))
T(XD + WD / 2, 97.8, "embedding → Gaussian mixture", 5.7, INK2, ha="center")
prot = [("own", "own clustering", "mclust, Leiden, k-means"), ("best", "20 starts, best fit", "label-free selection"),
        ("dice", "20 single starts", "the 'lottery'"), ("perm", "R mclust perturbed", "spot order · 1% noise")]
for i, (g, t1, t2) in enumerate(prot):
    y0 = 71.0 - i * 10.6
    box(XD + 1.2, y0 - 4.3, WD - 2.4, 9.0, fc="white", ec=LINE, lw=0.5, r=1.0, z=1)
    gx = XD + 4.4
    if g == "own":
        for k_, c in enumerate(DOM[:3]): ax.add_patch(Rectangle((gx - 2.2 + k_ * 1.5, y0 - 1.7), 1.2, 3.4, fc=c, ec="none", zorder=3))
    elif g == "best":
        for k_ in range(3): ax.add_patch(Ellipse((gx - 0.5 + k_ * 0.45, y0 + 0.2 - k_ * 0.25), 4.4, 2.4, angle=25, fc="none", ec=MUTE if k_ < 2 else INK, lw=0.7, zorder=3))
        T(gx + 2.0, y0 + 2.0, "★", 5.6, BLUE, ha="center")
    elif g == "dice":
        ax.add_patch(FancyBboxPatch((gx - 2.0, y0 - 2.0), 4.0, 4.0, boxstyle="round,pad=0,rounding_size=0.7", fc="white", ec=INK, lw=0.7, zorder=3))
        for px, py in ((-1.05, 1.05), (0, 0), (1.05, -1.05), (1.05, 1.05), (-1.05, -1.05)): ax.add_patch(Circle((gx + px, y0 + py), 0.33, fc=INK, zorder=4))
    else:
        ax.add_patch(FancyArrowPatch((gx - 2.3, y0 + 1.1), (gx + 2.3, y0 - 1.1), arrowstyle="-|>", mutation_scale=4.5, color=INK, lw=0.7, zorder=3, connectionstyle="arc3,rad=-0.25"))
        ax.add_patch(FancyArrowPatch((gx - 2.3, y0 - 1.1), (gx + 2.3, y0 + 1.1), arrowstyle="-|>", mutation_scale=4.5, color=INK, lw=0.7, zorder=3, connectionstyle="arc3,rad=0.25"))
    T(XD + 8.2, y0 + 1.7, t1, 5.8, INK); T(XD + 8.2, y0 - 1.6, t2, 5.1, MUTE)
T(XD + WD / 2, BOT + 2.0, "same embedding, many fits", 5.6, MUTE, ha="center", style="italic")

# ------------------------------------------------------------------ 5 Evaluation
chips = [("ARI · NMI · AMI", "agreement"), ("macro-F1 · missed", "per-domain accuracy"), ("CHAOS · PAS · boundary", "spatial coherence"), ("run time · memory", "cost")]
for i, (t1, t2) in enumerate(chips):
    y0 = 95.6 - i * 7.9
    box(XE + 1.2, y0 - 3.4, WE - 2.4, 6.8, fc="white", ec=LINE, lw=0.5, r=1.0, z=1)
    T(XE + 2.6, y0 + 1.1, t1, 5.8, INK); T(XE + 2.6, y0 - 1.6, t2, 5.2, MUTE)
icon("clock.svg", XE + WE - 5.6, 70.6, 3.4, w=3.4)
tx, ty = XE + WE / 2, 60.0
T(tx, 63.2, "hierarchical bootstrap", 5.8, INK, ha="center")
ax.add_patch(Circle((tx, ty - 1.2), 0.9, fc=INK2, zorder=3))
lv1 = [tx - 8.6, tx - 4.3, tx, tx + 4.3, tx + 8.6]
for i, xx in enumerate(lv1):
    ax.plot([tx, xx], [ty - 1.2, ty - 5.6], color=MUTE, lw=0.5, zorder=2)
    ax.add_patch(Circle((xx, ty - 5.6), 0.75, fc=[BLUE, BLUE, BLUE, ORANGE, AQUA][i], zorder=3))
    for d_ in ((-0.9, 0, 0.9) if i < 3 else (-0.9, 0.9)):
        ax.plot([xx, xx + d_], [ty - 5.6, ty - 9.0], color=MUTE, lw=0.4, zorder=2); ax.add_patch(Circle((xx + d_, ty - 9.0), 0.33, fc=MUTE, zorder=3))
T(tx, ty - 11.6, "donors · datasets → sections", 5.3, MUTE, ha="center")
ry = 40.5
ax.add_patch(Rectangle((tx - 1.3, ry - 4.4), 2.6, 9.2, fc="#e7e6e1", ec="none", zorder=1.5))
for i, (c0, c1, m) in enumerate(((0.4, 3.0, 1.6), (2.0, 6.4, 4.0), (5.0, 9.6, 7.2))):
    yy = ry + 3.2 - i * 3.2
    ax.plot([XE + 3.0 + c0 * 2.2, XE + 3.0 + c1 * 2.2], [yy, yy], color=[BLUE, AQUA, ORANGE][i], lw=1.2, solid_capstyle="round", zorder=3)
    ax.add_patch(Circle((XE + 3.0 + m * 2.2, yy), 0.6, fc=[BLUE, AQUA, ORANGE][i], zorder=4))
T(tx, 33.0, "differences, ranks,", 5.3, MUTE, ha="center"); T(tx, 30.4, "equivalence margin", 5.3, MUTE, ha="center")

# ------------------------------------------------------------------ bottom: three questions
out = [(BLUE, "Accuracy", "Which methods agree best with the annotation?", "Fig. 2 · Fig. 5 · Tables 1–2"),
       (ORANGE, "Robustness", "Does the clustering step change the answer?", "Figs 3–4"),
       (AQUA, "Reproducibility", "Do published results and released code hold up?", "HiSTaR re-run · code audit")]
for i, (col, t1, t2, t3) in enumerate(out):
    x0 = 1.5 + i * 57.4
    box(x0, 2.0, 55.6, 20.0, fc="white", ec=col, lw=1.0, r=2.0, z=1)
    ax.add_patch(Rectangle((x0 + 0.5, 2.5), 2.0, 19.0, fc=col, ec="none", zorder=2))
    T(x0 + 5.0, 17.2, t1, 7.4, INK, "bold"); T(x0 + 5.0, 11.8, t2, 6.0, INK2); T(x0 + 5.0, 6.6, t3, 5.7, MUTE)
icon("magnifying-glass.svg", 1.5 + 2 * 57.4 + 46.0, 13.0, 7.0, w=7.0)
ax.plot([1.5, 173.5], [24.4, 24.4], color=LINE, lw=0.6, zorder=1)

for ext in ("pdf", "png"):
    fig.savefig(os.path.join(FIG, f"nar_fig1_pipeline.{ext}"))
print("written nar_fig1_pipeline")
