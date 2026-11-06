"""Novae (Blampey et al., Nat Methods 2025; PyPI novae) in its own environment (envs/novae), ZERO-SHOT with the published pretrained weights (Hugging Face MICS-Lab/novae-human-0 for human data,
MICS-Lab/novae-mouse-0 for mouse data; weights cached under $BASE/.cache/huggingface): spatial graph -> compute_representations(zero_shot=True) -> assign_domains(n_domains = K).
Graph: spot grids (spatialbench VISIUM group) technology='visium'; every other platform a Delaunay graph pruned at 6 x the median nearest-neighbour distance (documented choice; the tutorials use per-technology radii in microns).
Novae needs gene SYMBOLS: datasets whose var_names are not symbols fail with a clear error (recorded, not worked around).
Usage: python novae_worker.py <indir> <out.npz> <k> <seed> <dataset> <species human|mouse> <is_visium 0|1>"""
import sys, os, numpy as np, scipy.sparse as sp, pandas as pd
indir, out, k, seed, ds, species, vis = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6], int(sys.argv[7])
import anndata, scanpy as sc, torch, novae
from scipy.spatial import cKDTree
torch.set_num_threads(1); torch.manual_seed(seed); np.random.seed(seed)
X = sp.load_npz(os.path.join(indir, "counts.npz")).tocsr().astype(np.float32)
genes = open(os.path.join(indir, "genes.txt")).read().split("\n")[:X.shape[1]]
a = anndata.AnnData(X, obs=pd.DataFrame(index=[f"s{i}" for i in range(X.shape[0])]), var=pd.DataFrame(index=genes))
C = np.load(os.path.join(indir, "spatial.npy")); a.var_names_make_unique(); a.obsm["spatial"] = C
if sum(g.startswith(("ENSG", "ENSMUSG")) for g in genes) > 0.5 * len(genes):
    raise RuntimeError("Novae needs gene symbols but the var_names of this dataset are Ensembl ids: not run (no id-to-symbol table is part of the data)")
if vis: novae.spatial_neighbors(a, technology="visium")
else:
    d, _ = cKDTree(C).query(C, k=2); r = 6 * float(np.median(d[:, 1])); novae.spatial_neighbors(a, delaunay=True, radius=[0, r])
name = "MICS-Lab/novae-human-0" if species == "human" else "MICS-Lab/novae-mouse-0"
model = novae.Novae.from_pretrained(name)
model.compute_representations(a, zero_shot=True)
key = model.assign_domains(a, n_domains=k)
lab = pd.Categorical(a.obs[key]).codes.astype(int)
emb = np.asarray(a.obsm["novae_latent"], np.float32)
np.savez(out, labels=lab, emb=emb, versions=np.array([f"novae {novae.__version__}", name]))
