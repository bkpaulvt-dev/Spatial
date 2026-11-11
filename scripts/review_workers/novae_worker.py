"""Novae (Bunne/Blampey et al., Nat Methods 2025; PyPI novae) in its own environment (envs/novae), ZERO-SHOT use of the pretrained model of the matching species (prism-oncology/novae-human-0 for DLPFC and breast,
novae-mouse-0 for every mouse dataset), no fine-tuning: spatial graph (Delaunay, edges longer than the 99th percentile removed) -> compute_representations(zero_shot=True) -> assign_domains(n_domains = K).
The pretrained weights come from Hugging Face (cache under $BASE/.cache/huggingface via HF_HOME). Deviation recorded: our coordinate scales do not allow Novae's technology-specific radius, hence the percentile pruning.
Usage: python novae_worker.py <indir> <out.npz> <k> <seed> <dataset>"""
import sys, os, numpy as np, scipy.sparse as sp, pandas as pd
indir, out, k, seed, ds = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
import anndata, scanpy as sc, torch, novae
torch.set_num_threads(1); torch.manual_seed(seed); np.random.seed(seed)
X = sp.load_npz(os.path.join(indir, "counts.npz")).tocsr().astype(np.float32)
a = anndata.AnnData(X, obs=pd.DataFrame(index=[f"s{i}" for i in range(X.shape[0])]), var=pd.DataFrame(index=open(os.path.join(indir, "genes.txt")).read().split("\n")[:X.shape[1]]))
a.obsm["spatial"] = np.load(os.path.join(indir, "spatial.npy"))
human = ds in ("dlpfc", "brca")
name = "prism-oncology/novae-human-0" if human else "prism-oncology/novae-mouse-0"
novae.spatial_neighbors(a, percentile=99, delaunay=True)
model = novae.Novae.from_pretrained(name)
model.compute_representations(a, zero_shot=True, accelerator="cpu", num_workers=0)
key = model.assign_domains(a, n_domains=k)
lab = pd.Categorical(a.obs[key].astype(str)).codes.astype(int)
np.savez(out, labels=lab, emb=np.asarray(a.obsm["novae_latent"], np.float32), versions=np.array([f"novae {novae.__version__}", name]))
