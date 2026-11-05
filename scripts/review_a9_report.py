"""A9 report (docs/PREREGISTERED_A9.md): per section and seed the ARI of the rules F, P, L next to the existing label-free value (final epoch, original records) and the existing
label-selected-epoch value; mean over sections and the paired difference to F with a section-level bootstrap (10,000 draws, seed 0; draws saved).
Writes results/review_a9_table.csv, results/review_a9_summary.json, results/review_a9_summary.md, results/review_a9_draws.npz."""
import json, os
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
old = {}
for l in open(os.path.join(ROOT, "results", "benchmark_runs.jsonl")):
    r = json.loads(l)
    if r["method"] == "spatial_mgcn" and r["status"] == "ok": old[(r["dataset"], r["section"], r["seed"])] = r
rows = []
f = os.path.join(ROOT, "results", "review_runs_deepmed2.jsonl"); new = {}
if os.path.exists(f):
    for l in open(f):
        r = json.loads(l)
        if r["method"] == "spatial_mgcn_a9": new[r["id"]] = r
for r in new.values():
    k = (r["dataset"], r["section"], r["seed"]); o = old.get(k)
    row = dict(dataset=r["dataset"], section=r["section"], seed=r["seed"], status=r["status"], outcome=r.get("outcome"))
    if r["status"] == "ok":
        e = r["extra"]; row.update(ARI_F=e["ARI_rule_F"], ARI_P=e["ARI_rule_P"], ARI_L=e["ARI_rule_L"], plateau_epoch=e["plateau_epoch"])
    if o:
        row.update(ARI_existing_final=o["metrics"]["ARI"], ARI_existing_label_selected=o.get("extra", {}).get("ARI_label_selected_epoch"))
    rows.append(row)
df = pd.DataFrame(rows); df.to_csv(os.path.join(ROOT, "results", "review_a9_table.csv"), index=False)
out = {"n_records": len(df), "n_ok": int((df.status == "ok").sum()) if len(df) else 0}
if out["n_ok"]:
    d = df[df.status == "ok"]; sec = d.groupby(["dataset", "section"])[["ARI_F", "ARI_P", "ARI_L", "ARI_existing_final", "ARI_existing_label_selected"]].mean()
    out["mean_over_sections"] = sec.mean().round(4).to_dict(); out["n_sections"] = len(sec)
    rng = np.random.default_rng(0); idx = rng.integers(0, len(sec), (10000, len(sec))); draws = {}
    for r_ in ("P", "L"):
        diff = (sec[f"ARI_{r_}"] - sec["ARI_F"]).to_numpy(); draws[r_] = diff[idx].mean(1)
        out[f"diff_{r_}_minus_F"] = {"mean": float(diff.mean()), "ci95": [float(np.percentile(draws[r_], 2.5)), float(np.percentile(draws[r_], 97.5))]}
    if sec["ARI_existing_final"].notna().any():
        dd = (sec["ARI_F"] - sec["ARI_existing_final"]).dropna(); out["reproducibility_F_minus_existing_final"] = {"mean": float(dd.mean()), "max_abs": float(dd.abs().max())}
    np.savez(os.path.join(ROOT, "results", "review_a9_draws.npz"), **draws)
json.dump(out, open(os.path.join(ROOT, "results", "review_a9_summary.json"), "w"), indent=1)
open(os.path.join(ROOT, "results", "review_a9_summary.md"), "w").write("# A9 summary (auto-generated)\n\n```\n" + json.dumps(out, indent=1) + "\n```\nRules and pre-registration: docs/PREREGISTERED_A9.md\n")
print(json.dumps(out, indent=1))
