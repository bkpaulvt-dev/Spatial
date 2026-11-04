"""Simulated tissues for the domain-size experiment of the new-datasets extension (docs/PREREGISTERED_SIM.md).

120 x 120 square lattice (14,400 spots, spacing 1), K = 6 domains, per-domain mean expression profiles taken from the layers L1-L6 of
DLPFC section 151507 (a dev section), negative-binomial counts (phi = 0.5, lognormal size factors, sigma = 0.3). Self-written generator
(gamma-Poisson with numpy): SRTsim / scDesign3 estimate their own models and give no control over the geometry at a fixed effect size.

  geometry A "layered bands"  -> dataset sim_bands,  sections m<m>_r<rep>,  m in {1, 2, 4, 7}  (domain = floor(row * 6m / 120) mod 6)
  geometry B "random blocks"  -> dataset sim_blocks, sections w<w>_r<rep>,  w in {3, 5, 8, 12, 20}  (random domain per w x w block)

    python scripts/simulate_domains.py                  # all 45 sections into data/Sim/<dataset>/<section>.h5ad (skips existing files)
    python scripts/simulate_domains.py --examples       # also docs/figures/newdata_sim_examples.png (domain maps, no expression)
Writes results/newdata_sim_manifest.json (generator, parameters, per-section checks).
"""
import argparse, hashlib, json, os, sys, time
import numpy as np, scipy.sparse as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path[:0] = [ROOT]
N = 120; K = 6; PHI = 0.5; SIGMA = 0.3; N_GENES = 5000; REPS = 5; REF_SECTION = "151507"
LAYERS = ["Layer1", "Layer2", "Layer3", "Layer4", "Layer5", "Layer6"]
SETTINGS = [("sim_bands", f"m{m}", m, 1) for m in (1, 2, 4, 7)] + [("sim_blocks", f"w{w}", w, 2) for w in (3, 5, 8, 12, 20)]
OUT = os.path.join(ROOT, "data", "Sim")
MANIFEST = os.path.join(ROOT, "results", "newdata_sim_manifest.json")


def domain_map(geometry: int, param: int, rep: int) -> np.ndarray:
    """(N, N) array of domain indices 0..K-1 (axis 0 = row = y, axis 1 = column = x)."""
    rows = np.arange(N)[:, None] * np.ones((1, N), int)
    if geometry == 1:                                           # bands along the row axis, same order repeated m times
        return (rows * K * param // N) % K
    rng = np.random.default_rng([2026, geometry, param, rep])
    nb = N // param
    while True:                                                 # rejection: all K domains must occur
        blocks = rng.integers(0, K, size=(nb, nb))
        if len(np.unique(blocks)) == K:
            return np.kron(blocks, np.ones((param, param), int))


def profiles():
    """mu[g, d]: composition of domain d (layers L1-L6 of the reference section) on the top N_GENES genes, scaled to L0 counts."""
    from spatialbench.data import load_section
    a = load_section("dlpfc", REF_SECTION)
    lab = a.obs["ground_truth"].astype(str).to_numpy()
    keep = np.isin(lab, LAYERS)
    X = a.X[keep].tocsc(); lab = lab[keep]
    top = np.argsort(-np.asarray(X.mean(0)).ravel(), kind="stable")[:N_GENES]
    X = X[:, top].tocsr()
    lib = np.asarray(X.sum(1)).ravel(); L0 = float(np.median(lib))
    mu = np.zeros((N_GENES, K))
    for d, l in enumerate(LAYERS):
        m = lab == l
        mu[:, d] = np.asarray(X[m].sum(0)).ravel() / lib[m].sum() * L0
    return mu, [str(g) for g in a.var_names[top]], L0


def simulate(mu, dom, rng, chunk=500):
    """Counts (spots x genes, csr float32) from NB(mean = s_i * mu[g, d(i)], var = mean + PHI * mean^2)."""
    n = dom.size
    s = np.exp(rng.normal(-SIGMA ** 2 / 2, SIGMA, n))
    parts = []
    for g0 in range(0, mu.shape[0], chunk):
        m = s[:, None] * mu[g0:g0 + chunk][:, dom].T
        lam = rng.gamma(1 / PHI, PHI * np.maximum(m, 1e-12))
        parts.append(sp.csr_matrix(rng.poisson(lam).astype(np.float32)))
    return sp.hstack(parts, format="csr")


def write_section(ds, sec, geometry, param, rep, mu, genes):
    import anndata, pandas as pd
    path = os.path.join(OUT, ds, f"{sec}.h5ad")
    if os.path.exists(path):
        return None
    dom = domain_map(geometry, param, rep).ravel()
    rng = np.random.default_rng([2026, geometry, param, rep, 1])          # expression stream (separate from the geometry stream)
    X = simulate(mu, dom, rng)
    yy, xx = np.divmod(np.arange(N * N), N)
    a = anndata.AnnData(X, obs=pd.DataFrame({"ground_truth": [f"domain_{d + 1}" for d in dom], "array_row": yy, "array_col": xx},
                                            index=[f"s{i}" for i in range(N * N)]), var=pd.DataFrame(index=genes))
    a.obsm["spatial"] = np.column_stack([xx, yy]).astype(np.float64)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    a.write_h5ad(path + ".tmp"); os.replace(path + ".tmp", path)
    frac = np.bincount(dom, minlength=K) / dom.size
    return {"id": f"{ds}/{sec}", "n_spots": int(a.n_obs), "n_genes": int(a.n_vars), "K": int(len(np.unique(dom))),
            "domain_area_min": float(frac.min()), "domain_area_max": float(frac.max()), "density": float(X.nnz / np.prod(X.shape)),
            "mean_library": float(X.sum(1).mean()), "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}


def examples():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#8a5cd6", "#c9a227", "#5a5a5a"]
    items = [("A: m = 1 (bands about 20 wide)", 1, 1), ("A: m = 4 (about 5)", 1, 4), ("A: m = 7 (about 3)", 1, 7),
             ("B: w = 20", 2, 20), ("B: w = 8", 2, 8), ("B: w = 3", 2, 3)]
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.9))
    for a, (t, g, p) in zip(ax.ravel(), items):
        a.imshow(domain_map(g, p, 0), cmap=matplotlib.colors.ListedColormap(cols),
                 interpolation="nearest", origin="upper"); a.set_title(t, fontsize=8, loc="left"); a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Simulated tissues (120 x 120 lattice, K = 6): geometry A layered bands, geometry B random blocks (replicate 0)", fontsize=8, x=0.01, ha="left")
    fig.tight_layout(); os.makedirs(os.path.join(ROOT, "docs", "figures"), exist_ok=True)
    out = os.path.join(ROOT, "docs", "figures", "newdata_sim_examples.png"); fig.savefig(out, dpi=200); print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--examples", action="store_true"); a = ap.parse_args()
    t0 = time.time(); mu, genes, L0 = profiles(); print(f"profiles: {len(genes)} genes, L0 = {L0:.0f}", flush=True)
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    man.update(generator="self-written numpy gamma-Poisson (SRTsim / scDesign3 not used)", lattice=N, K=K, phi=PHI, size_factor_sigma=SIGMA,
               n_genes=N_GENES, reference=f"DLPFC {REF_SECTION} layers L1-L6", L0=L0, replicates=REPS, preregistration="docs/PREREGISTERED_SIM.md")
    man.setdefault("sections", {})
    for ds, tag, param, geometry in SETTINGS:
        for rep in range(REPS):
            r = write_section(ds, f"{tag}_r{rep}", geometry, param, rep, mu, genes)
            if r:
                man["sections"][r["id"]] = r; print(f"{r['id']:<22} K={r['K']} area {r['domain_area_min']:.3f}-{r['domain_area_max']:.3f} "
                                                   f"density {r['density']:.2f}  [{time.time() - t0:.0f}s]", flush=True)
                json.dump(man, open(MANIFEST, "w"), indent=1)
    json.dump(man, open(MANIFEST, "w"), indent=1)
    if a.examples:
        examples()
    print("SIM_DONE", len(man["sections"]), "sections")
