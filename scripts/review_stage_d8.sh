#!/bin/bash
# D8 Allen MERFISH: the benchmark (all methods x 3 seeds), G3 (a-e) and the handoff are run by the real-data phase of the newdata pipeline (scripts/newdata_phase2.sh, its one heavy slot),
# NOT here (two copies would break the 2-job cap). This stage only checks that the three sections, the registry entry and the label provenance exist, and writes results/review_d8_status.json
# with the progress of that phase (number of Allen records so far). The review methods (M1-M6) are run on the Allen sections by their own stages (group "newreal").
set -e
source "$(dirname "$0")/review_stage_common.sh"
python - <<'PY'
import glob, json, os, yaml
reg = yaml.safe_load(open("configs/datasets_newdata.yaml"))["datasets"].get("allenmerfish")
secs = list(reg["sections"]) if reg else []
have = [s for s in secs if os.path.exists(f"data/ext/csv/allenmerfish_{s}_counts.csv")]
recs = {}
for f in glob.glob("results/newdata_runs_*.jsonl"):
    for l in open(f):
        r = json.loads(l)
        if r["dataset"] == "allenmerfish": recs[r["id"]] = r["status"]
st = {"registered": bool(reg), "sections": secs, "sections_with_data": have, "allen_records_so_far": len(recs), "ok": sum(v == "ok" for v in recs.values()),
      "note": "benchmark and G3 are run by newdata_phase2.sh in the newdata slot; see results/newdata_dataset_outcomes.txt"}
json.dump(st, open("results/review_d8_status.json", "w"), indent=1); print(st)
assert reg and len(have) == 3, "Allen MERFISH not registered or data files missing"
PY
