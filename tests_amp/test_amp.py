import numpy as np
import pandas as pd
import torch

from amp import synthetic, train
from amp.data import cluster_sequences, load_table, split_by_cluster
from amp.metrics import task_metrics
from amp.model import masked_bce
from amp.tokenizer import CLS, EOS, PAD, encode_batch


def test_tokenizer_matches_esm_conventions():
    ids, attn, res = encode_batch(["AC", "ACDE"])
    assert ids[0].tolist() == [CLS, 5, 23, EOS, PAD, PAD]
    assert res.sum(1).tolist() == [2, 4] and attn.sum(1).tolist() == [4, 6]


def test_load_table_cleans_and_merges_conflicts():
    df = pd.DataFrame(dict(sequence=["kkllk", "KKLLK", "AAAAAA", "AXAAAA", "KK"],
                           activity=[1, 0, 1, 1, 1], toxicity=[0, 0, np.nan, 0, 0]))
    out = load_table(df).set_index("sequence")
    assert set(out.index) == {"KKLLK", "AAAAAA"}      # non-standard residue + too short dropped
    assert np.isnan(out.loc["KKLLK", "activity"])      # conflicting duplicate labels -> unknown
    assert out.loc["KKLLK", "toxicity"] == 0


def test_cluster_split_has_no_leakage():
    df = load_table(synthetic.make(300, seed=1))
    base = list(df.sequence[:60])
    near = [s[:-1] + "A" for s in base]                # near-duplicates must share a cluster
    seqs = base + near
    cid = cluster_sequences(seqs, 0.8)
    assert all(cid[i] == cid[i + 60] for i in range(60))
    d = pd.DataFrame(dict(sequence=seqs, activity=0.0))
    parts = split_by_cluster(d, cid, seed=0)
    sets = [set(p.sequence) for p in parts]
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    for i in range(60):                                # a sequence and its near-twin land together
        assert sum(base[i] in s for s in sets) == 1 and any(base[i] in s and near[i] in s for s in sets)


def test_masked_bce_ignores_missing_labels():
    logits = torch.tensor([[2.0, 100.0, 0.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]]); m = torch.tensor([[1.0, 0.0, 0.0]])
    assert torch.isclose(masked_bce(logits, y, m), torch.nn.functional.softplus(torch.tensor(-2.0)))


def test_metrics_skip_single_class_tasks():
    y = np.array([[1, 0, np.nan], [0, 0, np.nan], [1, 0, np.nan], [0, 0, np.nan]], dtype=np.float32)
    out = task_metrics(np.nan_to_num(y), ~np.isnan(y), np.array([[.9, .1, .5]] * 2 + [[.8, .2, .5]] * 2))
    assert out["activity"]["auroc"] is not None and out["toxicity"]["auroc"] is None


def test_end_to_end_tiny_run(tmp_path):
    train.main(["--synthetic", "--tiny", "--out", str(tmp_path), "--epochs", "3", "--bs", "16", "--head-lr", "3e-3",
                "--lr", "1e-3", "--bf16"])
    import json
    r = json.load(open(tmp_path / "metrics.json"))
    assert r["esm_test"]["activity"]["auroc"] is not None
    assert (tmp_path / "test_predictions.csv").exists()
