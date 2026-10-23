"""Export the seed-0 embeddings saved by the standardised runner (results/runs/<id>.npz, key 'emb') for the datasets that
were run only there (breast cancer, Stereo-seq) to results/emb/<dataset>_<section>_<method>.npy, the input of
clustering_lottery.py, k_sensitivity.py and (via its CSV export) mclust_seed.R.

python scripts/export_runner_emb.py [--force] [method ...]
"""
import glob, os, sys
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
force = "--force" in sys.argv
only = [a for a in sys.argv[1:] if not a.startswith("--")]
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, "results", "runs", "*__s0.npz"))):
    ds, sec, method, _ = os.path.basename(f)[:-4].split("__")
    if ds not in ("brca", "stereo") or (only and method not in only):
        continue
    out = os.path.join(ROOT, "results", "emb", f"{ds}_{sec}_{method}.npy")
    if os.path.exists(out) and not force:
        continue
    z = np.load(f)
    if "emb" not in z:
        continue
    np.save(out, z["emb"].astype(np.float32)); n += 1
print(n, "embeddings exported")
