import numpy as np
from sklearn.cluster import KMeans
from spatialbench import invariance as I


def toy(n=600, seed=0):
    rs = np.random.RandomState(seed)
    c = rs.rand(n, 2) * 100
    lab = (c[:, 0] > 50).astype(int) + 2 * (c[:, 1] > 50)
    X = rs.randn(n, 10) * 0.5 + np.eye(4)[lab] @ rs.randn(4, 10) * 3
    return X, c, 4


def expression_only(X, coords, k, seed):                  # ignores coordinates: invariant to all coordinate transforms
    return KMeans(k, n_init=10, random_state=seed).fit_predict(X)


def absolute_radius_graph(X, coords, k, seed):            # DELIBERATELY not unit invariant: radius of 8 *units*
    from scipy.spatial import cKDTree
    t = cKDTree(coords)
    nb = t.query_ball_point(coords, 8.0)
    S = np.array([X[i].mean(0) if len(i) == 0 else X[i].mean(0) for i in nb])
    return KMeans(k, n_init=10, random_state=seed).fit_predict(S)


def test_invariant_method_passes_coordinate_transforms():
    X, c, k = toy()
    r = I.run_invariance(expression_only, X, c, k, transforms=["rescale_coords_x100", "translate_coords",
                                                                "rotate_coords_37deg", "reflect_coords"])
    assert all(r["pass"].values()) and min(r["consistency"].values()) > 0.99


def test_detects_unit_dependent_method():
    X, c, k = toy()
    r = I.run_invariance(absolute_radius_graph, X, c, k, transforms=["rescale_coords_x100", "rescale_coords_x0.01",
                                                                      "rotate_coords_37deg"], tol=0.02)
    assert not r["pass"]["rescale_coords_x100"] or not r["pass"]["rescale_coords_x0.01"]
    assert r["pass"]["rotate_coords_37deg"]                 # rotation does not change distances


def test_permutation_is_mapped_back_correctly():
    X, c, k = toy()
    r = I.run_invariance(expression_only, X, c, k, transforms=["permute_spots"], repeats=3)
    assert r["consistency"]["permute_spots"] > 0.95        # a wrong inverse mapping would give ARI ~ 0
