"""Equivalence check of the STAGATE mclust wrapper (owner decision 2026-11-06), run BEFORE the wrapper is used for any record:
1. one STAGATE embedding (DLPFC 151673, seed 0) produced by the unchanged adapter (STAGATE's own mclust_R is replaced only to capture the embedding);
2. cluster it (a) with the wrapper (Mclust inside an R function, through rpy2, np/R seed 2020, EEE, K = 7) and (b) with plain Rscript (no rpy2, same Mclust call, set.seed(2020));
3. report the adjusted Rand index between the two label vectors (must be 1) and the number of differing labels. Writes results/review_stagate_mclust_check.json.
Usage: python scripts/review_stagate_mclust_check.py <path of the patched new_methods.py holding mclust_R_wrapped>"""
import ast, json, os, subprocess, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [ROOT, HERE]
patched = sys.argv[1]
import STAGATE_pyG as st  # noqa: E402
import new_methods  # noqa: E402  (unchanged adapter code)
from spatialbench.data import load_section  # noqa: E402
cap = {}
def capture(adata, num_cluster, modelNames="EEE", used_obsm="STAGATE", random_seed=2020):
    cap["emb"] = np.asarray(adata.obsm[used_obsm], dtype=np.float64).copy(); cap["k"] = num_cluster
    adata.obs["mclust"] = 1; adata.obs["mclust"] = adata.obs["mclust"].astype("category"); return adata
st.mclust_R = capture
a, = (load_section("dlpfc", "151673"),)
import scipy.sparse as sp
truth = a.obs["ground_truth"].to_numpy(dtype=object)
from spatialbench import metrics as M
k = int(len(set(truth[M.valid_mask(truth)].astype(str))))
new_methods.stagate(a, k, 0, "dlpfc")
Z, k = cap["emb"], cap["k"]
# (a) wrapper through rpy2: take the function source from the patched file
src = open(patched).read(); tree = ast.parse(src)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "mclust_R_wrapped")
ns = {"np": np}; exec(compile(ast.Module([fn], []), patched, "exec"), ns)
import anndata, pandas as pd
b = anndata.AnnData(np.zeros((Z.shape[0], 1)), obs=pd.DataFrame(index=[str(i) for i in range(Z.shape[0])])); b.obsm["STAGATE"] = Z
lab_a = ns["mclust_R_wrapped"](b, k, "EEE", "STAGATE", 2020).obs["mclust"].astype(int).to_numpy()
# (b) plain Rscript, no rpy2
with tempfile.TemporaryDirectory() as td:
    np.savetxt(os.path.join(td, "z.csv"), Z, delimiter=","); out = os.path.join(td, "lab.csv")
    code = f'suppressPackageStartupMessages(library(mclust)); x <- as.matrix(read.csv("{td}/z.csv", header=FALSE)); set.seed(2020); r <- Mclust(x, G={k}, modelNames="EEE"); write.csv(data.frame(label=r$classification), "{out}", row.names=FALSE)'
    p = subprocess.run(["Rscript", "-e", code], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-500:]
    lab_b = pd.read_csv(out)["label"].to_numpy().astype(int)
from sklearn.metrics import adjusted_rand_score
res = {"section": "dlpfc 151673", "seed": 0, "K": int(k), "n": int(len(lab_a)), "ARI_wrapper_vs_plain_Rscript": float(adjusted_rand_score(lab_a, lab_b)),
       "n_labels_differing_after_identity_relabel": int((lab_a != lab_b).sum()), "identical_label_vectors": bool(np.array_equal(lab_a, lab_b))}
json.dump(res, open(os.path.join(ROOT, "results", "review_stagate_mclust_check.json"), "w"), indent=1); print(json.dumps(res, indent=1))
