import numpy as np
from sklearn.metrics import average_precision_score, matthews_corrcoef, roc_auc_score

from .data import TASKS


def task_metrics(y, mask, prob, thresholds=None):
    """Per-task AUROC/AUPRC (threshold-free) and MCC at a threshold (default 0.5)."""
    out = {}
    for j, t in enumerate(TASKS):
        m = mask[:, j]
        yt, pt = y[m, j], prob[m, j]
        if m.sum() == 0 or len(np.unique(yt)) < 2:
            out[t] = dict(n=int(m.sum()), auroc=None, auprc=None, mcc=None)
            continue
        th = 0.5 if thresholds is None else thresholds[j]
        out[t] = dict(n=int(m.sum()), pos=float(yt.mean()), auroc=float(roc_auc_score(yt, pt)),
                      auprc=float(average_precision_score(yt, pt)),
                      mcc=float(matthews_corrcoef(yt, pt >= th)))
    vals = [v["auroc"] for v in out.values() if v["auroc"] is not None]
    out["mean_auroc"] = float(np.mean(vals)) if vals else None
    return out
