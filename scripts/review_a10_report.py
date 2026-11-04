"""A10 cross-host check: ARI of the same seed on this host (deepmed2) and on the original benchmark machine; writes results/review_a10_cross_host.json."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ARI = lambda r: r["metrics"]["ARI"]
orig, here_old, new = {}, {}, {}
for r in map(json.loads, open(os.path.join(ROOT, "results", "benchmark_runs.jsonl"))):
    if r["status"] == "ok" and r["dataset"] == "stereo" and r["section"] == "E10.5_E2S1":
        (here_old if r.get("host") == "deepmed2" else orig)[r["id"]] = r
for r in map(json.loads, open(os.path.join(ROOT, "results", "review_runs_deepmed2.jsonl"))):
    if r["status"] == "ok": new[r["id"]] = r
out = {"section": "stereo E10.5_E2S1", "rows": []}
for m in ("deepst", "linear_diffusion"):
    i0 = f"stereo__E10.5_E2S1__{m}__s0"
    row = {"method": m, "seed0_original_machine": ARI(orig[i0]) if i0 in orig else None, "seed0_this_host": ARI(new[i0]) if i0 in new else None}
    if row["seed0_original_machine"] is not None and row["seed0_this_host"] is not None: row["same_seed_difference_host_minus_original"] = row["seed0_this_host"] - row["seed0_original_machine"]
    row["seeds_1_2_this_host_earlier_rerun"] = {k.split("__")[-1]: ARI(v) for k, v in here_old.items() if f"__{m}__" in k}
    row["seeds_1_2_original_machine"] = {k.split("__")[-1]: ARI(v) for k, v in orig.items() if f"__{m}__" in k and not k.endswith("s0")}
    out["rows"].append(row)
json.dump(out, open(os.path.join(ROOT, "results", "review_a10_cross_host.json"), "w"), indent=1); print(json.dumps(out, indent=1))
