"""Cluster-aware re-analysis of the accuracy comparison (replaces the pooled Wilcoxon over 20 sections).

Unit of analysis: sections are nested in clusters = DLPFC donors (3) and the STARmap, MERFISH, BRCA and Stereo-seq
datasets (one cluster each, since their sections come from one animal/experiment/study). Hierarchical bootstrap: resample clusters, then sections within
a cluster; the estimate is the equal-weight mean of cluster means. Reference method: linear diffusion (declared exploratory:
it was picked after seeing the means). Equivalence margin: ARI 0.03, fixed before looking (about the seed SD).
Also: rank uncertainty (P(best), 95% rank interval) and a sensitivity analysis that excludes the development sections.

python scripts/stats_cluster_aware.py -> results/stats_cluster_aware.json (+ prints a table)
"""
import json, os, sys, warnings
import numpy as np, pandas as pd, yaml

warnings.filterwarnings("ignore")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda f: os.path.join(ROOT, "results", f)
B, MARGIN = 5000, 0.03
rng = np.random.default_rng(0)

rd = lambda f: pd.read_json(R(f), lines=True) if os.path.exists(R(f)) else pd.DataFrame()
a = rd("anisost_main.jsonl").assign(dataset="dlpfc"); b = rd("baselines.jsonl").assign(dataset="dlpfc")
e = rd("extra.jsonl"); g = rd("graphst.jsonl"); b3 = rd("baselines_3start.jsonl")
nm = rd("new_methods.jsonl"); nm["slice"] = nm["slice"].astype(str)
nm = nm[nm.status == "ok"].drop_duplicates(["method", "dataset", "slice", "seed"], keep="last")
nm_std = nm[["dataset", "method", "slice", "seed", "ARI"]]
nm_rob = nm[["dataset", "method", "slice", "seed", "ARI_robust"]].rename(columns={"ARI_robust": "ARI"}) \
    .assign(method=lambda x: x.method + "+robust").dropna(subset=["ARI"])
# Datasets added later (Visium breast cancer, Stereo-seq) were run only through the standardised runner
# (scripts/bench_run.py), which records each method's own clustering ("metrics") and the matched clustering
# ("metrics_matched"). Named here with the same keys as the pipeline results (see STD / ROB below).
RUNNER_ONLY = ("brca", "stereo")
# sensitivity analysis (STATS_SOURCE=runner): every dataset from the standardised runner (one execution environment)
SOURCE = os.environ.get("STATS_SOURCE", "pipeline")
if SOURCE == "runner":
    RUNNER_ONLY = tuple(yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"])
OWN_KEY = {"anisost": "anisost_single_gmm"}
NO_EMB = ("spagcn", "bass", "bayesspace")
ru = []
for r in ({x["id"]: x for x in rd("benchmark_runs.jsonl").to_dict("records")}.values() if os.path.exists(R("benchmark_runs.jsonl")) else []):   # newest record per run
    if r.get("status") != "ok" or r["dataset"] not in RUNNER_ONLY: continue
    base = dict(dataset=r["dataset"], slice=str(r["section"]), seed=r["seed"])
    if r["method"] not in ("linear_diffusion", "pca_gmm", "anisost"):   # own (3-start) fits of the baselines: baselines_3start.jsonl   # own clustering of these two: baselines_3start.jsonl
        ru.append(dict(base, method=OWN_KEY.get(r["method"], r["method"]), ARI=r["metrics"]["ARI"]))
    if r["method"] not in NO_EMB and isinstance(r.get("metrics_matched"), dict):
        m = r["method"] if r["method"] in ("linear_diffusion", "pca_gmm", "anisost") else r["method"] + "+robust"
        ru.append(dict(base, method=m, ARI=r["metrics_matched"]["ARI"]))
ru = pd.DataFrame(ru)
if SOURCE == "runner":
    d = pd.concat([b3, ru], ignore_index=True)
else:
    d = pd.concat([a, b, e, g, b3, nm_std, nm_rob, ru], ignore_index=True)
d["slice"] = d["slice"].astype(str)
d.loc[d.method == "histar_rerun", "method"] = "histar"
P = d.groupby(["dataset", "method", "slice"]).ARI.mean()

cfg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"]
rows = []
for ds, v in cfg.items():
    for s, m in v["sections"].items():
        rows.append(dict(dataset=ds, slice=str(s), cluster=(m.get("donor") if ds == "dlpfc" else ds), split=m["split"]))
SEC = pd.DataFrame(rows)

REF = "linear_diffusion"
LABEL = {"histar": "HiSTaR", "graphst": "GraphST", "banksy_l0.8": "BANKSY λ=0.8", "banksy_l0.2": "BANKSY λ=0.2", "spagcn": "SpaGCN",
         "stagate": "STAGATE", "sedr": "SEDR", "spaceflow": "SpaceFlow", "nichepca": "NichePCA", "ccst": "CCST",
         "spatial_mgcn": "Spatial-MGCN", "deepst": "DeepST", "bass": "BASS", "anisost": "AnisoST", "pca_gmm": "PCA", "bayesspace": "BayesSpace"}
# "standard" = each method's own clustering (training-free baselines: the same 3-start GMM as AnisoST, HiSTaR, BANKSY);
# "robust" = matched clustering: every embedding clustered with the same 20-start best-likelihood GMM. Methods that
# cluster internally (SpaGCN, BASS, BayesSpace) have no embedding and keep their own clustering under both protocols.
STD = {m: m for m in LABEL}; STD["anisost"] = "anisost_single_gmm"; STD["pca_gmm"] = "pca_gmm_single_gmm"
STD[REF] = "linear_diffusion_single_gmm"
ROB = {m: m + "+robust" for m in LABEL}; ROB["anisost"] = "anisost"; ROB["pca_gmm"] = "pca_gmm"; ROB[REF] = REF
for m in ("spagcn", "bass", "bayesspace"): ROB[m] = m

def series(key):
    out = {}
    for ds, s in zip(SEC.dataset, SEC.slice):
        if (ds, key, s) in P.index: out[(ds, s)] = float(P.loc[(ds, key, s)])
    return out

def hboot(delta, sec, nboot=B):
    """delta: dict (dataset, slice) -> value; returns bootstrap draws of the equal-weight mean of cluster means."""
    df = sec.assign(v=[delta.get((ds, s), np.nan) for ds, s in zip(sec.dataset, sec.slice)]).dropna(subset=["v"])
    groups = [grp.v.values for _, grp in df.groupby("cluster")]
    if not groups: return np.array([np.nan]), np.nan
    point = float(np.mean([g_.mean() for g_ in groups]))
    draws = np.empty(nboot)
    for i in range(nboot):
        ci = rng.integers(0, len(groups), len(groups))
        draws[i] = np.mean([rng.choice(groups[c], len(groups[c])).mean() for c in ci])
    return draws, point

def classify(draws):
    lo95, hi95 = np.percentile(draws, [2.5, 97.5]); lo90, hi90 = np.percentile(draws, [5, 95])
    if -MARGIN <= lo90 and hi90 <= MARGIN: return "equivalent"
    if lo95 > 0: return "baseline_better"
    if hi95 < 0: return "baseline_worse"
    return "unresolved"

test_sec = SEC[SEC.split == "test"]
out = {"reference": REF, "margin": MARGIN, "n_boot": B, "clusters": sorted(SEC.cluster.unique()), "comparisons": {}}
for proto, MAP in (("standard", STD), ("robust", ROB)):
    ref = series(MAP[REF])
    for m, lab in LABEL.items():
        if m not in MAP or m == REF: continue
        s = series(MAP[m])
        if not s: continue
        delta = {k: ref[k] - s[k] for k in s if k in ref}
        draws, point = hboot(delta, SEC)
        dt, pt = hboot(delta, test_sec)
        per = {}
        for ds in cfg:   # every registered dataset (brca and stereo: one cluster each)
            vals = [v for (d_, _), v in delta.items() if d_ == ds]
            if vals: per[ds] = round(float(np.mean(vals)), 3)
        out["comparisons"][f"{proto}/{m}"] = {
            "method": lab, "protocol": proto, "n_sections": len(delta), "delta": round(point, 3),
            "ci95": [round(float(x), 3) for x in np.percentile(draws, [2.5, 97.5])],
            "ci90": [round(float(x), 3) for x in np.percentile(draws, [5, 95])],
            # Bonferroni over the 16 comparisons of a protocol: two-sided 1 - 0.05/16 interval
            "ci_bonf": [round(float(x), 3) for x in np.percentile(draws, [100 * 0.025 / 16, 100 - 100 * 0.025 / 16])],
            "category": classify(draws), "per_dataset": per,
            "test_only": {"delta": round(pt, 3), "ci95": [round(float(x), 3) for x in np.percentile(dt, [2.5, 97.5])]}}

# rank uncertainty (methods with all 20 sections), for both protocols
cand = [m for m in LABEL if m != "bayesspace"]
def ranking(MAP, shared=True):
  """shared=True: every method (BayesSpace aside) on the sections all of them completed (methods stopped at the memory
  cap on one section stay in); shared=False: only methods with a result on every section, all sections."""
  cand_keys = {m: MAP[m] for m in cand + [REF]}
  allser = {m: series(k) for m, k in cand_keys.items()}
  if shared:
      common = set.intersection(*[set(v) for v in allser.values() if v])
      full = {m: v for m, v in allser.items() if v}
      sec = SEC[[(d_, s_) in common for d_, s_ in zip(SEC.dataset, SEC.slice)]]
  else:
      full = {m: v for m, v in allser.items() if len(v) == len(SEC)}
      sec = SEC
  names = list(full)
  groups = {c: sec[sec.cluster == c] for c in sec.cluster.unique()}
  ranks = np.empty((B, len(names)), dtype=int)
  for i in range(B):
      cl = rng.choice(list(groups), len(groups))
      score = np.zeros(len(names))
      for c in cl:
          idx = rng.integers(0, len(groups[c]), len(groups[c]))
          sel = groups[c].iloc[idx]
          score += np.array([np.mean([full[m][(ds, s)] for ds, s in zip(sel.dataset, sel.slice)]) for m in names])
      ranks[i] = (-score).argsort().argsort() + 1
  return {LABEL.get(m, "Linear diffusion"): {"p_best": round(float((ranks[:, j] == 1).mean()), 3),
                                              "median_rank": float(np.median(ranks[:, j])),
                                              "rank95": [int(x) for x in np.percentile(ranks[:, j], [2.5, 97.5])]}
          for j, m in enumerate(names)}, len(names), int(len(sec))
out["ranking"], out["ranking_methods"], out["ranking_sections"] = ranking(ROB)          # primary: matched clustering
out["ranking_own"], _, _ = ranking(STD)
out["ranking_complete"], out["ranking_complete_methods"], _ = ranking(ROB, shared=False)   # methods with every section
# per-method per-dataset means (both protocols) for the figures
def dmeans(key):
    r_ = {}
    for ds in cfg:   # every registered dataset (brca and stereo: one cluster each)
        v = [x for (d_, _), x in series(key).items() if d_ == ds]
        if v: r_[ds] = round(float(np.mean(v)), 4)
    return r_
out["means_standard"] = {m: dmeans(STD[m]) for m in list(LABEL) + [REF]}
out["means_robust"] = {m: dmeans(ROB[m]) for m in list(LABEL) + [REF]}
json.dump(out, open(R("stats_cluster_aware.json" if SOURCE == "pipeline" else "stats_cluster_aware_runner.json"), "w"), indent=1)

print(f"reference: linear diffusion; clusters: {out['clusters']}; margin {MARGIN}")
for proto in ("standard", "robust"):
    print(f"\n--- {proto} clustering: delta = linear diffusion minus method (95% hierarchical-bootstrap CI)")
    for k, v in out["comparisons"].items():
        if v["protocol"] != proto: continue
        print(f"{v['method']:<14} n={v['n_sections']:<3} d={v['delta']:+.3f} [{v['ci95'][0]:+.3f},{v['ci95'][1]:+.3f}]  {v['category']:<16}"
              f" per-dataset {v['per_dataset']}  test-only d={v['test_only']['delta']:+.3f}")
print(f"\n--- rank uncertainty (matched clustering, {out['ranking_sections']} sections completed by every method)")
for lab, v in sorted(out["ranking"].items(), key=lambda kv: kv[1]["median_rank"]):
    print(f"{lab:<16} P(best)={v['p_best']:.2f} median rank {v['median_rank']:.0f}  95% interval {v['rank95']}")
