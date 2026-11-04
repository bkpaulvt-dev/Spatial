"""Explicit-job queue for the review runs (docs/DEEPMED2_NEXT.md). Reuses the standardised runner of bench_queue.py (run() -> bench_run.py under resource
measurement) without touching it; jobs are given on the command line, so no registry file is involved and the original registry is never changed.
Records go to NEW files: results/review_runs_<host>.jsonl (newest per id wins; host, device, outcome and design tags), per-job files in results/review_runs/.

  python scripts/review_queue.py --job stereo:E10.5_E2S1:deepst:0 --job stereo:E10.5_E2S1:linear_diffusion:0 [--workers 1] [--dry-run]
  python scripts/review_queue.py --jobs-file jobs.txt        (one dataset:section:method:seed per line)
Out-of-memory and timeout records are final (never retried); other errors are retried up to --max-attempts with unchanged settings. 24 h and the memory cap
(SPATIALBENCH_MAX_RSS_GB, set by the runner) apply to every job.
"""
import argparse, json, os, socket, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [ROOT, HERE]
import review_methods  # noqa: E402
import bench_queue as bq  # noqa: E402
from adapters import SERIAL  # noqa: E402
from bench_run import job_id  # noqa: E402

HOST = socket.gethostname().lower()


def run(job, timeout, threads):
    """Same as bench_queue.run (same record, same resource measurement) but runs scripts/review_bench_run.py, which also knows the methods of review_methods.py."""
    ds, sec, m, seed = job
    jid = job_id(ds, sec, m, seed); runs = bq.RUNS
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads), OPENBLAS_NUM_THREADS=str(threads))
    cmd = [sys.executable, os.path.join(HERE, "review_bench_run.py"), "--method", m, "--dataset", ds, "--section", sec, "--seed", str(seed), "--out", runs] + (["--save-emb"] if seed == 0 else [])
    res = bq.measure_command(cmd, timeout=timeout, env=env)
    path = os.path.join(runs, jid + ".json")
    rec = json.load(open(path)) if os.path.exists(path) else {"id": jid, "method": m, "dataset": ds, "section": sec, "seed": seed, "status": "error", "error": "no result file"}
    if res["exit_code"] != 0 or res["timed_out"]:
        rec["status"] = "error"
        rec["error"] = ("timeout" if res["timed_out"] else "killed (out of memory)" if res["oom_killed"] else f"exit code {res['exit_code']}") + " | " + res["stderr"][-300:]
    rec["resources"] = {k: res[k] for k in ("wall_s", "cpu_s", "peak_rss_gb", "peak_gpu_mem_gb", "energy_kwh", "energy_source", "exit_code", "oom_killed", "timed_out")}
    rec["resources"]["threads"] = threads
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", action="append", default=[], help="dataset:section:method:seed (repeatable)"); ap.add_argument("--jobs-file")
    ap.add_argument("--workers", type=int, default=2); ap.add_argument("--timeout", type=int, default=24 * 3600); ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--device", default=os.environ.get("SPATIALBENCH_DEVICE", "cpu")); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", f"review_runs_{HOST}.jsonl")); ap.add_argument("--runs-dir", default=os.path.join(ROOT, "results", "review_runs"))
    a = ap.parse_args()
    specs = list(a.job) + ([l.strip() for l in open(a.jobs_file) if l.strip() and not l.startswith("#")] if a.jobs_file else [])
    jobs = []
    for s in specs:
        ds, sec, m, sd = s.split(":"); jobs.append((ds, sec, m, int(sd)))
    done, attempts = set(), {}
    if os.path.exists(a.out):
        for r in map(json.loads, open(a.out)):
            res = r.get("resources") or {}; attempts[r["id"]] = attempts.get(r["id"], 0) + 1
            if r["status"] == "ok" or res.get("oom_killed") or res.get("timed_out") or attempts[r["id"]] >= a.max_attempts: done.add(r["id"])
            else: done.discard(r["id"])
    todo = [j for j in jobs if job_id(*j[:3], j[3]) not in done]
    print(f"{len(todo)} of {len(jobs)} jobs to run ({len(jobs) - len(todo)} already recorded)", flush=True)
    if a.dry_run or not todo:
        return
    os.makedirs(a.runs_dir, exist_ok=True); bq.RUNS = a.runs_dir
    for batch, w in (([j for j in todo if j[2] not in SERIAL], a.workers), ([j for j in todo if j[2] in SERIAL], 1)):
        with ThreadPoolExecutor(w) as ex:
            for fut in as_completed([ex.submit(run, j, a.timeout, 1) for j in batch]):
                r = fut.result(); res = r.get("resources") or {}
                r.update(host=HOST, extension="review", device=a.device, method_version=review_methods.version_of(r["method"]),
                         outcome="ok" if r["status"] == "ok" else "time limit" if (res.get("timed_out") or "time limit (24 h)" in str(r.get("error", ""))) else "memory limit" if res.get("oom_killed") else "error")
                open(a.out, "a").write(json.dumps(r) + "\n")
                met = r.get("metrics", {})
                print(f"{r['id']:<52} {r['outcome']:<12} ARI={met.get('ARI', float('nan')):.3f} t={res.get('wall_s', 0):.0f}s mem={res.get('peak_rss_gb', 0):.1f}GB", flush=True)
    print("REVIEW_QUEUE_DONE", flush=True)


if __name__ == "__main__":
    main()
