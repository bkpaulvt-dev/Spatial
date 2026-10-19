"""Check that numbers quoted in paper/main.tex match results/paper_numbers*.json.

Each claim = (text that must appear in main.tex, value computed from the JSON, decimals).
Run after scripts/paper_numbers.py and scripts/paper_v2.py.
"""
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
v1 = json.load(open(os.path.join(ROOT, "results", "paper_numbers.json")))
v2 = json.load(open(os.path.join(ROOT, "results", "paper_numbers_v2.json")))
tex = re.sub(r"\s+", " ", open(os.path.join(ROOT, "paper", "main.tex")).read())
f = lambda x, d=3: f"{x:.{d}f}"
rng = lambda *xs: f"{min(xs):.2f}--{max(xs):.2f}"
claims = [
 ("HiSTaR median DLPFC", "median ARI over the twelve DLPFC sections of " + f(v1["bench_histar"]["median_slice"])),
 ("HiSTaR mean DLPFC", "(mean " + f(v1["bench_histar"]["mean"])),
 ("HiSTaR CI", f"CI over sections {f(v1['bench_histar']['ci_lo'])}--{f(v1['bench_histar']['ci_hi'])}"),
 ("HiSTaR deterministic", "(" + f(v1["bench_histar_deterministic"]["mean"])),
 ("HiSTaR + R mclust DLPFC", "placeholder"),   # replaced below
 ("HiSTaR seed SD", f"{f(v2['seed_sd']['dlpfc']['histar'])} on DLPFC and {f(v2['seed_sd']['starmap']['histar'],2)} on STARmap"),
 ("AnisoST vs lin MERFISH", f"(MERFISH: {f(v2['means']['merfish']['anisost'])} vs {f(v2['means']['merfish']['linear_diffusion'])})"),
 ("boundary", f"(by {f(v1['boundary_acc_boundary']['delta'])}, {v1['boundary_acc_boundary']['wins']} of 12 sections, Wilcoxon signed-rank $p={f(v1['boundary_acc_boundary']['p'])}$"),
]
# HiSTaR clustered with R mclust (seed-0 embeddings) is computed from the mclust results directly
import glob, pandas as pd
mc = pd.concat([pd.read_csv(p) for p in glob.glob(os.path.join(ROOT, "results", "mclust_lottery_*.csv"))])
h = mc[(mc.kind == "base") & (mc.dataset == "dlpfc") & (mc.method == "histar")].ARI.mean()
claims[4] = ("HiSTaR + R mclust DLPFC", f"and {h:.3f} (mean, seed 0)")
bad = 0
for name, text in claims:
    ok = re.sub(r"\s+", " ", text) in tex
    bad += not ok
    print(("OK   " if ok else "MISMATCH ") + f"{name:<28} {text}")

print(f"\n{len(claims) - bad}/{len(claims)} claims match.")

# every macro used in main.tex must be defined (macros are generated from the same JSON by paper_v2.py)
mac = open(os.path.join(ROOT, "results", "paper_macros.tex")).read()
defined = set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", mac))
raw = open(os.path.join(ROOT, "paper", "main.tex")).read()
used = {m for m in re.findall(r"\\([A-Za-z]+)", raw) if re.match(r"(mean[A-Z]|robust|overall|dLin|winsLin|pLin|gain|lot|rho[A-Z]|mc[A-Z]|mcs|mgcn|best|n[A-Z]|time|mem|rob[DLH]|std[DLH]|stat[A-Z]|pBest|rank[A-Z])", m)}
undefined = sorted(m for m in used if m not in defined and m not in {"newcommand", "mathcal"})
print(f"{len(used) - len(undefined)}/{len(used)} macros used in the text are defined; undefined: {undefined}")
unused = sorted(defined - set(re.findall(r"\\([A-Za-z]+)", raw)))
print(f"{len(unused)} generated macros are unused (fine).")
import sys
sys.exit(1 if (bad or undefined) else 0)
