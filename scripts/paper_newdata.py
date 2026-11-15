"""Numbers, figure and supplementary table for the new-data section of the paper (domain-size simulation, Allen MERFISH whole brain).

Reads only result files of the new-datasets extension (never the original benchmark results) and writes NEW files only:
  results/paper_macros_newdata.tex      LaTeX macros used in paper/main.tex and paper/supplementary.tex
  results/supp/newdata_sim.tex          simulation: Delta and mean ARI per setting (Supplementary Table; added by make_supplement.py)
  results/supp/newdata_allen.tex        per-method ARI on the Allen MERFISH sections (Supplementary Table; added by make_supplement.py)
  docs/figures/nar_fig6_newdata.pdf/png the new main-text figure
Inputs: results/newdata_runs_*.jsonl (newest record per id), results/newdata_stats_sim.json, results/newdata_sim_delta.csv,
results/newdata_sim_ari_table.csv (all three from scripts/newdata_stats.py), results/newdata_g3_verdicts.csv (scripts/newdata_g3.py).
Incomplete cells are reported as such, never imputed.

    python scripts/newdata_stats.py && python scripts/paper_newdata.py
"""
import glob, json, os, sys
from collections import defaultdict
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path[:0] = [ROOT, os.path.join(ROOT, "scripts")]
R = lambda *p: os.path.join(ROOT, "results", *p)
FIG = os.path.join(ROOT, "docs", "figures")

LAB = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "graphst": "GraphST",
       "banksy_l0.8": "BANKSY $\\lambda=0.8$", "banksy_l0.2": "BANKSY $\\lambda=0.2$", "spagcn": "SpaGCN", "stagate": "STAGATE",
       "sedr": "SEDR", "spaceflow": "SpaceFlow", "nichepca": "NichePCA", "ccst": "CCST", "spatial_mgcn": "Spatial-MGCN",
       "deepst": "DeepST", "bass": "BASS", "bayesspace": "BayesSpace"}
PLAIN = {k: v.replace("$\\lambda=", "λ = ").replace("$", "") for k, v in LAB.items()}
FAMILY = {"linear_diffusion": 0, "anisost": 0, "pca_gmm": 0, "histar": 1, "graphst": 1, "spagcn": 1, "stagate": 1, "sedr": 1,
          "spaceflow": 1, "ccst": 1, "spatial_mgcn": 1, "deepst": 1, "banksy_l0.8": 2, "banksy_l0.2": 2, "nichepca": 2, "bass": 2}
INTERNAL = ("spagcn", "bass", "bayesspace")
BLUE, ORANGE, AQUA, INK, INK2, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#4a4a4a", "#e4e3df"
FCOL = [BLUE, ORANGE, AQUA]
SECS = ["ABCA1-066", "ABCA1-085", "ABCA1-103"]


def join(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def f3(x): return f"{x:.3f}".replace("-", "$-$") if x < 0 else f"{x:.3f}"
def f2(x): return f"{x:.2f}".replace("-", "$-$") if x < 0 else f"{x:.2f}"


def records():
    last, hist = {}, defaultdict(int)
    for f in sorted(glob.glob(R("newdata_runs_*.jsonl"))):
        for l in open(f):
            r = json.loads(l); last[r["id"]] = r; hist[r["id"]] += 1
    return last, hist


def allen(last, hist):
    rows = []
    for r in last.values():
        if r["dataset"] != "allenmerfish":
            continue
        ok = r["status"] == "ok"
        mm = (r.get("metrics_matched") or {}).get("ARI") if ok else None
        rows.append(dict(method=r["method"], section=r["section"], seed=r["seed"], ok=ok,
                         ari=r["metrics"]["ARI"] if ok else np.nan,
                         ari_m=(r["metrics"]["ARI"] if r["method"] in INTERNAL else mm) if ok else np.nan,
                         peak=(r.get("resources") or {}).get("peak_rss_gb") or 0.0, outcome=r.get("outcome"),
                         infra=bool(r.get("infra_kill")), err=str(r.get("error") or "")[:60], attempts=hist[r["id"]]))
    return pd.DataFrame(rows)


def failure_reason(g):
    """One short phrase per method for the jobs that did not finish (from the records, newest per id)."""
    bad = g[~g.ok]
    out = []
    real = bad[(bad.outcome == "memory limit") & (bad.peak >= 24)]
    if len(real): out.append(f"{len(real)} at the 30 GB cap")
    infra = bad[bad.infra]
    if len(infra): out.append(f"{len(infra)} stopped by the machine-wide memory guard")
    other = bad[~bad.index.isin(real.index) & ~bad.index.isin(infra.index)]
    for msg, n in other.err.str.split(":").str[0].value_counts().items():
        out.append(f"{n} error ({'R mclust call' if 'RRuntime' in msg else 'length-scale search' if 'ValueError' in msg else msg})")
    return "; ".join(out)


def main():
    last, hist = records()
    sim = json.load(open(R("newdata_stats_sim.json")))
    delta = pd.read_csv(R("newdata_sim_delta.csv")); tab = pd.read_csv(R("newdata_sim_ari_table.csv"))
    g3 = pd.read_csv(R("newdata_g3_verdicts.csv"))
    al = allen(last, hist)
    m = {}

    # ---------------- simulation
    simrecs = [r for r in last.values() if r["dataset"].startswith("sim_") and r["status"] == "ok"]
    full = tab[tab.design.str.startswith("full")]
    m["simNRuns"] = f"{len(simrecs)}"; m["simNMethods"] = f"{full.method.nunique()}"
    D = {(g, int(p)): r for (g, p), r in delta.set_index(["geometry", "param"]).iterrows()}
    for key, nm in [(("A", 1), "Aone"), (("A", 2), "Atwo"), (("A", 4), "Afour"), (("A", 7), "Aseven"), (("B", 3), "Bthree"),
                    (("B", 5), "Bfive"), (("B", 8), "Beight"), (("B", 12), "Btwelve"), (("B", 20), "Btwenty")]:
        d = D[key]; m[f"simD{nm}"] = f3(d.delta); m[f"simD{nm}Lo"] = f3(d.ci_low); m[f"simD{nm}Hi"] = f3(d.ci_high)
    h1, h2 = sim["H1"], sim["H2"]
    m["simHone"] = f3(h1["delta_m1_minus_m7"]); m["simHoneLo"] = f3(h1["ci"][0]); m["simHoneHi"] = f3(h1["ci"][1])
    m["simHtwo"] = f3(h2["delta_B3_minus_A7"]); m["simHtwoLo"] = f3(h2["ci"][0]); m["simHtwoHi"] = f3(h2["ci"][1])
    m["simHoneVerdict"] = h1["verdict"]; m["simHtwoVerdict"] = h2["verdict"]
    T = {(r.method, r.geometry, int(r.param)): r.ari_mean for r in full.itertuples()}
    for meth, nm in [("linear_diffusion", "Lin"), ("pca_gmm", "Pca"), ("anisost", "Aniso"), ("banksy_l0.8", "BanksyHi")]:
        for key, k in [(("A", 1), "Aone"), (("A", 7), "Aseven"), (("B", 3), "Bthree"), (("B", 20), "Btwenty")]:
            m[f"sim{nm}{k}"] = f2(T[(meth,) + key])
    pca_vals = [v for (mm_, g, p), v in T.items() if mm_ == "pca_gmm"]
    m["simPcaLo"], m["simPcaHi"] = f2(min(pca_vals)), f2(max(pca_vals))

    # ---------------- Allen MERFISH
    info = json.load(open(R("newdata_allen_sections.json")))
    ps = info["per_section"]
    cells = [v["n_cells"] for v in ps.values()]; Ks = [v["K"] for v in ps.values()]
    m["alNSections"] = f"{len(ps)}"; m["alCellsLo"] = f"{min(cells):,}"; m["alCellsHi"] = f"{max(cells):,}"
    m["alKLo"], m["alKHi"] = f"{min(Ks)}", f"{max(Ks)}"; m["alNCand"] = f"{info['n_candidate_sections']}"
    m["alNJobs"] = f"{len(al)}"; m["alNOk"] = f"{int(al.ok.sum())}"; m["alNMethods"] = f"{al.method.nunique()}"
    sec_mean = al[al.ok].groupby(["method", "section"]).agg(ari=("ari", "mean"), ari_m=("ari_m", "mean"), n=("ok", "size")).reset_index()
    meth_mean = sec_mean.groupby("method").agg(ari=("ari", "mean"), ari_m=("ari_m", "mean"), nsec=("section", "nunique")).reset_index()
    complete = sorted(meth_mean[meth_mean.nsec == 3].method)
    m["alNComplete"] = f"{len(complete)}"
    mm_ = meth_mean.set_index("method")
    for meth, nm in [("linear_diffusion", "Lin"), ("stagate", "Stagate"), ("bass", "Bass"), ("spaceflow", "Spaceflow"),
                     ("nichepca", "Nichepca"), ("pca_gmm", "Pca"), ("anisost", "Aniso"), ("histar", "Histar"), ("banksy_l0.8", "BanksyHi")]:
        m[f"al{nm}"] = f3(mm_.loc[meth, "ari_m"]); m[f"al{nm}Def"] = f3(mm_.loc[meth, "ari"])
    comp = mm_.loc[complete].sort_values("ari_m", ascending=False)
    m["alTopMatched"] = ", ".join(LAB[x] for x in comp.index[:4])
    compd = mm_.loc[complete].sort_values("ari", ascending=False)
    m["alTopDefault"] = ", ".join(LAB[x] for x in compd.index[:3])
    m["alLinRankMatched"] = f"{list(comp.index).index('linear_diffusion') + 1}"
    m["alLinRankDefault"] = f"{list(compd.index).index('linear_diffusion') + 1}"
    # failures
    fails = {meth: failure_reason(g) for meth, g in al.groupby("method") if (~g.ok).any()}
    nok = al.groupby("method").ok.sum().astype(int); ntot = al.groupby("method").size()
    m["alNoneDone"] = join(LAB[x] for x in sorted(nok[nok == 0].index))
    m["alPartial"] = join(f"{LAB[x]} {nok[x]} of {ntot[x]}" for x in sorted(nok[(nok > 0) & (nok < ntot)].index))
    real = al[(~al.ok) & (al.outcome == "memory limit") & (al.peak >= 24)]
    m["alNCap"] = f"{len(real)}"; m["alNInfra"] = f"{int(((~al.ok) & al.infra).sum())}"

    # ---------------- G3 re-tests on Allen
    g = g3[g3.unit == "allenmerfish"].set_index("finding")
    for k, nm in zip("abcde", ["A", "B", "C", "D", "E"]):
        r = g.loc[k]
        m[f"gThree{nm}"] = f3(r.S); m[f"gThree{nm}Lo"] = f3(r.ci_low); m[f"gThree{nm}Hi"] = f3(r.ci_high)
        m[f"gThree{nm}Ref"] = f3(r.S0_original); m[f"gThree{nm}Verdict"] = r.verdict
    m["gThreeNMethods"] = f"{int(g.n_methods.iloc[0])}"

    # ---------------- supplementary table: simulation per setting
    meths = ["linear_diffusion", "pca_gmm", "anisost", "banksy_l0.2", "banksy_l0.8"]
    sl = [r"\begin{tabular}{llr" + "r" * len(meths) + "}", r"\toprule",
          "Geometry & Setting & $\\Delta$ (95\\% interval) & " + " & ".join(LAB[x] for x in meths) + r" \\", r"\midrule"]
    for (geo, p), d in sorted(D.items(), key=lambda kv: (kv[0][0], kv[0][1] if kv[0][0] == "B" else -kv[0][1])):
        name = ("Bands" if geo == "A" else "Blocks") + (f", $m={p}$ (width {120 / (6 * p):.1f})" if geo == "A" else f", $w={p}$")
        sl.append(f"{geo} & {name} & {f3(d.delta)} ({f3(d.ci_low)} to {f3(d.ci_high)}) & " +
                  " & ".join(f2(T[(x, geo, p)]) for x in meths) + r" \\")
    sl += [r"\bottomrule", r"\end{tabular}"]
    open(R("supp", "newdata_sim.tex"), "w").write("% Generated by scripts/paper_newdata.py\n" + "\n".join(sl) + "\n")

    with open(R("paper_macros_newdata.tex"), "w") as fh:
        fh.write("% Generated by scripts/paper_newdata.py from the new-datasets result files. Do not edit by hand.\n")
        for k, v in m.items():
            fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    print(f"wrote {len(m)} macros")

    # ---------------- supplementary table
    order = list(comp.index) + sorted(set(meth_mean.method) - set(complete), key=lambda x: -mm_.loc[x, "ari_m"]) + \
        sorted(set(al.method) - set(meth_mean.method))
    S = {(r.method, r.section): r for r in sec_mean.itertuples()}
    lines = [r"\begin{tabular}{lrrrrrrl}", r"\toprule",
             r" & \multicolumn{3}{c}{Matched clustering} & & & & \\ \cmidrule(lr){2-4}",
             r"Method & 066 & 085 & 103 & Mean & Default & Runs & Did not finish \\", r"\midrule"]
    for meth in order:
        cells_ = []
        for s in SECS:
            r = S.get((meth, s))
            cells_.append("--" if r is None else (f3(r.ari_m) + ("" if r.n == 3 else f"$^{{{r.n}}}$")))
        if meth in mm_.index:
            mean_m = f3(mm_.loc[meth, "ari_m"]) + ("" if mm_.loc[meth, "nsec"] == 3 else "$^*$"); mean_d = f3(mm_.loc[meth, "ari"])
        else:
            mean_m = mean_d = "--"
        lines.append(f"{LAB[meth]} & " + " & ".join(cells_) + f" & {mean_m} & {mean_d} & {nok[meth]}/{ntot[meth]} & "
                     f"{fails.get(meth, '')} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(R("supp", "newdata_allen.tex"), "w").write("% Generated by scripts/paper_newdata.py\n" + "\n".join(lines) + "\n")

    # ---------------- figure
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from simulate_domains import domain_map
    plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 7, "axes.labelsize": 7.5, "axes.titlesize": 8,
                         "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5, "axes.linewidth": 0.6,
                         "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "axes.edgecolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK, "axes.labelcolor": INK, "text.color": INK})
    CM = 1 / 2.54
    fig = plt.figure(figsize=(17.5 * CM, 12.4 * CM))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.05], hspace=0.42)
    top = gs[0].subgridspec(1, 3, width_ratios=[1.0, 1.25, 1.25], wspace=0.32)
    ex = top[0].subgridspec(2, 2, wspace=0.08, hspace=0.28)
    dcm = ListedColormap(["#2a78d6", "#eb6834", "#1baf7a", "#8b5fd6", "#c9a227", "#5a5a5a"])
    for i, (geo, p, title) in enumerate([(1, 1, "bands, m = 1"), (1, 7, "bands, m = 7"), (2, 20, "blocks, w = 20"), (2, 3, "blocks, w = 3")]):
        ax = fig.add_subplot(ex[i // 2, i % 2]); ax.imshow(domain_map(geo, p, 0), cmap=dcm, interpolation="nearest")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=6.5, pad=2)
        for s in ax.spines.values(): s.set_visible(True); s.set_color(INK2); s.set_linewidth(0.4)
        if i == 0: ax.text(-0.25, 1.32, "A", transform=ax.transAxes, fontsize=10, fontweight="bold")
    STY = {"linear_diffusion": dict(color=BLUE, lw=1.8, marker="o"), "pca_gmm": dict(color="#3a3a3a", lw=1.4, marker="s"),
           "anisost": dict(color=BLUE, lw=1.0, marker="^", ls="--"), "banksy_l0.2": dict(color=AQUA, lw=1.0, marker="D", ls=":"),
           "banksy_l0.8": dict(color=AQUA, lw=1.0, marker="v")}
    for j, (geo, xs, xl, lab) in enumerate([("A", [1, 2, 4, 7], "Band width (spot spacings)", "B"),
                                            ("B", [3, 5, 8, 12, 20], "Block side $w$ (spot spacings)", "C")]):
        ax = fig.add_subplot(top[j + 1])
        xv = [120 / (6 * x) for x in xs] if geo == "A" else xs
        for meth, st in STY.items():
            ax.plot(xv, [T[(meth, geo, x)] for x in xs], ms=3.2, label=PLAIN[meth], **st)
        ax.set_xscale("log"); ax.set_xticks([3, 5, 10, 20]); ax.set_xticklabels(["3", "5", "10", "20"]); ax.minorticks_off()
        ax.set_ylim(0.25, 1.02); ax.set_xlabel(xl); ax.grid(axis="y", color=GRID, lw=0.5)
        ax.set_title("Layered bands" if geo == "A" else "Random blocks", loc="left")
        if j == 0: ax.set_ylabel("Mean ARI (5 tissues × 3 seeds)")
        else: ax.legend(frameon=False, loc="lower right")
        ax.text(-0.2, 1.08, lab, transform=ax.transAxes, fontsize=10, fontweight="bold")
    ax = fig.add_subplot(gs[1])
    ordr = [x for x in order if x in mm_.index]
    for i, meth in enumerate(ordr):
        col = FCOL[FAMILY[meth]]; v = mm_.loc[meth, "ari_m"]
        ax.bar(i, v, color=col, alpha=0.35 if mm_.loc[meth, "nsec"] < 3 else 0.8, width=0.7, edgecolor="none")
        for s, mk in zip(SECS, ["o", "^", "s"]):
            r = S.get((meth, s))
            if r is not None: ax.plot(i, r.ari_m, mk, ms=3.0, mfc="white", mec=INK, mew=0.6, zorder=3)
        ax.plot(i, mm_.loc[meth, "ari"], "_", ms=9, mew=1.4, color=INK, zorder=4)
    missing = [x for x in order if x not in mm_.index]
    for k, meth in enumerate(missing):
        ax.text(len(ordr) + k, 0.02, "not\nfinished", ha="center", va="bottom", fontsize=5.5, color=INK2)
    ax.set_xticks(range(len(ordr) + len(missing)))
    ax.set_xticklabels([PLAIN[x] + ("*" if x in mm_.index and mm_.loc[x, "nsec"] < 3 else "") for x in ordr + missing], rotation=35, ha="right")
    ax.set_ylabel("ARI"); ax.set_ylim(0, 0.6); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.set_title("Mouse whole brain, MERFISH (Allen Brain Cell Atlas, 3 coronal sections; domains = CCF divisions)", loc="left")
    from matplotlib.lines import Line2D
    hand = [Line2D([], [], marker=mk, ls="", mfc="white", mec=INK, ms=3.5, label=f"section {s[-3:]}") for s, mk in zip(SECS, ["o", "^", "s"])]
    hand += [Line2D([], [], marker="_", ls="", color=INK, ms=8, mew=1.4, label="default clustering (mean)")]
    ax.legend(handles=hand, frameon=False, ncol=4, loc="upper right", fontsize=6)
    ax.text(-0.055, 1.06, "D", transform=ax.transAxes, fontsize=10, fontweight="bold")
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"nar_fig6_newdata.{ext}"), dpi=300, bbox_inches="tight")
    print("wrote figure")


if __name__ == "__main__":
    main()
