"""M6 fidelity checks: official code versus our re-implementation, per section (mean ARI over seeds, matched and default clustering) -> results/review_m6_fidelity.{json,csv}.
(i) HiSTaR official (review_runs_*.jsonl method histar_official) vs port (benchmark_runs.jsonl method histar); (ii) CCST original (method ccst_original) vs ours (method ccst)."""
import glob, json, os, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def last(files):
    d = {}
    for f in files:
        for l in open(f):
            r = json.loads(l); d[r["id"]] = r
    return d


def ari(r, key="metrics"):
    return (r.get(key) or {}).get("ARI")


def main():
    rev = last(glob.glob(os.path.join(ROOT, "results", "review_runs_*.jsonl"))); orig = last([os.path.join(ROOT, "results", "benchmark_runs.jsonl")])
    rows = []
    for off, ours, label in (("histar_official", "histar", "HiSTaR"), ("ccst_original", "ccst", "CCST")):
        secs = sorted({(r["dataset"], r["section"]) for r in rev.values() if r["method"] == off})
        for ds, sec in secs:
            o = [r for r in rev.values() if r["method"] == off and r["dataset"] == ds and r["section"] == sec]
            p = [r for r in orig.values() if r["method"] == ours and r["dataset"] == ds and r["section"] == sec and r["status"] == "ok"]
            row = {"pair": label, "dataset": ds, "section": sec, "n_official": len(o), "n_ours": len(p)}
            for tag, rs in (("official", o), ("ours", p)):
                for key, nm in (("metrics", "default"), ("metrics_matched", "matched")):
                    v = [ari(r, key) for r in rs if r["status"] == "ok" and ari(r, key) is not None]
                    row[f"{tag}_{nm}_ari"] = st.mean(v) if v else None
            for nm in ("default", "matched"):
                a, b = row[f"official_{nm}_ari"], row[f"ours_{nm}_ari"]
                row[f"diff_{nm}"] = None if a is None or b is None else a - b
            rows.append(row)
    json.dump(rows, open(os.path.join(ROOT, "results", "review_m6_fidelity.json"), "w"), indent=1)
    if rows:
        import csv
        with open(os.path.join(ROOT, "results", "review_m6_fidelity.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for p in ("HiSTaR", "CCST"):
        d = [r["diff_default"] for r in rows if r["pair"] == p and r["diff_default"] is not None]
        if d: print(f"{p}: official minus ours (default clustering), {len(d)} sections: mean {st.mean(d):+.3f}, min {min(d):+.3f}, max {max(d):+.3f}")


if __name__ == "__main__":
    main()
