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
        C = np.asarray(a.obsm["spatial"], float); row, col = _lattice(C)
        pd.DataFrame({"x": C[:, 0], "y": C[:, 1], "row": row, "col": col}, index=bc).to_csv(os.path.join(td, "coords.csv"))
        p = subprocess.run(["Rscript", os.path.join(HERE, script), td, str(k), str(seed), ds, *map(str, extra)], capture_output=True, text=True,
                           timeout=timeout, env=dict(os.environ, **(env or {})))
        if p.returncode != 0:
            raise RuntimeError(f"{script} failed (exit code {p.returncode}; -9 = killed, e.g. out of memory): {p.stderr[-1200:]} | stdout: {p.stdout[-300:]}")
        return pd.read_csv(os.path.join(td, "labels.csv")).set_index("barcode").loc[bc, "label"].to_numpy().astype(int)


def bayesspace_st(a, k, seed, ds):
    """BayesSpace with platform 'ST' (square-lattice neighbours) on a bin/spot grid: same settings as the Visium run of run_r_method.R otherwise."""
    lab = run_r("review_bayesspace_st.R", a, k, seed, ds, env={"BSPACE_NREP": os.environ.get("REVIEW_DRY_NREP", "50000")})
    return {"labels": lab, "emb": None, "extra": {"platform_ST": 1.0}}


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
            p = subprocess.run(["Rscript", os.path.join(HERE, "review_bass_multi.R"), td, str(len(secs)), str(R), str(seed), ds], capture_output=True, text=True, timeout=24 * 3600,
                               env=dict(os.environ, **({"BASS_NSAMPLE": dry} if dry else {})))
            if p.returncode != 0:
                raise RuntimeError(f"review_bass_multi.R failed (exit code {p.returncode}; -9 = killed, e.g. out of memory): {p.stderr[-1200:]} | stdout: {p.stdout[-300:]}")
            labs = {s: pd.read_csv(os.path.join(td, f"labels_{i}.csv"))["label"].astype(int).tolist() for i, s in enumerate(secs)}
        json.dump({"R": R, "group": group, "labels": labs, "joint_fit_wall_s": time.time() - t0}, open(cf, "w"))
    c = json.load(open(cf))
    return {"labels": np.asarray(c["labels"][sec]), "emb": None, "extra": {"group_size": len(group), "R": c["R"], "joint_fit_wall_s": c["joint_fit_wall_s"]}}


ADAPTERS = {"bayesspace_st": bayesspace_st, "bass_multisample": bass_multisample}
