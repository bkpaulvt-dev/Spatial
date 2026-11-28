"""Revision V3 item 4a: every job record that did not finish OK, with host, threads, memory cap, peak memory, failure reason and number of
attempts (all records of the job id, newest last). Sources: the record files of the second server (newdata, review, crossed-seed, cavity) and
the benchmark records (first machine and big-memory reruns). Writes results/v3_failures.csv and results/supp/v3_failures_summary.tex."""
import json, os
import pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); R = lambda f: os.path.join(ROOT, "results", f)
FILES = ["benchmark_runs.jsonl", "benchmark_runs_bigmem.jsonl", "newdata_runs_deepmed2.jsonl", "review_runs_deepmed2.jsonl", "review_runs_d3d4_deepmed2.jsonl",
         "cs_runs_deepmed2.jsonl", "cavity_runs_deepmed2.jsonl"]
rows = []
for f in FILES:
    if not os.path.exists(R(f)):
        continue
    hist = {}
    for l in open(R(f)):
        try:
            r = json.loads(l)
        except Exception:
            continue
        hist.setdefault(r["id"], []).append(r)
    for jid, recs in hist.items():
        last = recs[-1]
        if last.get("status") == "ok":
            continue
        res = last.get("resources") or {}
        rows.append(dict(file=f, id=jid, method=last.get("method"), dataset=last.get("dataset"), section=last.get("section"), seed=last.get("seed"),
                         host=last.get("host", "benchmark machine"), threads=res.get("threads"), memory_cap_gb=30 if "deepmed2" in f else None,
                         peak_rss_gb=round(float(res.get("peak_rss_gb") or 0), 2), outcome=last.get("outcome") or ("memory limit" if res.get("oom_killed") else "error"),
                         infra_kill=bool(last.get("infra_kill")), attempts=len(recs), reason=str(last.get("error", ""))[:200].replace("\n", " ")))
df = pd.DataFrame(rows); df.to_csv(R("v3_failures.csv"), index=False)
s = df.groupby(["file", "outcome"]).size().unstack(fill_value=0)
with open(R("supp/v3_failures_summary.tex"), "w") as fh:
    fh.write("\\begin{tabular}{l" + "r" * len(s.columns) + "}\\toprule\nRecord file & " + " & ".join(s.columns) + " \\\\\\midrule\n")
    for f, row in s.iterrows():
        fh.write(f.replace("_", "\\_") + " & " + " & ".join(str(int(x)) for x in row) + " \\\\\n")
    fh.write("\\bottomrule\\end{tabular}\n")
print(s); print(len(df), "jobs not ok; csv: results/v3_failures.csv")
