"""Resumable benchmark queue with resource measurement.

Runs bench_run.py for every (dataset, section, method, seed) under spatialbench.resources.measure_command,
so each record also carries wall time, CPU seconds, peak memory of the whole process tree, energy and
out-of-memory / timeout flags. Finished jobs (status ok) are skipped on restart; failures are kept
as results and only retried with --retry-errors.

python scripts/bench_queue.py --methods linear_diffusion nichepca --datasets starmap --seeds 0 1 2 --workers 2
python scripts/bench_queue.py --dry-run          # list the jobs
"""
import argparse, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from spatialbench.data import load_registry, sections  # noqa: E402
from spatialbench.resources import measure_command  # noqa: E402
from adapters import ADAPTERS, SERIAL, VISIUM_ONLY  # noqa: E402
from bench_run import job_id  # noqa: E402

OUT = os.path.join(ROOT, "results", "benchmark_runs.jsonl")
RUNS = os.path.join(ROOT, "results", "runs")


def run(job, timeout, threads):
    ds, sec, m, seed = job
    jid = job_id(ds, sec, m, seed)
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads), OPENBLAS_NUM_THREADS=str(threads))
    cmd = [sys.executable, os.path.join(HERE, "bench_run.py"), "--method", m, "--dataset", ds, "--section", sec,
           "--seed", str(seed), "--out", RUNS] + (["--save-emb"] if seed == 0 else [])
    res = measure_command(cmd, timeout=timeout, env=env)
    path = os.path.join(RUNS, jid + ".json")
    rec = json.load(open(path)) if os.path.exists(path) else {"id": jid, "method": m, "dataset": ds, "section": sec, "seed": seed,
                                                             "status": "error", "error": "no result file"}
    if res["exit_code"] != 0 or res["timed_out"]:
        rec["status"] = "error"
        rec["error"] = ("timeout" if res["timed_out"] else "killed (out of memory)" if res["oom_killed"]
                        else f"exit code {res['exit_code']}") + " | " + res["stderr"][-300:]
    rec["resources"] = {k: res[k] for k in ("wall_s", "cpu_s", "peak_rss_gb", "peak_gpu_mem_gb", "energy_kwh", "energy_source",
                                            "exit_code", "oom_killed", "timed_out")}
    rec["resources"]["threads"] = threads
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="+", default=sorted(ADAPTERS)); ap.add_argument("--datasets", nargs="+")
    ap.add_argument("--sections", nargs="+"); ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--splits", nargs="+", default=["dev", "test"]); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--threads", type=int, default=1); ap.add_argument("--timeout", type=int, default=6 * 3600)
    ap.add_argument("--retry-errors", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--shard", default="0/1", help="i/n: run only jobs with index %% n == i of the sorted job list, "
                    "so a benchmark can be split across machines (merge the .jsonl files afterwards)")
    ap.add_argument("--out", default=OUT, help="result file (use a different file per machine)")
    a = ap.parse_args()
    done = set()
    if os.path.exists(a.out):
        for r in map(json.loads, open(a.out)):
            if r["status"] == "ok" or not a.retry_errors:
                done.add(r["id"])
    jobs = [(ds, sec, m, s) for (ds, sec, sp_) in sections() for m in a.methods for s in a.seeds
            if sp_ in a.splits and (not a.datasets or ds in a.datasets) and (not a.sections or sec in a.sections)
            and not (m in VISIUM_ONLY and ds != "dlpfc") and job_id(ds, sec, m, s) not in done]
    si, sn = map(int, a.shard.split("/"))
    jobs = [j for n, j in enumerate(sorted(jobs)) if n % sn == si]
    serial = [j for j in jobs if j[2] in SERIAL]
    par = [j for j in jobs if j[2] not in SERIAL]
    print(f"{len(jobs)} jobs ({len(par)} parallel, {len(serial)} serial), {len(done)} already recorded", flush=True)
    if a.dry_run:
        return
    os.makedirs(RUNS, exist_ok=True)

    def go(batch, workers):
        with ThreadPoolExecutor(workers) as ex:
            futs = [ex.submit(run, j, a.timeout, a.threads) for j in batch]
            for fut in as_completed(futs):
                r = fut.result()
                with open(a.out, "a") as f:
                    f.write(json.dumps(r) + "\n")
                met = r.get("metrics", {})
                print(f"{r['id']:<60} {r['status']:<5} ARI={met.get('ARI', float('nan')):.3f} "
                      f"t={r['resources']['wall_s']:.0f}s mem={r['resources']['peak_rss_gb']:.1f}GB", flush=True)
    go(par, a.workers)
    go(serial, 1)


if __name__ == "__main__":
    main()
