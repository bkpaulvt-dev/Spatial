"""Primary analysis of the domain-size simulation, exactly as pre-registered in docs/PREREGISTERED_SIM.md.

Reads results/newdata_runs_*.jsonl (newest record per run id, status ok) and writes NEW files only:
  results/newdata_sim_delta.csv        Delta = ARI(linear_diffusion) - ARI(pca_gmm) per setting with a 95% bootstrap interval over replicates
  results/newdata_sim_ari_table.csv    mean ARI per method and setting (+ number of jobs)
  results/newdata_stats_sim.json       H1 / H2 verdicts, ceiling/floor check, best three per setting, coverage
  results/newdata_sim_summary.md       the same in words
  docs/figures/newdata_sim_ari.png     ARI of linear diffusion, PCA and the best three methods versus domain size
Missing cells (jobs not run yet) are reported as such, never imputed. Re-run at any time.
"""
import glob, json, os, re
import numpy as np, pandas as pd

ROOT = os.environ.get("NEWDATA_ROOT") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # NEWDATA_ROOT: tests only
R = lambda *p: os.path.join(ROOT, "results", *p)
MARGIN = 0.03; NBOOT = 10000; SEED = 20261104
# Amendment (2026-11-04, cost only): tier-3 methods ran a REDUCED design (seed 0, replicate 0, 9 tissues). They are never pooled with the
# full design (tiers 1-2: 45 tissues x 3 seeds) in one interval; the headline contrast uses linear diffusion and PCA (full design) only.
TIER3 = ("bass", "deepst", "spaceflow", "stagate", "graphst", "spatial_mgcn", "bayesspace", "ccst")
M_A, W_B = [1, 2, 4, 7], [3, 5, 8, 12, 20]


def load():
    last = {}
    for f in sorted(glob.glob(R("newdata_runs_*.jsonl"))):
        for l in open(f):
            r = json.loads(l); last[r["id"]] = r
    rows = []
    for r in last.values():
        if r["status"] != "ok" or r["dataset"] not in ("sim_bands", "sim_blocks"):
            continue
        t, rep = re.match(r"([mw])(\d+)_r(\d+)", r["section"]).group(1, 2), int(re.match(r"([mw])(\d+)_r(\d+)", r["section"]).group(3))
        rows.append(dict(geometry="A" if r["dataset"] == "sim_bands" else "B", param=int(t[1]), rep=rep, seed=r["seed"], method=r["method"],
                         ari=r["metrics"]["ARI"], ari_matched=(r.get("metrics_matched") or {}).get("ARI", np.nan)))
    return pd.DataFrame(rows), last


def boot_ci(x, rng):
    x = np.asarray(x, float)
    if len(x) == 0: return (np.nan, np.nan, np.nan)
    b = rng.choice(x, size=(NBOOT, len(x)), replace=True).mean(1)
    return float(x.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def diff_ci(xa, xb, rng):
    """Mean(xa) - mean(xb), 95% interval; replicate indices resampled jointly (paired by replicate index) over the replicates present in both."""
    n = min(len(xa), len(xb))
    if n < 2: return (np.nan, np.nan, np.nan)
    d = np.asarray(xa[:n]) - np.asarray(xb[:n]); idx = rng.integers(0, n, size=(NBOOT, n))
    b = d[idx].mean(1)
    return float(d.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main():
    d, last = load(); rng = np.random.default_rng(SEED)
    if d.empty:
        print("no simulation records yet"); return
    settings = [("A", m) for m in M_A] + [("B", w) for w in W_B]
    # Delta per setting and replicate (mean over seeds present for both methods)
    per = {}
    for g, p in settings:
        s = d[(d.geometry == g) & (d.param == p)]
        lde, pca = s[s.method == "linear_diffusion"].groupby("rep").ari.mean(), s[s.method == "pca_gmm"].groupby("rep").ari.mean()
        reps = sorted(set(lde.index) & set(pca.index)); per[(g, p)] = np.array([lde[r] - pca[r] for r in reps])
    rows = []
    for (g, p), v in per.items():
        m, lo, hi = boot_ci(v, rng); rows.append(dict(geometry=g, param=p, n_replicates=len(v), delta=m, ci_low=lo, ci_high=hi))
    delta = pd.DataFrame(rows); delta.to_csv(R("newdata_sim_delta.csv"), index=False)
    # mean ARI per method and setting
    tab = (d.groupby(["method", "geometry", "param"]).ari.agg(["mean", "size"]).reset_index().rename(columns={"mean": "ari_mean", "size": "n_jobs"}))
    tab["design"] = np.where(tab.method.isin(TIER3), "reduced (seed 0, replicate 0)", "full (5 replicates x 3 seeds)")
    tab.to_csv(R("newdata_sim_ari_table.csv"), index=False)
    # hypotheses
    out = {"n_records": int(len(d)), "settings_with_delta": int(sum(len(v) > 0 for v in per.values()))}
    dm = {k: (v.mean() if len(v) else np.nan) for k, v in per.items()}
    a1, a7 = per[("A", 1)], per[("A", 7)]
    h1 = diff_ci(a1, a7, rng)
    seq = [dm[("A", m)] for m in M_A]
    mono = all(np.isfinite(seq)) and all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))
    v1 = ("supported" if h1[0] > MARGIN and h1[1] > 0 and mono else "contradicted" if h1[0] < -MARGIN and h1[2] < 0
          else "inconclusive") if np.isfinite(h1[0]) else "not computable yet"
    out["H1"] = dict(delta_m1_minus_m7=h1[0], ci=[h1[1], h1[2]], monotone_non_increasing=bool(mono), verdict=v1)
    b3 = per[("B", 3)]; h2 = diff_ci(b3, a7, rng)
    allm = [x for x in dm.values() if np.isfinite(x)]
    smallest = bool(len(allm) == 9 and dm[("B", 3)] == min(allm))
    bseq = [dm[("B", w)] for w in W_B]; bmono = all(np.isfinite(bseq)) and all(bseq[i] <= bseq[i + 1] for i in range(len(bseq) - 1))
    v2 = ("supported" if h2[0] < -MARGIN and h2[2] < 0 and smallest and bmono else "contradicted" if h2[0] > MARGIN and h2[1] > 0
          else "inconclusive") if np.isfinite(h2[0]) else "not computable yet"
    out["H2"] = dict(delta_B3_minus_A7=h2[0], ci=[h2[1], h2[2]], B3_is_smallest_of_nine=smallest, B_non_decreasing_in_w=bool(bmono), verdict=v2)
    ms = tab.groupby(["geometry", "param"]).ari_mean.agg(["min", "max"])
    full = tab.groupby("method").n_jobs.sum()
    out["ceiling_floor"] = ("uninformative: every mean ARI > 0.95 or < 0.10" if ((tab.ari_mean > 0.95) | (tab.ari_mean < 0.10)).all() else "ok (not all methods at ceiling or floor)")
    tf, tr = tab[~tab.method.isin(TIER3)], tab[tab.method.isin(TIER3)]
    out["best_three_full_design"] = {f"{g}{p}": tf[(tf.geometry == g) & (tf.param == p)].nlargest(3, "ari_mean")[["method", "ari_mean", "n_jobs"]].to_dict("records") for g, p in settings}
    out["reduced_design_ari"] = {f"{g}{p}": tr[(tr.geometry == g) & (tr.param == p)].sort_values("ari_mean", ascending=False)[["method", "ari_mean"]].to_dict("records") for g, p in settings}
    out["coverage_jobs_ok_per_method"] = {k: int(v) for k, v in full.items()}
    json.dump(out, open(R("newdata_stats_sim.json"), "w"), indent=1, default=float)
    with open(R("newdata_sim_summary.md"), "w") as f:
        f.write("# Domain-size simulation: primary analysis (pre-registered)\n\nGenerated by scripts/newdata_stats.py; incomplete cells are not imputed.\n\n")
        f.write(f"- Records used: {out['n_records']}; settings with a Delta: {out['settings_with_delta']} of 9. Ceiling/floor: {out['ceiling_floor']}.\n")
        f.write(f"- **H1** (advantage falls with narrower bands): Delta(m=1) - Delta(m=7) = {h1[0]:.3f} (95% CI {h1[1]:.3f} to {h1[2]:.3f}); monotone: {mono}; **{v1}**.\n")
        f.write(f"- **H2** (smallest for random blocks): Delta(B, w=3) - Delta(A, m=7) = {h2[0]:.3f} (95% CI {h2[1]:.3f} to {h2[2]:.3f}); w=3 smallest of nine: {smallest}; "
                f"non-decreasing in w: {bool(bmono)}; **{v2}**.\n\n| Geometry | Setting | Replicates | Delta (LD - PCA) | 95% CI |\n|---|---|---|---|---|\n")
        for _, r in delta.iterrows():
            f.write(f"| {r.geometry} | {'m' if r.geometry == 'A' else 'w'}={int(r.param)} | {int(r.n_replicates)} | {r.delta:.3f} | {r.ci_low:.3f} to {r.ci_high:.3f} |\n")
        f.write("\n(Headline contrast: FULL design, linear diffusion and PCA only.)\n\n## Tier-3 methods: REDUCED design (seed 0, replicate 0 of each setting; one tissue per cell, no interval)\n\n")
        if len(tr):
            pv = tr.pivot_table(index="method", columns=["geometry", "param"], values="ari_mean")
            f.write("| method | " + " | ".join(f"{g}:{p}" for g, p in pv.columns) + " |\n|---|" + "---|" * len(pv.columns) + "\n")
            for m, row in pv.iterrows():
                f.write(f"| {m} | " + " | ".join("" if np.isnan(v) else f"{v:.3f}" for v in row) + " |\n")
        else:
            f.write("not run yet\n")
    print(open(R("newdata_sim_summary.md")).read())
    figure(tab, d)


def figure(tab, d):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    tf, tr = tab[~tab.method.isin(TIER3)], tab[tab.method.isin(TIER3)]
    cands = [m for m in tf.method.unique() if m not in ("linear_diffusion", "pca_gmm")]
    top = tf[tf.method.isin(cands)].groupby("method").ari_mean.mean().nlargest(3).index.tolist()
    cols = {"linear_diffusion": "#2a78d6", "pca_gmm": "#5a5a5a"}; pal = ["#eb6834", "#1baf7a", "#8a5cd6"]
    for m, c in zip(top, pal): cols[m] = c
    rcols = dict(zip(sorted(tr.method.unique()), ["#eb6834", "#1baf7a", "#8a5cd6", "#c9a227", "#2a78d6", "#5a5a5a", "#b04a8a"]))
    fig, ax = plt.subplots(2, 2, figsize=(7.4, 5.4), sharey=True)
    for k, (g, xs, xl, ttl) in enumerate([("A", M_A, "band width (spot spacings, about 120 / 6m)", "A: layered bands"),
                                          ("B", W_B, "block side w (spot spacings)", "B: random blocks")]):
        x = [120 / (6 * m) for m in xs] if g == "A" else xs
        for m, c in cols.items():
            y = [tf[(tf.method == m) & (tf.geometry == g) & (tf.param == p)].ari_mean.mean() for p in xs]
            ax[0, k].plot(x, y, "-o", ms=3.5, lw=1.5 if m in ("linear_diffusion", "pca_gmm") else 1.0, color=c, label=m.replace("_", " "))
        for m, c in rcols.items():
            y = [tr[(tr.method == m) & (tr.geometry == g) & (tr.param == p)].ari_mean.mean() for p in xs]
            ax[1, k].plot(x, y, "--s", ms=3.5, lw=0.9, color=c, label=m.replace("_", " "))
        for r in (0, 1):
            ax[r, k].set_xscale("log"); ax[r, k].grid(axis="y", color="#e4e3df", lw=0.5); ax[r, k].spines[["top", "right"]].set_visible(False); ax[r, k].tick_params(labelsize=7)
        ax[0, k].set_title(ttl + ": FULL design (5 replicates x 3 seeds)", fontsize=8, loc="left"); ax[1, k].set_title(ttl + ": REDUCED design (seed 0, replicate 0)", fontsize=8, loc="left")
        ax[1, k].set_xlabel(xl, fontsize=8)
    ax[0, 0].set_ylabel("mean ARI", fontsize=8); ax[1, 0].set_ylabel("ARI (one tissue)", fontsize=8)
    ax[0, 1].legend(fontsize=6.5, frameon=False, loc="lower right"); ax[1, 1].legend(fontsize=6.5, frameon=False, loc="lower right")
    fig.suptitle("Domain-size simulation (K = 6, 14,400 spots): ARI versus domain size; tier-3 methods shown separately", fontsize=8.5, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "docs", "figures", "newdata_sim_ari.png"), dpi=200); print("saved figure")


if __name__ == "__main__":
    main()
