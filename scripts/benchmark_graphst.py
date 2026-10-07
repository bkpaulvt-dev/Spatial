"""GraphST (Long et al., Nat. Commun. 2023) on DLPFC, STARmap and MERFISH.

Official package and tutorial pipeline: GraphST builds its own spatial graph and features
(3000 seurat_v3 HVGs for Visium; all genes for the targeted STARmap/MERFISH panels, which
have fewer than 3000 genes), trains for 600 epochs, reduces the embedding to 20 PCs and
clusters it with R mclust (EEE) via rpy2. We report
  graphst          : official mclust clustering, no refinement
  graphst_refined  : + the tutorial's label refinement (radius 50)
  graphst+robust   : the same 20-PC embedding clustered with the 20-start GMM
Seed-0 embeddings (emb_pca) are saved to results/emb/ for the lottery experiments.

Needs rpy2 compatible with the installed R (rpy2==3.5.17 for R 4.3).
python scripts/benchmark_graphst.py --out results/graphst.jsonl
"""
import argparse, json, os, sys, time, warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
from benchmark_anisost import DLPFC_SLICES, N_CLUSTERS  # noqa: E402
from prepare_extra import EXTRA  # noqa: E402


def make_adata(ds, sec, data_root):
    import anndata, pandas as pd, scanpy as sc
    if ds == "dlpfc":
        from hicast.data import load_dlpfc_adata
        a = load_dlpfc_adata(data_root, sec)
        a.var_names_make_unique()
        return a, N_CLUSTERS[sec]                      # GraphST.preprocess selects HVGs itself
    csv = os.path.join(ROOT, "data", "ext", "csv")
    cnt = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_counts.csv"), index_col=0)
    info = pd.read_csv(os.path.join(csv, f"{ds}_{sec}_info.csv"), index_col=0).loc[cnt.index]
    keep = cnt.sum(1).to_numpy() > 0
    a = anndata.AnnData(cnt[keep].to_numpy(np.float32), obs=pd.DataFrame(index=cnt.index[keep]),
                        var=pd.DataFrame(index=cnt.columns))
    a.obs["ground_truth"] = info.loc[keep, "z"].astype(str).to_numpy()
    a.obsm["spatial"] = info.loc[keep, ["x", "y"]].to_numpy(np.float64)
    a.var["highly_variable"] = True                    # targeted panel: keep every gene,
    sc.pp.normalize_total(a, target_sum=1e4)           # then GraphST.preprocess's remaining steps
    sc.pp.log1p(a)
    sc.pp.scale(a, zero_center=False, max_value=10)
    return a, EXTRA[ds]["n_clusters"]


def run(job):
    warnings.filterwarnings("ignore")
    import contextlib, io, torch
    torch.set_num_threads(1)
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    from GraphST import GraphST
    from GraphST.utils import clustering
    from anisost import robust_gmm
    ds, sec, seed, data_root = job
    a, k = make_adata(ds, sec, data_root)
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        a = GraphST.GraphST(a, device=torch.device("cpu"), random_seed=41 + seed).train()
        clustering(a, k, radius=50, method="mclust", refinement=False)
    t = time.time() - t0
    y = a.obs["ground_truth"].to_numpy().astype(object)
    keep = np.array([isinstance(v, str) and v != "nan" for v in y])
    sc_ = lambda p: {"ARI": adjusted_rand_score(y[keep], np.asarray(p)[keep]),
                     "NMI": normalized_mutual_info_score(y[keep], np.asarray(p)[keep])}
    base = {"dataset": ds, "slice": sec, "seed": seed, "time": t}
    out = [{**base, "method": "graphst", **sc_(a.obs["domain"].astype(int).to_numpy())}]
    with contextlib.redirect_stdout(io.StringIO()):
        b = a.copy(); clustering(b, k, radius=50, method="mclust", refinement=True)
    out.append({**base, "method": "graphst_refined", **sc_(b.obs["domain"].astype(str).to_numpy())})
    out.append({**base, "method": "graphst+robust", **sc_(robust_gmm(a.obsm["emb_pca"], k, seed=seed))})
    if seed == 0:
        np.save(os.path.join(ROOT, "results", "emb", f"{ds}_{sec}_graphst.npy"), a.obsm["emb_pca"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "DLPFC"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "graphst.jsonl"))
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--datasets", nargs="+", default=["dlpfc", "starmap", "merfish"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "results", "emb"), exist_ok=True)
    secs = {"dlpfc": DLPFC_SLICES, **{d: m["sections"] for d, m in EXTRA.items()}}
    done = set()
    if os.path.exists(a.out):
        done = {(r["dataset"], r["slice"], r["seed"]) for r in map(json.loads, open(a.out))}
    jobs = [(ds, s, sd, a.data) for sd in a.seeds for ds in a.datasets for s in secs[ds] if (ds, s, sd) not in done]
    print(f"{len(jobs)} jobs", flush=True)
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("spawn")) as ex, open(a.out, "a") as f:
        futs = {ex.submit(run, j): j for j in jobs}
        for fut in as_completed(futs):
            try:
                rows = fut.result()
            except Exception as e:
                print(f"FAILED {futs[fut][:3]}: {type(e).__name__}: {e}", flush=True); continue
            for r in rows:
                f.write(json.dumps(r) + "\n")
                print(f"{r['method']:<16} {r['dataset']} {r['slice']} s{r['seed']} ARI={r['ARI']:.3f} t={r['time']:.0f}s", flush=True)
            f.flush()


if __name__ == "__main__":
    main()
