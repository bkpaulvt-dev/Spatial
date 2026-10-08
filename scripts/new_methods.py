"""Additional published methods, each run with its official tutorial settings.

Every function takes an AnnData with raw counts in .X, coordinates in .obsm['spatial'],
labels in .obs['ground_truth'], the number of domains k, a seed and the dataset name, and
returns (official_labels, embedding_or_None). Deviations from the tutorials are noted inline.
"""
import contextlib, io, os, random, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _seed(seed):
    import torch
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def _nn_spacing(coords):
    """Median distance to the nearest neighbour (= spot spacing on Visium), in the data's own units."""
    from sklearn.neighbors import NearestNeighbors
    C = np.asarray(coords, dtype=np.float64)
    return float(np.median(NearestNeighbors(n_neighbors=2).fit(C).kneighbors(C)[0][:, 1]))


def mclust_eee(Z, k, seed):
    """R mclust EEE called exactly as SEDR.mclust_R does (np/R seed, Mclust(Z, k, 'EEE')), minus its
    line that sets R_HOME to the authors' machine, which breaks R's LAPACK in a running session."""
    import rpy2.robjects as ro, rpy2.robjects.numpy2ri as n2r
    np.random.seed(seed)
    ro.r.library("mclust")
    n2r.activate()
    ro.r["set.seed"](seed)
    res = ro.r["Mclust"](n2r.numpy2rpy(np.asarray(Z, dtype=np.float64)), k, "EEE")
    return np.array(res[-2]).astype(int)


def _lognorm_hvg(a, n_top=3000):
    """HVG (seurat_v3 on counts; all genes for targeted panels) -> normalize 1e4 -> log1p."""
    import scanpy as sc
    if a.n_vars > n_top:
        sc.pp.highly_variable_genes(a, flavor="seurat_v3", n_top_genes=n_top)
    else:
        a.var["highly_variable"] = True
    sc.pp.normalize_total(a, target_sum=1e4)
    sc.pp.log1p(a)
    return a


def stagate(a, k, seed, ds):
    """STAGATE (Dong & Zhang, Nat Commun 2022), PyG version. Tutorial: 3000 HVGs, rad_cutoff=150
    full-resolution pixels for DLPFC Visium (~1.1 spot spacings, ~6 neighbours; expressed in spot
    spacings because our coordinates are on another scale); KNN graph with 6 neighbours for single-cell data (no tutorial radius exists for
    our STARmap/MERFISH coordinates). Clustering: STAGATE's mclust_R (EEE)."""
    try:
        import torch_sparse  # noqa: F401  real extension if installed
    except ImportError:
        sys.path.insert(0, os.path.join(HERE, "_shims"))
    import torch, STAGATE_pyG as st
    a = _lognorm_hvg(a.copy(), 3000)
    a = a[:, a.var["highly_variable"]].copy()
    with contextlib.redirect_stdout(io.StringIO()):
        if ds == "dlpfc":   # tutorial: rad_cutoff=150 full-resolution pixels = ~1.1 spot spacings
            st.Cal_Spatial_Net(a, rad_cutoff=1.1 * _nn_spacing(a.obsm["spatial"]))
        else:
            st.Cal_Spatial_Net(a, k_cutoff=6, model="KNN")
        a.uns["mean_neighbours"] = a.uns["Spatial_Net"].shape[0] / a.n_obs
        a = st.train_STAGATE(a, random_seed=seed, device=torch.device("cpu"), verbose=False)
        a = st.mclust_R(a, used_obsm="STAGATE", num_cluster=k)
    return a.obs["mclust"].astype(int).to_numpy(), a.obsm["STAGATE"]


def sedr(a, k, seed, ds):
    """SEDR (Xu et al., Genome Med 2024), Tutorial1_Clustering: filter genes, normalize 1e6,
    2000 HVGs, scale, PCA(200) (all genes and n_genes-1 PCs for targeted panels), 12-NN graph,
    DEC training, mclust (EEE)."""
    import scanpy as sc, torch, SEDR
    from sklearn.decomposition import PCA
    a = a.copy()
    SEDR.fix_seed(seed)
    a.layers["count"] = a.X.toarray() if hasattr(a.X, "toarray") else np.asarray(a.X)
    if ds == "dlpfc":
        sc.pp.filter_genes(a, min_cells=50); sc.pp.filter_genes(a, min_counts=10)
    sc.pp.normalize_total(a, target_sum=1e6)
    if a.n_vars > 2000:
        sc.pp.highly_variable_genes(a, flavor="seurat_v3", layer="count", n_top_genes=2000)
        a = a[:, a.var["highly_variable"]].copy()
    sc.pp.scale(a)
    a.obsm["X_pca"] = PCA(n_components=min(200, a.n_vars - 1), random_state=42).fit_transform(a.X)
    with contextlib.redirect_stdout(io.StringIO()):
        g = SEDR.graph_construction(a, 12)
        net = SEDR.Sedr(a.obsm["X_pca"], g, mode="clustering", device="cpu")
        net.train_with_dec(N=1)
        feat, _, _, _ = net.process()
    return mclust_eee(feat, k, 2023), feat   # SEDR.mclust_R's default random_seed is 2023


def spaceflow(a, k, seed, ds):
    """SpaceFlow (Ren et al., Nat Commun 2022), README defaults: 3000 HVGs (all genes for targeted
    panels), z_dim 50, spatial regularization 0.1, 1000 epochs with early stopping. Its own
    segmentation is Leiden at a fixed resolution; to match the true number of domains we use a
    Leiden resolution search on its embedding (as for SpaGCN/NichePCA)."""
    import networkx as nx, scipy.sparse as sp
    if not hasattr(nx, "to_scipy_sparse_matrix"):   # removed in networkx 3; same graph, same matrix
        nx.to_scipy_sparse_matrix = lambda G, **kw: sp.csr_matrix(nx.to_scipy_sparse_array(G, **kw))
    import SpaceFlow.SpaceFlow as S
    from nichepca.clustering import leiden_with_nclusters
    import anndata, scanpy as sc, tempfile
    import scanpy as sc0
    a = a.copy()
    sc0.pp.filter_genes(a, min_cells=1)   # all-zero genes break SpaceFlow's cell_ranger HVG binning
                                          # under pandas 3 (duplicate bin edges); they are never HVGs
    # SpaceFlow's count_matrix/spatial_locs constructor path fails on numpy arrays,
    sf = S.SpaceFlow(adata=a)   # so the documented AnnData path is used (counts in .X, obsm['spatial'])
    with contextlib.redirect_stdout(io.StringIO()), tempfile.TemporaryDirectory() as td:
        sf.preprocessing_data(n_top_genes=3000 if a.n_vars > 3000 else None)
        sf.train(embedding_save_filepath=os.path.join(td, "e.tsv"), random_seed=seed, gpu=-1)
    Z = np.asarray(sf.embedding)
    b = anndata.AnnData(Z); b.obsm["X_emb"] = Z
    sc.pp.neighbors(b, use_rep="X_emb", n_neighbors=50, random_state=seed)
    with contextlib.redirect_stdout(io.StringIO()):
        leiden_with_nclusters(b, n_clusters=k, seed=seed)
    return b.obs["leiden"].astype(int).to_numpy(), Z


def nichepca(a, k, seed, ds):
    """NichePCA (Bioinformatics 2025): normalise, log1p, mean-aggregate over a 6-NN spatial graph,
    PCA(30); Leiden with a resolution search to k clusters (package function)."""
    import nichepca as npc, scanpy as sc
    a = a.copy()
    with contextlib.redirect_stdout(io.StringIO()):
        npc.workflows.nichepca(a, knn=6)
        sc.pp.neighbors(a, use_rep="X_npca", random_state=seed)
        npc.clustering.leiden_with_nclusters(a, n_clusters=k, seed=seed)
    return a.obs["leiden"].astype(int).to_numpy(), np.asarray(a.obsm["X_npca"])


METHODS = {"stagate": stagate, "sedr": sedr, "spaceflow": spaceflow, "nichepca": nichepca}


def ccst(a, k, seed, ds):
    """CCST (Li et al., Nat Comput Sci 2022), ported from the official repository (CCST.py,
    data_generation_ST.py, CCST_ST_utils.py) because its scripts pin PyTorch 1.7 / PyG 1.6:
      features : filter genes (min_cells=5), normalize_total(target_sum=1, exclude_highly_expressed),
                 scale, PCA(200) (n_genes-1 for targeted panels)
      graph    : binary distance-threshold adjacency; the repository hand-picks a threshold per dataset
                 "so that on average each cell has x neighbour cells", so we set it to give a mean
                 degree of 6 on every section; A = (1-lambda_I) A0 + lambda_I I, lambda_I = 0.3 (Visium)
                 or 0.8 (single-cell), as in the README
      model    : Deep Graph Infomax, 4 GCNConv layers (hidden 256) + PReLU, Adam lr 1e-6, 5000 epochs
      cluster  : PCA(30) of the embedding, k-means (k-means++, n_init=100, max_iter=1000, tol=1e-6)."""
    import scanpy as sc, scipy.sparse as sp, torch, torch.nn as nn
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv, DeepGraphInfomax
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.neighbors import NearestNeighbors
    _seed(seed)
    a = a.copy()
    sc.pp.filter_genes(a, min_cells=5)
    X = sc.pp.normalize_total(a, target_sum=1, exclude_highly_expressed=True, inplace=False)["X"]
    X = sc.pp.scale(X.toarray() if hasattr(X, "toarray") else np.asarray(X))
    X = PCA(n_components=min(200, X.shape[1] - 1), random_state=seed).fit_transform(X).astype(np.float32)
    C = np.asarray(a.obsm["spatial"], dtype=np.float64)
    d = NearestNeighbors(n_neighbors=7).fit(C).kneighbors(C)[0][:, 1:]
    thr = float(np.median(d[:, -1]))          # median 6th-neighbour distance -> mean degree close to 6
    A0 = NearestNeighbors(radius=thr).fit(C).radius_neighbors_graph(C, mode="connectivity").tocsr()
    A0.setdiag(0); A0.eliminate_zeros()
    lam = 0.3 if ds == "dlpfc" else 0.8
    A = ((1 - lam) * A0 + lam * sp.eye(A0.shape[0], format="csr")).tocoo()
    data = Data(x=torch.tensor(X), edge_index=torch.tensor(np.vstack([A.row, A.col]), dtype=torch.long),
                edge_attr=torch.tensor(A.data, dtype=torch.float))

    class Encoder(nn.Module):
        def __init__(self, i, h):
            super().__init__()
            self.c1, self.c2, self.c3, self.c4 = GCNConv(i, h), GCNConv(h, h), GCNConv(h, h), GCNConv(h, h)
            self.prelu = nn.PReLU(h)

        def forward(self, x, edge_index, edge_weight):
            for c in (self.c1, self.c2, self.c3, self.c4):
                x = c(x, edge_index, edge_weight=edge_weight)
            return self.prelu(x)

    def corruption(x, edge_index, edge_weight):
        return x[torch.randperm(x.size(0))], edge_index, edge_weight

    model = DeepGraphInfomax(256, encoder=Encoder(X.shape[1], 256),
                             summary=lambda z, *args, **kw: torch.sigmoid(z.mean(dim=0)), corruption=corruption)
    opt = torch.optim.Adam(model.parameters(), lr=1e-6)
    for _ in range(5000):
        model.train(); opt.zero_grad()
        pos, neg, s = model(data.x, data.edge_index, data.edge_attr)
        loss = model.loss(pos, neg, s); loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        Z = model(data.x, data.edge_index, data.edge_attr)[0].numpy()
    Zp = PCA(n_components=30, random_state=seed).fit_transform(Z)
    lab = KMeans(n_clusters=k, init="k-means++", n_init=100, max_iter=1000, tol=1e-6, random_state=seed).fit_predict(Zp)
    return lab, Zp


METHODS["ccst"] = ccst


MGCN_DIR = os.path.join(HERE, "..", "data", "ext", "methods", "Spatial-MGCN", "Spatial-MGCN")
LAST_ORACLE = {}   # Spatial-MGCN: ARI of the label-selected epoch, for the leakage analysis


def spatial_mgcn(a, k, seed, ds, labels=None):
    """Spatial-MGCN (Wang et al., Brief Bioinform 2023), using the repository's own model and graph
    code (models.py, layers.py, utils.py) and config/DLPFC.ini (lr 1e-3, wd 5e-4, feature-graph
    k=14, spatial radius 560, hidden 128/64, alpha/beta/gamma 1/10/0.1, 200+1 epochs):
      * DLPFC_generate_data.py drops unannotated spots before training; we keep all spots, as for
        every other method.
      * DLPFC_test.py keeps the epoch whose k-means clustering has the highest ARI against the
        ground truth. We report the label-free result (final epoch, k-means as in the script, with
        scikit-learn's former default n_init=10) and store the label-selected ARI separately.
      * The spatial radius (560 full-resolution Visium pixels, about 4.1 spot spacings) is expressed
        as 4.1 x the median nearest-neighbour distance, so it is independent of coordinate units."""
    import importlib, scanpy as sc, scipy.sparse as sp, torch
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score
    from sklearn.neighbors import NearestNeighbors
    sys.path.insert(0, MGCN_DIR)
    U = importlib.import_module("utils"); Mo = importlib.import_module("models")
    sys.path.remove(MGCN_DIR)
    _seed(seed)
    a = a.copy()
    if a.n_vars > 3000:
        sc.pp.filter_genes(a, min_cells=100)
        sc.pp.highly_variable_genes(a, flavor="seurat_v3", n_top_genes=3000)
        a = a[:, a.var["highly_variable"]].copy()
    X = a.X.toarray() if hasattr(a.X, "toarray") else np.asarray(a.X, dtype=np.float64)
    a.X = X / X.sum(1, keepdims=True) * 10000
    sc.pp.scale(a, zero_center=False, max_value=10)
    radius = 4.1 * _nn_spacing(a.obsm["spatial"])   # config: 560 full-resolution px = ~4.1 spot spacings
    with contextlib.redirect_stdout(io.StringIO()):
        fadj = U.features_construct_graph(a.X, k=14)
        sadj, graph_nei, graph_neg = U.spatial_construct_graph1(a, radius=radius)
    nf = U.sparse_mx_to_torch_sparse_tensor(U.normalize_sparse_matrix(fadj + sp.eye(fadj.shape[0])))
    ns = U.sparse_mx_to_torch_sparse_tensor(U.normalize_sparse_matrix(sadj + sp.eye(sadj.shape[0])))
    gnei, gneg = torch.LongTensor(np.asarray(graph_nei)), torch.LongTensor(np.asarray(graph_neg))
    feats = torch.FloatTensor(np.asarray(a.X))
    model = Mo.Spatial_MGCN(nfeat=feats.shape[1], nhid1=128, nhid2=64, dropout=0)
    opt = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=5e-4)
    y = labels if labels is not None else a.obs["ground_truth"].to_numpy().astype(object)
    keep = np.array([isinstance(v, str) and v != "nan" for v in y])
    best = -1.0
    for epoch in range(201):
        model.train(); opt.zero_grad()
        com1, com2, emb, pi, disp, mean = model(feats, ns, nf)
        loss = (1 * U.ZINB(pi, theta=disp, ridge_lambda=0).loss(feats, mean, mean=True)
                + 10 * U.consistency_loss(com1, com2) + 0.1 * U.regularization_loss(emb, gnei, gneg))
        loss.backward(); opt.step()
        e = np.nan_to_num(emb.detach().numpy())
        lab = KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(e)
        best = max(best, adjusted_rand_score(y[keep], lab[keep]))   # what DLPFC_test.py reports
    LAST_ORACLE["ARI_label_selected_epoch"] = best
    return lab, e


METHODS["spatial_mgcn"] = spatial_mgcn


def _run_r(method, a, k, seed, ds, timeout=6 * 3600):
    """Export one section and run scripts/run_r_method.R (BASS / BayesSpace)."""
    import scipy.io, scipy.sparse as sp, subprocess, tempfile, pandas as pd
    with tempfile.TemporaryDirectory() as td:
        X = sp.csr_matrix(a.X)
        scipy.io.mmwrite(os.path.join(td, "counts.mtx"), X.T.tocoo())
        open(os.path.join(td, "genes.txt"), "w").write("\n".join(map(str, a.var_names)) + "\n")
        bc = [f"s{i}" for i in range(a.n_obs)]
        open(os.path.join(td, "barcodes.txt"), "w").write("\n".join(bc) + "\n")
        C = np.asarray(a.obsm["spatial"])
        df = pd.DataFrame({"x": C[:, 0], "y": C[:, 1],
                           "row": a.obs["array_row"].to_numpy() if "array_row" in a.obs else 0,
                           "col": a.obs["array_col"].to_numpy() if "array_col" in a.obs else 0}, index=bc)
        df.to_csv(os.path.join(td, "coords.csv"))
        p = subprocess.run(["Rscript", os.path.join(HERE, "run_r_method.R"), method, td, str(k), str(seed), ds],
                           capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            raise RuntimeError(f"{method} failed (exit code {p.returncode}; -9 = killed, e.g. out of memory): "
                               f"{p.stderr[-1200:]} | stdout: {p.stdout[-300:]}")
        lab = pd.read_csv(os.path.join(td, "labels.csv")).set_index("barcode").loc[bc, "label"].to_numpy()
    return lab.astype(int), None


def bass(a, k, seed, ds):
    """BASS (Li & Zhou, Genome Biol 2022): authors' settings per dataset (scripts/run_r_method.R)."""
    return _run_r("bass", a, k, seed, ds)


def bayesspace(a, k, seed, ds):
    """BayesSpace (Zhao et al., Nat Biotechnol 2021) v1.5.1 defaults; Visium (hexagonal lattice) only."""
    if ds != "dlpfc":
        raise NotImplementedError("BayesSpace requires a Visium/ST spot lattice (not applicable to single-cell data)")
    return _run_r("bayesspace", a, k, seed, ds)


DEEPST_DIR = os.path.join(HERE, "..", "data", "ext", "methods", "DeepST")


def deepst(a, k, seed, ds):
    """DeepST (Xu et al., Nucleic Acids Res 2022), README pipeline without histology:
    pre_epochs 500, epochs 500, augmentation (BallTree, use_morphological=False), KDTree graph,
    PCA 200 (n_genes-1 for targeted panels), Leiden at the given number of domains (priori=True),
    then DeepST's spatial refinement ('DeepST_refine_domain', the label the README reports)."""
    import tempfile
    if DEEPST_DIR not in sys.path:
        sys.path.insert(0, DEEPST_DIR)
    import deepstkit as dt
    a = a.copy()
    with contextlib.redirect_stdout(io.StringIO()), tempfile.TemporaryDirectory() as td:
        dt.utils_func.seed_torch(seed=seed)
        run = dt.main.run(save_path=td, task="Identify_Domain", pre_epochs=500, epochs=500, use_gpu=False)
        a = run._get_augment(a, spatial_type="BallTree", use_morphological=False)
        g = run._get_graph(a.obsm["spatial"], distType="KDTree")
        data = run._data_process(a, pca_n_comps=min(200, a.n_vars - 1))
        emb = run._fit(data=data, graph_dict=g)
        a.obsm["DeepST_embed"] = emb
        a = run._get_cluster_data(a, n_domains=k, priori=True)
    return a.obs["DeepST_refine_domain"].astype(int).to_numpy(), np.asarray(emb)


METHODS.update({"bass": bass, "bayesspace": bayesspace, "deepst": deepst})
