"""Multi-perspective metric panel for spatial domain identification (plan section 3).

Conventions
-----------
* ``pred`` and ``truth`` are 1-D label arrays of equal length; ``truth`` may contain missing values
  (None / NaN / 'nan'), which are excluded from every label-based metric (see ``valid_mask``).
* ``coords`` is an (n, 2) array. Every distance is divided by the median nearest-neighbour spacing
  of the *annotated* spots, so metrics are unit free (pixels, micrometres, ...).
* Every function returns plain floats / dicts so results can be written to CSV or JSON.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn import metrics as skm
from sklearn.metrics.cluster import contingency_matrix

__all__ = ["valid_mask", "agreement", "hungarian_match", "per_domain", "spatial_quality", "topology",
           "internal_quality", "k_metrics", "evaluate", "bootstrap_ci", "paired_bootstrap_diff",
           "rank_robustness", "knn_graph", "spacing"]


# --------------------------------------------------------------------------- helpers
def valid_mask(truth) -> np.ndarray:
    """True where the annotation is present (not None / NaN / 'nan' / 'NA' / '')."""
    s = pd.Series(np.asarray(truth, dtype=object))
    return (~s.isna() & ~s.astype(str).isin(["nan", "NaN", "NA", "None", ""])).to_numpy()


def _codes(x):
    return pd.factorize(pd.Series(np.asarray(x, dtype=object)))[0]


def spacing(coords) -> float:
    """Median nearest-neighbour distance (the spot spacing on Visium)."""
    c = np.asarray(coords, dtype=float)
    d = cKDTree(c).query(c, k=2)[0][:, 1]
    d = d[d > 0]
    return float(np.median(d)) if len(d) else 1.0


def knn_graph(coords, k: int = 6):
    """Symmetric binary k-nearest-neighbour adjacency (csr) without self loops, plus neighbour indices."""
    c = np.asarray(coords, dtype=float)
    k = min(k, len(c) - 1)
    idx = cKDTree(c).query(c, k=k + 1)[1][:, 1:]
    rows = np.repeat(np.arange(len(c)), k)
    A = coo_matrix((np.ones(len(rows)), (rows, idx.ravel())), shape=(len(c), len(c))).tocsr()
    A = ((A + A.T) > 0).astype(float)
    A.setdiag(0)
    A.eliminate_zeros()
    return A, idx


def hungarian_match(pred, truth):
    """Optimal one-to-one matching of predicted clusters to annotated domains (maximises overlap).

    Returns (mapping {pred_label: truth_label}, contingency, pred_labels, truth_labels).
    Clusters left unmatched (more clusters than domains) are absent from the mapping.
    """
    pred, truth = np.asarray(pred, dtype=object), np.asarray(truth, dtype=object)
    pl, tl = pd.unique(pred), pd.unique(truth)
    C = contingency_matrix(_codes(truth), _codes(pred))  # rows: truth (order of first appearance)
    # factorize order == pd.unique order, so columns of C line up with pl and rows with tl
    r, c = linear_sum_assignment(-C)
    return {pl[j]: tl[i] for i, j in zip(r, c)}, C, pl, tl


# --------------------------------------------------------------------------- 3A agreement
def agreement(pred, truth) -> dict:
    """3A: global agreement with the annotation (annotated spots only)."""
    m = valid_mask(truth)
    p, t = _codes(np.asarray(pred, dtype=object)[m]), _codes(np.asarray(truth, dtype=object)[m])
    C = contingency_matrix(t, p).astype(float)
    n = C.sum()
    pairs = lambda x: (x * (x - 1) / 2).sum()
    tp, a, b = pairs(C), pairs(C.sum(1)), pairs(C.sum(0))
    hom, comp, v = skm.homogeneity_completeness_v_measure(t, p)
    return {"ARI": skm.adjusted_rand_score(t, p), "AMI": skm.adjusted_mutual_info_score(t, p),
            "NMI": skm.normalized_mutual_info_score(t, p), "FMI": skm.fowlkes_mallows_score(t, p),
            "V": v, "homogeneity": hom, "completeness": comp,
            "purity": float(C.max(0).sum() / n),
            "jaccard_pairs": float(tp / (a + b - tp)) if (a + b - tp) > 0 else 1.0}


# --------------------------------------------------------------------------- 3B per-domain
def per_domain(pred, truth, missed_f1: float = 0.2, small_frac: float = 0.05,
               cover_frac: float = 0.2, extra_frac: float = 0.01) -> dict:
    """3B: class-balanced accuracy, per-domain F1, missed/extra domains, splits/merges, small-domain recall.

    A domain is *missed* if its F1 after Hungarian matching is below ``missed_f1``; a predicted
    cluster is *extra* if it is unmatched and holds at least ``extra_frac`` of the annotated spots;
    *split events* count, for each annotated domain, the clusters covering >= ``cover_frac`` of it
    beyond the first; *merge events* count the same from the cluster's side.
    """
    m = valid_mask(truth)
    p, t = np.asarray(pred, dtype=object)[m], np.asarray(truth, dtype=object)[m]
    mp, C, pl, tl = hungarian_match(p, t)
    inv = {v: k for k, v in mp.items()}
    pcol = {lab: j for j, lab in enumerate(pl)}
    n = len(t)
    f1s, recs, precs, sizes = [], [], [], C.sum(1)
    for i, d in enumerate(tl):
        if d in inv:
            j = pcol[inv[d]]
            tp = C[i, j]
            rec, prec = tp / C[i].sum(), tp / max(C[:, j].sum(), 1)
        else:
            rec = prec = 0.0
        recs.append(rec); precs.append(prec)
        f1s.append(0.0 if rec + prec == 0 else 2 * rec * prec / (rec + prec))
    f1s, recs, precs = map(np.array, (f1s, recs, precs))
    frac = sizes / n
    small = frac < small_frac
    split = int(sum(max(0, int((C[i] / C[i].sum() >= cover_frac).sum()) - 1) for i in range(len(tl))))
    merge = int(sum(max(0, int((C[:, j] / max(C[:, j].sum(), 1) >= cover_frac).sum()) - 1) for j in range(len(pl))))
    unmatched = [lab for lab in pl if lab not in mp]
    extra = int(sum(C[:, pcol[lab]].sum() / n >= extra_frac for lab in unmatched))
    return {"accuracy_matched": float(sum(C[i, pcol[inv[d]]] for i, d in enumerate(tl) if d in inv) / n),
            "balanced_accuracy": float(recs.mean()), "macro_F1": float(f1s.mean()),
            "weighted_F1": float((f1s * frac).sum()),
            "n_missed_domains": int((f1s < missed_f1).sum()), "n_extra_clusters": extra,
            "split_events": split, "merge_events": merge, "n_clusters": int(len(pl)), "n_domains": int(len(tl)),
            "small_domain_recall": float(recs[small].mean()) if small.any() else float("nan"),
            "per_domain": [{"domain": str(d), "frac": float(frac[i]), "recall": float(recs[i]),
                            "precision": float(precs[i]), "F1": float(f1s[i])} for i, d in enumerate(tl)]}


# --------------------------------------------------------------------------- 3C spatial structure
def _boundary(labels, idx):
    return (labels[idx] != labels[:, None]).any(1)


def spatial_quality(pred, coords, truth=None, k: int = 6, tol_spacings: float = 1.5) -> dict:
    """3C: spatial coherence of a labelling (CHAOS, PAS, homophily, Moran's I, fragmentation, boundary
    fraction) and, when ``truth`` is given, boundary F1 / boundary distance / HD95 / size error.

    Spatial-coherence metrics are computed on the annotated spots only, so that predictions and
    annotation are compared on the same spots.
    """
    pred = np.asarray(pred, dtype=object)
    coords = np.asarray(coords, dtype=float)
    m = valid_mask(truth) if truth is not None else np.ones(len(pred), bool)
    p, c = pred[m], coords[m]
    sp = spacing(c)
    A, idx = knn_graph(c, k)
    codes = _codes(p)
    out = {}
    # CHAOS: mean within-cluster 1-NN distance (unit free)
    tot = 0.0
    for lab in np.unique(codes):
        cc = c[codes == lab]
        if len(cc) > 1:
            tot += cKDTree(cc).query(cc, k=2)[0][:, 1].sum()
    out["CHAOS"] = float(tot / len(c) / sp)
    # PAS: share of spots with more than half of their k neighbours in another cluster
    out["PAS"] = float(((codes[idx] != codes[:, None]).sum(1) > k / 2).mean())
    ei, ej = A.nonzero()
    out["edge_homophily"] = float((codes[ei] == codes[ej]).mean())
    # Moran's I of cluster indicators (mean over clusters)
    W = A.sum()
    mi = []
    for lab in np.unique(codes):
        x = (codes == lab).astype(float)
        z = x - x.mean()
        den = (z ** 2).sum()
        if den > 0:
            mi.append(len(x) / W * (z @ (A @ z)) / den)
    out["morans_I"] = float(np.mean(mi)) if mi else float("nan")
    # fragmentation: connected components of the within-cluster kNN graph
    comps, main = [], 0
    for lab in np.unique(codes):
        sel = np.where(codes == lab)[0]
        nc, cl = connected_components(A[sel][:, sel], directed=False)
        comps.append(nc)
        main += np.bincount(cl).max()
    out["mean_components_per_cluster"] = float(np.mean(comps))
    out["main_component_fraction"] = float(main / len(codes))
    bp = _boundary(codes, idx)
    out["boundary_fraction"] = float(bp.mean())
    if truth is not None:
        t = _codes(np.asarray(truth, dtype=object)[m])
        bt = _boundary(t, idx)
        out["boundary_fraction_truth"] = float(bt.mean())
        if bp.any() and bt.any():
            dpt = cKDTree(c[bt]).query(c[bp])[0] / sp   # predicted boundary -> truth boundary
            dtp = cKDTree(c[bp]).query(c[bt])[0] / sp   # truth boundary -> predicted boundary
            prec, rec = float((dpt <= tol_spacings).mean()), float((dtp <= tol_spacings).mean())
            out.update(boundary_precision=prec, boundary_recall=rec,
                       boundary_F1=0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec),
                       boundary_mean_dist=float((dpt.mean() + dtp.mean()) / 2),
                       boundary_hd95=float(max(np.percentile(dpt, 95), np.percentile(dtp, 95))))
        else:
            out.update(boundary_precision=float("nan"), boundary_recall=float("nan"), boundary_F1=float("nan"),
                       boundary_mean_dist=float("nan"), boundary_hd95=float("nan"))
        mp, C, pl, tl = hungarian_match(p, np.asarray(truth, dtype=object)[m])
        errs = []   # relative error of the matched cluster's size vs the annotated domain's size
        for i, d in enumerate(tl):
            lab = next((q for q, v in mp.items() if v == d), None)
            if lab is not None:
                n_true = C[i].sum()
                errs.append(abs((p == lab).sum() - n_true) / n_true)
        out["domain_size_error"] = float(np.mean(errs)) if errs else float("nan")
    return out


# --------------------------------------------------------------------------- 3D topology
def topology(pred, truth, coords, k: int = 6, min_edges: int = 3) -> dict:
    """3D: similarity of the domain-adjacency graph and (for ordered tissue) the spatial order of domains."""
    m = valid_mask(truth)
    p, t, c = np.asarray(pred, dtype=object)[m], np.asarray(truth, dtype=object)[m], np.asarray(coords, float)[m]
    mp, C, pl, tl = hungarian_match(p, t)
    A, _ = knn_graph(c, k)
    ei, ej = A.nonzero()
    keep = ei < ej
    ei, ej = ei[keep], ej[keep]

    def adjacency(lab):
        cnt = {}
        for a, b in zip(lab[ei], lab[ej]):
            if a != b:
                cnt[tuple(sorted((str(a), str(b))))] = cnt.get(tuple(sorted((str(a), str(b)))), 0) + 1
        return {e for e, n in cnt.items() if n >= min_edges}

    pm = np.array([mp.get(x, "__unmatched__") for x in p], dtype=object)
    A_t = adjacency(t)
    A_p = {e for e in adjacency(pm) if "__unmatched__" not in e}
    jac = len(A_t & A_p) / len(A_t | A_p) if (A_t | A_p) else 1.0
    out = {"adjacency_jaccard": float(jac)}
    # order along the principal axis of the annotated domain centroids
    cen_t = np.array([c[t == d].mean(0) for d in tl])
    if len(tl) >= 3:
        axis = np.linalg.svd(cen_t - cen_t.mean(0), full_matrices=False)[2][0]
        proj_t, proj_p = [], []
        for i, d in enumerate(tl):
            lab = next((q for q, v in mp.items() if v == d), None)
            if lab is not None and (p == lab).sum() > 0:
                proj_t.append(cen_t[i] @ axis)
                proj_p.append(c[p == lab].mean(0) @ axis)
        out["domain_order_spearman"] = float(spearmanr(proj_t, proj_p)[0]) if len(proj_t) >= 3 else float("nan")
    else:
        out["domain_order_spearman"] = float("nan")
    return out


# --------------------------------------------------------------------------- 3E label-free
def internal_quality(emb, pred, coords=None, max_n: int = 5000, seed: int = 0) -> dict:
    """3E: label-free quality of a partition in an embedding (and in space if ``coords`` given)."""
    pred = _codes(pred)
    if len(np.unique(pred)) < 2:
        return {k: float("nan") for k in ("silhouette", "davies_bouldin", "calinski_harabasz", "spatial_silhouette")}
    emb = np.asarray(emb, float)
    rs = np.random.RandomState(seed)
    sub = rs.choice(len(pred), min(max_n, len(pred)), replace=False)
    out = {"silhouette": float(skm.silhouette_score(emb[sub], pred[sub])) if len(np.unique(pred[sub])) > 1 else float("nan"),
           "davies_bouldin": float(skm.davies_bouldin_score(emb, pred)),
           "calinski_harabasz": float(skm.calinski_harabasz_score(emb, pred))}
    if coords is not None:
        cc = np.asarray(coords, float)
        out["spatial_silhouette"] = (float(skm.silhouette_score(cc[sub], pred[sub]))
                                     if len(np.unique(pred[sub])) > 1 else float("nan"))
    return out


# --------------------------------------------------------------------------- 3I number of domains
def k_metrics(k_hat: int, k_true: int) -> dict:
    return {"K_abs_error": abs(int(k_hat) - int(k_true)), "K_correct": int(k_hat) == int(k_true),
            "K_signed_error": int(k_hat) - int(k_true)}


# --------------------------------------------------------------------------- full panel
def evaluate(pred, truth, coords, emb=None, k: int = 6) -> dict:
    """The complete label-based + spatial (+ label-free if ``emb``) panel as one flat dict."""
    out = {}
    out.update(agreement(pred, truth))
    pdm = per_domain(pred, truth)
    out.update({k_: v for k_, v in pdm.items() if k_ != "per_domain"})
    out.update(spatial_quality(pred, coords, truth, k=k))
    out.update(topology(pred, truth, coords, k=k))
    if emb is not None:
        m = valid_mask(truth)
        out.update(internal_quality(np.asarray(emb)[m], np.asarray(pred, dtype=object)[m], np.asarray(coords)[m]))
    return out


# --------------------------------------------------------------------------- 3K / 3M statistics
def bootstrap_ci(values, stat=np.mean, n_boot: int = 5000, alpha: float = 0.05, seed: int = 0):
    """Percentile bootstrap CI of ``stat`` over units (e.g. sections)."""
    v = np.asarray(values, float)
    v = v[~np.isnan(v)]
    rs = np.random.RandomState(seed)
    b = np.array([stat(v[rs.randint(0, len(v), len(v))]) for _ in range(n_boot)])
    return float(stat(v)), float(np.percentile(b, 100 * alpha / 2)), float(np.percentile(b, 100 * (1 - alpha / 2)))


def paired_bootstrap_diff(a, b, n_boot: int = 5000, seed: int = 0) -> dict:
    """Mean paired difference a-b over units, its bootstrap CI and the probability that a > b."""
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[~np.isnan(d)]
    rs = np.random.RandomState(seed)
    bs = np.array([d[rs.randint(0, len(d), len(d))].mean() for _ in range(n_boot)])
    return {"mean_diff": float(d.mean()), "ci_lo": float(np.percentile(bs, 2.5)), "ci_hi": float(np.percentile(bs, 97.5)),
            "p_superior": float((bs > 0).mean()), "n_units": int(len(d))}


def rank_robustness(scores: pd.DataFrame, n_draws: int = 2000, seed: int = 0) -> pd.DataFrame:
    """3M: how much does the ranking depend on how perspectives are weighted?

    ``scores``: methods x perspectives (higher is better; each column already normalised, e.g. rank- or
    min-max-normalised across methods). Weights are drawn from a flat Dirichlet. Returns, per method,
    the fraction of draws in which it ranks 1st / in the top 3 and its median / 5th-95th percentile rank.
    """
    X = scores.to_numpy(float)
    rs = np.random.RandomState(seed)
    W = rs.dirichlet(np.ones(X.shape[1]), n_draws)
    S = W @ X.T                                  # draws x methods
    ranks = (-S).argsort(1).argsort(1) + 1
    return pd.DataFrame({"p_rank1": (ranks == 1).mean(0), "p_top3": (ranks <= 3).mean(0),
                         "median_rank": np.median(ranks, 0), "rank_p05": np.percentile(ranks, 5, 0),
                         "rank_p95": np.percentile(ranks, 95, 0)}, index=scores.index)
