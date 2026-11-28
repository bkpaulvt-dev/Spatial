"""Revision V3 part 2 numbers: boundary/size (results/v3_boundary_size.json), crossed seeds (results/cs_summary.json) and Cavity
(results/v3_cavity.json) -> results/paper_macros_v3c.tex (prefix \\vc) and results/supp/v3_bound.tex, v3_cs.tex, v3_cavity.tex.
Missing inputs leave a 'pending' macro, so the manuscript builds at every stage."""
import json, os, re
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); R = lambda f: os.path.join(ROOT, "results", f)
M = {}; s3 = lambda x: f"{x:+.3f}".replace("-", "$-$").replace("+", "$+$"); f3 = lambda x: f"{x:.3f}"
GORD = ["Br5292", "Br5595", "Br8100", "starmap", "merfish", "brca", "stereo"]; GN = {"starmap": "STARmap", "merfish": "MERFISH", "brca": "Breast", "stereo": "Stereo-seq"}
# ---- boundary / size
if os.path.exists(R("v3_boundary_size.json")):
    b = json.load(open(R("v3_boundary_size.json")))
    with open(R("supp/v3_bound.tex"), "w") as fh:
        fh.write("\\begin{tabular}{ll" + "r" * 8 + "}\\toprule\nAxis & Bin & " + " & ".join(GN.get(g, g) for g in GORD) + " & Group mean (spots) \\\\\\midrule\n")
        for kind, order, lab in (("distance", ["1", "2", "3-4", "5-8", ">8"], "Distance to boundary (spacings)"), ("prevalence", ["<5%", "5-10%", "10-20%", ">20%"], "Domain prevalence")):
            for bn in order:
                v = b[kind].get(bn)
                if not v:
                    continue
                fh.write(f"{lab if bn == order[0] else ''} & {bn.replace('%', '\\%').replace('>', '$>$').replace('<', '$<$')} & " + " & ".join(f"{v['per_group'][g]:+.3f}" if g in v["per_group"] else "--" for g in GORD)
                         + f" & {v['group_mean']:+.3f} ({v['n_spots']:,}) \\\\\n")
        fh.write("\\bottomrule\\end{tabular}\n")
    d = b["distance"]
    M["vcBoundOne"] = s3(d["1"]["group_mean"]); M["vcBoundTwo"] = s3(d["2"]["group_mean"]); M["vcBoundMid"] = s3(d["3-4"]["group_mean"])
    M["vcBoundFar"] = s3(d["5-8"]["group_mean"]); M["vcBoundDeep"] = s3(d[">8"]["group_mean"])
    M["vcBoundDeepBrca"] = s3(d[">8"]["per_group"]["brca"]); M["vcBoundDeepStereo"] = s3(d[">8"]["per_group"]["stereo"])
    M["vcBoundOneStereo"] = s3(d["1"]["per_group"]["stereo"]); M["vcBoundFarBrca"] = s3(d["5-8"]["per_group"]["brca"])
    p = b["prevalence"]; M["vcPrevSmall"] = s3(p["<5%"]["group_mean"]); M["vcPrevSmallN"] = str(p["<5%"]["n_groups"]); M["vcPrevLarge"] = s3(p[">20%"]["group_mean"])
    M["vcKnnVisium"] = f"{b['neighbourhood']['dlpfc']['knn6_um']:.0f}"
# ---- crossed seeds
if os.path.exists(R("cs_summary.json")):
    t = pd.DataFrame(json.load(open(R("cs_summary.json"))))
    for cl in ("gmm", "kmeans"):
        x = t[t.clusterer == cl]
        g = x.groupby("group")[["within_sd", "between_sd_corrected", "within_range"]].mean()
        M[f"vcWithinSD{cl.capitalize()}"] = f3(g.within_sd.mean()); M[f"vcBetweenSD{cl.capitalize()}"] = f3(g.between_sd_corrected.mean())
        M[f"vcWithinRange{cl.capitalize()}"] = f3(g.within_range.mean())
        r = x.assign(ratio=x.within_sd / x.between_sd_corrected.replace(0, np.nan))
        M[f"vcNWithinLarger{cl.capitalize()}"] = str(int((x.within_sd > x.between_sd_corrected).sum())); M[f"vcNCells{cl.capitalize()}"] = str(int(len(x)))
        pm = x.groupby("method")[["within_sd", "between_sd_corrected"]].mean()
        M[f"vcNMethodWithin{cl.capitalize()}"] = str(int((pm.within_sd > pm.between_sd_corrected).sum())); M[f"vcNMethods{cl.capitalize()}"] = str(len(pm))
        for k in (1, 3, 20):
            M[f"vcSel{['', 'One', '', 'Three'][k] if k < 20 else 'Twenty'}{cl.capitalize()}"] = f3(x.groupby("group")[f"select_{k}"].mean().mean())
    with open(R("supp/v3_cs.tex"), "w") as fh:
        fh.write("\\begin{tabular}{llrrrrrrr}\\toprule\nClusterer & Method & Mean ARI & Within SD & Within range & Between SD & Between SD (corr.) & Best of 3 & Best of 20 \\\\\\midrule\n")
        for cl in ("gmm", "kmeans"):
            pm = t[t.clusterer == cl].groupby("method")[["mean_ari", "within_sd", "within_range", "between_sd_uncorrected", "between_sd_corrected", "select_3", "select_20"]].mean()
            for m, r in pm.sort_values("mean_ari", ascending=False).iterrows():
                fh.write(f"{'GMM' if cl == 'gmm' else 'k-means'} & {m.replace('_', ' ')} & " + " & ".join(f"{v:.3f}" for v in r.values) + " \\\\\n")
        fh.write("\\bottomrule\\end{tabular}\n")
    M["vcAbstract"] = (f"In a crossed design with five training seeds on seven sections, the standard deviation of ARI over clustering starts on a fixed "
                       f"embedding was {M['vcWithinSDGmm']} on average, against {M['vcBetweenSDGmm']} between training seeds.")
else:
    M["vcAbstract"] = "\\todo{crossed-seed sentence pending}"
# ---- Cavity
if os.path.exists(R("v3_cavity.json")):
    c = json.load(open(R("v3_cavity.json"))); mean = pd.DataFrame(c["means"]).T
    M["vcCavRankAll"] = str(int(c["rank_linear_diffusion"]["all"])); M["vcCavRankNo"] = str(int(c["rank_linear_diffusion"]["no_cavity"]))
    M["vcCavNMethods"] = str(c["rank_linear_diffusion"]["n_methods"]); M["vcCavRho"] = f"{c['spearman_rank_change']:.2f}"
    M["vcCavMeanChange"] = s3(mean.change.mean()); M["vcCavLinAll"] = f3(mean.loc["linear_diffusion", "ari_all"]); M["vcCavLinNo"] = f3(mean.loc["linear_diffusion", "ari_no_cavity"])
    M["vcCavN"] = str(c["n_predictions"])
    with open(R("supp/v3_cavity.tex"), "w") as fh:
        fh.write("\\begin{tabular}{lrrrr}\\toprule\nMethod & Sections & ARI, all bins & ARI, Cavity excluded & Change \\\\\\midrule\n")
        for m, r in mean.sort_values("ari_all", ascending=False).iterrows():
            fh.write(f"{m.replace('_', ' ')} & {c['sections_per_method'].get(m, '')} & {r.ari_all:.3f} & {r.ari_no_cavity:.3f} & {r.change:+.3f} \\\\\n")
        fh.write("\\bottomrule\\end{tabular}\n")
with open(R("paper_macros_v3c.tex"), "w") as fh:
    fh.write("% generated by scripts/v3_part2_numbers.py\n")
    for k, v in sorted(M.items()):
        assert re.fullmatch(r"[A-Za-z]+", k), k
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(M)
