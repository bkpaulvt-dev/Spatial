"""Phase 1 baseline: CPA (Lotfollahi et al. 2023, cpa-tools 0.8.8) on the fixed Norman folds.

Same cells, folds (results/phase1/splits.json), train-only HVGs, truth profiles and metrics as
scripts/phase1_norman.py. CPA trains on raw counts (NB loss) from controls, all singles and the
fold's training doubles. As in the CPA Norman tutorial, CPA's own validation set (for early
stopping and best-epoch restore) is a random 10% of cells from the training conditions; the
fold's validation doubles are left out entirely, as for CIPHER. (Validating CPA on the unseen
validation doubles made its metric peak at epoch 5, before its autoencoder pretraining ends.)
Hyperparameters follow the tutorial; training runs at least 70 epochs (pretraining + warm-ups).

Prediction is counterfactual: control cells are encoded and given the test pair, so CPA never
sees the held-out cells. Like our truth profiles, the prediction is log1p of the mean over
cells of 1e4 * mu / sum(mu).

Run with the CPA environment:
    .venv-cpa/bin/python scripts/phase1_cpa.py --folds 0 --seeds 0 1 2 3 4 --max-cells 0
Output: <outdir>/fold{k}_cpa.jsonl (picked up by scripts/phase1_summary.py).
"""
import argparse, json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from phase1_norman import load_raw, make_data, profiles, metrics, baselines  # noqa: E402

MODEL_PARAMS = {
    "n_latent": 32, "recon_loss": "nb", "doser_type": "linear",
    "n_hidden_encoder": 256, "n_layers_encoder": 4, "n_hidden_decoder": 256, "n_layers_decoder": 2,
    "use_batch_norm_encoder": True, "use_layer_norm_encoder": False,
    "use_batch_norm_decoder": False, "use_layer_norm_decoder": False,
    "dropout_rate_encoder": 0.2, "dropout_rate_decoder": 0.0, "variational": False,
}
TRAINER_PARAMS = {
    "n_epochs_kl_warmup": None, "n_epochs_pretrain_ae": 50, "n_epochs_adv_warmup": 10,
    "n_epochs_mixup_warmup": 10, "mixup_alpha": 0.1, "adv_steps": 2, "n_hidden_adv": 64,
    "n_layers_adv": 2, "use_batch_norm_adv": True, "use_layer_norm_adv": False,
    "dropout_rate_adv": 0.3, "reg_adv": 20.0, "pen_adv": 20.0, "lr": 3e-4, "wd": 4e-7,
    "adv_lr": 3e-4, "adv_wd": 4e-7, "adv_loss": "cce", "doser_lr": 3e-4, "doser_wd": 4e-7,
    "do_clip_grad": False, "gradient_clip_value": 1.0, "step_size_lr": 45,
}


def cpa_adata(d, split_of, seed):
    import anndata as ad
    import pandas as pd
    cond = ["ctrl" if c == "control" else c for c in d.conds]
    obs = pd.DataFrame({"condition": cond,
                        "dose": ["+".join(["1.0"] * len(c.split("+"))) for c in cond],
                        "cell_type": "K562",
                        "split": [split_of.get(c, "train") for c in d.conds]},
                       index=[f"c{i}" for i in range(len(cond))])
    var = pd.DataFrame(index=list(d.genes))
    tr = np.where(obs["split"].values == "train")[0]
    rng = np.random.default_rng(seed)
    obs.iloc[rng.choice(tr, len(tr) // 10, replace=False), obs.columns.get_loc("split")] = "valid"
    # dense counts: scvi data loading from sparse rows is the bottleneck on a busy CPU
    return ad.AnnData(d.X.toarray(), obs=obs, var=var)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5ad", default="data/perturb/NormanWeissman2019_filtered.h5ad")
    ap.add_argument("--outdir", default="results/phase1_full")
    ap.add_argument("--splits", default="results/phase1/splits.json")
    ap.add_argument("--workdir", default="results/cache/cpa")
    ap.add_argument("--folds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--max-cells", type=int, default=0)
    ap.add_argument("--max-epochs", type=int, default=2000)
    ap.add_argument("--n-ctrl-pred", type=int, default=2000, help="control cells used per prediction")
    args = ap.parse_args()
    import scvi
    import cpa

    os.makedirs(args.outdir, exist_ok=True)
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
        split_of = {**{c: "unused" for c in val}, **{c: "ood" for c in test}}
        ctrl_all = np.where(d.conds == "control")[0]
        rows = []
        for seed in args.seeds:
            t = time.time()
            scvi.settings.seed = seed
            cpa.CPA.pert_encoder = None          # fresh perturbation encoding per run
            a = cpa_adata(d, split_of, seed)
            cpa.CPA.setup_anndata(a, perturbation_key="condition", control_group="ctrl",
                                  dosage_key="dose", categorical_covariate_keys=["cell_type"],
                                  is_count_data=True, max_comb_len=2)
            m = cpa.CPA(a, split_key="split", train_split="train", valid_split="valid",
                        test_split="ood", seed=seed, **MODEL_PARAMS)
            m.train(max_epochs=args.max_epochs, use_gpu=True, batch_size=2048,
                    plan_kwargs=TRAINER_PARAMS, early_stopping_patience=5, check_val_every_n_epoch=5,
                    min_epochs=TRAINER_PARAMS["n_epochs_pretrain_ae"] + 20,
                    save_path=os.path.join(args.workdir, f"fold{k}_seed{seed}"))
            rng = np.random.default_rng(seed)
            cidx = rng.choice(ctrl_all, min(args.n_ctrl_pred, len(ctrl_all)), replace=False)
            for c in test:
                q = a[cidx].copy()
                q.obs["condition"] = c
                q.obs["dose"] = "1.0+1.0"
                q.obs["split"] = "ood"
                cpa.CPA.setup_anndata(q, perturbation_key="condition", control_group="ctrl",
                                      dosage_key="dose", categorical_covariate_keys=["cell_type"],
                                      is_count_data=True, max_comb_len=2)
                m.predict(q, batch_size=2048, n_samples=1)
                mu = np.asarray(q.obsm["CPA_pred"], dtype=np.float64)
                p = np.log1p((1e4 * mu / mu.sum(1, keepdims=True)).mean(0))
                a_, b_ = c.split("+")
                r = metrics(p, prof[c], ctrl, prof[a_], prof[b_], mp)
                r.update(method="cpa", fold=k, seed=seed, cond=c, selected=None, val_mse_de20=None,
                         n_genes=len(d.genes), n_cells=int(d.X.shape[0]))
                rows.append(r)
            print(f"[fold {k} seed {seed}] CPA done ({time.time() - t:.0f}s)", flush=True)
        with open(os.path.join(args.outdir, f"fold{k}_cpa.jsonl"), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
