"""BayesSpace version check: 1.12.0 (installed here, used for Stereo-seq) vs 1.5.1 (the paper's Visium runs) on DLPFC 151673, seed 0, paper settings (run_r_method.R, platform Visium, gamma = Visium default 3).
Writes results/review_bayesspace_version_check.json."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
old = [json.loads(l) for l in open(os.path.join(ROOT, "results", "benchmark_runs.jsonl"))]
old = [r for r in old if r["id"] == "dlpfc__151673__bayesspace__s0" and r["status"] == "ok"][-1]
new = {}
for l in open(os.path.join(ROOT, "results", "review_runs_deepmed2.jsonl")):
    r = json.loads(l)
    if r["id"] == "dlpfc__151673__bayesspace__s0": new = r
out = {"section": "dlpfc 151673 seed 0", "paper_run": {"version": "1.5.1", "ARI": old["metrics"]["ARI"], "wall_s": old["resources"]["wall_s"]}}
if new.get("status") == "ok":
    out["this_host"] = {"version": new.get("method_version"), "ARI": new["metrics"]["ARI"], "wall_s": new["resources"]["wall_s"], "host": new.get("host")}
    out["ARI_difference_new_minus_old"] = new["metrics"]["ARI"] - old["metrics"]["ARI"]
else:
    out["this_host"] = {"status": new.get("status", "no record"), "error": str(new.get("error", ""))[:400]}
json.dump(out, open(os.path.join(ROOT, "results", "review_bayesspace_version_check.json"), "w"), indent=1); print(json.dumps(out, indent=1))
