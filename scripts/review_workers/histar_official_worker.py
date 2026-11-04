"""OFFICIAL HiSTaR code (github.com/Anglejuebi/HiSTaR @ 0039a3b, its own environment envs/histar) with the settings of its Tutorials/1_DLPFC_Clustering.ipynb:
filter genes (min_cells 50, min_counts 10), normalize_total 1e6, 2000 HVG (seurat_v3 on counts), scale, PCA 200, graph_construction(adata, 12),
histar(gcn_hidden2=12, lambda_sim=0.619) in float64, HiSTaR.mclust_R (EEE). The tutorial's configure_r_environment() is Windows-only (hard-coded D:\\R-4.4.2 paths) and is not called.
If the official mclust_R call fails (mclust 6.1.3 rpy2 'dimnames' error, as seen for GraphST), the same Mclust call is made inside an R function and this is recorded in `versions`.
Usage: python histar_official_worker.py <indir> <out.npz> <k> <seed> <dataset>"""
import sys, os, numpy as np, scipy.sparse as sp, pandas as pd
indir, out, k, seed, ds = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
os.environ.setdefault("R_HOME", "/mnt/disk/bikashkumar/SpatialBench/env/lib/R")
import anndata, scanpy as sc, torch
import HiSTaR
from sklearn.decomposition import PCA
torch.set_num_threads(1); torch.set_default_dtype(torch.float64)
X = sp.load_npz(os.path.join(indir, "counts.npz")).tocsr().astype(np.float32)
a = anndata.AnnData(X, obs=pd.DataFrame(index=[f"s{i}" for i in range(X.shape[0])]), var=pd.DataFrame(index=open(os.path.join(indir, "genes.txt")).read().split("\n")[:X.shape[1]]))
a.obsm["spatial"] = np.load(os.path.join(indir, "spatial.npy"))
HiSTaR.fix_seed(seed)
a.layers["count"] = a.X.toarray()
sc.pp.filter_genes(a, min_cells=50); sc.pp.filter_genes(a, min_counts=10)
sc.pp.normalize_total(a, target_sum=1e6)
sc.pp.highly_variable_genes(a, flavor="seurat_v3", layer="count", n_top_genes=2000)
a = a[:, a.var["highly_variable"] == True].copy()   # noqa: E712
sc.pp.scale(a)
a.obsm["X_pca"] = PCA(n_components=200, random_state=42).fit_transform(a.X)
g = HiSTaR.graph_construction(a, 12)
net = HiSTaR.histar(a.obsm["X_pca"], g, device="cpu", gcn_hidden2=12, lambda_sim=0.619)
net.train()
feat, _, _, _ = net.process()
a.obsm["HiSTaR"] = np.asarray(feat)
note = "official HiSTaR.mclust_R"
try:
    HiSTaR.mclust_R(a, k, use_rep="HiSTaR", key_added="HiSTaR_clust", random_seed=seed)
except Exception as e:   # noqa: BLE001
    import rpy2.robjects as ro, rpy2.robjects.numpy2ri as n2r
    ro.r.library("mclust"); ro.r["set.seed"](seed); np.random.seed(seed)
    fit = ro.r("function(x, G, m) Mclust(x, G, m)$classification")
    a.obs["HiSTaR_clust"] = np.asarray(fit(n2r.numpy2rpy(np.asarray(a.obsm["HiSTaR"], float)), k, "EEE")).astype(int)
    note = "Mclust inside an R function (official call failed: %s)" % str(e)[:150]
np.savez(out, labels=a.obs["HiSTaR_clust"].astype(int).to_numpy(), emb=np.asarray(feat, np.float32), versions=np.array(["HiSTaR@0039a3b", note]))
