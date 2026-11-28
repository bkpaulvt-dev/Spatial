"""Revision item 1 (V3): paired group-level effects and sensitivity analyses for the main comparison (Figure 2), from the SAME run-level
records as scripts/stats_cluster_aware.py (its data-building code is executed unchanged; nothing is rerun).

For every comparator (matched clustering, primary protocol): per-section paired difference linear diffusion minus method (seeds averaged
within section) on the sections both completed; then
  - effect per group (3 DLPFC donors, STARmap, MERFISH, breast, Stereo-seq) with its number of sections,
  - the existing group-weighted estimate (equal weight per group) with the hierarchical bootstrap (groups, then sections, resampled
    jointly for the pair),
  - an equal-weight average over the five DATASETS (DLPFC = mean of its sections), with a bootstrap that resamples datasets then sections,
  - the group-weighted estimate with all DLPFC sections omitted (4 groups).
Also: matched minus default clustering per method as group-level effects (Figure 5F) and the AnisoST boundary result per DLPFC donor.
Writes results/v3_paired_effects.json, results/supp/v3_paired.tex and results/paper_macros_v3.tex (prefix \\vt).
"""
import json, os, re, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
src = open(os.path.join(HERE, "stats_cluster_aware.py")).read()
cut = src.index("test_sec = SEC[")
ns = {"__file__": os.path.join(HERE, "stats_cluster_aware.py"), "__name__": "stats_v3"}
os.environ.pop("STATS_EXCLUDE", None); os.environ.pop("STATS_SOURCE", None)
exec(compile(src[:cut], "stats_cluster_aware.py", "exec"), ns)
P, SEC, series, ROB, STD, LABEL, REF = ns["P"], ns["SEC"], ns["series"], ns["ROB"], ns["STD"], ns["LABEL"], ns["REF"]
rng = np.random.default_rng(20261128); B = 5000
R = lambda f: os.path.join(ROOT, "results", f)
GROUP = {(d, s): c for d, s, c in zip(SEC.dataset, SEC.slice, SEC.cluster)}


def boot(delta, level):
    """level='group': resample the 7 groups then sections within; 'dataset': resample the 5 datasets then sections within."""
    key = (lambda k: GROUP[k]) if level == "group" else (lambda k: k[0])
    g = {}
    for k, v in delta.items():
        g.setdefault(key(k), []).append(v)
    G = [np.array(x) for x in g.values()]
    if not G:
        return None
    point = float(np.mean([x.mean() for x in G])); dr = np.empty(B)
    for i in range(B):
        ci = rng.integers(0, len(G), len(G)); dr[i] = np.mean([rng.choice(G[c], len(G[c])).mean() for c in ci])
    lo, hi = np.percentile(dr, [2.5, 97.5])
    return dict(d=point, lo=float(lo), hi=float(hi), units=len(G), sections=int(sum(len(x) for x in G)),
                verdict="LD better" if lo > 0 else "LD worse" if hi < 0 else "unresolved")


ref = series(ROB[REF]); out = {"comparisons": {}, "matched_minus_default": {}, "boundary": {}}
for m, lab in LABEL.items():
    if m == REF:
        continue
    s = series(ROB[m])
    delta = {k: ref[k] - v for k, v in s.items() if k in ref}
    if not delta:
        continue
    per_group = {}
    for k, v in delta.items():
        per_group.setdefault(GROUP[k], []).append(v)
    nod = {k: v for k, v in delta.items() if k[0] != "dlpfc"}
    out["comparisons"][m] = dict(label=lab, n_sections=len(delta), groups=sorted(per_group),
                                 per_group={g: dict(d=float(np.mean(v)), n=len(v)) for g, v in per_group.items()},
                                 group_weighted=boot(delta, "group"), dataset_weighted=boot(delta, "dataset"), no_dlpfc=boot(nod, "group"))
# Figure 5F: matched minus default clustering, group level
for m, lab in LABEL.items():
    if m in ("spagcn", "bass", "bayesspace"):
        continue
    a, b = series(ROB[m]), series(STD[m])
    d = {k: a[k] - b[k] for k in a if k in b}
    if d:
        pg = {}
        for k, v in d.items():
            pg.setdefault(GROUP[k], []).append(v)
        out["matched_minus_default"][m] = dict(label=lab, n_sections=len(d), group_weighted=boot(d, "group"),
                                               per_group={g: float(np.mean(v)) for g, v in pg.items()})
for m, lab in [(REF, "Linear diffusion")]:
    s = series(ROB[m]); d = {k: s[k] - series(STD[m]).get(k, np.nan) for k in s}
    pg = {}
    for k, v in d.items():
        if np.isfinite(v):
            pg.setdefault(GROUP[k], []).append(v)
    out["matched_minus_default"][m] = dict(label=lab, n_sections=sum(len(v) for v in pg.values()),
                                           group_weighted=boot({k: v for k, v in d.items() if np.isfinite(v)}, "group"), per_group={g: float(np.mean(v)) for g, v in pg.items()})
# AnisoST boundary result per DLPFC donor (results/anisost_boundary.jsonl)
bpath = R("anisost_boundary.jsonl")
if os.path.exists(bpath):
    bd = pd.read_json(bpath, lines=True)
    out["boundary_columns"] = list(bd.columns)
json.dump(out, open(R("v3_paired_effects.json"), "w"), indent=1)

# table + macros
NAMEK = lambda m: re.sub(r"[^A-Za-z]", "", {"banksy_l0.8": "BanksyHi", "banksy_l0.2": "BanksyLo", "pca_gmm": "Pca", "spatial_mgcn": "Mgcn"}.get(m, m.capitalize()))
f = lambda x: f"{x:+.3f}"
M = {}
GORDER = ["Br5292", "Br5595", "Br8100", "starmap", "merfish", "brca", "stereo"]
with open(R("supp/v3_paired.tex"), "w") as fh:
    fh.write("\\begin{tabular}{l" + "r" * 7 + "lll}\\toprule\nMethod & Br5292 & Br5595 & Br8100 & STARmap & MERFISH & Breast & Stereo & Group-weighted & Dataset-weighted & No DLPFC \\\\\\midrule\n")
    for m, c in sorted(out["comparisons"].items(), key=lambda kv: -kv[1]["group_weighted"]["d"]):
        pg = c["per_group"]; cells = [f(pg[g]["d"]) if g in pg else "--" for g in GORDER]
        def ci(x): return "--" if not x else f"{x['d']:+.3f} ({x['lo']:+.3f}, {x['hi']:+.3f})"
        fh.write(f"{c['label']} & " + " & ".join(cells) + f" & {ci(c['group_weighted'])} & {ci(c['dataset_weighted'])} & {ci(c['no_dlpfc'])} \\\\\n")
        k = NAMEK(m)
        for tag, x in (("G", c["group_weighted"]), ("D", c["dataset_weighted"]), ("N", c["no_dlpfc"])):
            if x:
                M[f"vt{k}{tag}"] = f(x["d"]); M[f"vt{k}{tag}Lo"] = f(x["lo"]); M[f"vt{k}{tag}Hi"] = f(x["hi"])
    fh.write("\\bottomrule\\end{tabular}\n")
cnt = lambda key, v: sum(1 for c in out["comparisons"].values() if c[key] and c[key]["verdict"] == v)
for key, tag in (("group_weighted", "G"), ("dataset_weighted", "D"), ("no_dlpfc", "N")):
    M[f"vtNBetter{tag}"] = str(cnt(key, "LD better")); M[f"vtNWorse{tag}"] = str(cnt(key, "LD worse")); M[f"vtNUnres{tag}"] = str(cnt(key, "unresolved"))
M["vtNComp"] = str(len(out["comparisons"]))
mm = out["matched_minus_default"]
M["vtNMatchedUp"] = str(sum(1 for v in mm.values() if v["group_weighted"]["lo"] > 0)); M["vtNMatchedDown"] = str(sum(1 for v in mm.values() if v["group_weighted"]["hi"] < 0))
M["vtNMatched"] = str(len(mm))
with open(R("paper_macros_v3.tex"), "w") as fh:
    fh.write("% generated by scripts/v3_paired_effects.py\n")
    for k, v in sorted(M.items()):
        assert re.fullmatch(r"[A-Za-z]+", k), k
        fh.write(f"\\newcommand{{\\{k}}}{{{v.replace('-', '$-$').replace('+', '$+$')}}}\n")
for m, c in sorted(out["comparisons"].items(), key=lambda kv: -kv[1]["group_weighted"]["d"]):
    g, d, n = c["group_weighted"], c["dataset_weighted"], c["no_dlpfc"]
    print(f"{c['label']:<14} n={c['n_sections']:2d} G {g['d']:+.3f} [{g['lo']:+.3f},{g['hi']:+.3f}] {g['verdict']:<10} | D {d['d']:+.3f} [{d['lo']:+.3f},{d['hi']:+.3f}] {d['verdict']:<10} | "
          + ("noDLPFC --" if not n else f"noDLPFC {n['d']:+.3f} [{n['lo']:+.3f},{n['hi']:+.3f}] {n['verdict']}"))
print({k: v for k, v in M.items() if k.startswith("vtN")})
for m, v in mm.items():
    g = v["group_weighted"]; print(f"matched-default {v['label']:<14} {g['d']:+.3f} [{g['lo']:+.3f},{g['hi']:+.3f}]")
print("boundary columns:", out.get("boundary_columns"))
