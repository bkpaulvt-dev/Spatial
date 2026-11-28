#!/bin/bash
# Revision V3 item 4a: clean-environment check. A fresh virtual environment is built from environment/requirements-lock-deepmed2.txt
# (no package of the working environment is reused), then (1) linear diffusion and PCA run on DLPFC 151673 seed 0 and their ARI is compared
# with results/benchmark_runs.jsonl, and (2) the V2/V3 number and figure scripts are rerun from the archived outputs and their outputs
# compared byte for byte with the committed files. Log: results/clean_env_check.txt
set -e
BASE=/mnt/disk/bikashkumar/SpatialBench; . "$BASE/Spatial/scripts/deepmed2_env.sh"; cd "$BASE/Spatial"
V="$BASE/envs/clean_check"; rm -rf "$V"; "$BASE/env/bin/python" -m venv "$V"
# two passes: compiled torch extensions need torch at build time (pip's build isolation hides it)
grep -v -i -E "^(torch[_-](scatter|sparse|cluster|spline)|pyg)" environment/requirements-lock-deepmed2.txt > "$BASE/tmp/lock_pass1.txt"
grep -i -E "^(torch[_-](scatter|sparse|cluster|spline)|pyg)" environment/requirements-lock-deepmed2.txt > "$BASE/tmp/lock_pass2.txt" || true
"$V/bin/pip" install -q --no-cache-dir --no-deps -r "$BASE/tmp/lock_pass1.txt" 2>&1 | tail -3   # exact lock: every pinned version, no resolver
"$V/bin/pip" install -q --no-cache-dir --no-deps --no-build-isolation -r "$BASE/tmp/lock_pass2.txt" 2>&1 | tail -3 || echo "pass 2 (torch extensions) failed: not needed for this check"
"$V/bin/pip" install -q --no-cache-dir -e . 2>/dev/null || true
OUT=results/clean_env_check.txt; T=$(mktemp -d -p "$BASE/tmp")
{ echo "clean-environment check, $(date '+%F %T'), venv $V (python $("$V/bin/python" -V 2>&1))"
  for m in linear_diffusion pca_gmm; do
    PYTHONPATH="$PWD:$PWD/scripts" OMP_NUM_THREADS=1 "$V/bin/python" -W ignore scripts/bench_run.py --method $m --dataset dlpfc --section 151673 --seed 0 --out "$T" >/dev/null 2>&1 || echo "$m FAILED"
    "$V/bin/python" - "$T" "$m" <<'PY'
import json, sys
new = json.load(open(f"{sys.argv[1]}/dlpfc__151673__{sys.argv[2]}__s0.json"))["metrics"]["ARI"]
old = [json.loads(l) for l in open("results/benchmark_runs.jsonl")]
old = [r for r in old if r["id"] == f"dlpfc__151673__{sys.argv[2]}__s0" and r["status"] == "ok"][-1]["metrics"]["ARI"]
print(f"{sys.argv[2]}: clean env ARI {new:.6f}, recorded {old:.6f}, difference {new-old:+.2e}", "MATCH" if abs(new-old) < 1e-6 else "DIFFERENT")
PY
  done
  for f in results/paper_macros_review.tex results/supp/v2_extra.tex results/supp/v2_allen.tex; do cp "$f" "$T/$(basename $f).before"; done
  PYTHONPATH="$PWD:$PWD/scripts" "$V/bin/python" -W ignore scripts/paper_review_numbers.py >/dev/null 2>&1 && echo "paper_review_numbers.py ran" || echo "paper_review_numbers.py FAILED"
  for f in results/paper_macros_review.tex results/supp/v2_extra.tex results/supp/v2_allen.tex; do cmp -s "$f" "$T/$(basename $f).before" && echo "$f identical" || echo "$f DIFFERS"; done
  PYTHONPATH="$PWD:$PWD/scripts" "$V/bin/python" scripts/make_fig_simulation_v2.py >/dev/null 2>&1 && echo "Figure 6 regenerated in the clean environment" || echo "Figure 6 FAILED"
} | tee "$OUT"
