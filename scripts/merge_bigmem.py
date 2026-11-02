"""Merge the rerun of the memory-capped jobs (made on DeepMed2, see docs/BIGMEM_RERUN.md) into results/benchmark_runs.jsonl.

Each record gets host = "deepmed2": different CPU and 125 GB RAM instead of the 15 GB benchmark machine, so its run time is
not comparable (the timing tables skip records with a host tag) while accuracy and peak memory are. Records are appended once;
analyses use the newest record of each run id (so the earlier out-of-memory records are replaced).

python scripts/merge_bigmem.py [results/benchmark_runs_bigmem.jsonl]
"""
import json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "benchmark_runs_bigmem.jsonl")
dst = os.path.join(ROOT, "results", "benchmark_runs.jsonl")
have = {json.dumps({k: v for k, v in r.items()}, sort_keys=True) for r in map(json.loads, open(dst))}
n = 0
with open(dst, "a") as f:
    for line in open(src):
        r = json.loads(line); r["host"] = "deepmed2"
        key = json.dumps(r, sort_keys=True)
        if key in have: continue
        f.write(json.dumps(r) + "\n"); have.add(key); n += 1
print(n, "records appended to", dst)
