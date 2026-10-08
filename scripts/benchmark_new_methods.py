"""Full benchmark of the additional methods (scripts/new_methods.py) on all 20 sections.

Seeds: 3 for fast methods, 1 for slow ones (as for GraphST on DLPFC). Each job runs in its own
subprocess (an out-of-memory kill only loses that job) and appends one JSON line to
results/new_methods.jsonl; finished jobs are skipped on restart. For methods that return an
embedding, the same embedding is also clustered with the 20-start GMM ("+robust"), and seed-0
embeddings are saved to results/emb/ for the clustering-lottery analyses.

python scripts/benchmark_new_methods.py --methods all --workers 3            # everything but DeepST
python scripts/benchmark_new_methods.py --methods deepst --workers 1         # DeepST (memory)
"""
import argparse, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from benchmark_anisost import DLPFC_SLICES  # noqa: E402
from prepare_extra import EXTRA  # noqa: E402

SEEDS = {"nichepca": [0, 1, 2], "sedr": [0, 1, 2], "spaceflow": [0, 1, 2], "deepst": [0, 1, 2],
         "stagate": [0], "bass": [0], "ccst": [0], "spatial_mgcn": [0], "bayesspace": [0]}
OUT = os.path.join(ROOT, "results", "new_methods.jsonl")

WORKER = r'''
import json, os, sys, time, traceback, warnings
warnings.filterwarnings("ignore")
sys.path[:0] = [{root!r}, {here!r}]
import numpy as np, torch
torch.set_num_threads(1)
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from feasibility_new_methods import load_raw
import new_methods
from anisost import robust_gmm
m, ds, sec, seed = {job!r}
t0 = time.time()
rec = {{"method": m, "dataset": ds, "slice": sec, "seed": seed}}
try:
    a, k = load_raw(ds, sec)
    y = a.obs["ground_truth"].to_numpy().astype(object)
    keep = np.array([isinstance(v, str) and v != "nan" for v in y])
    pred, Z = new_methods.METHODS[m](a, k, seed, ds)
    rec.update(status="ok", time=time.time() - t0, ARI=float(adjusted_rand_score(y[keep], pred[keep])),
               NMI=float(normalized_mutual_info_score(y[keep], pred[keep])), n_found=int(len(np.unique(pred))))
    rec.update({{k_: float(v) for k_, v in new_methods.LAST_ORACLE.items()}})
    if Z is not None:
        Z = np.asarray(Z, dtype=np.float64)
        pr = robust_gmm(Z, k, seed=seed)
        rec["ARI_robust"] = float(adjusted_rand_score(y[keep], pr[keep]))
        rec["NMI_robust"] = float(normalized_mutual_info_score(y[keep], pr[keep]))
        if seed == 0:
            np.save(os.path.join({root!r}, "results", "emb", f"{{ds}}_{{sec}}_{{m}}.npy"), Z)
except Exception as e:
    rec.update(status="error", time=time.time() - t0, error=f"{{type(e).__name__}}: {{e}}"[:2000],
               trace=traceback.format_exc()[-2000:])
print("RESULT_JSON " + json.dumps(rec), flush=True)
'''


def run_job(job, timeout):
    code = WORKER.format(root=ROOT, here=HERE, job=job)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=timeout, env=env)
        for line in p.stdout.splitlines()[::-1]:
            if line.startswith("RESULT_JSON "):
                return json.loads(line[len("RESULT_JSON "):])
        why = f"exit code {p.returncode} (killed, e.g. out of memory)" if p.returncode else "no result"
        return dict(zip(("method", "dataset", "slice", "seed"), job), status="error", time=time.time() - t0,
                    error=why, trace=p.stderr[-1500:])
    except subprocess.TimeoutExpired:
        return dict(zip(("method", "dataset", "slice", "seed"), job), status="error", time=time.time() - t0,
                    error=f"timeout after {timeout} s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="+", default=["all"])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=5 * 3600)
    ap.add_argument("--retry-errors", action="store_true")
    a = ap.parse_args()
    methods = [m for m in SEEDS if m != "deepst"] if a.methods == ["all"] else a.methods
    secs = [("dlpfc", s) for s in DLPFC_SLICES] + [(ds, s) for ds, m in EXTRA.items() for s in m["sections"]]
    done = set()
    if os.path.exists(OUT):
        for r in map(json.loads, open(OUT)):
            if r["status"] == "ok" or not a.retry_errors:
                done.add((r["method"], r["dataset"], r["slice"], r["seed"]))
    jobs = [(m, ds, s, sd) for sd in [0, 1, 2] for (ds, s) in secs for m in methods
            if sd in SEEDS[m] and not (m == "bayesspace" and ds != "dlpfc") and (m, ds, s, sd) not in done]
    print(f"{len(jobs)} jobs", flush=True)
    os.makedirs(os.path.join(ROOT, "results", "emb"), exist_ok=True)
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(run_job, j, a.timeout) for j in jobs]
        for fut in as_completed(futs):
            r = fut.result()
            with open(OUT, "a") as f:
                f.write(json.dumps(r) + "\n")
            msg = f"ARI={r['ARI']:.3f}" if r["status"] == "ok" else r["error"][:120]
            print(f"{r['method']:<13} {r['dataset']:<8} {r['slice']:<22} s{r['seed']} {r['status']:<5} "
                  f"t={r['time']:.0f}s {msg}", flush=True)


if __name__ == "__main__":
    main()
