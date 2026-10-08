"""Feasibility check for additional methods: one STARmap and one DLPFC section, seed 0.

python scripts/feasibility_new_methods.py [methods...]   -> results/feasibility.jsonl
"""
import json, os, sys, time, traceback, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]


def load_raw(ds, sec):
    """AnnData with raw counts, obs['ground_truth'], obsm['spatial'], and the number of domains."""
    import anndata, pandas as pd
    if ds == "dlpfc":
        from hicast.data import load_dlpfc_adata
        from benchmark_anisost import N_CLUSTERS
        a = load_dlpfc_adata(os.path.join(ROOT, "data", "DLPFC"), sec); a.var_names_make_unique()
        return a, N_CLUSTERS[sec]
    from prepare_extra import EXTRA
    csv = os.path.join(ROOT, "data", "ext", "csv")
    cnt = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_counts.csv"), index_col=0)
    info = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_info.csv"), index_col=0).loc[cnt.index]
    keep = cnt.sum(1).to_numpy() > 0
    a = anndata.AnnData(cnt[keep].to_numpy(np.float32), obs=pd.DataFrame(index=cnt.index[keep].astype(str)),
                        var=pd.DataFrame(index=cnt.columns.astype(str)))
    a.obs["ground_truth"] = info.loc[keep, "z"].astype(str).to_numpy()
    a.obsm["spatial"] = info.loc[keep, ["x", "y"]].to_numpy(np.float64)
    return a, EXTRA[ds]["n_clusters"]


def run(job):
    warnings.filterwarnings("ignore")
    import torch; torch.set_num_threads(1)
    from sklearn.metrics import adjusted_rand_score
    from new_methods import METHODS
    method, ds, sec = job
    t0 = time.time()
    try:
        a, k = load_raw(ds, sec)
        pred, Z = METHODS[method](a, k, 0, ds)
        y = a.obs["ground_truth"].to_numpy().astype(object)
        keep = np.array([isinstance(v, str) and v != "nan" for v in y])
        return {"method": method, "dataset": ds, "slice": sec, "status": "ok", "ARI": float(adjusted_rand_score(y[keep], pred[keep])),
                "n_clusters_found": int(len(np.unique(pred))), "emb_dim": None if Z is None else int(Z.shape[1]),
                "time": time.time() - t0}
    except Exception as e:
        return {"method": method, "dataset": ds, "slice": sec, "status": "error", "time": time.time() - t0,
                "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}


if __name__ == "__main__":
    methods = sys.argv[1:] or ["stagate", "sedr", "spaceflow", "nichepca"]
    jobs = [(m, ds, s) for m in methods for ds, s in [("starmap", "20180417_BZ5_control"), ("dlpfc", "151673")]]
    out = os.path.join(ROOT, "results", "feasibility.jsonl")
    with ProcessPoolExecutor(4, mp_context=mp.get_context("spawn")) as ex, open(out, "a") as f:
        for fut in as_completed([ex.submit(run, j) for j in jobs]):
            r = fut.result(); f.write(json.dumps(r) + "\n"); f.flush()
            msg = f"ARI={r['ARI']:.3f} k={r['n_clusters_found']}" if r["status"] == "ok" else r["error"][:150]
            print(f"{r['method']:<10} {r['dataset']:<8} {r['status']:<6} t={r['time']:.0f}s  {msg}", flush=True)
