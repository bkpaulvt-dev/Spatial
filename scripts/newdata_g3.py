"""G3: re-test the paper's clustering findings (a-e) on the new datasets (docs/PREREGISTERED_SIM.md, section "G3"; docs/NEWDATA_COMMAND.md).

Inputs: seed-0 embeddings saved by the runner (results/newdata_runs/<id>.npz, key emb), the run records (results/newdata_runs_*.jsonl).
Protocols are those of the original analysis (clustering_lottery.py, k_sensitivity.py, mclust_seed.R), re-implemented here so that no
existing script is touched:
  (a) ARI range over 20 single-start fits (tied-covariance Gaussian mixture, n_init 1, reg_covar 1e-5, random_state 0..19) of the same embedding
  (b) R mclust default fit vs the R seed (10 seeds; scripts/newdata_mclust_seed.R = a copy of mclust_seed.R with an optional full-data fit: run only for simulation replicate 0; noise runs skipped)
  (c) matched (20-start, best likelihood) minus default clustering, ARI gain from the run records
  (d) Spearman rho between log-likelihood and ARI over the 20 fits
  (e) K sensitivity: ARI(K) minus the mean of ARI(K-1) and ARI(K+1), matched protocol (n_init 20, best likelihood)
Verdict per unit (simulation setting, or real dataset) and finding, with the original reference S0 pooled from the existing result files and the
null n0 fixed in the pre-registration: replicates / weakens / reverses; (b) is "not informative" when every section has <= 2000 observations
(mclust then initialises on all observations: no seed variation by construction).

  python scripts/newdata_g3.py --datasets allenmerfish --stage all [--workers 2]
  stages: export (csv for R) | fits (a, d, e in Python) | mclust (b, R) | verdicts (all five; cheap, re-run any time)
Outputs (new files only, in --outdir, default results/): newdata_g3_fits.jsonl, newdata_g3_mclust.csv, newdata_g3_verdicts.csv/.json, newdata_g3_summary.md
Tier-3 (reduced-design) simulation methods are excluded unless --include-reduced; they never get a verdict.
"""
import argparse, glob, json, os, re, subprocess, sys, warnings
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [ROOT, HERE]
RUNS = os.path.join(ROOT, "results", "newdata_runs")
TIER3 = ("bass", "deepst", "spaceflow", "stagate", "graphst", "spatial_mgcn", "bayesspace", "ccst")
NO_EMB = ("spagcn", "bass", "bayesspace")
N_FITS = 20; NBOOT = 10000; SEED = 20261104
NULL = {"a": 0.03, "b": 0.03, "c": 0.0, "d": 0.0, "e": 0.0}
LABEL = {"a": "(a) ARI range over 20 single-start fits", "b": "(b) R mclust seed effect (ARI range, 10 seeds)", "c": "(c) matched minus default ARI",
         "d": "(d) Spearman rho, log-likelihood vs ARI", "e": "(e) K sensitivity: ARI(K) minus mean ARI(K+-1)"}


def records(pattern):
    last = {}
    for f in sorted(glob.glob(pattern)):
        for l in open(f):
            r = json.loads(l); last[r["id"]] = r
    return last


def truth(ds, sec):
    from spatialbench.data import load_section
    from spatialbench import metrics as M
    a = load_section(ds, sec); y = a.obs["ground_truth"].to_numpy(dtype=object)
    return y, M.valid_mask(y)


def jobs(recs, datasets, include_reduced):
    out = []
    for r in recs.values():
        if r["status"] != "ok" or r["seed"] != 0 or r["dataset"] not in datasets or r["method"] in NO_EMB:
            continue
        if r["dataset"].startswith("sim_") and r["method"] in TIER3 and not include_reduced:
            continue
        p = os.path.join(RUNS, r["id"] + ".npz")
        if os.path.exists(p) and "emb" in np.load(p):
            out.append((r["dataset"], r["section"], r["method"], int(r["K"]), p, int(r["n_obs"])))
    return sorted(out)


def export(todo, outdir):
    d = os.path.join(outdir, "newdata_emb", "csv"); os.makedirs(d, exist_ok=True); seen = set()
    for ds, sec, m, k, p, n in todo:
        f = os.path.join(d, f"{ds}__{sec}__{m}__k{k}.csv")
        if not os.path.exists(f):
            np.savetxt(f, np.load(p)["emb"].astype(np.float64), delimiter=",")
        if (ds, sec) not in seen:
            seen.add((ds, sec)); lf = os.path.join(d, f"{ds}__{sec}__labels.csv")
            if not os.path.exists(lf):
                y, v = truth(ds, sec); np.savetxt(lf, np.where(v, y.astype(str), "NA"), fmt="%s")
    return d


def fit_one(job):
    warnings.filterwarnings("ignore")
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import adjusted_rand_score as ari
    from scipy.stats import spearmanr
    ds, sec, m, k, p, n = job
    Z = np.asarray(np.load(p)["emb"], dtype=np.float64); y, v = truth(ds, sec); yv = y[v].astype(str)
    fits = []
    for rs in range(N_FITS):
        g = GaussianMixture(k, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=rs).fit(Z)
        fits.append({"rs": rs, "ll": float(g.score(Z)), "ARI": float(ari(yv, g.predict(Z)[v]))})
    a = [f["ARI"] for f in fits]; ll = [f["ll"] for f in fits]
    rho = float(spearmanr(ll, a)[0]) if np.std(a) > 0 and np.std(ll) > 0 else float("nan")
    ks = {}
    for dk in (-1, 0, 1):
        if k + dk < 2: continue
        g = GaussianMixture(k + dk, covariance_type="tied", n_init=20, reg_covar=1e-5, random_state=0).fit(Z)
        ks[dk] = float(ari(yv, g.predict(Z)[v]))
    e = ks[0] - np.mean([ks[d] for d in (-1, 1) if d in ks]) if 0 in ks and (-1 in ks or 1 in ks) else float("nan")
    return {"dataset": ds, "section": sec, "method": m, "k": k, "n_obs": n, "range": max(a) - min(a), "rho": rho, "best_ll_ari": max(fits, key=lambda f: f["ll"])["ARI"],
            "mean_single_ari": float(np.mean(a)), "k_ari": ks, "k_sens": float(e), "fits": fits}


def run_fits(todo, out, workers):
    done = set()
    if os.path.exists(out):
        done = {(r["dataset"], r["section"], r["method"]) for r in map(json.loads, open(out))}
    todo = [j for j in todo if j[:3] not in done]; print(f"fits: {len(todo)} embeddings", flush=True)
    if workers > 1:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn")) as ex, open(out, "a") as f:
            for fut in as_completed([ex.submit(fit_one, j) for j in todo]):
                r = fut.result(); f.write(json.dumps(r) + "\n"); f.flush(); print("fits", r["dataset"], r["section"], r["method"], f"range {r['range']:.3f}", flush=True)
    else:
        with open(out, "a") as f:
            for j in todo:
                r = fit_one(j); f.write(json.dumps(r) + "\n"); f.flush(); print("fits", r["dataset"], r["section"], r["method"], f"range {r['range']:.3f}", flush=True)


def run_mclust(csvdir, out, datasets, workers):
    """R mclust seeds. Slow (about 10+ min per embedding at 14,400 observations), so the work is ordered: real datasets first, then the simulation
    replicate by replicate (replicate 0 of every setting, then 1, ...), so that a partial run is balanced and the verdict table shows how many units each verdict has."""
    env = dict(os.environ, MCLUST_NO_JIT="1", R_LIBS_USER=os.environ.get("R_LIBS_USER", os.path.join(os.path.dirname(ROOT), "Rlib")))
    sims = [d for d in datasets if d.startswith("sim_")]; real = [d for d in datasets if not d.startswith("sim_")]
    passes = (["(" + "|".join(real) + ")__"] if real else []) + [("(" + "|".join(sims) + f")__[mw][0-9]+_r{rep}__") for rep in range(5)] * bool(sims)
    for rx in passes:
        env["MCLUST_FULL"] = "1" if rx.endswith("_r0__") else "0"      # full-data fit only for simulation replicate 0 (cost); never for real data (n ~ 30,000)
        procs = [subprocess.Popen(["Rscript", os.path.join(HERE, "newdata_mclust_seed.R"), csvdir, out, rx], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for _ in range(max(1, workers))]
        for p in procs:
            o, _ = p.communicate(); print("\n".join(o.strip().splitlines()[-3:]), flush=True)


def boot(x, rng):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    if len(x) == 0: return (np.nan, np.nan, np.nan, 0)
    if len(x) == 1: return (float(x[0]), np.nan, np.nan, 1)
    b = rng.choice(x, size=(NBOOT, len(x)), replace=True).mean(1)
    return (float(x.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)), len(x))


def reference():
    """S0: each statistic pooled over the ORIGINAL datasets, from the existing result files (never modified)."""
    R = lambda *p: os.path.join(ROOT, "results", *p); S0 = {}
    try:
        from scipy.stats import spearmanr
        rows = [json.loads(l) for l in open(R("clustering_lottery.jsonl"))]
        S0["a"] = float(np.mean([max(x["ARI"] for x in r["fits"]) - min(x["ARI"] for x in r["fits"]) for r in rows]))
        S0["d"] = float(np.nanmedian([spearmanr([x["ll"] for x in r["fits"]], [x["ARI"] for x in r["fits"]])[0] for r in rows]))
    except Exception as e: print("reference a/d unavailable:", e)
    try:
        ms = pd.concat([pd.read_csv(f) for f in glob.glob(R("mclust_seed_g*.csv"))]); ms = ms[(ms.kind == "seed") & (ms.n > 2000)]
        S0["b"] = float(ms.groupby(["dataset", "slice", "method"]).ARI.agg(lambda s: s.max() - s.min()).mean())
    except Exception as e: print("reference b unavailable:", e)
    try:
        g = [r["metrics_matched"]["ARI"] - r["metrics"]["ARI"] for r in map(json.loads, open(R("benchmark_runs.jsonl")))
             if r.get("status") == "ok" and isinstance(r.get("metrics_matched"), dict) and "ARI" in r["metrics_matched"]]
        S0["c"] = float(np.mean(g))
    except Exception as e: print("reference c unavailable:", e)
    try:
        ks = []
        for r in map(json.loads, open(R("k_sensitivity.jsonl"))):
            a = {f["dk"]: f["ARI"] for f in r["fits"]}
            if 0 in a and (-1 in a or 1 in a): ks.append(a[0] - np.mean([a[d] for d in (-1, 1) if d in a]))
        S0["e"] = float(np.mean(ks))
    except Exception as e: print("reference e unavailable:", e)
    return S0


def unit_of(ds, sec):
    if ds.startswith("sim_"):
        t, p, rep = re.match(r"([mw])(\d+)_r(\d+)", sec).groups(); return f"{ds}:{t}={p}", int(rep)
    return ds, sec


def verdicts(recs, fits_path, mclust_path, outdir, include_reduced):
    rng = np.random.default_rng(SEED); S0 = reference()
    fits = [json.loads(l) for l in open(fits_path)] if os.path.exists(fits_path) else []
    rows = []   # (unit, replicate/section, method, finding, value)
    for r in fits:
        if r["dataset"].startswith("sim_") and r["method"] in TIER3 and not include_reduced: continue
        u, rep = unit_of(r["dataset"], r["section"])
        for f, key in (("a", "range"), ("d", "rho"), ("e", "k_sens")): rows.append((u, rep, r["method"], f, r[key], r["n_obs"]))
    if os.path.exists(mclust_path):
        ms = pd.read_csv(mclust_path); ms = ms[ms.kind == "seed"]
        for (ds, sec, m), g in ms.groupby(["dataset", "slice", "method"]):
            if ds.startswith("sim_") and m in TIER3 and not include_reduced: continue
            u, rep = unit_of(ds, sec); rows.append((u, rep, m, "b", float(g.ARI.max() - g.ARI.min()), int(g.n.iloc[0])))
    for r in recs.values():
        if r["status"] == "ok" and isinstance(r.get("metrics_matched"), dict) and "ARI" in r["metrics_matched"] and r["dataset"] in {x[0].split(":")[0] for x in rows} | {"allenmerfish"}:
            if r["dataset"].startswith("sim_") and r["method"] in TIER3 and not include_reduced: continue
            u, rep = unit_of(r["dataset"], r["section"]); rows.append((u, rep, r["method"], "c", r["metrics_matched"]["ARI"] - r["metrics"]["ARI"], r["n_obs"]))
    df = pd.DataFrame(rows, columns=["unit", "rep", "method", "finding", "value", "n_obs"]); out = []
    for (u, f), g in df.groupby(["unit", "finding"]):
        per = g.groupby("rep").value.agg(lambda s: np.nanmedian(s) if f == "d" else np.nanmean(s))   # statistic per replicate / section
        m, lo, hi, n = boot(per.values, rng); n0 = NULL[f]; s0 = S0.get(f, np.nan)
        informative = not (f == "b" and (g.n_obs <= 2000).all())
        if not informative: v = "not informative (<= 2000 observations: mclust initialises on all observations)"
        elif not np.isfinite(s0): v = "reference unavailable"
        elif not np.isfinite(lo): v = "no interval (one unit)"
        else:
            d0 = np.sign(s0 - n0) or 1.0
            v = "replicates" if (d0 * (lo - n0) > 0 if d0 > 0 else d0 * (hi - n0) > 0) else ("reverses" if (hi < n0 if d0 > 0 else lo > n0) else "weakens")
        out.append(dict(unit=u, finding=f, statistic=LABEL[f], n_units=n, S=m, ci_low=lo, ci_high=hi, n0=n0, S0_original=s0, n_methods=int(g.method.nunique()), verdict=v))
    res = pd.DataFrame(out).sort_values(["unit", "finding"]) if out else pd.DataFrame()
    res.to_csv(os.path.join(outdir, "newdata_g3_verdicts.csv"), index=False); json.dump({"S0": S0, "verdicts": res.to_dict("records")}, open(os.path.join(outdir, "newdata_g3_verdicts.json"), "w"), indent=1, default=float)
    with open(os.path.join(outdir, "newdata_g3_summary.md"), "w") as fh:
        fh.write("# G3 re-tests on the new datasets\n\nVerdict rule (pre-registered): with d0 = sign(S0 - n0), 'replicates' if d0*(S - n0) > 0 and the 95% bootstrap interval excludes n0; "
                 "'reverses' if d0*(S - n0) < 0 with the interval excluding n0; otherwise 'weakens'. Intervals are bootstrap over replicates (simulation) or sections (real data); with few units they are wide.\n\n")
        fh.write("Original reference S0 (pooled over the original datasets): " + ", ".join(f"{k}={v:.3f}" for k, v in S0.items()) + "\n\n| unit | finding | n units | S (95% CI) | n0 | S0 | verdict |\n|---|---|---|---|---|---|---|\n")
        for r in res.itertuples():
            fh.write(f"| {r.unit} | {r.finding} | {r.n_units} | {r.S:.3f} ({r.ci_low:.3f} to {r.ci_high:.3f}) | {r.n0} | {r.S0_original:.3f} | {r.verdict} |\n")
    print(open(os.path.join(outdir, "newdata_g3_summary.md")).read())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True); ap.add_argument("--stage", default="all", choices=["all", "export", "fits", "mclust", "verdicts"])
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--include-reduced", action="store_true")
    ap.add_argument("--records", default=os.path.join(ROOT, "results", "newdata_runs_*.jsonl")); ap.add_argument("--outdir", default=os.path.join(ROOT, "results"))
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    recs = records(a.records); todo = jobs(recs, a.datasets, a.include_reduced); print(len(todo), "seed-0 embeddings", flush=True)
    fp, mp_ = os.path.join(a.outdir, "newdata_g3_fits.jsonl"), os.path.join(a.outdir, "newdata_g3_mclust.csv")
    if a.stage in ("all", "export", "mclust"): csvdir = export(todo, a.outdir)
    if a.stage in ("all", "fits"): run_fits(todo, fp, a.workers)
    if a.stage in ("all", "mclust"): run_mclust(csvdir, mp_, a.datasets, a.workers)
    if a.stage in ("all", "verdicts"): verdicts(recs, fp, mp_, a.outdir, a.include_reduced)
