"""Sanity-check baseline: composition + physico-chemical features -> logistic regression.
If ESM-2 does not clearly beat this on a homology-split test set, something is wrong."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from .data import TASKS

AA = "ACDEFGHIKLMNPQRSTVWY"
KD = dict(zip(AA, [1.8, 2.5, -3.5, -3.5, 2.8, -0.4, -3.2, 4.5, -3.9, 3.8, 1.9, -3.5, -1.6, -3.5, -4.5, -0.8, -0.7, 4.2, -0.9, -1.3]))


def features(seq):
    L = len(seq)
    comp = [seq.count(a) / L for a in AA]
    charge = seq.count("K") + seq.count("R") + 0.1 * seq.count("H") - seq.count("D") - seq.count("E")
    h = np.array([KD[c] for c in seq])
    ang = np.deg2rad(100 * np.arange(L))  # helical hydrophobic moment
    mu = np.hypot((h * np.cos(ang)).sum(), (h * np.sin(ang)).sum()) / L
    return comp + [L, charge, charge / L, h.mean(), mu]


def fit_predict(train_df, y, mask, eval_dfs):
    Xtr = np.array([features(s) for s in train_df["sequence"]])
    Xev = [np.array([features(s) for s in d["sequence"]]) for d in eval_dfs]
    probs = [np.full((len(d), len(TASKS)), 0.5) for d in eval_dfs]
    for j in range(len(TASKS)):
        m = mask[:, j]
        if len(np.unique(y[m, j])) < 2:
            continue
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
        clf.fit(Xtr[m], y[m, j])
        for p, X in zip(probs, Xev):
            p[:, j] = clf.predict_proba(X)[:, 1]
    return probs
