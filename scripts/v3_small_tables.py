"""Revision V3 items 1d, 1e, 3e, 4b: AnisoST boundary result per DLPFC donor; Table 1 with untuned (Arm A) and tuned ARI on the same 18 test
sections and seeds; Novae paired with linear diffusion on its completed sections; Allen completion by method and seed; HiSTaR official code
vs port paired by section and seed. Reads existing records only. Writes results/v3_small_tables.json, results/supp/v3_*.tex and
results/paper_macros_v3b.tex (prefix \\vs)."""
import json, os, re
import numpy as np, pandas as pd, yaml
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); R = lambda f: os.path.join(ROOT, "results", f)
rng = np.random.default_rng(20261128); B = 5000; M = {}; out = {}
f3 = lambda x: f"{x:.3f}"; s3 = lambda x: f"{x:+.3f}".replace("-", "$-$").replace("+", "$+$")


def newest(p, keep=lambda r: True):
    d = {}
    for l in open(R(p)):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if keep(r):
            d[r["id"]] = r
    return d


reg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"]
GROUP = {(ds, str(s)): (m.get("donor") if ds == "dlpfc" else ds) for ds, c in reg.items() for s, m in c["sections"].items()}
SPLIT = {(ds, str(s)): m["split"] for ds, c in reg.items() for s, m in c["sections"].items()}


def boot(delta):
    g = {}
    for k, v in delta.items():
        g.setdefault(GROUP[k], []).append(v)
    G = [np.array(x) for x in g.values()]
    pt = float(np.mean([x.mean() for x in G])); dr = np.empty(B)
    for i in range(B):
        ci = rng.integers(0, len(G), len(G)); dr[i] = np.mean([rng.choice(G[c], len(G[c])).mean() for c in ci])
    lo, hi = np.percentile(dr, [2.5, 97.5]); return dict(d=pt, lo=float(lo), hi=float(hi), groups=len(G), sections=int(sum(map(len, G))))


# 1d: AnisoST boundary per donor
b = pd.read_json(R("anisost_boundary.jsonl"), lines=True); b["slice"] = b.slice.astype(str)
b["donor"] = [GROUP[("dlpfc", s)] for s in b.slice]
w = b.pivot_table(index=["donor", "slice", "seed"], columns="diffusion", values="acc_boundary"); w["eff"] = w.anisotropic - w.linear
per_sec = w.groupby(["donor", "slice"]).eff.mean(); per_don = per_sec.groupby("donor").mean()
out["boundary_per_donor"] = per_don.round(4).to_dict()
for dnr, v in per_don.items():
    M[f"vsBound{dnr.replace('Br', 'Br')}".replace("5292", "A").replace("5595", "B").replace("8100", "C")] = s3(v)
M["vsBoundMean"] = s3(per_don.mean()); M["vsBoundPos"] = str(int((per_don > 0).sum()))
# 1e: Table 1, untuned vs tuned on the same 18 test sections and seeds
rv = newest("review_runs_deepmed2.jsonl", lambda r: r["method"].endswith("__tuned"))
bench = newest("benchmark_runs.jsonl")
ARM = {"linear_diffusion": "linear_diffusion", "anisost": "anisost", "pca_gmm": "pca_gmm", "banksy": "banksy_l0.8", "nichepca": "nichepca"}
def sec_means(recs, m):
    v = {}
    for r in recs.values():
        if r["method"] == m and r["status"] == "ok" and r["seed"] in (0, 1, 2):
            v.setdefault((r["dataset"], str(r["section"])), {})[r["seed"]] = r["metrics"]["ARI"]
    return v
tab = {}
for m, a in ARM.items():
    t = sec_means(rv, f"r5__{m}__tuned"); u = sec_means(bench, a)
    common = {k: sorted(set(t[k]) & set(u[k])) for k in t if k in u and SPLIT[k] == "test"}
    tt = {k: np.mean([t[k][s] for s in ss]) for k, ss in common.items() if ss}; uu = {k: np.mean([u[k][s] for s in ss]) for k, ss in common.items() if ss}
    def cm(x):
        g = {}
        for k, v in x.items():
            g.setdefault(GROUP[k], []).append(v)
        return float(np.mean([np.mean(v) for v in g.values()]))
    tab[m] = dict(untuned=cm(uu), tuned=cm(tt), gain=boot({k: tt[k] - uu[k] for k in tt}), n_sections=len(tt), n_seeds=int(np.mean([len(s) for s in common.values()])))
    k = {"linear_diffusion": "Lin", "anisost": "Anisost", "pca_gmm": "Pca", "banksy": "Banksy", "nichepca": "Nichepca"}[m]
    M[f"vsUntuned{k}"] = f3(tab[m]["untuned"]); M[f"vsTuned{k}"] = f3(tab[m]["tuned"]); M[f"vsGain{k}"] = s3(tab[m]["gain"]["d"])
    M[f"vsGain{k}Lo"] = s3(tab[m]["gain"]["lo"]); M[f"vsGain{k}Hi"] = s3(tab[m]["gain"]["hi"])
M["vsTabSections"] = str(tab["linear_diffusion"]["n_sections"])
out["table1"] = tab
# Novae paired with linear diffusion (runner) on its completed sections
rvall = newest("review_runs_deepmed2.jsonl", lambda r: r["method"] == "novae")
nv = {k: np.mean(list(v.values())) for k, v in sec_means(rvall, "novae").items() if k in GROUP}
ld = {k: np.mean(list(v.values())) for k, v in sec_means(bench, "linear_diffusion").items()}
nd = {k: ld[k] - v for k, v in nv.items() if k in ld}
out["novae"] = dict(boot(nd), datasets=sorted({k[0] for k in nd}))
M["vsNovaeD"] = s3(out["novae"]["d"]); M["vsNovaeLo"] = s3(out["novae"]["lo"]); M["vsNovaeHi"] = s3(out["novae"]["hi"]); M["vsNovaeN"] = str(out["novae"]["sections"]); M["vsNovaeG"] = str(out["novae"]["groups"])
# 3e: Allen completion by method and seed
nd_ = newest("newdata_runs_deepmed2.jsonl", lambda r: r["dataset"] == "allenmerfish")
comp = {}
for r in nd_.values():
    comp.setdefault(r["method"], {}).setdefault(int(r["seed"]), []).append("ok" if r.get("status") == "ok" else (r.get("outcome") or "error"))
out["allen_completion"] = comp
with open(R("supp/v3_allen_completion.tex"), "w") as fh:
    fh.write("\\begin{tabular}{lccc}\\toprule\nMethod & Seed 0 & Seed 1 & Seed 2 \\\\\\midrule\n")
    ab = {"ok": "ok", "memory limit": "mem", "error": "err", "time limit": "time"}
    for m in sorted(comp):
        fh.write(m.replace("_", "\\_") + " & " + " & ".join(" ".join(ab.get(x, x) for x in comp[m].get(s, [])) or "--" for s in (0, 1, 2)) + " \\\\\n")
    fh.write("\\bottomrule\\end{tabular}\n")
# 4b: HiSTaR official vs port, paired by section and seed
off = sec_means(newest("review_runs_deepmed2.jsonl", lambda r: r["method"] == "histar_official"), "histar_official")
ours = sec_means(bench, "histar")
pairs = [(k[1], s, off[k][s], ours[k][s]) for k in sorted(off) if k in ours for s in sorted(off[k]) if s in ours[k]]
pdf = pd.DataFrame(pairs, columns=["section", "seed", "official", "port"]); pdf["diff"] = pdf.official - pdf.port
out["histar_pairs"] = pdf.round(4).to_dict(orient="records")
M["vsHistarPairs"] = str(len(pdf)); M["vsHistarOffMed"] = f3(pdf.groupby("section").official.mean().median()); M["vsHistarPortMed"] = f3(pdf.groupby("section").port.mean().median())
M["vsHistarOffMean"] = f3(pdf.official.mean()); M["vsHistarPortMean"] = f3(pdf.port.mean()); M["vsHistarDiffMean"] = s3(pdf["diff"].mean())
M["vsHistarDiffSD"] = f3(pdf["diff"].std(ddof=1))
with open(R("supp/v3_histar_pairs.tex"), "w") as fh:
    fh.write("\\begin{tabular}{lrrrr}\\toprule\nSection & Seed & Official code & Port & Official $-$ port \\\\\\midrule\n")
    for r in pairs:
        fh.write(f"{r[0]} & {r[1]} & {r[2]:.3f} & {r[3]:.3f} & {r[2]-r[3]:+.3f} \\\\\n")
    fh.write("\\bottomrule\\end{tabular}\n")
json.dump(out, open(R("v3_small_tables.json"), "w"), indent=1, default=float)
with open(R("paper_macros_v3b.tex"), "w") as fh:
    fh.write("% generated by scripts/v3_small_tables.py\n")
    for k, v in sorted(M.items()):
        assert re.fullmatch(r"[A-Za-z]+", k), k
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(json.dumps({k: v for k, v in M.items()}, indent=0))
