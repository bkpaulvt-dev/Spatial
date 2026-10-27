"""Phase 1 baseline: GEARS (Roohani et al. 2024) on the fixed Norman folds.

Same cells, folds (results/phase1/splits.json), train-only HVGs, truth profiles and metrics as
scripts/phase1_norman.py. GEARS trains on controls, all singles and the fold's training doubles,
and picks its best epoch on the fold's validation doubles (its built-in rule, val DE MSE).

GEARS predicts the mean of log1p-normalised expression over control cells, whereas our profiles
are log1p of the mean normalised expression. We therefore score GEARS's predicted change:
    pred = ctrl_profile + (gears_pred - mean log1p expression of control cells)

GEARS can only perturb genes in its GO graph. Two Norman genes are not in it (IER5L, KIAA1804);
cells whose perturbation involves them are dropped for GEARS, and the one held-out pair that
needs them (IER5L+LYL1, fold 0 test) gets no GEARS score.

Run with the GEARS environment:
    .venv-gears/bin/python scripts/phase1_gears.py --folds 0 --seeds 0 1 2 3 4 --max-cells 0
Output: <outdir>/fold{k}_gears.jsonl (picked up by scripts/phase1_summary.py).
"""
import argparse, json, os, pickle, random, sys, time
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(__file__))
from phase1_norman import load_raw, make_data, profiles, metrics, baselines  # noqa: E402


def gears_adata(d, keep):
    import anndata as ad
    import pandas as pd
    L = d.lib[keep]
    X = sp.diags(1e4 / L) @ d.X[keep]
    X = sp.csr_matrix(X, dtype=np.float32)
    X.data = np.log1p(X.data)
    cond = ["ctrl" if c == "control" else (c if "+" in c else c + "+ctrl") for c in d.conds[keep]]
    obs = pd.DataFrame({"condition": cond, "cell_type": "K562"},
                       index=[f"c{i}" for i in range(len(cond))])
    var = pd.DataFrame({"gene_name": list(d.genes)}, index=list(d.genes))
    return ad.AnnData(X, obs=obs, var=var)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5ad", default="data/perturb/NormanWeissman2019_filtered.h5ad")
    ap.add_argument("--outdir", default="results/phase1_full")
    ap.add_argument("--splits", default="results/phase1/splits.json")
    ap.add_argument("--workdir", default="results/cache/gears")
    ap.add_argument("--folds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--max-cells", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--preddir", default=None,
                    help="if set, save predicted profiles to <preddir>/fold{k}_preds.npz")
    args = ap.parse_args()
    import torch
    from gears import PertData, GEARS
    from gears.utils import dataverse_download

    os.makedirs(args.outdir, exist_ok=True)
    os.makedirs(args.workdir, exist_ok=True)
    splits = json.load(open(args.splits))
    b, conds = load_raw(args.h5ad, max_cells=args.max_cells, n_ctrl=4000 if args.max_cells else 0)
    for k in args.folds:
        s = splits[str(k)]
        test, val, train_d = s["test"], s["val"], s["train"]
        d = make_data(b, conds, np.where(~np.isin(conds, test))[0])
        prof = profiles(d)
        ctrl = prof["control"]
        singles = [c for c in prof if c != "control" and "+" not in c]
        _, mp = baselines(prof, train_d, singles + train_d, test, ctrl)

        t = time.time()
        np.random.seed(k)
        gdir = os.path.join(args.workdir, "gears_data")
        pdat = PertData(gdir)
        ep = os.path.join(gdir, "essential_all_data_pert_genes.pkl")
        dataverse_download("https://dataverse.harvard.edu/api/access/datafile/6934320", ep)
        graph_genes = set(pickle.load(open(ep, "rb"))) & set(pdat.gene2go)
        ok = lambda c: c == "control" or all(g in graph_genes for g in c.split("+"))  # noqa: E731
        dropped = sorted(c for c in prof if not ok(c))
        print(f"[fold {k}] conditions dropped for GEARS (genes not in its graph): {dropped}", flush=True)
        a = gears_adata(d, np.array([ok(c) for c in d.conds]))
        ctrl_meanlog = np.asarray(a.X[(a.obs["condition"] == "ctrl").values].mean(0)).ravel()
        pdat.new_data_process(dataset_name=f"norman_full_f{k}" if not args.max_cells else f"norman_sub_f{k}", adata=a)
        test_ok = [c for c in test if ok(c)]
        split_path = os.path.join(pdat.dataset_path, f"split_fold{k}.pkl")
        pickle.dump({"train": ["ctrl"] + [c + "+ctrl" for c in singles if ok(c)] + [c for c in train_d if ok(c)],
                     "val": [c for c in val if ok(c)], "test": test_ok}, open(split_path, "wb"))
        pdat.prepare_split(split="custom", split_dict_path=split_path)
        print(f"[fold {k}] GEARS data ready ({time.time() - t:.0f}s)", flush=True)

        rows = []
        seed_preds_all = {}  # cond -> list of pred arrays across seeds
        for seed in args.seeds:
            t = time.time()
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
            pdat.get_dataloader(batch_size=args.batch_size, test_batch_size=128)
            m = GEARS(pdat, device=args.device)
            m.model_initialize(hidden_size=args.hidden)
            m.train(epochs=args.epochs)
            pred = m.predict([c.split("+") for c in test_ok])
            for c in test_ok:
                p = ctrl + (pred["_".join(c.split("+"))] - ctrl_meanlog)
                seed_preds_all.setdefault(c, []).append(p)
                a_, b_ = c.split("+")
                r = metrics(p, prof[c], ctrl, prof[a_], prof[b_], mp)
                r.update(method="gears", fold=k, seed=seed, cond=c, selected=None, val_mse_de20=None,
                         n_genes=len(d.genes), n_cells=int(d.X.shape[0]))
                rows.append(r)
            print(f"[fold {k} seed {seed}] GEARS done ({time.time() - t:.0f}s)", flush=True)
        with open(os.path.join(args.outdir, f"fold{k}_gears.jsonl"), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        if args.preddir:
            # Merge GEARS predictions into existing fold npz (pred|gears|<cond> keys)
            npz_path = os.path.join(args.preddir, f"fold{k}_preds.npz")
            if os.path.exists(npz_path):
                existing = dict(np.load(npz_path, allow_pickle=True))
                target_genes = list(existing["genes"])
            else:
                existing = {"genes": np.asarray(d.genes), "test": np.asarray(test), "ctrl": ctrl}
                target_genes = list(d.genes)
            gears_genes = list(d.genes)
            # build index map: target_genes[i] -> gears_genes position (or -1)
            g2i = {g: i for i, g in enumerate(gears_genes)}
            idx = [g2i.get(g, -1) for g in target_genes]
            for c in test_ok:
                avg = np.mean(seed_preds_all[c], axis=0)  # seed-averaged prediction
                aligned = np.full(len(target_genes), np.nan, dtype=np.float32)
                for j, gi in enumerate(idx):
                    if gi >= 0:
                        aligned[j] = avg[gi]
                existing[f"pred|gears|{c}"] = aligned
            os.makedirs(args.preddir, exist_ok=True)
            np.savez_compressed(npz_path, **existing)
            print(f"[fold {k}] GEARS preds merged into {npz_path}", flush=True)


if __name__ == "__main__":
    main()
