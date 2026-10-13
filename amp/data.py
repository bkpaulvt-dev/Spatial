"""Data loading, cleaning and homology-aware splitting.

Input CSV columns: sequence, and any of the TASKS columns (activity, toxicity, hemolysis)
holding 0/1, blank = label unknown. Unknown labels are masked out of the loss.
"""
import numpy as np
import pandas as pd

TASKS = ["activity", "toxicity", "hemolysis"]
AA = set("ACDEFGHIKLMNPQRSTVWY")


def load_table(src, min_len=5, max_len=100):
    df = src.copy() if isinstance(src, pd.DataFrame) else pd.read_csv(src)
    df["sequence"] = df["sequence"].astype(str).str.strip().str.upper()
    df = df[df["sequence"].map(lambda s: set(s) <= AA and min_len <= len(s) <= max_len)]
    for t in TASKS:
        if t not in df:
            df[t] = np.nan
    # Merge duplicate sequences; a label with conflicting values becomes unknown.
    def agg(col):
        v = col.dropna().unique()
        return v[0] if len(v) == 1 else np.nan
    out = df.groupby("sequence", sort=True)[TASKS].agg(agg).reset_index()
    return out


def cluster_sequences(seqs, threshold=0.4):
    """Greedy single-pass clustering, longest first; a sequence joins the first
    representative with normalised Levenshtein similarity >= threshold.

    This is an edit-distance proxy for sequence identity. For publication-grade splits
    produce clusters with MMseqs2 (easy-cluster --min-seq-id 0.4) and pass them via
    split_by_cluster(cluster_ids=...).
    """
    from rapidfuzz import process
    from rapidfuzz.distance import Levenshtein
    order = sorted(range(len(seqs)), key=lambda i: -len(seqs[i]))
    reps, rep_ids = [], []
    cid = np.empty(len(seqs), dtype=int)
    for i in order:
        if reps:
            sims = process.cdist([seqs[i]], reps, scorer=Levenshtein.normalized_similarity,
                                 workers=-1)[0]
            j = int(np.argmax(sims))
            if sims[j] >= threshold:
                cid[i] = rep_ids[j]
                continue
        reps.append(seqs[i])
        rep_ids.append(len(reps) - 1)
        cid[i] = len(reps) - 1
    return cid


def split_by_cluster(df, cluster_ids, fracs=(0.8, 0.1, 0.1), seed=0):
    """Assign whole clusters to train/val/test so no cluster spans two splits."""
    rng = np.random.default_rng(seed)
    uniq = rng.permutation(np.unique(cluster_ids))
    sizes = pd.Series(cluster_ids).value_counts()
    n, target = len(df), np.array(fracs) * len(df)
    assign, counts = {}, np.zeros(3)
    for c in uniq:  # fill splits in order of largest remaining deficit
        k = int(np.argmax(target - counts))
        assign[c] = k
        counts[k] += sizes[c]
    which = np.array([assign[c] for c in cluster_ids])
    return tuple(df[which == k].reset_index(drop=True) for k in range(3))


def label_matrix(df):
    y = df[TASKS].to_numpy(dtype=np.float32)
    return y, ~np.isnan(y)
