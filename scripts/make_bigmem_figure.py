"""Table and figure for the Stereo-seq big-memory rerun (results/benchmark_runs_bigmem.jsonl).

Writes docs/figures/bigmem_stereo.{pdf,png} and results/bigmem_stereo_table.{csv,md}. Re-run when more jobs finish; the last
record per job id wins, so a rerun of a failed job replaces its error row.
"""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CM = 1 / 2.54
INK, INK2, GRID = "#0b0b0b", "#4a4a4a", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 7, "axes.labelsize": 7.5, "axes.titlesize": 8,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
                     "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK, "axes.labelcolor": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "savefig.dpi": 600})
LAB = {"graphst": "GraphST", "nichepca": "NichePCA", "spatial_mgcn": "Spatial-MGCN", "deepst": "DeepST", "bass": "BASS"}
FAM = {"graphst": 1, "spatial_mgcn": 1, "deepst": 1, "nichepca": 2, "bass": 2}        # same families as make_figures_nar.py
FCOL = {1: ORANGE, 2: AQUA}
ORDER = ["bass", "nichepca", "graphst", "spatial_mgcn", "deepst"]

last = {}
for l in open(os.path.join(ROOT, "results", "benchmark_runs_bigmem.jsonl")):
    r = json.loads(l); last[r["id"]] = r
rows = []
for r in last.values():
    m, res = r.get("metrics") or {}, r.get("resources") or {}
    rows.append(dict(section=r["section"].replace("E10.5_", ""), method=r["method"], seed=r["seed"], status=r["status"],
                     ARI=m.get("ARI", np.nan), NMI=m.get("NMI", np.nan), macroF1=m.get("macro_F1", np.nan),
                     boundaryF1=m.get("boundary_F1", np.nan), hours=res.get("wall_s", np.nan) / 3600, peak_gb=res.get("peak_rss_gb", np.nan)))
d = pd.DataFrame(rows)
d["origin"] = "rerun"
# E2S1 DeepST seed 0 fitted under the 12 GB cap on the original machine and was never rerun: take it from the original benchmark.
# Its run time and memory come from another host, so they are left out of the time/RAM columns.
for l in open(os.path.join(ROOT, "results", "benchmark_runs.jsonl")):
    r = json.loads(l)
    if r["id"] == "stereo__E10.5_E2S1__deepst__s0" and r["status"] == "ok":
        m = r["metrics"]
        d.loc[len(d)] = dict(section="E2S1", method="deepst", seed=0, status="ok", ARI=m["ARI"], NMI=m["NMI"], macroF1=m["macro_F1"],
                             boundaryF1=m["boundary_F1"], hours=np.nan, peak_gb=np.nan, origin="original")
ok = d[d.status == "ok"]

g = ok.groupby(["section", "method"])
tab = g.agg(n=("seed", "size"), ARI_mean=("ARI", "mean"), ARI_sd=("ARI", "std"), NMI=("NMI", "mean"), macroF1=("macroF1", "mean"),
            boundaryF1=("boundaryF1", "mean"), hours=("hours", "mean"), peak_gb=("peak_gb", "max")).reset_index()
tab["_o"] = tab.method.map(ORDER.index)
tab = tab.sort_values(["section", "_o"]).drop(columns="_o")
failed = d[d.status != "ok"].groupby(["section", "method"]).size()
tab.to_csv(os.path.join(ROOT, "results", "bigmem_stereo_table.csv"), index=False)
with open(os.path.join(ROOT, "results", "bigmem_stereo_table.md"), "w") as f:
    f.write("| Section | Method | Seeds | ARI (mean ± sd) | NMI | Macro-F1 | Boundary F1 | Time (h) | Peak RAM (GB) |\n|---|---|---|---|---|---|---|---|---|\n")
    for _, t in tab.iterrows():
        f.write(f"| {t.section} | {LAB[t.method]} | {t.n} | {t.ARI_mean:.3f} ± {0 if np.isnan(t.ARI_sd) else t.ARI_sd:.3f} | {t.NMI:.3f} | "
                f"{t.macroF1:.3f} | {t.boundaryF1:.3f} | {t.hours:.2f} | {t.peak_gb:.1f} |\n")
    for (s, m), n in failed.items():
        f.write(f"| {s} | {LAB[m]} | 0/{n} | failed | – | – | – | – | – |\n")
    f.write("\nE2S1 DeepST: seeds 1-2 rerun on Deepmed2; seed 0 from the original benchmark machine (fitted under the 12 GB cap), "
            "so time and RAM are means over the two reruns.\n")
print(open(os.path.join(ROOT, "results", "bigmem_stereo_table.md")).read())

fig, ax = plt.subplots(1, 3, figsize=(17.5 * CM, 7.0 * CM), gridspec_kw=dict(wspace=0.55, bottom=0.3, width_ratios=[1.35, 1, 1]))
rng = np.random.RandomState(0)
e1 = ok[ok.section == "E1S1"]
for i, m in enumerate(ORDER):
    v = e1[e1.method == m]
    if v.empty:
        ax[0].text(0.01, i, "failed / pending", va="center", fontsize=6.5, color=INK2, style="italic"); continue
    ax[0].barh(i, v.ARI.mean(), height=0.62, color=FCOL[FAM[m]], alpha=0.28, lw=0)
    ax[0].scatter(v.ARI, i + rng.uniform(-0.12, 0.12, len(v)), s=14, color=FCOL[FAM[m]], ec="white", lw=0.5, zorder=3)
    ax[0].text(v.ARI.max() + 0.012, i, f"{v.ARI.mean():.2f}", va="center", fontsize=6.5, color=INK2)
e2 = ok[(ok.section == "E2S1") & (ok.method == "deepst")]
if len(e2):
    for _, q in e2.iterrows():   # filled = rerun on Deepmed2, hollow = original benchmark machine
        ax[0].scatter(q.ARI, 4.38, s=16, marker="D", color=FCOL[1] if q.origin == "rerun" else "white", ec=FCOL[1], lw=0.9, zorder=3)
    ax[0].text(e2.ARI.max() + 0.015, 4.38, f"E2S1 (n=3), mean {e2.ARI.mean():.2f}", va="center", fontsize=6, color=INK2)
ax[0].set_yticks(range(len(ORDER))); ax[0].set_yticklabels([LAB[m] for m in ORDER]); ax[0].invert_yaxis()
ax[0].set_xlim(0, 0.52); ax[0].set_xlabel("ARI"); ax[0].set_title("Accuracy (E1S1 bars; E2S1 diamonds)", loc="left")
ax[0].xaxis.grid(True, color=GRID, lw=0.5); ax[0].set_axisbelow(True)

for k, (col, lab, title, log) in enumerate([("hours", "Wall time per job (h, log scale)", "Run time", True),
                                           ("peak_gb", "Peak RAM per job (GB)", "Memory", False)], start=1):
    for i, m in enumerate(ORDER):
        v = e1[e1.method == m][col]
        if v.empty: continue
        ax[k].plot([v.mean()] * 2, [i - 0.3, i + 0.3], color=FCOL[FAM[m]], lw=1.4, zorder=2)   # mean tick (no bars on a log axis)
        ax[k].scatter(v, i + rng.uniform(-0.12, 0.12, len(v)), s=14, color=FCOL[FAM[m]], ec="white", lw=0.5, zorder=3)
    ax[k].set_yticks(range(len(ORDER))); ax[k].set_yticklabels([] if k else [LAB[m] for m in ORDER]); ax[k].invert_yaxis()
    ax[k].set_xlabel(lab); ax[k].set_title(title, loc="left"); ax[k].xaxis.grid(True, color=GRID, lw=0.5); ax[k].set_axisbelow(True)
    if log: ax[k].set_xscale("log")
ax[2].axvline(30, color=INK2, lw=0.6, ls=(0, (3, 2))); ax[2].text(29.5, 4.45, "30 GB cap", ha="right", fontsize=6, color=INK2)
ax[2].set_xlim(0, 36)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([], [], marker="s", ls="", color=FCOL[1], alpha=0.6, label="Deep graph encoders"),
                    Line2D([], [], marker="s", ls="", color=FCOL[2], alpha=0.6, label="Statistical / neighbourhood"),
                    Line2D([], [], marker="o", ls="", color=INK2, ms=3.5, label="single seed"),
                    Line2D([], [], marker="D", ls="", color=INK2, ms=3.5, label="E2S1 seed, rerun"),
                    Line2D([], [], marker="D", ls="", mfc="white", mec=INK2, ms=3.5, label="E2S1 seed 0, original machine")],
           loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.suptitle("Stereo-seq MOSTA E10.5: memory-capped jobs rerun on a high-memory CPU host (Deepmed2) + E2S1 seed 0 from the original run", x=0.01, ha="left", fontsize=7.5, y=1.02)
out = os.path.join(ROOT, "docs", "figures")
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(out, f"bigmem_stereo.{ext}"), bbox_inches="tight")
print("saved", out)

# full metric tables (every metric, per seed and mean), E2S1 DeepST seed 0 taken from the original benchmark
full = {}
for fn in ("benchmark_runs.jsonl", "benchmark_runs_bigmem.jsonl"):          # bigmem last: it wins over the old OOM records
    for l in open(os.path.join(ROOT, "results", fn)):
        r = json.loads(l)
        if r["dataset"] == "stereo" and r["status"] == "ok" and (r["id"] in last and last[r["id"]]["status"] == "ok"
                                                                  or r["id"] == "stereo__E10.5_E2S1__deepst__s0"):
            full[r["id"]] = dict(section=r["section"][-4:], method=r["method"], seed=r["seed"], K=r["K"], k_found=r.get("k_found"),
                                 origin="original" if fn == "benchmark_runs.jsonl" else "rerun", **r["metrics"],
                                 hours=(r.get("resources") or {}).get("wall_s", np.nan) / 3600,
                                 peak_rss_gb=(r.get("resources") or {}).get("peak_rss_gb", np.nan))
fd = pd.DataFrame(full.values())
fd["_o"] = fd.method.map(ORDER.index); fd = fd.sort_values(["section", "_o", "seed"]).drop(columns="_o")
fd.to_csv(os.path.join(ROOT, "results", "bigmem_stereo_full_per_seed.csv"), index=False)
fm = fd.groupby(["section", "method"], sort=False).mean(numeric_only=True).drop(columns="seed")
fm["n"] = fd.groupby(["section", "method"], sort=False).size()
fm.loc[("E2S1", "deepst"), ["hours", "peak_rss_gb"]] = fd[(fd.section == "E2S1") & (fd.origin == "rerun")][["hours", "peak_rss_gb"]].mean().values
fm.to_csv(os.path.join(ROOT, "results", "bigmem_stereo_full_mean.csv"))
