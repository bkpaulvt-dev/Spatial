"""Unit tests for spatialbench.metrics on synthetic tissues with known answers."""
import numpy as np, pandas as pd, pytest
from spatialbench import metrics as M


def stripes(n_side=40, k=4, seed=0):
    """A square lattice cut into k vertical stripes; returns coords, truth labels."""
    xs, ys = np.meshgrid(np.arange(n_side), np.arange(n_side))
    coords = np.c_[xs.ravel(), ys.ravel()].astype(float)
    truth = np.array([f"D{int(x * k // n_side)}" for x in coords[:, 0]], dtype=object)
    return coords, truth


def test_perfect_and_label_permutation_invariance():
    c, t = stripes()
    perm = {"D0": "x", "D1": "y", "D2": "z", "D3": "w"}
    p = np.array([perm[v] for v in t], dtype=object)
    a = M.agreement(p, t)
    assert a["ARI"] == pytest.approx(1) and a["NMI"] == pytest.approx(1) and a["purity"] == pytest.approx(1)
    assert a["jaccard_pairs"] == pytest.approx(1)
    d = M.per_domain(p, t)
    assert d["macro_F1"] == pytest.approx(1) and d["n_missed_domains"] == 0 and d["split_events"] == 0
    s = M.spatial_quality(p, c, t)
    assert s["boundary_F1"] == pytest.approx(1) and s["boundary_hd95"] == pytest.approx(0)
    assert s["domain_size_error"] == pytest.approx(0)
    tp = M.topology(p, t, c)
    assert tp["adjacency_jaccard"] == pytest.approx(1) and tp["domain_order_spearman"] == pytest.approx(1)


def test_random_labels_score_near_zero():
    c, t = stripes()
    p = np.random.RandomState(0).choice(["a", "b", "c", "d"], len(t)).astype(object)
    assert abs(M.agreement(p, t)["ARI"]) < 0.02
    s = M.spatial_quality(p, c, t)
    assert s["edge_homophily"] < 0.35 and s["PAS"] > 0.4
    assert s["mean_components_per_cluster"] > 5            # salt-and-pepper is fragmented


def test_missing_annotations_are_ignored():
    c, t = stripes()
    t2 = t.copy()
    t2[:200] = None
    assert M.valid_mask(t2).sum() == len(t) - 200
    assert M.agreement(t, t2)["ARI"] == pytest.approx(1)


def test_merge_split_and_small_domain():
    c, t = stripes()
    merged = np.where(np.isin(t, ["D0", "D1"]), "m", t).astype(object)      # two domains merged
    d = M.per_domain(merged, t)
    assert d["merge_events"] == 1 and d["n_missed_domains"] >= 1 and M.agreement(merged, t)["ARI"] < 1
    split = t.copy()
    split[(t == "D3") & (c[:, 1] < 20)] = "D3b"                              # one domain split in two
    d = M.per_domain(split, t)
    assert d["split_events"] == 1 and d["n_extra_clusters"] == 1
    # tiny domain (1% of spots) that the prediction swallows -> small_domain_recall 0
    t3 = t.copy(); t3[:16] = "tiny"
    p3 = t.copy()
    d = M.per_domain(p3, t3, small_frac=0.05)
    assert d["small_domain_recall"] < 0.5


def test_spatial_metrics_prefer_smooth_over_noisy():
    c, t = stripes()
    rs = np.random.RandomState(1)
    noisy = t.copy()
    flip = rs.rand(len(t)) < 0.2
    noisy[flip] = rs.choice(["D0", "D1", "D2", "D3"], flip.sum())
    a, b = M.spatial_quality(t, c, t), M.spatial_quality(noisy, c, t)
    assert a["CHAOS"] < b["CHAOS"] and a["PAS"] < b["PAS"] and a["edge_homophily"] > b["edge_homophily"]
    assert a["morans_I"] > b["morans_I"] and a["boundary_F1"] > b["boundary_F1"]


def test_unit_free_under_coordinate_rescaling():
    c, t = stripes()
    c = c + np.random.RandomState(5).normal(0, 1e-3, c.shape)   # real coordinates have no exact ties; on a
    #                                                          # perfect grid the choice among equidistant
    #                                                          # neighbours is arbitrary after rescaling
    rs = np.random.RandomState(2)
    p = t.copy(); flip = rs.rand(len(t)) < 0.1; p[flip] = "D0"
    a = M.spatial_quality(p, c, t)
    b = M.spatial_quality(p, c * 7.3 + 100, t)
    for key in ("CHAOS", "PAS", "boundary_F1", "boundary_hd95", "mean_components_per_cluster"):
        assert a[key] == pytest.approx(b[key], rel=1e-9), key


def test_k_metrics_and_internal_quality():
    assert M.k_metrics(5, 7) == {"K_abs_error": 2, "K_correct": False, "K_signed_error": -2}
    rs = np.random.RandomState(0)
    emb = np.r_[rs.randn(100, 5), rs.randn(100, 5) + 8]
    lab = np.r_[np.zeros(100), np.ones(100)].astype(int)
    good = M.internal_quality(emb, lab)
    bad = M.internal_quality(emb, rs.randint(0, 2, 200))
    assert good["silhouette"] > 0.5 > bad["silhouette"] and good["davies_bouldin"] < bad["davies_bouldin"]
    assert np.isnan(M.internal_quality(emb, np.zeros(200, int))["silhouette"])


def test_bootstrap_and_rank_robustness():
    m, lo, hi = M.bootstrap_ci(np.arange(100.0))
    assert lo < m < hi
    d = M.paired_bootstrap_diff(np.ones(30) * 0.6, np.ones(30) * 0.5)
    assert d["p_superior"] == 1.0 and d["mean_diff"] == pytest.approx(0.1)
    sc = pd.DataFrame({"p1": [1.0, 0.5, 0.0], "p2": [1.0, 0.5, 0.0]}, index=["A", "B", "C"])
    r = M.rank_robustness(sc)
    assert r.loc["A", "p_rank1"] == 1.0 and r.loc["C", "median_rank"] == 3
    flip = pd.DataFrame({"p1": [1.0, 0.0], "p2": [0.0, 1.0]}, index=["A", "B"])
    rr = M.rank_robustness(flip)
    assert 0.3 < rr.loc["A", "p_rank1"] < 0.7               # ranking depends on the weights
