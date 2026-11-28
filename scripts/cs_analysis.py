"""Crossed-seed analysis (docs/PREREGISTERED_CROSSED_SEED.md). Reads the embeddings saved by scripts/review_stage_cs.sh
(results/cs_runs/<id>.npz, key 'emb') and the annotation of each section; fits 20 single-start tied GMMs and 20 single-start k-means per
embedding; writes results/cs_fits.csv (one row per fit), results/cs_summary.json and results/cs_summary.md.
python scripts/cs_analysis.py [--workers 4]"""
import argparse, json, os, sys, warnings
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT, HERE]
warnings.filterwarnings("ignore")
RUNS = os.path.join(ROOT, "results", "cs_runs"); R = lambda f: os.path.join(ROOT, "results", f)
SECTIONS = [("dlpfc", "151507", "Br5292"), ("dlpfc", "151669", "Br5595"), ("dlpfc", "151673", "Br8100"), ("starmap", "20180419_BZ9_control", "starmap"),
            ("merfish", "-0.14", "merfish"), ("brca", "block_a_1", "brca"), ("stereo", "E9.5_E1S1", "stereo")]
METHODS = ["linear_diffusion", "anisost", "pca_gmm", "banksy_l0.8", "nichepca", "histar", "graphst", "stagate", "spaceflow"]
SEEDS = [0, 1, 2, 3, 4]; NF = 20


def fit_one(args):
    ds, sec, m, s = args
    from sklearn.mixture import GaussianMixture
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score as ari
    from spatialbench.data import load_section
    from spatialbench import metrics as M
    f = os.path.join(RUNS, f"{ds}__{sec}__{m}__s{s}.npz")
    if not os.path.exists(f):
        return []
    z = np.load(f, allow_pickle=True)
    if "emb" not in z.files:
        return []
    Z = np.asarray(z["emb"], np.float64)
    a = load_section(ds, sec); truth = a.obs["ground_truth"].to_numpy(dtype=object); v = M.valid_mask(truth)
    K = int(len(set(truth[v].astype(str)))); rows = []
    for r in range(NF):
        g = GaussianMixture(K, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=r).fit(Z)
        lab = g.predict(Z); rows.append(dict(dataset=ds, section=sec, method=m, seed=s, clusterer="gmm", start=r,
                                             ari=float(ari(truth[v].astype(str), lab[v])), objective=float(g.score(Z)), dim=int(Z.shape[1])))
        km = KMeans(K, n_init=1, random_state=r).fit(Z)
        rows.append(dict(dataset=ds, section=sec, method=m, seed=s, clusterer="kmeans", start=r,
                         ari=float(ari(truth[v].astype(str), km.labels_[v])), objective=float(-km.inertia_), dim=int(Z.shape[1])))
    return rows


def summarise(df):
    import pandas as pd
    out = {}
    for (cl, ds, sec, m), g in df.groupby(["clusterer", "dataset", "section", "method"]):
        per = g.groupby("seed")
        within_sd = per.ari.std(ddof=1); within_rng = per.ari.max() - per.ari.min(); means = per.ari.mean()
        n = len(means)
        between_var = float(means.var(ddof=1)) if n > 1 else np.nan
        train_var = max(between_var - float((within_sd ** 2).mean()) / NF, 0.0) if n > 1 else np.nan
        sel = {}
        for k in (1, 3, 20):
            sel[k] = float(np.mean([gg[gg.start < k].sort_values("objective").iloc[-1].ari for _, gg in per]))
        out[(cl, ds, sec, m)] = dict(n_seeds=n, mean_ari=float(means.mean()), within_sd=float(within_sd.mean()), within_range=float(within_rng.mean()),
                                     between_sd_uncorrected=float(np.sqrt(between_var)) if n > 1 else None,
                                     between_sd_corrected=float(np.sqrt(train_var)) if n > 1 else None, select_1=sel[1], select_3=sel[3], select_20=sel[20])
    return out


if __name__ == "__main__":
    import pandas as pd
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=4); a = ap.parse_args()
    jobs = [(ds, sec, m, s) for ds, sec, _ in SECTIONS for m in METHODS for s in SEEDS]
    rows = []
    with ProcessPoolExecutor(a.workers) as ex:
        for r in ex.map(fit_one, jobs):
            rows += r
    df = pd.DataFrame(rows); df.to_csv(R("cs_fits.csv"), index=False)
    S = summarise(df); grp = {sec: g for _, sec, g in SECTIONS}
    js = [dict(clusterer=k[0], dataset=k[1], section=k[2], group=grp[k[2]], method=k[3], **v) for k, v in S.items()]
    json.dump(js, open(R("cs_summary.json"), "w"), indent=1)
    t = pd.DataFrame(js)
    lines = ["# Crossed-seed experiment: summary (auto-generated; docs/PREREGISTERED_CROSSED_SEED.md)", "",
             f"Embeddings analysed: {df.groupby(['dataset','section','method','seed']).ngroups} of {len(jobs)} planned.", ""]
    for cl in ("gmm", "kmeans"):
        tt = t[t.clusterer == cl]
        if tt.empty:
            continue
        pm = tt.groupby("method")[["mean_ari", "within_sd", "within_range", "between_sd_uncorrected", "between_sd_corrected", "select_1", "select_3", "select_20"]].mean()
        lines += [f"## {cl}: mean over the 7 sections (one per group)", "", pm.round(3).to_markdown(), ""]
        pd_ = tt.groupby("dataset")[["within_sd", "between_sd_corrected"]].mean()
        lines += [f"### {cl}: per dataset (mean over methods)", "", pd_.round(3).to_markdown(), ""]
    g = t[t.clusterer == "gmm"].set_index(["section", "method"]).mean_ari; k = t[t.clusterer == "kmeans"].set_index(["section", "method"]).mean_ari
    rho = {sec: float(pd.Series(g.loc[sec]).rank().corr(pd.Series(k.loc[sec]).rank())) for sec in g.index.get_level_values(0).unique() if sec in k.index.get_level_values(0)}
    lines += ["## Method order, GMM vs k-means (Spearman rho of mean ARI per section)", "", json.dumps({s: round(v, 3) for s, v in rho.items()}), ""]
    open(R("cs_summary.md"), "w").write("\n".join(lines)); print("\n".join(lines))
