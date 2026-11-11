"""Additional methods of the review extension (docs/DEEPMED2_NEXT.md). Registered by scripts/review_bench_run.py; scripts/adapters.py and
scripts/new_methods.py (existing method code and settings) are not changed. Each adapter: f(adata, k, seed, dataset) -> {"labels","emb","extra"}."""
import os, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _lattice(C):
    """Integer lattice (row, col) of bins/spots from their coordinates (spacing = median nearest-neighbour distance)."""
    from scipy.spatial import cKDTree
    C = np.asarray(C, float); d, _ = cKDTree(C).query(C, k=2); s = float(np.median(d[:, 1])) or 1.0
    return np.round((C[:, 1] - C[:, 1].min()) / s).astype(int), np.round((C[:, 0] - C[:, 0].min()) / s).astype(int)


def run_r(script, a, k, seed, ds, extra=(), timeout=24 * 3600, env=None):
    """Export counts + coordinates (+ integer lattice) of one section, run `Rscript scripts/<script> dir k seed ds`, return integer labels."""
    import scipy.io, scipy.sparse as sp, pandas as pd
    with tempfile.TemporaryDirectory() as td:
        scipy.io.mmwrite(os.path.join(td, "counts.mtx"), sp.csr_matrix(a.X).T.tocoo())
        open(os.path.join(td, "genes.txt"), "w").write("\n".join(map(str, a.var_names)) + "\n")
        bc = [f"s{i}" for i in range(a.n_obs)]; open(os.path.join(td, "barcodes.txt"), "w").write("\n".join(bc) + "\n")
        C = np.asarray(a.obsm["spatial"], float)
        row, col = (a.obs["array_row"].to_numpy(int), a.obs["array_col"].to_numpy(int)) if "array_row" in a.obs and "array_col" in a.obs else _lattice(C)
        pd.DataFrame({"x": C[:, 0], "y": C[:, 1], "row": row, "col": col}, index=bc).to_csv(os.path.join(td, "coords.csv"))
        p = subprocess.run(["Rscript", os.path.join(HERE, script), td, str(k), str(seed), ds, *map(str, extra)], capture_output=True, text=True,
                           timeout=timeout, env=dict(os.environ, **(env or {})))
        if p.returncode != 0:
            raise RuntimeError(f"{script} failed (exit code {p.returncode}; -9 = killed, e.g. out of memory): {p.stderr[-1200:]} | stdout: {p.stdout[-300:]}")
        global LAST_R_EMB
        LAST_R_EMB = pd.read_csv(os.path.join(td, "emb.csv"), index_col=0).loc[bc].to_numpy(float) if os.path.exists(os.path.join(td, "emb.csv")) else None
        lab = pd.read_csv(os.path.join(td, "labels.csv")).set_index("barcode").loc[bc, "label"]
        return lab.fillna(-1).to_numpy().astype(int)   # a spot that the method dropped (its own quality filter) gets label -1 = unassigned (counted as wrong, never removed from the score)


LAST_R_EMB = None


def bayesspace_st(a, k, seed, ds):
    """BayesSpace with platform 'ST' (square-lattice neighbours) on a bin/spot grid: same settings as the Visium run of run_r_method.R otherwise."""
    lab = run_r("review_bayesspace_st.R", a, k, seed, ds, env={"BSPACE_NREP": os.environ.get("REVIEW_DRY_NREP", "50000")})
    return {"labels": lab, "emb": None, "extra": {"platform_ST": 1.0, "gamma": 2.0}}   # gamma = package default of platform ST (2); differs from the Visium value 3


def run_env_worker(env, worker, a, k, seed, ds, extra=(), timeout=24 * 3600):
    """Run scripts/review_workers/<worker> with the python of $BASE/envs/<env> (own environment). The section is passed as files (raw counts, gene names, coordinates); no label is given
    to the worker. Returns (labels, embedding or None, version strings)."""
    import scipy.sparse as sp
    base = os.environ.get("BASE", "/mnt/disk/bikashkumar/SpatialBench")
    with tempfile.TemporaryDirectory() as td:
        sp.save_npz(os.path.join(td, "counts.npz"), sp.csr_matrix(a.X)); open(os.path.join(td, "genes.txt"), "w").write("\n".join(map(str, a.var_names)) + "\n")
        np.save(os.path.join(td, "spatial.npy"), np.asarray(a.obsm["spatial"], float))
        out = os.path.join(td, "out.npz")
        p = subprocess.run([os.path.join(base, "envs", env, "bin", "python"), os.path.join(HERE, "review_workers", worker), td, out, str(k), str(seed), ds, *map(str, extra)],
                           capture_output=True, text=True, timeout=timeout, env=dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"))
        if p.returncode != 0:
            raise RuntimeError(f"{worker} failed (exit code {p.returncode}; -9 = killed, e.g. out of memory): {p.stderr[-1200:]} | stdout: {p.stdout[-300:]}")
        z = np.load(out, allow_pickle=False)
        return z["labels"].astype(int), (np.asarray(z["emb"]) if "emb" in z.files else None), list(z["versions"])


def cellcharter(a, k, seed, ds):
    lab, emb, ver = run_env_worker("m2", "cellcharter_worker.py", a, k, seed, ds)
    return {"labels": lab, "emb": emb, "extra": {}}


def histar_official(a, k, seed, ds):
    lab, emb, ver = run_env_worker("histar", "histar_official_worker.py", a, k, seed, ds)
    return {"labels": lab, "emb": emb, "extra": {"used_fallback_mclust": float("inside an R function" in ver[1])}}


def novae_zs(a, k, seed, ds):
    lab, emb, ver = run_env_worker("novae", "novae_worker.py", a, k, seed, ds)
    return {"labels": lab, "emb": emb, "extra": {}}


def mender(a, k, seed, ds):
    from spatialbench.data import VISIUM
    lab, emb, ver = run_env_worker("mender", "mender_worker.py", a, k, seed, ds, extra=(int(ds in VISIUM),))
    return {"labels": lab, "emb": emb, "extra": {}}


# ---- M5: multi-sample BASS (the way the BASS authors ran it: sections of one donor / animal jointly; BASS-Analysis analysis/DLPFC.Rmd and MERFISH.Rmd) ----
BASS_GROUPS = {"dlpfc": [["151507", "151508", "151509", "151510"], ["151669", "151670", "151671", "151672"], ["151673", "151674", "151675", "151676"]],
               "merfish": [["-0.04", "-0.09", "-0.14", "-0.19", "-0.24"]]}


def bass_multisample(a, k, seed, ds):
    """Joint BASS fit of all sections of the group of the current section (cached per group and seed so that each section's job reads its own labels).
    Settings = the single-section BASS branch of run_r_method.R (which follows the authors' Rmd files); R = the K of the group (authors: 7 for DLPFC, 8 for MERFISH)."""
    import json, time, scipy.io, scipy.sparse as sp, pandas as pd
    from spatialbench.data import load_section
    sec = os.environ["REVIEW_SECTION"]
    group = next(g for g in BASS_GROUPS[ds] if sec in g)
    base = os.environ.get("BASE", "/mnt/disk/bikashkumar/SpatialBench")
    dry = os.environ.get("REVIEW_DRY_NREP")   # dry runs only: fewer MCMC samples and a separate cache (never mixed with real results)
    cache = os.path.join(base, "review_scratch", "bassms_dry" if dry else "bassms"); os.makedirs(cache, exist_ok=True)
    cf = os.path.join(cache, f"{ds}_{group[0]}_s{seed}.json")
    if not os.path.exists(cf):
        t0 = time.time(); secs = {s: (a if s == sec else load_section(ds, s)) for s in group}
        from spatialbench import metrics as M
        Ks = [len(set(map(str, x.obs["ground_truth"].to_numpy(dtype=object)[M.valid_mask(x.obs["ground_truth"].to_numpy(dtype=object))]))) for x in secs.values()]
        R = max(set(Ks), key=Ks.count)   # K shared by the group's sections (the authors' R)
        with tempfile.TemporaryDirectory() as td:
            for i, (s, x) in enumerate(secs.items()):
                d = os.path.join(td, str(i)); os.makedirs(d)
                scipy.io.mmwrite(os.path.join(d, "counts.mtx"), sp.csr_matrix(x.X).T.tocoo())
                open(os.path.join(d, "genes.txt"), "w").write("\n".join(map(str, x.var_names)) + "\n")
                open(os.path.join(d, "barcodes.txt"), "w").write("\n".join(f"s{j}" for j in range(x.n_obs)) + "\n")
                C = np.asarray(x.obsm["spatial"], float); pd.DataFrame({"x": C[:, 0], "y": C[:, 1]}).to_csv(os.path.join(d, "coords.csv"), index=False)
            try:
                p = subprocess.run(["Rscript", os.path.join(HERE, "review_bass_multi.R"), td, str(len(secs)), str(R), str(seed), ds], capture_output=True, text=True,
                                   timeout=24 * 3600 - 600, env=dict(os.environ, **({"BASS_NSAMPLE": dry} if dry else {})))
            except subprocess.TimeoutExpired:   # the joint fit is shared by the group's jobs: record the limit once, so the siblings fail at once instead of repeating a 24 h fit
                msg = "time limit (24 h) of the joint multi-sample fit"
                json.dump({"failed": msg}, open(cf, "w")); raise RuntimeError(msg)
            if p.returncode != 0:
                msg = f"review_bass_multi.R failed (exit code {p.returncode}; -9 = killed, e.g. out of memory): {p.stderr[-1200:]} | stdout: {p.stdout[-300:]}"
                if p.returncode in (-9, 137): json.dump({"failed": "memory limit of the joint multi-sample fit (killed)"}, open(cf, "w"))
                raise RuntimeError(msg)
            labs = {s: pd.read_csv(os.path.join(td, f"labels_{i}.csv"))["label"].astype(int).tolist() for i, s in enumerate(secs)}
        json.dump({"R": R, "group": group, "labels": labs, "joint_fit_wall_s": time.time() - t0}, open(cf, "w"))
    c = json.load(open(cf))
    if "failed" in c:
        raise RuntimeError(c["failed"] + " (recorded by the first job of the group)")
    return {"labels": np.asarray(c["labels"][sec]), "emb": None, "extra": {"group_size": len(group), "R": c["R"], "joint_fit_wall_s": c["joint_fit_wall_s"]}}


# ---- A9: Spatial-MGCN with pre-registered label-free stopping rules (docs/PREREGISTERED_A9.md); model, graphs, loss and preprocessing = new_methods.spatial_mgcn ----
def spatial_mgcn_a9(a, k, seed, ds):
    import importlib, io, contextlib, scanpy as sc, scipy.sparse as sp, torch
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score
    import new_methods as nm
    sys_path = list(__import__("sys").path); __import__("sys").path.insert(0, nm.MGCN_DIR)
    U = importlib.import_module("utils"); Mo = importlib.import_module("models")
    __import__("sys").path.remove(nm.MGCN_DIR)
    nm._seed(seed)
    a = a.copy()
    if a.n_vars > 3000:
        sc.pp.filter_genes(a, min_cells=100)
        sc.pp.highly_variable_genes(a, flavor="seurat_v3", n_top_genes=3000)
        a = a[:, a.var["highly_variable"]].copy()
    X = a.X.toarray() if hasattr(a.X, "toarray") else np.asarray(a.X, dtype=np.float64)
    a.X = X / np.maximum(X.sum(1, keepdims=True), 1) * 10000
    sc.pp.scale(a, zero_center=False, max_value=10)
    radius = 4.1 * nm._nn_spacing(a.obsm["spatial"])
    with contextlib.redirect_stdout(io.StringIO()):
        fadj = U.features_construct_graph(a.X, k=14)
        sadj, graph_nei, graph_neg = U.spatial_construct_graph1(a, radius=radius)
    nf = U.sparse_mx_to_torch_sparse_tensor(U.normalize_sparse_matrix(fadj + sp.eye(fadj.shape[0])))
    ns = U.sparse_mx_to_torch_sparse_tensor(U.normalize_sparse_matrix(sadj + sp.eye(sadj.shape[0])))
    gnei, gneg = torch.LongTensor(np.asarray(graph_nei)), torch.LongTensor(np.asarray(graph_neg))
    feats = torch.FloatTensor(np.asarray(a.X))
    model = Mo.Spatial_MGCN(nfeat=feats.shape[1], nhid1=128, nhid2=64, dropout=0)
    opt = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=5e-4)
    EP = 401; losses = []; embs = {}
    for epoch in range(EP):
        model.train(); opt.zero_grad()
        com1, com2, emb, pi, disp, mean = model(feats, ns, nf)
        loss = (1 * U.ZINB(pi, theta=disp, ridge_lambda=0).loss(feats, mean, mean=True)
                + 10 * U.consistency_loss(com1, com2) + 0.1 * U.regularization_loss(emb, gnei, gneg))
        loss.backward(); opt.step(); losses.append(float(loss.detach()))
        if epoch >= 100: embs[epoch] = np.nan_to_num(emb.detach().numpy()).astype(np.float32)
    L = np.asarray(losses)
    t_p = next((t for t in range(100, EP) if abs(L[t - 50]) > 0 and (L[t - 50] - L[t]) / abs(L[t - 50]) < 0.001), EP - 1)
    rule = {"F": 200, "P": int(t_p), "L": EP - 1}
    labs = {r: KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(embs[e]) for r, e in rule.items()}
    y = a.obs["ground_truth"].to_numpy().astype(object); keep = np.array([isinstance(v, str) and v != "nan" for v in y])
    ari = {r: float(adjusted_rand_score(y[keep], labs[r][keep])) for r in labs}   # reporting only: no label enters any selection
    base = os.environ.get("BASE", "/mnt/disk/bikashkumar/SpatialBench")
    d = os.path.join(base, "Spatial", "results", "review_a9_labels"); os.makedirs(d, exist_ok=True)
    np.savez_compressed(os.path.join(d, f"{ds}__{os.environ.get('REVIEW_SECTION', '')}__s{seed}.npz"), losses=L, labels_F=labs["F"], labels_P=labs["P"], labels_L=labs["L"], epochs=np.array([200, t_p, EP - 1]))
    return {"labels": labs["F"], "emb": embs[200], "extra": {"ARI_rule_F": ari["F"], "ARI_rule_P": ari["P"], "ARI_rule_L": ari["L"], "plateau_epoch": float(t_p), "loss_end": float(L[-1])}}


def spatialpca(a, k, seed, ds):
    lab = run_r("review_spatialpca.R", a, k, seed, ds)
    emb = LAST_R_EMB
    if emb is not None and np.isnan(emb).any():
        emb = np.where(np.isnan(emb), np.nanmean(emb, axis=0), emb)    # dropped spots: column mean (they are also label -1)
    return {"labels": lab, "emb": emb, "extra": {"n_unassigned": float((lab < 0).sum())}}


def precast(a, k, seed, ds):
    from spatialbench.data import VISIUM
    lab = run_r("review_precast.R", a, k, seed, ds, extra=(int(ds in VISIUM),))
    emb = LAST_R_EMB
    if emb is not None and np.isnan(emb).any():
        emb = np.where(np.isnan(emb), np.nanmean(emb, axis=0), emb)
    return {"labels": lab, "emb": emb, "extra": {"n_unassigned": float((lab < 0).sum())}}


HUMAN = {"dlpfc", "brca", "visiumhd_crc"}   # human datasets; all other registered datasets are mouse


def novae_zero_shot(a, k, seed, ds):
    from spatialbench.data import VISIUM
    lab, emb, ver = run_env_worker("novae", "novae_worker.py", a, k, seed, ds, extra=("human" if ds in HUMAN else "mouse", int(ds in VISIUM)))
    return {"labels": lab, "emb": emb, "extra": {}}


def drsc(a, k, seed, ds):
    from spatialbench.data import VISIUM
    lab = run_r("review_drsc.R", a, k, seed, ds, extra=(int(ds in VISIUM),))
    return {"labels": lab, "emb": LAST_R_EMB, "extra": {}}


ADAPTERS = {"drsc": drsc, "novae": novae_zero_shot, "precast": precast, "spatialpca": spatialpca, "bayesspace_st": bayesspace_st, "bass_multisample": bass_multisample, "cellcharter": cellcharter, "mender": mender, "histar_official": histar_official, "spatial_mgcn_a9": spatial_mgcn_a9}


_VER = {}


def version_of(method):
    """Package / code version string of a review method, stored in every record (field method_version)."""
    if method in _VER:
        return _VER[method]
    base = os.environ.get("BASE", "/mnt/disk/bikashkumar/SpatialBench")

    def rpkg(name):
        try:
            return subprocess.run(["Rscript", "-e", f"cat(as.character(packageVersion('{name}')))"], capture_output=True, text=True, timeout=120,
                                  env=dict(os.environ, R_LIBS=os.path.join(base, "Rlib"))).stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def freeze(env, pkg):
        try:
            for l in open(os.path.join(base, "envs", f"{env}.freeze.txt")):
                if l.lower().startswith(pkg.lower() + "=="):
                    return l.strip()
        except Exception:
            pass
        return f"{pkg} (version unknown)"
    v = {"drsc": lambda: "DR.SC " + rpkg("DR.SC"), "novae": lambda: freeze("novae", "novae") + "; zero-shot pretrained weights MICS-Lab/novae-human-0 (human) / novae-mouse-0 (mouse)", "novae_zs": lambda: freeze("novae", "novae") + "; zero-shot pretrained weights from Hugging Face (prism-oncology/novae-human-0 or novae-mouse-0)", "spatialpca": lambda: "SpatialPCA " + rpkg("SpatialPCA"), "precast": lambda: "PRECAST " + rpkg("PRECAST"), "bayesspace": lambda: "BayesSpace " + rpkg("BayesSpace"), "bayesspace_st": lambda: "BayesSpace " + rpkg("BayesSpace") + "; gamma = platform default (2 for ST), differs from the Visium value 3", "bass_multisample": lambda: "BASS " + rpkg("BASS"),
         "cellcharter": lambda: freeze("m2", "cellcharter") + "; " + freeze("m2", "scvi-tools"), "mender": lambda: freeze("mender", "SOMENDER"),
         "histar_official": lambda: "official HiSTaR code, pinned commit 0039a3b", "spatial_mgcn_a9": lambda: "Spatial-MGCN repository commit cf4412d; rules F=epoch 200, P=loss plateau, L=epoch 400 (docs/PREREGISTERED_A9.md)"}.get(method, lambda: "")
    _VER[method] = v()
    return _VER[method]
