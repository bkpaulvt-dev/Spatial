"""R5 analysis (docs/PREREGISTERED_TUNING.md, analyses P1-P3 and S1). Committed before any tuned-arm result.

Unit: per section, the mean ARI over seeds 0-2 (method's own clustering, metrics.ARI). Clusters as in scripts/stats_cluster_aware.py:
DLPFC donors, and one cluster each for STARmap, MERFISH, breast cancer and Stereo-seq. Hierarchical bootstrap (clusters, then sections within a
cluster; estimate = equal-weight mean of cluster means), 5000 draws, rng seed 0.
P1 (primary): on the 18 TEST sections, delta_B = ARI(r5 linear diffusion tuned) - ARI(r5 method tuned), 95% interval.
P2: tuning gain per method on the TEST sections = ARI(tuned) - ARI(Arm A record of the same method, results/review_runs + benchmark records).
P3: ranking of the 5 tuned methods (mean over test clusters) next to the Arm A ranking of the same 5 methods.
S1 (secondary): P1 on all 24 sections (dev sections are in-sample for the tuned arm; reported as such).
python scripts/r5_analysis.py -> results/r5_analysis.json (+ table)"""
import json, os, socket, sys
import numpy as np, yaml
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path.insert(0, HERE)
from r5_tuning import GRIDS, ARM_A  # noqa: E402
HOST = socket.gethostname().split(".")[0].lower()
B = 5000; rng = np.random.default_rng(0)

reg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"]
SEC = [(ds, str(s), (m.get("donor") if ds == "dlpfc" else ds), m["split"]) for ds, c in reg.items() for s, m in c["sections"].items()]


def newest(path, keep):
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


rv = newest(os.path.join(ROOT, "results", f"review_runs_{HOST}.jsonl"), lambda r: r.get("method", "").startswith("r5__") and r["method"].endswith("__tuned"))
arm_a = newest(os.path.join(ROOT, "results", "benchmark_runs.jsonl"), lambda r: r.get("method") in ARM_A.values())


def per_section(recs, method):
    v = {}
    for r in recs.values():
        if r["method"] == method and r.get("status") == "ok" and r.get("seed") in (0, 1, 2):
            v.setdefault((r["dataset"], str(r["section"])), []).append(r["metrics"]["ARI"])
    return {k: float(np.mean(x)) for k, x in v.items()}


def hboot(delta, split):
    groups = {}
    for ds, s, cl, sp in SEC:
        if split == "all" or sp == split:
            if (ds, s) in delta:
                groups.setdefault(cl, []).append(delta[(ds, s)])
    g = [np.array(x) for x in groups.values()]
    if not g:
        return None
    point = float(np.mean([x.mean() for x in g])); draws = np.empty(B)
    for i in range(B):
        ci = rng.integers(0, len(g), len(g))
        draws[i] = np.mean([rng.choice(g[c], len(g[c])).mean() for c in ci])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"estimate": point, "ci95": [float(lo), float(hi)], "n_clusters": len(g), "n_sections": int(sum(len(x) for x in g)),
            "verdict": "linear diffusion better" if lo > 0 else "method better" if hi < 0 else "unresolved"}


tuned = {m: per_section(rv, f"r5__{m}__tuned") for m in GRIDS}
armA = {m: per_section(arm_a, ARM_A[m]) for m in GRIDS}
out = {"P1_test": {}, "S1_all": {}, "P2_gain_test": {}, "P3_rank": {}}
for m in GRIDS:
    if m == "linear_diffusion":
        continue
    d = {k: tuned["linear_diffusion"][k] - v for k, v in tuned[m].items() if k in tuned["linear_diffusion"]}
    out["P1_test"][m] = hboot(d, "test"); out["S1_all"][m] = hboot(d, "all")
for m in GRIDS:
    out["P2_gain_test"][m] = hboot({k: v - armA[m][k] for k, v in tuned[m].items() if k in armA[m]}, "test")


def cl_mean(vals):
    g = {}
    for ds, s, cl, sp in SEC:
        if sp == "test" and (ds, s) in vals:
            g.setdefault(cl, []).append(vals[(ds, s)])
    return float(np.mean([np.mean(x) for x in g.values()])) if g else None


out["P3_rank"] = {"tuned": sorted(((cl_mean(tuned[m]), m) for m in GRIDS if cl_mean(tuned[m]) is not None), reverse=True),
                  "arm_a": sorted(((cl_mean(armA[m]), m) for m in GRIDS if cl_mean(armA[m]) is not None), reverse=True)}
out["coverage"] = {m: {"tuned_sections": len(tuned[m]), "arm_a_sections": len(armA[m])} for m in GRIDS}
json.dump(out, open(os.path.join(ROOT, "results", "r5_analysis.json"), "w"), indent=1)
for k in ("P1_test", "S1_all", "P2_gain_test"):
    print(k)
    for m, r in out[k].items():
        print(f"  {m:17s}", "no data" if not r else f"{r['estimate']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] {r['verdict']} ({r['n_sections']} sections)")
print("P3 tuned:", out["P3_rank"]["tuned"]); print("P3 arm A:", out["P3_rank"]["arm_a"])
