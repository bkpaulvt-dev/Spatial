"""Revision V3 item 3b: score each Stereo-seq prediction of the cavity stage with and without the MOSTA 'Cavity' bins (scoring only; the
prediction and the graph are unchanged). Reads results/cavity_runs/<id>.npz (labels, labels_matched, valid). Writes results/v3_cavity.csv/.json.
python scripts/v3_cavity.py"""
import glob, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT, HERE]
from sklearn.metrics import adjusted_rand_score as ari
from spatialbench.data import load_section
from spatialbench import metrics as M

RUNS = os.path.join(ROOT, "results", "cavity_runs"); rows = []; cache = {}
for f in sorted(glob.glob(os.path.join(RUNS, "stereo__*__s0.npz"))):
    _, sec, m, _ = os.path.basename(f)[:-4].split("__")
    if sec not in cache:
        a = load_section("stereo", sec); t = a.obs["ground_truth"].to_numpy(dtype=object); cache[sec] = (t, M.valid_mask(t))
    truth, valid = cache[sec]; z = np.load(f, allow_pickle=True); cav = truth.astype(str) == "Cavity"
    for key, proto in (("labels", "default"), ("labels_matched", "matched")):
        if key not in z.files:
            continue
        lab = np.asarray(z[key]); keep = valid & ~cav
        rows.append(dict(section=sec, method=m, protocol=proto, ari_all=float(ari(truth[valid].astype(str), lab[valid])),
                         ari_no_cavity=float(ari(truth[keep].astype(str), lab[keep])), cavity_frac=float(cav[valid].mean())))
df = pd.DataFrame(rows)
if df.empty:
    print("no predictions yet"); sys.exit(0)
df["change"] = df.ari_no_cavity - df.ari_all
df.to_csv(os.path.join(ROOT, "results", "v3_cavity.csv"), index=False)
# primary protocol = matched where the method has an embedding, otherwise its own clustering
prim = df[df.protocol == "matched"].copy()
own = df[(df.protocol == "default") & ~df.method.isin(prim.method.unique())]
prim = pd.concat([prim, own])
mean = prim.groupby("method")[["ari_all", "ari_no_cavity", "change"]].mean().sort_values("ari_all", ascending=False)
rank_all = mean.ari_all.rank(ascending=False); rank_nc = mean.ari_no_cavity.rank(ascending=False)
out = {"n_predictions": int(len(prim)), "sections_per_method": prim.groupby("method").section.nunique().to_dict(),
       "means": mean.round(4).to_dict(orient="index"), "rank_linear_diffusion": {"all": float(rank_all.get("linear_diffusion", np.nan)),
       "no_cavity": float(rank_nc.get("linear_diffusion", np.nan)), "n_methods": int(len(mean))},
       "spearman_rank_change": float(rank_all.corr(rank_nc, method="spearman"))}
json.dump(out, open(os.path.join(ROOT, "results", "v3_cavity.json"), "w"), indent=1)
print(mean.round(3).to_string()); print(json.dumps({k: out[k] for k in ("rank_linear_diffusion", "spearman_rank_change", "n_predictions")}))
