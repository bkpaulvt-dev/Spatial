"""Build the Supplementary Information: every table, supplementary figures and notes, generated from the result files.

Writes paper/supplementary.tex, paper/supp_labels.tex (macros \\ST..., \\SF..., \\SN... with the S-numbers used in the
main text) and results/supp/*.tex. Run after scripts/paper_v2.py and scripts/stats_cluster_aware.py.
"""
import json, os, re, glob, collections
import numpy as np, pandas as pd, yaml
from scipy.stats import spearmanr

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda f: os.path.join(ROOT, "results", f)
SUP = R("supp"); os.makedirs(SUP, exist_ok=True)
LAB = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "anisost_single_gmm": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR",
       "graphst": "GraphST", "banksy_l0.8": "BANKSY $\\lambda$=0.8", "banksy_l0.2": "BANKSY $\\lambda$=0.2", "spagcn": "SpaGCN", "stagate": "STAGATE",
       "sedr": "SEDR", "spaceflow": "SpaceFlow", "nichepca": "NichePCA", "ccst": "CCST", "spatial_mgcn": "Spatial-MGCN", "deepst": "DeepST",
       "bass": "BASS", "bayesspace": "BayesSpace", "graphst_refined": "GraphST (refined)", "banksy": "BANKSY",
       "linear_diffusion_single_gmm": "Linear diffusion", "pca_gmm_single_gmm": "PCA"}
DS = ["dlpfc", "starmap", "merfish"]; DSN = {"dlpfc": "DLPFC", "starmap": "STARmap", "merfish": "MERFISH"}
esc = lambda s: re.sub(r"([_&%#])", r"\\\1", str(s)).replace("λ", "$\\lambda$")
f3 = lambda x, d=3: "--" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def write(name, header, rows, colspec, size="\\small", note=None):
    L = [size, f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    L += [" & ".join(r) + " \\\\" for r in rows]
    L += ["\\bottomrule", "\\end{tabular}"]
    if note: L.append(f"\\par\\vspace{{2pt}}{{\\footnotesize {note}}}")
    open(os.path.join(SUP, name), "w").write("\n".join(L) + "\n")


# ------------------------------------------------------------------ shared data (paper pipeline)
rd = lambda f: pd.read_json(R(f), lines=True) if os.path.exists(R(f)) else pd.DataFrame()
a = rd("anisost_main.jsonl").assign(dataset="dlpfc"); b = rd("baselines.jsonl").assign(dataset="dlpfc")
e = rd("extra.jsonl"); g = rd("graphst.jsonl"); b3 = rd("baselines_3start.jsonl")
nm = rd("new_methods.jsonl"); nm["slice"] = nm["slice"].astype(str)
nm = nm[nm.status == "ok"].drop_duplicates(["method", "dataset", "slice", "seed"], keep="last")
nm_std = nm[["dataset", "method", "slice", "seed", "ARI", "NMI"]]
nm_rob = nm[["dataset", "method", "slice", "seed", "ARI_robust", "NMI_robust"]].rename(columns={"ARI_robust": "ARI", "NMI_robust": "NMI"}) \
    .assign(method=lambda x: x.method + "+robust").dropna(subset=["ARI"])
d = pd.concat([a, b, e, g, b3, nm_std, nm_rob], ignore_index=True); d["slice"] = d["slice"].astype(str)
d.loc[d.method == "histar_rerun", "method"] = "histar"
STD = {"linear_diffusion": "linear_diffusion_single_gmm", "anisost": "anisost_single_gmm", "pca_gmm": "pca_gmm_single_gmm", "histar": "histar", "graphst": "graphst",
       "banksy_l0.8": "banksy_l0.8", "banksy_l0.2": "banksy_l0.2", "spagcn": "spagcn", "stagate": "stagate", "sedr": "sedr",
       "spaceflow": "spaceflow", "nichepca": "nichepca", "ccst": "ccst", "spatial_mgcn": "spatial_mgcn", "deepst": "deepst",
       "bass": "bass", "bayesspace": "bayesspace"}
ROB = {m: (m if m in ("linear_diffusion", "pca_gmm", "anisost", "spagcn", "bass", "bayesspace") else m + "+robust") for m in STD}
items = []          # (kind, macro, title, body/latex)

# ------------------------------------------------------------------ S: data QC
qc = pd.read_csv(R("qc/section_qc.csv"))
rows = [[esc(r.section.replace("dlpfc/", "DLPFC ").replace("starmap/", "STARmap ").replace("merfish/", "MERFISH ")), f"{int(r.n_obs)}", f"{int(r.n_vars)}",
         f3(r.median_umi, 0), f3(r.sparsity, 2), f3(r.annotated_fraction, 2), f"{int(r.n_domains)}", f3(r.smallest_domain_fraction, 3),
         f3(r.domain_imbalance_ratio, 1)] for r in qc.itertuples()]
write("qc.tex", ["Section", "Spots/cells", "Genes", "Median counts", "Sparsity", "Annotated", "Domains", "Smallest domain", "Imbalance"], rows, "lrrrrrrrr", "\\scriptsize")
items.append(("table", "STqc", "Data and quality control per section. Sparsity: fraction of zero entries. Annotated: fraction of spots or cells with a domain label. Smallest domain: fraction of annotated spots in the smallest domain. Imbalance: largest over smallest domain size.", "qc.tex"))

# ------------------------------------------------------------------ S: method settings
my = yaml.safe_load(open(os.path.join(ROOT, "configs", "methods.yaml")))["methods"]
rows = []
for k, v in my.items():
    code = v.get("code", {}); clu = v.get("clustering", {})
    dev = "; ".join(v.get("deviations", []) or [])
    DEFCLU = {"histar": "3-start Gaussian mixture (scikit-learn, tied)", "banksy": "3-start Gaussian mixture (scikit-learn, tied)",
              "linear_diffusion": "3-start Gaussian mixture (scikit-learn, tied)", "anisost": "3-start Gaussian mixture (scikit-learn, tied)",
              "pca_gmm": "3-start Gaussian mixture (scikit-learn, tied)"}
    nice = lambda t: esc(str(t).replace("package_default", "package default").replace("our_rule", "fixed rule").replace("_", " "))
    rows.append([esc(LAB.get(k, k)), nice(v.get("kind", "")), esc(code.get("source", ""))[:60], esc(code.get("commit", "")),
                 nice(v.get("settings_source", "")), esc(DEFCLU.get(k, clu.get("official", clu.get("ours_standard", "")))), "\\parbox[t]{5.2cm}{\\raggedright " + esc(dev) + "}"])
write("methods.tex", ["Method", "Type", "Code", "Commit", "Settings", "Default clustering", "Deviations from the tutorial"], rows,
      "p{1.6cm}p{2.0cm}p{3.0cm}p{1.2cm}p{1.2cm}p{2.2cm}p{5.2cm}", "\\scriptsize")
items.append(("table", "STmethods", "Benchmarked methods: code source, version, settings source, clustering and every deviation from the published tutorial (from configs/methods.yaml).", "methods.tex"))

# ------------------------------------------------------------------ S: mean ARI and NMI per dataset, both protocols
def mean_table(metric, fname, macro, title):
    P = d.groupby(["dataset", "method", "slice"])[metric].mean()
    def mv(ds, key):
        try: return float(P.loc[(ds, key)].mean())
        except KeyError: return np.nan
    rows = []
    for m in STD:
        cells = []
        for ds in DS:
            cells += [f3(mv(ds, STD[m])) if STD[m] else "--", f3(mv(ds, ROB[m])) if m in ROB else "--"]
        rows.append([LAB[m]] + cells)
    hdr = ["Method"] + [f"{DSN[x]} {p}" for x in DS for p in ("default", "matched")]
    write(fname, hdr, rows, "l" + "rr" * 3, "\\footnotesize")
    items.append(("table", macro, title, fname))
mean_table("ARI", "ari.tex", "STari", "Mean ARI over sections and seeds per dataset with each method's default clustering and with matched clustering (the same 20-start best-likelihood Gaussian mixture on every embedding). The training-free baselines, HiSTaR and BANKSY use a 3-start Gaussian mixture as default clustering. SpaGCN, BASS and BayesSpace cluster internally and have the same value under both protocols.")
mean_table("NMI", "nmi.tex", "STnmi", "As Supplementary Table~\\STari{} for normalised mutual information (NMI).")

# ------------------------------------------------------------------ S: cluster-aware statistics
cs = json.load(open(R("stats_cluster_aware.json")))
for proto, fname, macro, title in (("standard", "stats_std.tex", "STstats", "Difference in mean ARI between linear diffusion and each method, both with their default clustering; equal-weight mean of group means; 95\\% interval from a hierarchical bootstrap over five groups (three DLPFC donors, STARmap, MERFISH). Test only: the same estimate without the development sections. Verdict: baseline higher if the interval is above zero; unresolved otherwise; no comparison met the equivalence criterion (90\\% interval within $\\pm$0.03)."),
                                   ("robust", "stats_rob.tex", "STstatsrob", "Primary analysis: as Supplementary Table~\\STstats{} with matched clustering (the same 20-start best-likelihood Gaussian mixture on every embedding; SpaGCN, BASS and BayesSpace use their internal clustering).")):
    vs = sorted([v for v in cs["comparisons"].values() if v["protocol"] == proto], key=lambda v: -v["delta"])
    rows = [[esc(v["method"]), f"{v['delta']:+.3f}", f"({v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f})", *[f"{v['per_dataset'].get(x):+.2f}" if x in v["per_dataset"] else "--" for x in DS],
             f"{v['test_only']['delta']:+.3f}", f"({v['test_only']['ci95'][0]:+.3f}, {v['test_only']['ci95'][1]:+.3f})", v["category"].replace("baseline_better", "baseline higher").replace("_", " ")] for v in vs]
    write(fname, ["Method", "$\\Delta$", "95\\% CI", "DLPFC", "STARmap", "MERFISH", "Test only", "95\\% CI", "Verdict"], rows, "lrrrrrrrl", "\\scriptsize")
    items.append(("table", macro, title, fname))
rk = cs["ranking"]; ro = cs["ranking_own"]
rows = [[esc(k), f3(v["p_best"], 2), f"{v['median_rank']:.0f}", f"{v['rank95'][0]}--{v['rank95'][1]}",
         f3(ro[k]["p_best"], 2), f"{ro[k]['median_rank']:.0f}", f"{ro[k]['rank95'][0]}--{ro[k]['rank95'][1]}"] for k, v in sorted(rk.items(), key=lambda kv: kv[1]["median_rank"])]
write("ranks.tex", ["Method", "P(rank 1)", "Median rank", "95\\% interval", "P(rank 1), default", "Median rank, default", "95\\% interval, default"], rows, "lrrrrrr", "\\footnotesize")
items.append(("table", "STranks", "Rank of each method in the hierarchical bootstrap with matched clustering (first three columns) and with default clustering (last three); methods with all 20 sections.", "ranks.tex"))

# ------------------------------------------------------------------ S: seed variability
sd = d.groupby(["dataset", "method", "slice"]).ARI.agg(["std", "count"]).reset_index()
rows = []
for m in STD:
    key = STD[m] or ROB.get(m)
    cells, ns = [], []
    for ds in DS:
        q = sd[(sd.method == key) & (sd.dataset == ds) & (sd["count"] > 1)]
        cells.append(f3(q["std"].mean())); ns.append(int(sd[(sd.method == key) & (sd.dataset == ds)]["count"].max()) if len(sd[(sd.method == key) & (sd.dataset == ds)]) else 0)
    rows.append([LAB[m]] + cells + ["/".join(str(n) for n in ns)])
write("seeds.tex", ["Method", "DLPFC", "STARmap", "MERFISH", "Seeds (D/S/M)"], rows, "lrrrr", "\\footnotesize")
items.append(("table", "STseeds", "Seed-to-seed standard deviation of ARI (mean over sections; default clustering). Methods run with one seed have no value.", "seeds.tex"))

# ------------------------------------------------------------------ S: lottery and likelihood
L = [json.loads(l) for l in open(R("clustering_lottery.jsonl"))]
lr = []
for r in L:
    x = np.array([f["ARI"] for f in r["fits"]]); ll = np.array([f["ll"] for f in r["fits"]])
    lr.append(dict(method=r["method"], dataset=r.get("dataset", "dlpfc"), rng=x.max() - x.min(), sd=x.std(), oracle=x.max() - x.mean(),
                   bll=r["ARI_bestll"] - x.mean(), rho=spearmanr(ll, x).statistic))
LT = pd.DataFrame(lr)
rows = []
for m, gq in sorted(LT.groupby("method"), key=lambda kv: kv[1].rng.median()):
    rows.append([LAB.get(m, m), f3(gq.rng.median(), 2), f"{gq.rng.quantile(.25):.2f}--{gq.rng.quantile(.75):.2f}", f3(gq.sd.mean(), 3), f3(gq.oracle.mean(), 3),
                 f"{gq.bll.mean():+.3f}", *[f"{gq[gq.dataset == x].rho.median():+.2f}" for x in DS]])
write("lottery.tex", ["Method", "Median range", "IQR", "Mean SD", "Best-by-ARI minus mean", "Best-likelihood minus mean", "$\\rho$ DLPFC", "$\\rho$ STARmap", "$\\rho$ MERFISH"], rows, "lrrrrrrrr", "\\scriptsize")
items.append(("table", "STlottery", "Initialisation experiment: one fixed embedding per section refitted 20 times with a single-start Gaussian mixture (20 sections per method). Range and SD of ARI across the 20 fits; best-by-ARI minus mean: ARI gain of choosing the best fit by agreement with the labels; best-likelihood minus mean: gain of choosing the fit with the highest likelihood; $\\rho$: median Spearman correlation between log-likelihood and ARI.", "lottery.tex"))

# ------------------------------------------------------------------ S: R mclust random seed vs full-data initialisation
mf = glob.glob(R("mclust_lottery_*.csv")); M = pd.concat([pd.read_csv(f) for f in mf]); M["slice"] = M["slice"].astype(str)
MSS = pd.read_csv(R("mclust_seed_summary.csv")) if os.path.exists(R("mclust_seed_summary.csv")) else pd.DataFrame()
rows = []
if len(MSS):
    for m, gq in sorted(MSS.groupby("method"), key=lambda kv: -kv[1].rng.mean()):
        big = gq[gq.n > 2000]
        rows.append([LAB.get(m, m), str(len(gq)), f3(big.rng.mean(), 2), f3(big.rng.max(), 2), f"{100 * (big.rng > 0.1).mean():.0f}\\%",
                     f3(gq.jrng.mean(), 2), f"{(gq.full - gq['mean']).mean():+.3f}"])
write("mclust.tex", ["Method", "Embeddings", "Seed range (mean)", "Seed range (max)", "Range $>$0.1", "Noise range, full init.", "Full minus seeded mean"], rows, "lrrrrrr", "\\footnotesize")
items.append(("table", "STmclust", "R mclust 6.0.1 (EEE) on fixed embeddings. Seed range: ARI range over ten R random seeds with the default initialisation, which uses a random subset of 2000 observations when there are more (sections with more than 2000 spots or cells only; STARmap sections are smaller and do not vary). Noise range: ARI range over five repetitions with 1\\% Gaussian noise when EM is initialised on all observations, which is deterministic. Full minus seeded mean: ARI of the full-data initialisation minus the mean of the ten seeded fits.", "mclust.tex"))

# ------------------------------------------------------------------ S: clustering protocol gain
pv = json.load(open(R("paper_numbers_v2.json")))
rows = [[LAB.get(k, k), f"{v['delta']:+.3f}", f"{v['wins']}/{v['n']}", f3(v["p"], 3)] for k, v in sorted(pv["clustering_gain_all"].items(), key=lambda kv: -kv[1]["delta"])]
write("gain.tex", ["Method", "Mean change in ARI", "Sections improved", "Wilcoxon $p$ (unadjusted)"], rows, "lrrr", "\\footnotesize")
items.append(("table", "STgain", "Change in mean ARI when each method's default clustering is replaced by matched clustering (20-start best-likelihood Gaussian mixture) on the same embedding (20 sections). The two protocols can differ in algorithm and number of starts.", "gain.tex"))

# ------------------------------------------------------------------ S: metric panel and resources (standardised runner)
ur = {}
for l in open(R("benchmark_runs.jsonl")):
    x = json.loads(l); ur[x["id"]] = x
rowsd = [dict(method=x["method"], dataset=x["dataset"], **{k: x["metrics"].get(k) for k in ("ARI", "NMI", "macro_F1", "n_missed_domains", "small_domain_recall", "CHAOS", "PAS", "boundary_F1")},
              t=x["resources"].get("wall_s"), mem=x["resources"].get("peak_rss_gb"), kwh=x["resources"].get("energy_kwh")) for x in ur.values() if x["status"] == "ok"]
U = pd.DataFrame(rowsd)
cols = ["ARI", "NMI", "macro_F1", "n_missed_domains", "small_domain_recall", "CHAOS", "PAS", "boundary_F1"]
dsm = U.groupby(["method", "dataset"])[cols].mean().groupby("method").mean()
cnt = U.groupby("method").size()
rows = [[LAB.get(m, m)] + [f3(r[c], 3 if c not in ("n_missed_domains",) else 2) for c in cols] + [str(cnt[m])] for m, r in dsm.sort_values("ARI", ascending=False).iterrows()]
write("metrics.tex", ["Method", "ARI", "NMI", "Macro-F1", "Missed domains", "Small-domain recall", "CHAOS$\\downarrow$", "PAS$\\downarrow$", "Boundary F1", "Runs"], rows, "lrrrrrrrrr", "\\scriptsize")
items.append(("table", "STmetrics", "Metric panel from the standardised runner (shared preprocessing for all methods; mean over the three datasets of the per-dataset means). Values differ slightly from Supplementary Table~\\STari{} because the preprocessing is shared. Missed domains: annotated domains with no matched cluster; small-domain recall: recall of domains below 5\\% of spots; CHAOS and PAS: spatial fragmentation (lower is better). Runs: 60 per method (20 sections, 3 seeds), except DeepST (20, seed 0) and BayesSpace (12 Visium sections, seed 0).", "metrics.tex"))
rs = U.groupby("method").agg(t=("t", "median"), mem=("mem", "max"), kwh=("kwh", "sum"))
rows = [[LAB.get(m, m), f"{r.t:.0f}", f"{r.mem:.1f}", f"{1000 * r.kwh / cnt[m]:.2f}"] for m, r in rs.sort_values("t").iterrows()]
write("resources.tex", ["Method", "Median time per job (s)", "Peak memory (GB)", "Energy per job (Wh, estimate)"], rows, "lrrr", "\\footnotesize")
items.append(("table", "STres", "Run time, peak memory and estimated energy of one whole job (data loading, embedding and clustering) in the standardised runner on one CPU thread. Energy is estimated at 10 W per busy core.", "resources.tex"))

# ------------------------------------------------------------------ S: published pipeline vs standardised runner
Pp = d.groupby(["dataset", "method", "slice"]).ARI.mean()
Ur = U.groupby(["method", "dataset"]).ARI.mean()
rows = []
for m in STD:
    cells = []
    for ds in DS:
        try: pv_ = float(Pp.loc[(ds, STD[m])].mean())
        except KeyError: pv_ = np.nan
        uv = float(Ur.get((m, ds), np.nan))
        cells += [f3(pv_), f3(uv), "--" if np.isnan(pv_) or np.isnan(uv) else f"{uv - pv_:+.3f}"]
    rows.append([LAB[m]] + cells)
write("agree.tex", ["Method"] + [f"{DSN[x]} {c}" for x in DS for c in ("pipeline", "runner", "diff.")], rows, "l" + "rrr" * 3, "\\scriptsize")
items.append(("table", "STagree", "Mean ARI with each method's default clustering in its published pipeline (used in the main text) and in the standardised runner (shared preprocessing, used for Supplementary Tables~\\STmetrics{} and~\\STres), and their difference (runner minus pipeline).", "agree.tex"))

# ------------------------------------------------------------------ S: HiSTaR reproduction
p1 = json.load(open(R("paper_numbers.json")))
h = p1["bench_histar"]; hd = p1["bench_histar_deterministic"]
mc = M[(M.kind == "base") & (M.dataset == "dlpfc") & (M.method == "histar")].ARI.mean()
rows = [["Reported (HiSTaR article)", "0.65 (median)", "--", "--", "HiSTaR article"],
        ["Official code, 3-start GMM (3 seeds)", f3(h["median_slice"]), f3(h["mean"]), f"{f3(h['ci_lo'])}--{f3(h['ci_hi'])}", "this study"],
        ["Masking at inference removed", f3(hd["median_slice"]), f3(hd["mean"]), f"{f3(hd['ci_lo'])}--{f3(hd['ci_hi'])}", "this study"],
        ["R mclust as in the official pipeline (seed 0)", "--", f3(mc), "--", "this study"]]
write("histar.tex", ["Setting", "Median ARI", "Mean ARI", "95\\% CI of mean", "Source"], rows, "lrrrl", "\\footnotesize")
items.append(("table", "SThistar", "Reproduction of HiSTaR on the twelve DLPFC sections.", "histar.tex"))

# ------------------------------------------------------------------ S: label-selected epoch
sm = nm[nm.method == "spatial_mgcn"]
rows = []
for ds in DS:
    q = sm[sm.dataset == ds]
    rows.append([DSN[ds], str(len(q)), f3(q.ARI.mean()), f3(q.ARI_label_selected_epoch.mean()), f"{(q.ARI_label_selected_epoch - q.ARI).mean():+.3f}"])
q = sm; rows.append(["All", str(len(q)), f3(q.ARI.mean()), f3(q.ARI_label_selected_epoch.mean()), f"{(q.ARI_label_selected_epoch - q.ARI).mean():+.3f}"])
write("labelepoch.tex", ["Dataset", "Sections", "Final epoch", "Label-selected epoch", "Difference"], rows, "lrrrr", "\\footnotesize")
items.append(("table", "STepoch", "Mean ARI of the final training epoch (used in the benchmark) and of the epoch with the highest ARI against the annotation, as selected by the released test scripts (seed 0).", "labelepoch.tex"))

# ------------------------------------------------------------------ S: code screening
au = pd.read_csv(R("leakage_scan/summary.csv"))
rows = [[esc(r.repo)] + [str(int(getattr(r, c))) for c in ("L1", "L2", "L3", "L4", "L5")] for r in au.itertuples()]
write("audit.tex", ["Repository", "L1", "L2", "L3", "L4", "L5"], rows, "lrrrrr", "\\footnotesize")
items.append(("table", "STaudit", "Automated screening of released code for patterns of label use (number of candidate lines per category; L1 result chosen by agreement with labels, L2 number of domains from labels, L3 unannotated spots removed, L4 settings keyed by section, L5 loops combined with a label metric). Candidate lines are not findings: each was read manually; the 14 repositories are the benchmarked methods with released code plus SPARK, SpatialPCA and conST, which were screened but not benchmarked, and only the label-selected epoch in Spatial-MGCN's test scripts was confirmed as L1 (Supplementary Note~\\SNaudit).", "audit.tex"))

# ------------------------------------------------------------------ S: invariance pilot
inv = json.load(open(R("invariance_pilot.json")))
tr = list(next(iter(inv.values()))["consistency"].keys())
NIC = lambda t: t.replace("pca_gmm", "PCA").replace("linear_diffusion", "Linear diffusion").replace("anisost", "AnisoST").replace("dlpfc", "DLPFC").replace("merfish", "MERFISH").replace("deg", "°").replace("coords", "coordinates").replace("_", " ")
rows = [[esc(NIC(k.replace("/", " ")))] + [f3(v["consistency"][t], 2) for t in tr] for k, v in inv.items()]
write("invariance.tex", ["Section and method"] + [esc(NIC(t)) for t in tr], rows, "l" + "r" * len(tr), "\\scriptsize")
items.append(("table", "STinv", "Pilot invariance test (three training-free methods, two sections): agreement (ARI) between the partition on the original data and on transformed data that should not change the answer. The methods are invariant to rescaling, rotating and reflecting the coordinates and to rescaling expression, but not fully to spot order, because the Gaussian mixture initialisation depends on it.", "invariance.tex"))

# ------------------------------------------------------------------ S: coverage
cov = pd.read_csv(R("coverage_matrix.csv"))
rows = [[esc(LAB.get(r[0], r[0]))] + [esc(str(x).replace("0/20", "not run").replace("0/12", "not run")) for x in r[1:]] for r in cov.itertuples(index=False)]
write("coverage.tex", [esc(c[:1].upper() + c[1:]).replace("lottery", "initialisation experiment") for c in cov.columns], rows, "l" + "p{2.6cm}" * (len(cov.columns) - 1), "\\scriptsize")
items.append(("table", "STcov", "Which method was run in which experiment (sections completed / expected; seeds). n/a: the experiment needs an embedding and the method clusters internally.", "coverage.tex"))

# ------------------------------------------------------------------ supplementary figures and notes
figs = [("SFlottery", "v2_fig1_lottery.png", "Initialisation experiment for three representative methods (HiSTaR, GraphST and AnisoST), per section: ARI of 20 single-start fits of one fixed embedding (grey), the best-likelihood fit (blue) and R mclust with default settings (open circle)."),
        ("SFsens", "fig3_sensitivity.png", "Sensitivity of linear diffusion (diffusion steps $T$, neighbours $k$, number of PCs, step size $\\alpha$) and of AnisoST (edge-scale quantile $q$) on the 12 DLPFC sections, one hyper-parameter at a time (open circle: default; dashed line: HiSTaR mean ARI)."),
        ("SFboundary", "fig4_boundary.png", "Accuracy on spots at layer boundaries and in layer interiors on the 12 DLPFC sections, linear diffusion versus AnisoST (labelled Anisotropic); one line per section; Wilcoxon signed-rank test, $n=12$ sections.")]
notes = {"SNdata": ("Data and preprocessing", "DLPFC count matrices from spatialLIBD and layer annotations from the SEDR analyses repository; STARmap and MERFISH matrices and annotations from the BASS analyses. Genes in fewer than 50 spots or with fewer than 10 counts were removed for Visium; 2000 highly variable genes were selected on the counts (Seurat v3 flavour; Visium) or all panel genes kept, then counts were normalised to the library size, log-transformed, scaled and reduced by PCA (200 components for Visium, 50 for panels). Sections, splits and label provenance are listed in configs/datasets.yaml; per-section statistics are in Supplementary Table~\\STqc."),
         "SNmethods": ("Methods and settings", "Every method was run from its official code with the settings of its tutorial or paper (Supplementary Table~\\STmethods). The true number of domains was given to every method. Neighbourhood radii given in pixels were converted to multiples of the spot or cell spacing so that they transfer across technologies. Methods that output an embedding were additionally clustered with matched clustering: a 20-start tied-covariance Gaussian mixture keeping the best likelihood, the same for every method."),
         "SNmetrics": ("Metrics", "Agreement: ARI, NMI, AMI. Per-domain: clusters matched to domains with the Hungarian algorithm; macro-F1, missed domains, recall of domains below 5\\% of spots. Spatial: CHAOS (mean distance to the nearest same-cluster neighbour), PAS (fraction of spots whose cluster differs from most of their ten neighbours), Moran's I of the labels, boundary F1. Label-free: silhouette, Davies--Bouldin, Calinski--Harabasz. Definitions and code: spatialbench/metrics.py (unit tests in tests/)."),
         "SNstats": ("Statistics", "Sections are nested in groups (three DLPFC donors, STARmap, MERFISH). Differences to the reference are equal-weight means of group means with 95\\% percentile intervals from a hierarchical bootstrap (5000 resamples: groups, then sections within groups). Equivalence: 90\\% interval within $\\pm$0.03 ARI, about the seed-to-seed standard deviation. No correction for multiple comparisons is applied. Ranks and the probability of ranking first come from the same resamples. The reference method was chosen after seeing the means, so these comparisons are exploratory. Code: \\texttt{scripts/stats\\_cluster\\_aware.py}."),
         "SNaudit": ("Audit of released code", "Repositories were screened with \\texttt{scripts/audit\\_leakage.py} for five patterns of label use (Supplementary Table~\\STaudit), and every candidate line was read by one author. The taxonomy and all judgements, including false alarms, are in \\texttt{docs/LEAKAGE\\_AUDIT.md}. The audit describes what the released code does; it does not establish how published results were obtained."),
         "SNcompute": ("Computing environment", "All runs used one CPU thread per job on a 4-core Intel Xeon (2.8 GHz) with 15 GB of memory, Python 3.13, R 4.3.3 and mclust 6.0.1. Memory-heavy methods (DeepST, BayesSpace, NichePCA) were run one job at a time.")}

# ------------------------------------------------------------------ write supplementary.tex and labels
lab_lines = ["% generated by scripts/make_supplement.py: S-numbers used in the main text"]
body = []
for i, (kind, macro, title, fn) in enumerate([it for it in items], 1):
    lab_lines.append(f"\\newcommand{{\\{macro}}}{{S{i}}}")
for i, (macro, fn, cap) in enumerate(figs, 1):
    lab_lines.append(f"\\newcommand{{\\{macro}}}{{S{i}}}")
for i, macro in enumerate(notes, 1):
    lab_lines.append(f"\\newcommand{{\\{macro}}}{{{i}}}")
open(os.path.join(ROOT, "paper", "supp_labels.tex"), "w").write("\n".join(lab_lines) + "\n")
body.append("\\section*{Supplementary Notes}")
for i, (macro, (t, txt)) in enumerate(notes.items(), 1):
    body.append(f"\\subsection*{{Supplementary Note {i}. {t}}}\n{txt}\n")
body.append("\\clearpage\\section*{Supplementary Tables}")
for i, (kind, macro, title, fn) in enumerate(items, 1):
    body.append(f"\\begin{{table}}[!htbp]\\centering\n\\caption*{{\\textbf{{Supplementary Table S{i}.}} {title}}}\n\\input{{../results/supp/{fn}}}\n\\end{{table}}\n")
body.append("\\clearpage\\section*{Supplementary Figures}")
for i, (macro, fn, cap) in enumerate(figs, 1):
    body.append(f"\\begin{{figure}}[H]\\centering\n\\includegraphics[width=0.9\\linewidth,height=0.78\\textheight,keepaspectratio]{{{fn}}}\n\\caption*{{\\textbf{{Supplementary Figure S{i}.}} {cap}}}\n\\end{{figure}}\n")
doc = r"""% Supplementary Information. Generated by scripts/make_supplement.py; do not edit by hand.
\documentclass[10pt]{article}
\usepackage[a4paper,margin=2cm,landscape]{geometry}
\usepackage{booktabs,graphicx,caption,xcolor,amssymb,float}
\usepackage[T1]{fontenc}
\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage{courier}\usepackage[hidelinks]{hyperref}
\graphicspath{{../docs/figures/}}
\captionsetup{labelformat=empty,justification=raggedright,singlelinecheck=false}
\newcommand{\todo}[1]{\textcolor{red}{[TODO: #1]}}
\input{supp_labels.tex}
\begin{document}
\begin{center}{\Large\bfseries Supplementary Information}\\[4pt]
Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods\end{center}
""" + "\n".join(body) + "\n\\end{document}\n"
open(os.path.join(ROOT, "paper", "supplementary.tex"), "w").write(doc)
print(f"{len(items)} supplementary tables, {len(figs)} figures, {len(notes)} notes")
