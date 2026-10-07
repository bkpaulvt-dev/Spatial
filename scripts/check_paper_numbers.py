"""Check that numbers quoted in paper/main.tex match results/paper_numbers*.json.

Each claim = (text that must appear in main.tex, value computed from the JSON, decimals).
Run after scripts/paper_numbers.py and scripts/paper_v2.py.
"""
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
v1 = json.load(open(os.path.join(ROOT, "results", "paper_numbers.json")))
v2 = json.load(open(os.path.join(ROOT, "results", "paper_numbers_v2.json")))
tex = re.sub(r"\s+", " ", open(os.path.join(ROOT, "paper", "main.tex")).read())
L, M, P, G = v2["lottery"], v2["mclust"], v2["pooled"], v2["clustering_gain"]
f = lambda x, d=3: f"{x:.{d}f}"
rng = lambda *xs: f"{min(xs):.2f}--{max(xs):.2f}"
claims = [
 ("HiSTaR median DLPFC", "median ARI over the twelve DLPFC sections of " + f(v1["bench_histar"]["median_slice"])),
 ("HiSTaR mean DLPFC", "(mean " + f(v1["bench_histar"]["mean"])),
 ("HiSTaR CI", f"CI {f(v1['bench_histar']['ci_lo'])}--{f(v1['bench_histar']['ci_hi'])}"),
 ("HiSTaR deterministic", "(" + f(v1["bench_histar_deterministic"]["mean"]) + ")"),
 ("HiSTaR + R mclust DLPFC", f(sum(1 for _ in [0]) and 0.449)),   # see check below
 ("lottery n", f"{v2['lottery_all']['n_embeddings']} fixed embeddings"),
 ("lottery mean range", f"changed ARI by {f(v2['lottery_all']['mean_range'],2)} on average"),
 ("lottery max range", f"up to {f(v2['lottery_all']['max_range'],2)}"),
 ("oracle inflation", f"inflate results by {f(v2['lottery_all']['oracle_minus_single'],2)}"),
 ("ranges HiSTaR/AnisoST DLPFC", rng(L['dlpfc/histar']['mean_range'], L['dlpfc/anisost']['mean_range']) + " for HiSTaR and AnisoST on DLPFC"),
 ("ranges STARmap", rng(L['starmap/histar']['mean_range'], L['starmap/anisost']['mean_range']) + " on STARmap"),
 ("ranges MERFISH", rng(L['merfish/histar']['mean_range'], L['merfish/anisost']['mean_range']) + " on MERFISH"),
 ("GraphST ranges", f"({f(L['dlpfc/graphst']['mean_range'],2)} on DLPFC, {f(L['starmap/graphst']['mean_range'],2)} on STARmap, {f(L['merfish/graphst']['mean_range'],2)} on MERFISH)"),
 ("permute DLPFC", rng(M['dlpfc/histar/permute']['mean_range'], M['dlpfc/anisost/permute']['mean_range']) + " on average within an embedding on DLPFC (up to " + f(max(M[f'dlpfc/{m}/permute']['max_range'] for m in ('histar','anisost')),2)),
 ("permute MERFISH", rng(M['merfish/histar/permute']['mean_range'], M['merfish/anisost/permute']['mean_range']) + " on MERFISH"),
 ("frac >0.05", f"{round(100*M['dlpfc/histar/permute']['frac_runs_dARI_gt_0.05'])}--{round(100*M['dlpfc/anisost/permute']['frac_runs_dARI_gt_0.05'])}\\% of the permutations"),
 ("frac GraphST", f"{round(100*M['dlpfc/graphst/permute']['frac_runs_dARI_gt_0.05'])}\\% for GraphST"),
 ("jitter STARmap HiSTaR", f"by {f(M['starmap/histar/jitter1pct']['mean_range'],2)} on average (up to {f(M['starmap/histar/jitter1pct']['max_range'],2)})"),
 ("mclust vs best20", f"lower mean ARI ({f(v2['mclust_vs_sklearn']['mean_ARI_mclust'],2)}) than the best-likelihood fit of 20 random starts ({f(v2['mclust_vs_sklearn']['mean_ARI_best20'],2)})"),
 ("mclust LL frac", f"only {round(100*v2['mclust_vs_sklearn']['frac_mclust_ll_ge_best20'])}\\% of cases"),
 ("gain HiSTaR", f"HiSTaR's mean ARI by {f(G['histar']['delta'])} ({G['histar']['wins']}/{G['histar']['n']} sections, $p={f(G['histar']['p'])}$)"),
 ("gain GraphST", f"GraphST's by {f(G['graphst']['delta'])} ({G['graphst']['wins']}/{G['graphst']['n']}, $p={f(G['graphst']['p'],2)}$)"),
 ("gain BANKSY", f"(+{f(G['banksy_l0.8']['delta'])}, {G['banksy_l0.8']['wins']}/{G['banksy_l0.8']['n']}, $p={f(G['banksy_l0.8']['p'],2)}$"),
 ("rho positive", rng(min(L[k]['median_rho'] for k in ('dlpfc/histar','dlpfc/anisost','starmap/histar','starmap/anisost')), max(L[k]['median_rho'] for k in ('dlpfc/histar','dlpfc/anisost','starmap/histar','starmap/anisost')))),
 ("rho MERFISH", f"(${f(L['merfish/anisost']['median_rho'],2)}$ to ${f(L['merfish/histar']['median_rho'],2)}$)"),
 ("lin means", f"(DLPFC {f(v2['means']['dlpfc']['linear_diffusion'])}, STARmap {f(v2['means']['starmap']['linear_diffusion'])}, MERFISH {f(v2['means']['merfish']['linear_diffusion'])})"),
 ("lin vs histar", f"(+{f(P['linear_diffusion_vs_histar']['delta'])}, {P['linear_diffusion_vs_histar']['wins']}/20 sections, Holm-adjusted $p={f(P['linear_diffusion_vs_histar']['p_holm'])}$)"),
 ("lin vs graphst", f"(+{f(P['linear_diffusion_vs_graphst']['delta'])}, {P['linear_diffusion_vs_graphst']['wins']}/20, adjusted $p={f(P['linear_diffusion_vs_graphst']['p_holm'])}$)"),
 ("lin vs graphst robust", f"(+{f(P['linear_diffusion_vs_graphst+robust']['delta'])}, {P['linear_diffusion_vs_graphst+robust']['wins']}/20, adjusted $p={f(P['linear_diffusion_vs_graphst+robust']['p_holm'])}$)"),
 ("lin vs spagcn", f"SpaGCN (+{f(P['linear_diffusion_vs_spagcn']['delta'])}, {P['linear_diffusion_vs_spagcn']['wins']}/20"),
 ("graphst refined", f"(DLPFC {f(v2['means']['dlpfc']['graphst_refined'])}, STARmap {f(v2['means']['starmap']['graphst_refined'])}, MERFISH {f(v2['means']['merfish']['graphst_refined'])})"),
 ("lin vs histar robust", f"(+{f(P['linear_diffusion_vs_histar+robust']['delta'])}, {P['linear_diffusion_vs_histar+robust']['wins']}/20, adjusted $p={f(P['linear_diffusion_vs_histar+robust']['p_holm'])}$)"),
 ("lin vs banksy", f"(+{f(min(P['linear_diffusion_vs_banksy_l0.8+robust']['delta'],P['linear_diffusion_vs_banksy_l0.8']['delta']))} to +{f(max(P['linear_diffusion_vs_banksy_l0.8+robust']['delta'],P['linear_diffusion_vs_banksy_l0.8']['delta']))}, adjusted $p={f(P['linear_diffusion_vs_banksy_l0.8']['p_holm'])}$)"),
 ("HiSTaR seed SD", f"{f(v2['seed_sd']['dlpfc']['histar'])} on DLPFC and {f(v2['seed_sd']['starmap']['histar'],2)} on STARmap"),
 ("AnisoST vs lin DLPFC", f"({f(v2['means']['dlpfc']['anisost'])} vs {f(v2['means']['dlpfc']['linear_diffusion'])})"),
 ("AnisoST vs lin MERFISH", f"({f(v2['means']['merfish']['anisost'])} vs {f(v2['means']['merfish']['linear_diffusion'])})"),
 ("boundary", f"by {f(v1['boundary_acc_boundary']['delta'])} ({v1['boundary_acc_boundary']['wins']}/12 sections, $p={f(v1['boundary_acc_boundary']['p'])}$"),
]
# HiSTaR clustered with R mclust (seed-0 embeddings) is computed from the mclust results directly
import glob, pandas as pd
mc = pd.concat([pd.read_csv(p) for p in glob.glob(os.path.join(ROOT, "results", "mclust_lottery_*.csv"))])
h = mc[(mc.kind == "base") & (mc.dataset == "dlpfc") & (mc.method == "histar")].ARI.mean()
claims[4] = ("HiSTaR + R mclust DLPFC", f"and {h:.3f} (mean, seed 0)")
# mclust default vs best-of-20, from unrounded values (the JSON stores 3 decimals; rounding twice is wrong)
lt = pd.DataFrame([dict(dataset=r.get("dataset", "dlpfc"), method=r["method"], slice=str(r["slice"]), best=r["ARI_bestll"])
                   for r in map(json.loads, open(os.path.join(ROOT, "results", "clustering_lottery.jsonl")))])
mb = mc[mc.kind == "base"].assign(slice=lambda x: x["slice"].astype(str)).merge(lt, on=["dataset", "method", "slice"])
i = [n for n, _ in claims].index("mclust vs best20")
claims[i] = ("mclust vs best20", f"lower mean ARI ({mb.ARI.mean():.2f}) than the best-likelihood fit of 20 random starts ({mb.best.mean():.2f})")
bad = 0
for name, text in claims:
    ok = re.sub(r"\s+", " ", text) in tex
    bad += not ok
    print(("OK   " if ok else "MISMATCH ") + f"{name:<28} {text}")
gst = v2["time_median_s"]["dlpfc"]["graphst"] / 60
print(f"\n{len(claims) - bad}/{len(claims)} claims match.  (GraphST DLPFC median time: {gst:.0f} min; text says 23 min)")
