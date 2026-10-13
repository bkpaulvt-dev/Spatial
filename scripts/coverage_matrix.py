"""Methods x experiments coverage matrix, computed from the result files (nothing typed by hand).

Cells: number of completed units / expected units, or 'n/a (reason)' where the experiment is
structurally impossible. Writes results/coverage_matrix.csv and results/coverage_matrix.md.
"""
import glob, json, os
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda f: os.path.join(ROOT, "results", f)
NSEC = {"dlpfc": 12, "starmap": 3, "merfish": 5}
METHODS = ["linear_diffusion", "anisost", "pca_gmm", "banksy_l0.2", "banksy_l0.8", "histar", "graphst", "spagcn", "stagate",
           "sedr", "spaceflow", "nichepca", "ccst", "spatial_mgcn", "deepst", "bass", "bayesspace"]
NO_EMB = {"spagcn", "bass", "bayesspace"}            # cluster internally: no embedding to re-cluster
VISIUM_ONLY = {"bayesspace"}
rd = lambda f: [json.loads(l) for l in open(R(f))] if os.path.exists(R(f)) else []

def nsec(m): return 12 if m in VISIUM_ONLY else 20

# --- accuracy sources: paper pipeline (older files + pilot) and the standardised runner
paper = set()
for f in ("anisost_main.jsonl", "baselines.jsonl", "extra.jsonl", "graphst.jsonl", "new_methods.jsonl"):
    for r in rd(f):
        if r.get("status", "ok") != "ok": continue
        m = {"anisost_single_gmm": "anisost", "histar_rerun": "histar", "histar+robust": "histar", "graphst+robust": "graphst",
             "banksy_l0.8+robust": "banksy_l0.8", "banksy_l0.2+robust": "banksy_l0.2", "graphst_refined": "graphst"}.get(r["method"], r["method"])
        paper.add((m, r.get("dataset", "dlpfc"), str(r["slice"]), r["seed"]))
unified = {}
for r in rd("benchmark_runs.jsonl"):
    if r.get("status") == "ok": unified[r["id"]] = r
uni = {(r["method"], r["dataset"], str(r["section"]), r["seed"]) for r in unified.values()}
lot = {(r["method"], r.get("dataset", "dlpfc"), str(r["slice"])) for r in rd("clustering_lottery.jsonl")}
mc = set()
for f in glob.glob(R("mclust_lottery_*.csv")):
    d = pd.read_csv(f)
    mc |= {(r.method, r.dataset, str(r["slice"])) for _, r in d[d.kind == "base"].iterrows()}
inv = {}
if os.path.exists(R("invariance_pilot.json")):
    inv = json.load(open(R("invariance_pilot.json")))
invm = set(inv) if isinstance(inv, dict) else set()

rows = []
for m in METHODS:
    n = nsec(m)
    acc_p = {(d, s) for (mm, d, s, sd) in paper if mm == m}
    seeds_p = sorted({sd for (mm, d, s, sd) in paper if mm == m})
    acc_u = {(d, s) for (mm, d, s, sd) in uni if mm == m}
    seeds_u = sorted({sd for (mm, d, s, sd) in uni if mm == m})
    rows.append({
        "method": m,
        "ARI, paper pipeline (sections / seeds)": f"{len(acc_p)}/{n} / {len(seeds_p)}",
        "standardised runner + metric panel + resources (sections / seeds)": f"{len(acc_u)}/{n} / {len(seeds_u)}",
        "lottery (20 starts)": "n/a (no embedding)" if m in NO_EMB else f"{len({k for k in lot if k[0] == m})}/{n}",
        "R mclust perturbation": "n/a (no embedding)" if m in NO_EMB else f"{len({k for k in mc if k[0] == m})}/{n}",
        "invariance tests (sections)": f"{len({k.rsplit('/', 1)[0] for k in invm if k.endswith('/' + m)})}/{n}",
    })
df = pd.DataFrame(rows); df.to_csv(R("coverage_matrix.csv"), index=False)
open(R("coverage_matrix.md"), "w").write(df.to_markdown(index=False) + "\n")
print(df.to_markdown(index=False))
