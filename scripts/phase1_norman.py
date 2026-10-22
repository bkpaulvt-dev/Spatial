"""Phase 1: clean evaluation of double-perturbation prediction on Norman et al. 2019.

Protocol (see docs/PAPER_PLAN.md, Phase 1)
* The 131 doubles are split once into 5 fixed test folds (results/phase1/splits.json).
* Inside each fold, 20% of the remaining doubles form a validation set. Learned methods
  train on singles + controls + the other training doubles; CIPHER's configuration is chosen
  per fold on validation MSE (top-20 DE), fixed in advance as the selection rule.
* Highly variable genes are selected from cells outside the test fold only.
* By default cells are subsampled (<=400 per condition, 4000 controls) to fit a 4-CPU machine;
  pass --max-cells 0 for the full data (GPU). --seeds runs every learned method once per seed.

Output: <outdir>/fold{k}.jsonl, one row per (method, test condition, seed); baselines have seed null.
"""
import argparse, json, os, sys, time
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cipher.data import PerturbData  # noqa: E402
from cipher.model import CIPHER  # noqa: E402

CONFIGS = {
    "cipher_direct": {"basal": False, "adversary": False, "direct": True},
    "cipher_nodirect": {"basal": False, "adversary": False},
}


def load_raw(path, max_cells=400, n_ctrl=4000, seed=0):
    import anndata as ad
    rng = np.random.default_rng(seed)
    a = ad.read_h5ad(path, backed="r")
    pert = a.obs["perturbation"].astype(str).values
    cells = []
    for c in np.unique(pert):
        idx = np.where(pert == c)[0]
        m = n_ctrl if c == "control" else max_cells
        if max_cells and len(idx) > m:
            idx = rng.choice(idx, m, replace=False)
        cells.append(idx)
    cells = np.sort(np.concatenate(cells))
    b = a[cells].to_memory()
    b.X = sp.csr_matrix(b.X)
    conds = np.array(["+".join(sorted(c.split("_"))) if c != "control" else "control"
                      for c in b.obs["perturbation"].astype(str)])
    return b, conds


def make_data(b, conds, hvg_cells, n_hvg=2000):
    import scanpy as sc
    units = sorted({g for c in np.unique(conds) if c != "control" for g in c.split("+")})
    sub = b[hvg_cells].copy()
    sc.pp.filter_genes(sub, min_cells=max(20, int(0.005 * sub.n_obs)))
    sc.pp.highly_variable_genes(sub, n_top_genes=n_hvg, flavor="seurat_v3")
    keep_names = set(sub.var_names[sub.var.highly_variable]) | set(units)
    keep = np.isin(b.var_names, list(keep_names))
    X = b.X[:, keep]
    ix = {u: i for i, u in enumerate(units)}
    P = -np.ones((b.n_obs, 2), dtype=np.int64)
    for n, c in enumerate(conds):
        if c != "control":
            for j, g in enumerate(c.split("+")):
                P[n, j] = ix[g]
    batch = b.obs["gemgroup"].astype(int).values - 1
    return PerturbData(sp.csr_matrix(X, dtype=np.float32), np.asarray(b.var_names[keep]), conds,
                       units, P, batch, {u: u for u in units})


def profiles(d):
    L = d.lib
    return {c: np.log1p(np.asarray(d.X[i].multiply(1e4 / L[i][:, None]).mean(0)).ravel())
            for c in np.unique(d.conds) for i in [np.where(d.conds == c)[0]]}


def corr(a, b):
    if np.std(a) < 1e-6 or np.std(b) < 1e-6:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def metrics(pred, true, ctrl, sA, sB, mp, n=20):
    dt, dp = true - ctrl, pred - ctrl
    de = np.argsort(-np.abs(dt))[:n]
    add = sA + sB - ctrl
    rt, rp = true - add, pred - add
    top_r = np.argsort(-np.abs(rt))[:n]
    # Systema-style: remove the average training-perturbation shift
    st, spd = true - mp, pred - mp
    de_s = np.argsort(-np.abs(st))[:n]
    return {"pearson_de20": corr(dp[de], dt[de]), "pearson_all": corr(dp, dt),
            "mse_de20": float(np.mean((dp[de] - dt[de]) ** 2)),
            "mse_all": float(np.mean((dp - dt) ** 2)),
            "dir_acc_de20": float(np.mean(np.sign(dp[de]) == np.sign(dt[de]))),
            "systema_pearson_de20": corr(spd[de_s], st[de_s]),
            "resid_corr_top20": corr(rp[top_r], rt[top_r]),
            "resid_mse_top20": float(np.mean((rp[top_r] - rt[top_r]) ** 2)),
            "resid_mse_all": float(np.mean((rp - rt) ** 2))}


def baselines(prof, train_d, train_conds, test, ctrl):
    out = {}
    mp = ctrl + np.mean([prof[c] - ctrl for c in train_conds], 0)
    # global and per-gene interaction models fitted on training doubles
    S, Y, PR = [], [], []
    for c in train_d:
        a, b = c.split("+")
        da, db = prof[a] - ctrl, prof[b] - ctrl
        S.append(da + db); PR.append(da * db); Y.append(prof[c] - ctrl)
    S, Y, PR = map(np.array, (S, Y, PR))
    alpha = float((S * Y).sum() / (S * S).sum())
    lam = 1.0
    G = S.shape[1]
    beta = np.zeros(G); gam = np.zeros(G)
    for g in range(G):  # ridge per gene: y = beta*s + gamma*a*b, shrunk to beta=alpha, gamma=0
        Xg = np.stack([S[:, g], PR[:, g]], 1)
        A = Xg.T @ Xg + lam * np.eye(2)
        coef = np.linalg.solve(A, Xg.T @ Y[:, g] + lam * np.array([alpha, 0.0]))
        beta[g], gam[g] = coef
    lin = {c: np.expm1(v) for c, v in prof.items()}
    for c in test:
        a, b = c.split("+")
        da, db = prof[a] - ctrl, prof[b] - ctrl
        out.setdefault("control", {})[c] = ctrl
        out.setdefault("mean_perturbation", {})[c] = mp
        out.setdefault("additive_log", {})[c] = ctrl + da + db
        out.setdefault("additive_lin", {})[c] = np.log1p(np.clip(lin[a] + lin[b] - lin["control"], 0, None))
        out.setdefault("scaled_additive", {})[c] = ctrl + alpha * (da + db)
        out.setdefault("pergene_interaction", {})[c] = ctrl + beta * (da + db) + gam * da * db
    return out, mp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5ad", default="data/perturb/NormanWeissman2019_filtered.h5ad")
    ap.add_argument("--outdir", default="results/phase1")
    ap.add_argument("--folds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--configs", nargs="*", default=list(CONFIGS))
    ap.add_argument("--seeds", type=int, nargs="+", default=None,
                    help="seeds for learned methods (default: one run with seed = fold)")
    ap.add_argument("--max-cells", type=int, default=400, help="cells per condition; 0 = all cells")
    ap.add_argument("--splits", default=None, help="splits.json (default: <outdir>/splits.json)")
    ap.add_argument("--device", default="cpu", help='e.g. "cpu", "cuda", "cuda:1"')
    ap.add_argument("--save-preds", action="store_true",
                    help="also save predicted and true profiles per fold (fold{k}_preds.npz), for Fig. 4")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    b, conds = load_raw(args.h5ad, max_cells=args.max_cells, n_ctrl=4000 if args.max_cells else 0)
    doubles = sorted(c for c in np.unique(conds) if "+" in c)
    sp_path = args.splits or os.path.join(args.outdir, "splits.json")
    if os.path.exists(sp_path):
        splits = json.load(open(sp_path))
    else:
        rng = np.random.default_rng(2026)
        order = list(rng.permutation(doubles))
        splits = {}
        for k in range(5):
            test = sorted(order[k::5])
            rest = [c for c in doubles if c not in test]
            val = sorted(np.random.default_rng(100 + k).choice(rest, len(rest) // 5, replace=False).tolist())
            splits[str(k)] = {"test": test, "val": val, "train": sorted(set(rest) - set(val))}
        json.dump(splits, open(sp_path, "w"), indent=1)
    for k in args.folds:
        s = splits[str(k)]
        test, val, train_d = s["test"], s["val"], s["train"]
        hvg_cells = np.where(~np.isin(conds, test))[0]
        d = make_data(b, conds, hvg_cells)
        prof = profiles(d)
        ctrl = prof["control"]
        singles = [c for c in prof if c != "control" and "+" not in c]
        train_idx = np.where(~np.isin(d.conds, test + val))[0]
        ctrl_idx = np.where(d.conds == "control")[0]
        base, mp = baselines(prof, train_d, singles + train_d, test, ctrl)
        rows = [(meth, None, pm, None, None) for meth, pm in base.items()]
        for seed in (args.seeds if args.seeds is not None else [k]):
            preds, val_score = {}, {}
            for name in args.configs:
                t = time.time()
                print(f"[fold {k} seed {seed}] {name}", flush=True)
                m = CIPHER(d, seed=seed, epochs=args.epochs, threads=args.threads, train_idx=train_idx,
                           device=args.device, verbose=False, **CONFIGS[name]).fit()
                vs = []
                for c in val:
                    a_, b_ = c.split("+")
                    p = np.log1p(m.predict_mean(c.split("+"), ctrl_idx))
                    vs.append(metrics(p, prof[c], ctrl, prof[a_], prof[b_], mp)["mse_de20"])
                val_score[name] = float(np.mean(vs))
                for c in test:
                    preds.setdefault(name, {})[c] = np.log1p(m.predict_mean(c.split("+"), ctrl_idx))
                print(f"   val mse_de20 {val_score[name]:.4f}  ({time.time() - t:.0f}s)", flush=True)
            best = min(val_score, key=val_score.get)
            preds["cipher_selected"] = preds[best]
            rows += [(meth, seed, pm, best if meth == "cipher_selected" else None, val_score.get(meth))
                     for meth, pm in preds.items()]
            print(f"[fold {k} seed {seed}] selected {best}", flush=True)
        with open(os.path.join(args.outdir, f"fold{k}.jsonl"), "w") as f:
            for meth, seed, pm, sel, vsc in rows:
                for c, p in pm.items():
                    a_, b_ = c.split("+")
                    r = metrics(p, prof[c], ctrl, prof[a_], prof[b_], mp)
                    r.update(method=meth, fold=k, seed=seed, cond=c, selected=sel,
                             val_mse_de20=vsc, n_genes=len(d.genes), n_cells=int(d.X.shape[0]))
                    f.write(json.dumps(r) + "\n")
        if args.save_preds:
            # seed-averaged predicted profiles per method, plus the true profiles needed downstream
            pm_all = {}
            for meth, seed, pm, sel, vsc in rows:
                for c, p in pm.items():
                    pm_all.setdefault(meth, {}).setdefault(c, []).append(p)
            out = {"genes": np.asarray(d.genes), "test": np.asarray(test), "ctrl": ctrl}
            for c in set(test) | {g for t in test for g in t.split("+")}:
                out[f"true|{c}"] = prof[c]
            for meth, pc in pm_all.items():
                for c, ps in pc.items():
                    out[f"pred|{meth}|{c}"] = np.mean(ps, 0)
            np.savez_compressed(os.path.join(args.outdir, f"fold{k}_preds.npz"), **out)
        print(f"[fold {k}] done", flush=True)


if __name__ == "__main__":
    main()
