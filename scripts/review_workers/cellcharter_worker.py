"""CellCharter (Varrone et al., Nat Genet 2024) in its own environment (envs/m2). Published workflow (docs/tutorials): scVI latent space -> Delaunay graph ->
aggregate neighbours over 3 layers (X_cellcharter) -> Gaussian mixture with K components (cc.tl.Cluster). Inputs via files (no label is passed to the worker).
Usage: python cellcharter_worker.py <indir> <out.npz> <k> <seed> <dataset>"""
import sys, os, numpy as np, scipy.sparse as sp, pandas as pd
indir, out, k, seed, ds = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
import anndata, scanpy as sc, scvi, squidpy as sq, cellcharter as cc, torch
torch.set_num_threads(1); scvi.settings.seed = seed; scvi.settings.num_threads = 1
X = sp.load_npz(os.path.join(indir, "counts.npz")).tocsr().astype(np.float32)
a = anndata.AnnData(X, obs=pd.DataFrame(index=[f"s{i}" for i in range(X.shape[0])]), var=pd.DataFrame(index=open(os.path.join(indir, "genes.txt")).read().split("\n")[:X.shape[1]]))
a.obsm["spatial"] = np.load(os.path.join(indir, "spatial.npy")); a.layers["counts"] = a.X.copy()
if a.n_vars > 2000:      # same gene selection as the benchmark's other whole-transcriptome inputs (2000 HVG, Seurat v3)
    sc.pp.highly_variable_genes(a, flavor="seurat_v3", n_top_genes=2000, layer="counts"); a = a[:, a.var["highly_variable"]].copy()
scvi.model.SCVI.setup_anndata(a, layer="counts")
m = scvi.model.SCVI(a); m.train(accelerator="cpu", enable_progress_bar=False)       # default architecture (n_latent 10) and default training budget
a.obsm["X_scVI"] = m.get_latent_representation()
sq.gr.spatial_neighbors(a, coord_type="generic", delaunay=True, spatial_key="spatial", percentile=99)    # CellCharter tutorial: Delaunay graph, long links removed
cc.gr.remove_long_links(a)
cc.gr.aggregate_neighbors(a, n_layers=3, use_rep="X_scVI", out_key="X_cellcharter", sample_key=None)
g = cc.tl.Cluster(n_clusters=k, random_state=seed, trainer_params=dict(accelerator="cpu", enable_progress_bar=False))
g.fit(a, use_rep="X_cellcharter")
lab = np.asarray(g.predict(a, use_rep="X_cellcharter")).astype(int)
np.savez(out, labels=lab, emb=np.asarray(a.obsm["X_cellcharter"], np.float32), versions=np.array([f"cellcharter {cc.__version__}", f"scvi {scvi.__version__}"]))
