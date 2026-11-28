"""Numbers for the revised manuscript (V2): review-round extensions. Reads only existing result files; writes
results/paper_review_numbers.json and results/paper_macros_review.tex (LaTeX macros, prefix \\rv...). Nothing is rerun.

A  added methods on the 24 original sections: mean ARI per dataset (method's own clustering) and the hierarchical-bootstrap difference
   linear diffusion minus method (7 groups, 5000 draws, as scripts/stats_cluster_aware.py; linear diffusion from the standardised runner).
B  Allen MERFISH (3 held-out sections, mouse brain, CCF labels): descriptive means over finished jobs.
C  osmFISH / BaristaSeq (SDMBench labels of undocumented provenance): descriptive, separate group.
D  simulation (results/newdata_stats_sim.json), E  R5 (results/r5_analysis.json, r5_selected.json),
F  A9 (results/review_a9_summary.json), M6 (results/review_m6_fidelity.json), A10, BayesSpace ST, M5.
python scripts/paper_review_numbers.py"""
import json, os, re
import numpy as np, yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda f: os.path.join(ROOT, "results", f)
rng = np.random.default_rng(0); B = 5000


def newest(path, keep=lambda r: True):
    d = {}
    if os.path.exists(path):
        for l in open(path):
            try:
                r = json.loads(l)
            except Exception:
                continue
            if keep(r):
                d[r["id"]] = r
    return d


reg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"]
SEC = [(ds, str(s), (m.get("donor") if ds == "dlpfc" else ds), m["split"]) for ds, c in reg.items() for s, m in c["sections"].items()]
DSETS = ["dlpfc", "starmap", "merfish", "brca", "stereo"]

bench = newest(P("benchmark_runs.jsonl"))
review = newest(P("review_runs_deepmed2.jsonl"), lambda r: not r["method"].startswith("r5__"))
review.update(newest(P("review_runs_d3d4_deepmed2.jsonl")))
newdata = newest(P("newdata_runs_deepmed2.jsonl"))


def per_section(recs, method, key="metrics"):
    v = {}
    for r in recs.values():
        if r["method"] == method and r.get("status") == "ok" and r.get(key):
            v.setdefault((r["dataset"], str(r["section"])), []).append(r[key]["ARI"])
    return {k: float(np.mean(x)) for k, x in v.items()}


def hboot(delta):
    g = {}
    for ds, s, cl, sp in SEC:
        if (ds, s) in delta:
            g.setdefault(cl, []).append(delta[(ds, s)])
    G = [np.array(x) for x in g.values()]
    if not G:
        return None
    point = float(np.mean([x.mean() for x in G])); dr = np.empty(B)
    for i in range(B):
        ci = rng.integers(0, len(G), len(G)); dr[i] = np.mean([rng.choice(G[c], len(G[c])).mean() for c in ci])
    lo, hi = np.percentile(dr, [2.5, 97.5])
    return {"d": point, "lo": float(lo), "hi": float(hi), "groups": len(G), "sections": int(sum(len(x) for x in G)),
            "verdict": "better" if lo > 0 else "worse" if hi < 0 else "unresolved"}


def dmeans(ps):
    out = {}
    for ds in DSETS + ["allenmerfish", "osmfish", "baristaseq"]:
        v = [x for (d, s), x in ps.items() if d == ds]
        if v:
            out[ds] = float(np.mean(v))
    return out


out = {}
LD = per_section(bench, "linear_diffusion")
ADDED = ["cellcharter", "mender", "spatialpca", "precast", "drsc", "novae", "bass_multisample", "histar_official"]
out["A"] = {}
for m in ADDED:
    ps = {k: v for k, v in per_section(review, m).items() if k[0] in DSETS}
    out["A"][m] = {"means": dmeans(ps), "n_sections": len(ps), "delta": hboot({k: LD[k] - v for k, v in ps.items() if k in LD})}
out["A"]["linear_diffusion"] = {"means": dmeans(LD), "n_sections": len(LD)}

# B / C: new real data (descriptive)
def real(ds):
    res = {}
    for m in sorted({r["method"] for r in list(newdata.values()) + list(review.values()) if r["dataset"] == ds}):
        recs = [r for r in list(newdata.values()) + list(review.values()) if r["dataset"] == ds and r["method"] == m]
        ok = [r for r in recs if r.get("status") == "ok"]
        secs = {}
        for r in ok:
            secs.setdefault(str(r["section"]), []).append(r["metrics"]["ARI"])
        res[m] = {"n_jobs": len(recs), "n_ok": len(ok), "n_sections_ok": len(secs),
                  "mean": float(np.mean([np.mean(v) for v in secs.values()])) if secs else None,
                  "memory_limit": sum(1 for r in recs if r.get("outcome") == "memory limit")}
    return res
out["B"] = real("allenmerfish"); out["C"] = {"osmfish": real("osmfish"), "baristaseq": real("baristaseq")}

out["D"] = json.load(open(P("newdata_stats_sim.json")))
out["E"] = {"analysis": json.load(open(P("r5_analysis.json"))), "selected": json.load(open(P("r5_selected.json")))["selected"]}
out["F"] = {"a9": json.load(open(P("review_a9_summary.json"))), "m6": json.load(open(P("review_m6_fidelity.json"))),
            "a10": json.load(open(P("review_a10_cross_host.json")))}
bst = per_section(review, "bayesspace_st"); out["F"]["bayesspace_st"] = {k[1]: v for k, v in bst.items()}
out["F"]["bayesspace_st_fail"] = sorted({str(r["section"]) for r in review.values() if r["method"] == "bayesspace_st" and r.get("status") != "ok"})
bm = {k: v for k, v in per_section(review, "bass_multisample").items()}
bs = per_section(bench, "bass")
out["F"]["m5"] = {ds: {"multi": float(np.mean([v for k, v in bm.items() if k[0] == ds])),
                       "single": float(np.mean([bs[k] for k in bm if k[0] == ds and k in bs])), "n": sum(1 for k in bm if k[0] == ds)}
                  for ds in sorted({k[0] for k in bm})}
json.dump(out, open(P("paper_review_numbers.json"), "w"), indent=1, default=float)

# ---------- macros
M = {}
f3 = lambda x: f"{x:.3f}"; s3 = lambda x: f"{x:+.3f}".replace("+", "$+$").replace("-", "$-$")
NAME = {"cellcharter": "CellCharter", "mender": "MENDER", "spatialpca": "SpatialPCA", "precast": "PRECAST", "drsc": "DRSC", "novae": "Novae",
        "bass_multisample": "BassMulti", "histar_official": "HistarOff"}
for m, k in NAME.items():
    a = out["A"][m]
    for ds, v in a["means"].items():
        M[f"rv{k}{ds.capitalize()}"] = f3(v)
    if a["delta"]:
        dd = a["delta"]; M[f"rv{k}D"] = s3(dd["d"]); M[f"rv{k}Lo"] = s3(dd["lo"]); M[f"rv{k}Hi"] = s3(dd["hi"]); M[f"rv{k}N"] = str(a["n_sections"])
for ds, v in out["A"]["linear_diffusion"]["means"].items():
    M[f"rvLin{ds.capitalize()}"] = f3(v)
# Allen
al = out["B"]; okm = {m: v for m, v in al.items() if v["mean"] is not None and v["n_sections_ok"] == 3}
rank = sorted(okm, key=lambda m: -okm[m]["mean"])
M["rvAllenLin"] = f3(al["linear_diffusion"]["mean"]); M["rvAllenRankLin"] = str(rank.index("linear_diffusion") + 1); M["rvAllenNRanked"] = str(len(rank))
M["rvAllenJobs"] = str(sum(v["n_jobs"] for m, v in al.items() if m in {r["method"] for r in newdata.values()}))
M["rvAllenOk"] = str(sum(v["n_ok"] for m, v in al.items() if m in {r["method"] for r in newdata.values()}))
for m, k in [("spaceflow", "Spaceflow"), ("nichepca", "Nichepca"), ("bass", "Bass"), ("stagate", "Stagate"), ("histar", "Histar"), ("pca_gmm", "Pca"),
             ("cellcharter", "Cellcharter"), ("mender", "Mender"), ("precast", "Precast"), ("drsc", "Drsc"), ("anisost", "Anisost"), ("banksy_l0.8", "BanksyHi")]:
    if m in al and al[m]["mean"] is not None:
        M[f"rvAllen{k}"] = f3(al[m]["mean"])
M["rvAllenAhead"] = ", ".join(rank[:rank.index("linear_diffusion")])
# simulation
sd = out["D"]; M["rvSimN"] = f"{sd['n_records']:,}".replace(",", "{,}")
M["rvSimHone"] = f3(sd["H1"]["delta_m1_minus_m7"]); M["rvSimHoneLo"] = f3(sd["H1"]["ci"][0]); M["rvSimHoneHi"] = f3(sd["H1"]["ci"][1])
M["rvSimHtwo"] = s3(sd["H2"]["delta_B3_minus_A7"]); M["rvSimHtwoLo"] = s3(sd["H2"]["ci"][0]); M["rvSimHtwoHi"] = s3(sd["H2"]["ci"][1])
import csv
for r in csv.DictReader(open(P("newdata_sim_delta.csv"))):
    M[f"rvSimD{r['geometry']}{['','one','two','three','four','five','six','seven','eight'][int(r['param'])] if int(r['param'])<9 else {'12':'twelve','20':'twenty'}[r['param']]}"] = s3(float(r["delta"]))
txt = open(P("newdata_sim_summary.md")).read()
red = {}
for line in txt.splitlines():
    mm = re.match(r"\| (\w+) \| ([\d. |]+)\|$", line)
    if mm and mm.group(1) not in ("method",):
        red[mm.group(1)] = [float(x) for x in mm.group(2).split("|") if x.strip()]
for m, k in [("bass", "Bass"), ("ccst", "Ccst"), ("deepst", "Deepst"), ("graphst", "Graphst"), ("spaceflow", "Spaceflow"), ("spatial_mgcn", "Mgcn"), ("stagate", "Stagate")]:
    if m in red:
        M[f"rvSimRed{k}Bthree"] = f3(red[m][4]); M[f"rvSimRed{k}Aseven"] = f3(red[m][3])
out["D_reduced"] = red
FULL = {(r["method"], r["geometry"], r["param"]): float(r["ari_mean"]) for r in csv.DictReader(open(P("newdata_sim_ari_table.csv"))) if r["design"].startswith("full")}
for m, k in [("linear_diffusion", "Lin"), ("pca_gmm", "Pca"), ("anisost", "Anisost"), ("histar", "Histar"), ("nichepca", "Nichepca"), ("banksy_l0.8", "BanksyHi")]:
    for g, pr, nm in [("A", "1", "Aone"), ("A", "7", "Aseven"), ("B", "3", "Bthree"), ("B", "20", "Btwenty")]:
        if (m, g, pr) in FULL:
            M[f"rvSimFull{k}{nm}"] = f3(FULL[(m, g, pr)])
# R5
e = out["E"]["analysis"]; RK = {"anisost": "Anisost", "pca_gmm": "Pca", "banksy": "Banksy", "nichepca": "Nichepca", "linear_diffusion": "Lin"}
for m, v in e["P1_test"].items():
    k = RK[m]; M[f"rvRfive{k}D"] = s3(v["estimate"]); M[f"rvRfive{k}Lo"] = s3(v["ci95"][0]); M[f"rvRfive{k}Hi"] = s3(v["ci95"][1])
for m, v in e["P2_gain_test"].items():
    k = RK[m]; M[f"rvRfiveGain{k}"] = s3(v["estimate"]); M[f"rvRfiveGain{k}Lo"] = s3(v["ci95"][0]); M[f"rvRfiveGain{k}Hi"] = s3(v["ci95"][1])
for i, (v, m) in enumerate(e["P3_rank"]["tuned"]):
    M[f"rvRfiveTuned{RK[m]}"] = f3(v)
for m, v in out["E"]["selected"].items():
    M[f"rvRfiveSel{RK[m]}"] = str(v["config"]); M[f"rvRfiveDev{RK[m]}"] = f3(v["score"]); M[f"rvRfiveDevA{RK[m]}"] = f3(v["arm_a_score"])
# A9, M6, A10, BayesSpace ST, M5
a9 = out["F"]["a9"]
M["rvAnineF"] = f3(a9["mean_over_sections"]["ARI_F"]); M["rvAnineP"] = f3(a9["mean_over_sections"]["ARI_P"]); M["rvAnineL"] = f3(a9["mean_over_sections"]["ARI_L"])
M["rvAnineLab"] = f3(a9["mean_over_sections"]["ARI_existing_label_selected"]); M["rvAnineNsec"] = str(a9["n_sections"])
M["rvAninePF"] = s3(a9["diff_P_minus_F"]["mean"]); M["rvAninePFLo"] = s3(a9["diff_P_minus_F"]["ci95"][0]); M["rvAninePFHi"] = s3(a9["diff_P_minus_F"]["ci95"][1])
M["rvAnineLF"] = s3(a9["diff_L_minus_F"]["mean"]); M["rvAnineLFLo"] = s3(a9["diff_L_minus_F"]["ci95"][0]); M["rvAnineLFHi"] = s3(a9["diff_L_minus_F"]["ci95"][1])
m6 = out["F"]["m6"]
M["rvMsixOffDef"] = f3(np.mean([r["official_default_ari"] for r in m6])); M["rvMsixOursDef"] = f3(np.mean([r["ours_default_ari"] for r in m6]))
M["rvMsixOffMat"] = f3(np.mean([r["official_matched_ari"] for r in m6])); M["rvMsixOursMat"] = f3(np.mean([r["ours_matched_ari"] for r in m6]))
M["rvMsixOffMed"] = f3(np.median([r["official_default_ari"] for r in m6])); M["rvMsixN"] = str(len(m6))
a10 = {r["method"]: r for r in out["F"]["a10"]["rows"]}
M["rvAtenDeepst"] = s3(a10["deepst"]["same_seed_difference_host_minus_original"]); M["rvAtenLin"] = f3(abs(a10["linear_diffusion"]["same_seed_difference_host_minus_original"]))
for s, v in out["F"]["bayesspace_st"].items():
    M["rvBsst" + {"E9.5_E1S1": "Enine", "E10.5_E2S1": "EtenTwo", "E10.5_E1S1": "EtenOne"}[s]] = f3(v)
for ds, v in out["F"]["m5"].items():
    M[f"rvMfive{ds.capitalize()}Multi"] = f3(v["multi"]); M[f"rvMfive{ds.capitalize()}Single"] = f3(v["single"])
with open(P("paper_macros_review.tex"), "w") as fh:
    fh.write("% generated by scripts/paper_review_numbers.py; do not edit by hand\n")
    for k, v in sorted(M.items()):
        assert re.fullmatch(r"[A-Za-z]+", k), k
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(M), "macros;", "Allen rank of linear diffusion", M["rvAllenRankLin"], "of", M["rvAllenNRanked"], "ahead:", M["rvAllenAhead"])
for m in ADDED:
    a = out["A"][m]; d = a["delta"]
    print(f"{m:17s} n={a['n_sections']:2d}", {k: round(v, 3) for k, v in a["means"].items()}, "" if not d else f"LD-m {d['d']:+.3f} [{d['lo']:+.3f},{d['hi']:+.3f}] {d['verdict']} ({d['groups']} groups)")
json.dump(out, open(P("paper_review_numbers.json"), "w"), indent=1, default=float)   # again, with the tier-3 reduced table

# ---------- supplementary tables of manuscript V2 (results/supp/v2_*.tex)
os.makedirs(P("supp"), exist_ok=True)
NM = {"linear_diffusion": "Linear diffusion", "anisost": "AnisoST", "pca_gmm": "PCA", "histar": "HiSTaR", "graphst": "GraphST", "banksy_l0.8": "BANKSY $\\lambda=0.8$",
      "banksy_l0.2": "BANKSY $\\lambda=0.2$", "spagcn": "SpaGCN", "stagate": "STAGATE", "sedr": "SEDR", "spaceflow": "SpaceFlow", "nichepca": "NichePCA",
      "ccst": "CCST", "spatial_mgcn": "Spatial-MGCN", "deepst": "DeepST", "bass": "BASS", "bayesspace": "BayesSpace", "cellcharter": "CellCharter",
      "mender": "MENDER", "spatialpca": "SpatialPCA", "precast": "PRECAST", "drsc": "DR-SC", "novae": "Novae (zero-shot)", "bass_multisample": "BASS multi-sample",
      "histar_official": "HiSTaR official code", "spatial_mgcn_a9": "Spatial-MGCN (A9 runs)", "bayesspace_st": "BayesSpace (ST lattice)"}
fx = lambda v: "--" if v is None else f"{v:.3f}"
with open(P("supp/v2_extra.tex"), "w") as fh:
    fh.write("\\begin{tabular}{lrrrrrrl}\\toprule\nMethod & DLPFC & STARmap & MERFISH & Breast & Stereo-seq & Sections & LD $-$ method (95\\% interval) \\\\\\midrule\n")
    for m in ["linear_diffusion"] + ADDED:
        a = out["A"][m]; mm = a["means"]; d = a.get("delta")
        fh.write(f"{NM[m]} & " + " & ".join(fx(mm.get(ds)) for ds in DSETS) + f" & {a['n_sections']} & " +
                 ("reference" if m == "linear_diffusion" else "--" if not d else f"{d['d']:+.3f} ({d['lo']:+.3f}, {d['hi']:+.3f}), {d['groups']} groups") + " \\\\\n")
    fh.write("\\bottomrule\\end{tabular}\n")
def realtab(res, fn):
    with open(P(fn), "w") as fh:
        fh.write("\\begin{tabular}{lrrrr}\\toprule\nMethod & Jobs & OK & Memory limit & Mean ARI (sections) \\\\\\midrule\n")
        for m, v in sorted(res.items(), key=lambda kv: -(kv[1]["mean"] if kv[1]["mean"] is not None else -1)):
            if m.startswith("r5__"):
                continue
            fh.write(f"{NM.get(m, m)} & {v['n_jobs']} & {v['n_ok']} & {v['memory_limit']} & {fx(v['mean'])} ({v['n_sections_ok']}) \\\\\n")
        fh.write("\\bottomrule\\end{tabular}\n")
realtab(out["B"], "supp/v2_allen.tex")
with open(P("supp/v2_sdm.tex"), "w") as fh:
    fh.write("\\begin{tabular}{lrr}\\toprule\nMethod & osmFISH (1 section) & BaristaSeq (3 slices) \\\\\\midrule\n")
    o, b = out["C"]["osmfish"], out["C"]["baristaseq"]
    for m in sorted(set(o) | set(b), key=lambda m: -((b.get(m) or {}).get("mean") or -1)):
        fh.write(f"{NM.get(m, m)} & {fx((o.get(m) or {}).get('mean'))} & {fx((b.get(m) or {}).get('mean'))} \\\\\n")
    fh.write("\\bottomrule\\end{tabular}\n")
print("supplementary tables written")
