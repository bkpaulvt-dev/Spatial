"""R5 selection (docs/PREREGISTERED_TUNING.md, rule S): from the tuning-phase records (seed 0, six development sections), choose per method the
configuration with the highest score = mean over the 3 development datasets (DLPFC, STARmap, MERFISH) of the per-dataset mean ARI (method's own
clustering, field metrics.ARI). A configuration that is missing or failed on any development section is not eligible. Ties (difference < 1e-9)
go to the lower configuration index (configuration 0 = Arm A). Writes results/r5_selected.json and prints the full score table.
python scripts/r5_select.py [--records results/review_runs_<host>.jsonl]"""
import argparse, json, os, socket, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from r5_tuning import GRIDS, DEV, SELECTED, ARM_A  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--records", default=os.path.join(HERE, "..", "results", f"review_runs_{socket.gethostname().split('.')[0].lower()}.jsonl"))
ap.add_argument("--out", default=SELECTED); a = ap.parse_args()
rec = {}
for l in open(a.records):
    try:
        r = json.loads(l)
    except Exception:
        continue
    if r.get("method", "").startswith("r5__") and r.get("seed") == 0:
        rec[r["id"]] = r
out = {"rule": "max over configurations of mean over dev datasets of per-dataset mean ARI (seed 0); ties -> lower index; incomplete configurations ineligible",
       "dev_sections": DEV, "selected": {}, "scores": {}}
for m, g in GRIDS.items():
    sc = {}
    for j in range(len(g)):
        per = {}
        ok = True
        for ds, sec in DEV:
            r = rec.get(f"{ds}__{sec}__r5__{m}__c{j}__s0")
            if not r or r.get("status") != "ok" or not np.isfinite(r["metrics"]["ARI"]):
                ok = False; break
            per.setdefault(ds, []).append(r["metrics"]["ARI"])
        sc[j] = float(np.mean([np.mean(v) for v in per.values()])) if ok else None
    out["scores"][m] = {str(j): v for j, v in sc.items()}
    elig = [(v, j) for j, v in sc.items() if v is not None]
    if not elig:
        out["selected"][m] = None; print(m, "NO ELIGIBLE CONFIGURATION"); continue
    best = max(v for v, _ in elig); j = min(j for v, j in elig if best - v < 1e-9)
    out["selected"][m] = {"config": j, "settings": g[j], "score": best, "arm_a_score": sc[0], "arm_a_method": ARM_A[m]}
    print(f"{m:17s} selected c{j} {g[j]} score {best:.4f} (Arm A c0: {sc[0] if sc[0] is None else round(sc[0], 4)})  all: " +
          " ".join(f"c{k}={'NA' if v is None else f'{v:.3f}'}" for k, v in sc.items()))
json.dump(out, open(a.out, "w"), indent=1)
print("written", a.out)
