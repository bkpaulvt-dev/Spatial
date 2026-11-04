"""Resumable queue for the new-datasets extension (docs/NEWDATA_COMMAND.md section 3; docs/PREREGISTERED_SIM.md).

Reuses the standardised runner of bench_queue.py (run() -> bench_run.py under resource measurement) without touching it, but
reads configs/datasets_newdata.yaml (the original registry must not change) and writes only new files:
  results/newdata_runs_<host>.jsonl      one record per run (newest per id wins), tagged host / extension
  results/newdata_runs/<id>.json|npz     per-job files (git-ignored like results/runs)
Methods are queued cheapest first (median wall seconds per observation in the original benchmark); all sections of one method before
the next method. Errors: out-of-memory / timeout are final (recorded, not retried); other errors are retried up to --max-attempts with
unchanged settings. Nothing about any method is changed.

  python scripts/newdata_queue.py --dry-run [--datasets sim_bands] [--max-methods N]
Tier-3 methods (TIER3) run only seed 0 / replicate 0 on the simulation (amendment of the pre-registration); real datasets: all methods x 3 seeds.
  python scripts/newdata_queue.py --datasets sim_bands sim_blocks --workers 2
"""
import argparse, json, os, socket, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [ROOT, HERE]
import yaml  # noqa: E402
import bench_queue as bq  # noqa: E402
from adapters import ADAPTERS, SERIAL, VISIUM_ONLY  # noqa: E402
from bench_run import job_id  # noqa: E402
from spatialbench.data import VISIUM  # noqa: E402

HOST = socket.gethostname().lower()
BASE = os.environ.get("BASE", "/mnt/disk/bikashkumar/SpatialBench")
HOLD = os.path.join(BASE, "newdata_hold")      # while this file exists the queue waits before starting (lets the real-data phase go first)
# Amendment of docs/PREREGISTERED_SIM.md (2026-11-04, based only on cost): the 8 tier-3 (deep) methods run a REDUCED design on the
# simulation: seed 0, replicate 0 of every setting (9 tissues per method). Tiers 1 and 2 keep the full design (45 tissues x 3 seeds).
TIER3 = ("bass", "deepst", "spaceflow", "stagate", "graphst", "spatial_mgcn", "bayesspace", "ccst")
REG = os.path.join(ROOT, "configs", "datasets_newdata.yaml")
RUNS = os.path.join(ROOT, "results", "newdata_runs")
ORIG = os.path.join(ROOT, "results", "benchmark_runs.jsonl")


def method_cost():
    """Median wall seconds per observation per method in the original benchmark (cheap first); unknown methods last."""
    c = {}
    if os.path.exists(ORIG):
        for r in map(json.loads, open(ORIG)):
            res = r.get("resources") or {}
            if r.get("status") == "ok" and not r.get("host") and r.get("n_obs") and "wall_s" in res:
                c.setdefault(r["method"], []).append(res["wall_s"] / r["n_obs"])
    return {m: statistics.median(v) for m, v in c.items()}


def final_error(r):
    res = r.get("resources") or {}
    return r.get("status") != "ok" and (res.get("oom_killed") or res.get("timed_out"))


def has_data(ds, sec):
    if ds.startswith("sim_"):
        return os.path.exists(os.path.join(ROOT, "data", "Sim", ds, f"{sec}.h5ad"))
    return True


def build(datasets, sections, seeds, methods, out, max_attempts, require_data=True):
    reg = yaml.safe_load(open(REG))["datasets"]
    done, attempts = set(), {}
    if os.path.exists(out):
        for r in map(json.loads, open(out)):
            attempts[r["id"]] = attempts.get(r["id"], 0) + 1
            if r["status"] == "ok" or final_error(r) or attempts[r["id"]] >= max_attempts:
                done.add(r["id"])
            else:
                done.discard(r["id"])
    cost = method_cost()
    order = sorted(methods, key=lambda m: (cost.get(m, 1e9), m))
    secs = [(ds, sec) for ds, card in reg.items() for sec in card["sections"]
            if (not datasets or ds in datasets) and (not sections or sec in sections)]
    plan = []
    for m in order:
        jobs = [(ds, sec, m, s) for ds, sec in secs for s in seeds
                if not (m in VISIUM_ONLY and ds not in VISIUM) and job_id(ds, sec, m, s) not in done
                and (not require_data or has_data(ds, sec))
                and not (m in TIER3 and ds.startswith("sim_") and (s != 0 or not sec.endswith("_r0")))]   # reduced design for tier 3
        plan.append((m, jobs))
    return plan, cost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+"); ap.add_argument("--sections", nargs="+")
    ap.add_argument("--methods", nargs="+", default=sorted(ADAPTERS)); ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--workers", type=int, default=2, help="parallel jobs (rule: at most 2 heavy jobs); serial methods run alone")
    ap.add_argument("--timeout", type=int, default=24 * 3600); ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--max-methods", type=int, help="only the N cheapest methods (tiering)")
    ap.add_argument("--no-require-data", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", f"newdata_runs_{HOST}.jsonl"))
    a = ap.parse_args()
    plan, cost = build(a.datasets, a.sections, a.seeds, a.methods, a.out, a.max_attempts, not a.no_require_data)
    if a.max_methods:
        plan = plan[:a.max_methods]
    n_obs = 14400
    tot = 0.0
    for m, jobs in plan:
        est = cost.get(m, float("nan")) * n_obs / 3600
        tot += est * len(jobs) / (1 if m in SERIAL else a.workers)
        print(f"  {m:<17s} {len(jobs):4d} jobs  ~{est:5.2f} h each (linear scaling to 14,400 obs; superlinear methods take longer)", flush=True)
    print(f"{sum(len(j) for _, j in plan)} jobs; rough lower bound {tot:.0f} h with {a.workers} workers", flush=True)
    if a.dry_run:
        return
    os.makedirs(RUNS, exist_ok=True); bq.RUNS = RUNS      # bq.run() reads this module global: keep the new per-job files apart
    if os.path.exists(HOLD):
        print(f"hold file {HOLD} present: waiting (real-data phase first)", flush=True)
        while os.path.exists(HOLD):
            time.sleep(300)
    for m, jobs in plan:
        if not jobs:
            continue
        with ThreadPoolExecutor(1 if m in SERIAL else a.workers) as ex:
            futs = [ex.submit(bq.run, j, a.timeout, 1) for j in jobs]
            for fut in as_completed(futs):
                r = fut.result(); r["host"] = HOST; r["extension"] = "newdata"
                res = r.get("resources") or {}
                r["outcome"] = "ok" if r["status"] == "ok" else "time limit" if res.get("timed_out") else "memory limit" if res.get("oom_killed") else "error"
                r["design"] = "reduced" if (r["method"] in TIER3 and r["dataset"].startswith("sim_")) else "full"
                with open(a.out, "a") as f:
                    f.write(json.dumps(r) + "\n")
                met = r.get("metrics", {})
                print(f"{r['id']:<48} {r['status']:<5} ARI={met.get('ARI', float('nan')):.3f} t={r['resources']['wall_s']:.0f}s "
                      f"mem={r['resources']['peak_rss_gb']:.1f}GB", flush=True)
    print("NEWDATA_QUEUE_DONE", flush=True)


if __name__ == "__main__":
    main()
