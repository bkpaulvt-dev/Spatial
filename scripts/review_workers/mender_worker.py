"""MENDER (Yuan, Nat Commun 2024; PyPI SOMENDER 1.1) in its own environment (envs/mender). Tutorial workflow: cell states 'ct' = Leiden (resolution 2) on a 4000-HVG PCA,
then context representation + Leiden with the resolution searched to reach K domains (run_clustering_normal(K)).
Spot grids (spatialbench VISIUM group): ring mode, 6 neighbours, 3 scales (Visium tutorial); every other platform: radius mode with the radius from MENDER's own estimate_radius
(median nearest-neighbour distance), 6 scales. Usage: python mender_worker.py <indir> <out.npz> <k> <seed> <dataset> <is_visium 0|1>"""
import sys, os, numpy as np, scipy.sparse as sp, pandas as pd
indir, out, k, seed, ds, vis = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], int(sys.argv[6])
import anndata, scanpy as sc, MENDER
from scipy.spatial import cKDTree
X = sp.load_npz(os.path.join(indir, "counts.npz")).tocsr().astype(np.float32)
a = anndata.AnnData(X, obs=pd.DataFrame(index=[f"s{i}" for i in range(X.shape[0])]), var=pd.DataFrame(index=open(os.path.join(indir, "genes.txt")).read().split("\n")[:X.shape[1]]))
C = np.load(os.path.join(indir, "spatial.npy")); a.obsm["spatial"] = C
sc.pp.highly_variable_genes(a, flavor="seurat_v3", n_top_genes=min(4000, a.n_vars))
sc.pp.normalize_total(a); sc.pp.log1p(a)
sc.pp.pca(a, random_state=seed); sc.pp.neighbors(a, random_state=seed)
sc.tl.leiden(a, resolution=2, key_added="ct", random_state=seed); a.obs["ct"] = a.obs["ct"].astype("category")
msm = MENDER.MENDER_single(a, ct_obs="ct", random_seed=seed)
if vis: msm.set_MENDER_para(n_scales=3, nn_mode="ring", nn_para=6)
else:
    d, _ = cKDTree(C).query(C, k=2); msm.set_MENDER_para(n_scales=6, nn_mode="radius", nn_para=float(np.median(d[:, 1])))
msm.run_representation(); msm.run_clustering_normal(k)
M = msm.adata_MENDER; lab = pd.Categorical(M.obs["MENDER"]).codes.astype(int)
emb = np.asarray(M.X.toarray() if sp.issparse(M.X) else M.X, np.float32)
np.savez(out, labels=lab, emb=emb, versions=np.array(["SOMENDER 1.1", f"scanpy {sc.__version__}"]))
