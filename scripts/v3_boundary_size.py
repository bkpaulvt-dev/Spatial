"""Revision V3 item 3c (frozen in docs/V3_REVISION_WORKPLAN.md): where does linear diffusion gain or lose against PCA on real tissue?
For the 24 sections, seeds 0-2: linear diffusion and PCA with the benchmark settings and matched clustering (20-start GMM; adapters.py),
per-spot correctness under the one-to-one Hungarian matching of clusters to annotated domains, distance to the nearest spot of another
domain (in median nearest-neighbour spacings) and domain prevalence. Writes results/v3_boundary_size.csv (per section, seed, method, bin)
and results/v3_boundary_size.json (group-level effects). python scripts/v3_boundary_size.py [--workers 2]"""
import argparse, json, os, sys, warnings
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd, yaml
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT, HERE]
warnings.filterwarnings("ignore")
DBINS = [(0, 1.5, "1"), (1.5, 2.5, "2"), (2.5, 4.5, "3-4"), (4.5, 8.5, "5-8"), (8.5, 1e9, ">8")]
PBINS = [(0, .05, "<5%"), (.05, .10, "5-10%"), (.10, .20, "10-20%"), (.20, 1.01, ">20%")]
UM = {"dlpfc": 100.0, "brca": 100.0}   # Visium centre-to-centre spacing in micrometres; others: coordinates already in micrometres (STARmap, MERFISH) or bins


def job(args):
    ds, sec, seed = args
    from scipy.optimize import linear_sum_assignment
    from scipy.spatial import cKDTree
    from sklearn.metrics import adjusted_rand_score
    from adapters import ADAPTERS
    from spatialbench.data import load_section
    from spatialbench import metrics as M
    a = load_section(ds, sec); truth = a.obs["ground_truth"].to_numpy(dtype=object); v = M.valid_mask(truth)
    C = np.asarray(a.obsm["spatial"], float); k = int(len(set(truth[v].astype(str))))
    d1, _ = cKDTree(C).query(C, k=2); sp = float(np.median(d1[:, 1])); d6, _ = cKDTree(C).query(C, k=7)
    t = truth[v].astype(str); Cv = C[v]; dist = np.empty(len(t))
    for lab in np.unique(t):
        o = t != lab
        if o.any():
            dist[t == lab] = cKDTree(Cv[o]).query(Cv[t == lab])[0] / sp
        else:
            dist[t == lab] = np.inf
    prev = pd.Series(t).map(pd.Series(t).value_counts(normalize=True)).to_numpy()
    rows = []
    for m in ("linear_diffusion", "pca_gmm"):
        lab = np.asarray(ADAPTERS[m](a, k, seed, ds)["labels"])[v]
        doms, ti = np.unique(t, return_inverse=True); cl, li = np.unique(lab, return_inverse=True)
        cont = np.zeros((len(cl), len(doms))); np.add.at(cont, (li, ti), 1)
        r, c = linear_sum_assignment(-cont); mp = dict(zip(r, c))
        ok = np.array([mp.get(x, -1) == y for x, y in zip(li, ti)])
        base = dict(dataset=ds, section=sec, seed=seed, method=m, ari=float(adjusted_rand_score(t, lab)), acc=float(ok.mean()), spacing=sp,
                    knn6_spacings=float(np.median(d6[:, 6]) / sp), knn6_um=float(np.median(d6[:, 6]) * (UM[ds] / sp if ds in UM else 1.0)) if ds in UM or ds in ("starmap", "merfish") else None)
        for lo, hi, name in DBINS:
            s = (dist >= lo) & (dist < hi)
            rows.append(dict(base, kind="distance", bin=name, n=int(s.sum()), acc_bin=float(ok[s].mean()) if s.any() else None))
        for lo, hi, name in PBINS:
            s = (prev >= lo) & (prev < hi)
            rows.append(dict(base, kind="prevalence", bin=name, n=int(s.sum()), acc_bin=float(ok[s].mean()) if s.any() else None))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); a = ap.parse_args()
    reg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"]
    grp = {(ds, str(s)): (m.get("donor") if ds == "dlpfc" else ds) for ds, c in reg.items() for s, m in c["sections"].items()}
    jobs = [(ds, s, sd) for (ds, s) in grp for sd in (0, 1, 2)]
    rows = []
    with ProcessPoolExecutor(a.workers) as ex:
        for r in ex.map(job, jobs):
            rows += r
    df = pd.DataFrame(rows); df["group"] = [grp[(d, s)] for d, s in zip(df.dataset, df.section)]
    df.to_csv(os.path.join(ROOT, "results", "v3_boundary_size.csv"), index=False)
    out = {}
    for kind in ("distance", "prevalence"):
        x = df[df.kind == kind].dropna(subset=["acc_bin"])
        w = x.pivot_table(index=["group", "section", "seed", "bin"], columns="method", values="acc_bin").dropna()
        w["eff"] = w["linear_diffusion"] - w["pca_gmm"]
        sec_eff = w.groupby(["group", "section", "bin"]).eff.mean().reset_index()
        g = sec_eff.groupby(["bin", "group"]).eff.mean().unstack()
        n = df[(df.kind == kind) & (df.method == "linear_diffusion") & (df.seed == 0)].groupby("bin").n.sum()
        out[kind] = {b: dict(per_group=g.loc[b].dropna().round(4).to_dict(), group_mean=float(g.loc[b].dropna().mean()), n_groups=int(g.loc[b].notna().sum()),
                             n_spots=int(n.get(b, 0))) for b in g.index}
    chk = df[df.kind == "distance"].drop_duplicates(["dataset", "section", "seed", "method"])[["dataset", "section", "seed", "method", "ari", "acc", "knn6_spacings", "knn6_um"]]
    out["neighbourhood"] = chk.groupby("dataset")[["knn6_spacings", "knn6_um"]].median().round(2).to_dict(orient="index")
    out["ari_check"] = chk.groupby(["dataset", "method"]).ari.mean().round(4).reset_index().to_dict(orient="records")
    json.dump(out, open(os.path.join(ROOT, "results", "v3_boundary_size.json"), "w"), indent=1)
    for kind in ("distance", "prevalence"):
        print(kind); [print(f"  {b:>7} mean {v['group_mean']:+.3f} ({v['n_groups']} groups, {v['n_spots']} spots) {v['per_group']}") for b, v in out[kind].items()]
    print(out["neighbourhood"])
