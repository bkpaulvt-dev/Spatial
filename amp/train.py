"""Fine-tune ESM-2 with activity/toxicity/hemolysis heads on a homology-aware split.

    python -m amp.train --data peptides.csv --model facebook/esm2_t33_650M_UR50D --out runs/esm650_s0
    CUDA_VISIBLE_DEVICES=1 python -m amp.train ... --seed 1        # second GPU, separate process
"""
import argparse
import json
import os
import random

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import matthews_corrcoef

from . import baseline_classical, metrics, synthetic
from .data import TASKS, cluster_sequences, label_matrix, load_table, split_by_cluster
from .model import MultiTaskESM, masked_bce
from .tokenizer import encode_batch


def batches(df, y, mask, bs, shuffle, rng, max_len):
    idx = rng.permutation(len(df)) if shuffle else np.arange(len(df))
    seqs = df["sequence"].to_numpy()
    for i in range(0, len(idx), bs):
        b = idx[i:i + bs]
        ids, attn, res = encode_batch(list(seqs[b]), max_len)
        yield ids, attn, res, torch.from_numpy(np.nan_to_num(y[b])), torch.from_numpy(mask[b].astype(np.float32))


@torch.no_grad()
def predict(model, df, y, mask, args, dev):
    model.eval()
    out = []
    for ids, attn, res, _, _ in batches(df, y, mask, args.bs * 2, False, None, args.max_len):
        with torch.autocast(dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda" and args.bf16):
            out.append(torch.sigmoid(model(ids.to(dev), attn.to(dev), res.to(dev)).float()).cpu())
    return torch.cat(out).numpy()


def best_thresholds(y, mask, prob):
    """Per-task threshold maximising MCC on validation data."""
    th = []
    for j in range(len(TASKS)):
        m = mask[:, j]
        if m.sum() == 0 or len(np.unique(y[m, j])) < 2:
            th.append(0.5)
            continue
        grid = np.linspace(0.05, 0.95, 91)
        th.append(float(grid[int(np.argmax([matthews_corrcoef(y[m, j], prob[m, j] >= g) for g in grid]))]))
    return th


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="CSV: sequence + activity/toxicity/hemolysis (0/1, blank=unknown); "
                                   "optional 'cluster' column (e.g. from MMseqs2) overrides internal clustering")
    ap.add_argument("--synthetic", action="store_true", help="toy data, smoke test only")
    ap.add_argument("--model", default="facebook/esm2_t33_650M_UR50D")
    ap.add_argument("--tiny", action="store_true", help="tiny random ESM (no download, smoke test only)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5, help="encoder LR")
    ap.add_argument("--head-lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=0.01)
    ap.add_argument("--freeze-layers", type=int, default=0, help="freeze embeddings+first N blocks; -1 = linear probe")
    ap.add_argument("--max-len", type=int, default=100)
    ap.add_argument("--identity", type=float, default=0.4, help="similarity threshold for clustering")
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---- data + homology-aware split (the split depends on --seed only through cluster->split assignment)
    if args.synthetic:
        df = load_table(synthetic.make(seed=args.seed))
    else:
        df = load_table(args.data)
        raw = pd.read_csv(args.data)
    cid = (raw.drop_duplicates("sequence").set_index("sequence").loc[df["sequence"], "cluster"].to_numpy()
           if (not args.synthetic and "cluster" in raw) else cluster_sequences(list(df["sequence"]), args.identity))
    tr, va, te = split_by_cluster(df, cid, seed=args.seed)
    assert not set(tr.sequence) & set(te.sequence) and not set(va.sequence) & set(te.sequence)
    for name, d in zip(("train", "val", "test"), (tr, va, te)):
        d.to_csv(f"{args.out}/{name}.csv", index=False)
    (ytr, mtr), (yva, mva), (yte, mte) = map(label_matrix, (tr, va, te))
    print(f"sizes train/val/test = {len(tr)}/{len(va)}/{len(te)}; labelled per task (train) = "
          f"{dict(zip(TASKS, mtr.sum(0).tolist()))}")

    result = dict(args=vars(args), sizes=[len(tr), len(va), len(te)])

    # ---- classical baseline
    pva, pte = baseline_classical.fit_predict(tr, ytr, mtr, [va, te])
    th = best_thresholds(yva, mva, pva)
    result["logreg_test"] = metrics.task_metrics(yte, mte, pte, th)
    print("logreg   test mean AUROC:", result["logreg_test"]["mean_auroc"])

    # ---- ESM-2
    if args.tiny:
        from transformers import EsmConfig
        cfg = EsmConfig(vocab_size=33, hidden_size=64, num_hidden_layers=2, num_attention_heads=4,
                        intermediate_size=128, max_position_embeddings=128, pad_token_id=1, mask_token_id=32,
                        position_embedding_type="rotary")
        model = MultiTaskESM(config=cfg, freeze_layers=args.freeze_layers)
    else:
        from .tokenizer import check_against_hf
        check_against_hf(args.model, list(tr.sequence[:8]))
        model = MultiTaskESM(model_name=args.model, freeze_layers=args.freeze_layers)
    model.to(dev)
    enc = [p for p in model.encoder.parameters() if p.requires_grad]
    groups = [dict(params=list(model.heads.parameters()), lr=args.head_lr)]
    if enc:
        groups.append(dict(params=enc, lr=args.lr))
    opt = torch.optim.AdamW(groups, weight_decay=args.wd)
    steps = args.epochs * ((len(tr) + args.bs - 1) // args.bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[g["lr"] for g in groups], total_steps=steps,
                                                pct_start=0.1, anneal_strategy="cos")
    rng = np.random.default_rng(args.seed)
    best, bad, hist = -1.0, 0, []
    for ep in range(args.epochs):
        model.train()
        tot = n = 0
        for ids, attn, res, y, m in batches(tr, ytr, mtr, args.bs, True, rng, args.max_len):
            with torch.autocast(dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda" and args.bf16):
                logits = model(ids.to(dev), attn.to(dev), res.to(dev))
            loss = masked_bce(logits.float(), y.to(dev), m.to(dev))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step()
            tot += loss.item() * len(ids); n += len(ids)
        pv = predict(model, va, yva, mva, args, dev)
        vm = metrics.task_metrics(yva, mva, pv)
        score = vm["mean_auroc"] if vm["mean_auroc"] is not None else -tot / n
        hist.append(dict(epoch=ep, train_loss=tot / n, val=vm))
        print(f"epoch {ep} train_loss {tot / n:.4f} val mean AUROC {vm['mean_auroc']}")
        if score > best:
            best, bad = score, 0
            torch.save(model.state_dict(), f"{args.out}/best.pt")
        else:
            bad += 1
            if bad >= args.patience:
                break

    model.load_state_dict(torch.load(f"{args.out}/best.pt", map_location=dev))
    pv = predict(model, va, yva, mva, args, dev)
    pt = predict(model, te, yte, mte, args, dev)
    th = best_thresholds(yva, mva, pv)  # thresholds chosen on val, applied to test
    result["thresholds"] = th
    result["history"] = hist
    result["esm_test"] = metrics.task_metrics(yte, mte, pt, th)
    pd.concat([te[["sequence"]], pd.DataFrame(pt, columns=[f"p_{t}" for t in TASKS])], axis=1) \
        .to_csv(f"{args.out}/test_predictions.csv", index=False)
    json.dump(result, open(f"{args.out}/metrics.json", "w"), indent=2)
    print("ESM-2    test mean AUROC:", result["esm_test"]["mean_auroc"])
    print(json.dumps(result["esm_test"], indent=1))



if __name__ == "__main__":
    main()
