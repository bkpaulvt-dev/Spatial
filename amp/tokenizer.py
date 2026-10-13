"""Minimal ESM-2-compatible tokenizer (same 33-token vocab as facebook/esm2_*).

Kept local so data pipelines and tests do not need a Hugging Face download.
`check_against_hf` verifies equivalence with the real tokenizer when it is available.
"""
import torch

VOCAB = ["<cls>", "<pad>", "<eos>", "<unk>", "L", "A", "G", "V", "S", "E", "R", "T", "I", "D",
         "P", "K", "Q", "N", "F", "Y", "M", "H", "W", "C", "X", "B", "U", "Z", "O", ".", "-",
         "<null_1>", "<mask>"]
TOK2ID = {t: i for i, t in enumerate(VOCAB)}
CLS, PAD, EOS, UNK = (TOK2ID[t] for t in ("<cls>", "<pad>", "<eos>", "<unk>"))
SPECIAL_IDS = (CLS, PAD, EOS, UNK)


def encode_batch(seqs, max_len=100):
    """Return input_ids, attention_mask, residue_mask (True on real residues only)."""
    seqs = [s[:max_len] for s in seqs]
    L = max(len(s) for s in seqs) + 2
    ids = torch.full((len(seqs), L), PAD, dtype=torch.long)
    res = torch.zeros((len(seqs), L), dtype=torch.bool)
    for i, s in enumerate(seqs):
        ids[i, 0] = CLS
        ids[i, 1:len(s) + 1] = torch.tensor([TOK2ID.get(c, UNK) for c in s])
        ids[i, len(s) + 1] = EOS
        res[i, 1:len(s) + 1] = True
    return ids, ids != PAD, res


def check_against_hf(model_name, seqs):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)
    ids, _, _ = encode_batch(seqs, max_len=10**6)
    ref = tok(list(seqs), padding=True, return_tensors="pt")["input_ids"]
    assert torch.equal(ids, ref), "local tokenizer disagrees with HF tokenizer"
