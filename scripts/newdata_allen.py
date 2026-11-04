"""Allen whole-mouse-brain MERFISH (Zhang et al., Nature 2023; Allen Brain Cell Atlas, dataset Zhuang-ABCA-1, coronal) for the new-datasets extension.

Rule fixed before running (docs/NEWDATA_COMMAND.md; owner's answers Q8): sections of Zhuang-ABCA-1 with MORE THAN 20,000 cells; sort them by
anterior-posterior position (median CCF x of their cells, checked against the section number); take the sections at the 25th, 50th and
75th percentile (nearest rank, idx = round(q * (n - 1))). Labels: the major CCF DIVISIONS (Allen CCFv3 term set "division") of the
registered cells, keeping divisions with at least 1% of the section's cells; every other cell gets label "NA" (stays in the data, is not scored).
Labels come from registration to the atlas (CCF), not from clustering. Targeted panel (1,122 genes): all genes, library-size normalised,
50 PCs (the paper's rule for panels); dataset name `allenmerfish` takes the targeted path through the CSV fallback of spatialbench.data.load_section.

    python scripts/newdata_allen.py --download     # metadata (~0.8 GB) + raw counts (1.2 GB) + CCF tables into data/Allen/ (resumable, SHA-256 recorded)
    python scripts/newdata_allen.py --select       # write results/newdata_allen_sections.json (the rule's output, with the per-section checks)
    python scripts/newdata_allen.py --export       # data/ext/csv/allenmerfish_<section>_{counts,info}.csv for the 3 chosen sections
"""
import argparse, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [HERE, ROOT]
B = "https://allen-brain-cell-atlas.s3.us-west-2.amazonaws.com/"
FILES = {   # local path relative to ROOT -> url
    "data/Allen/cell_metadata.csv": B + "metadata/Zhuang-ABCA-1/20230830/cell_metadata.csv",
    "data/Allen/ccf_coordinates.csv": B + "metadata/Zhuang-ABCA-1-CCF/20230830/ccf_coordinates.csv",
    "data/Allen/parcellation_membership.csv": B + "metadata/Allen-CCF-2020/20230630/parcellation_to_parcellation_term_membership.csv",
    "data/Allen/Zhuang-ABCA-1-raw.h5ad": B + "expression_matrices/Zhuang-ABCA-1/20230830/Zhuang-ABCA-1-raw.h5ad",
}
SEL = os.path.join(ROOT, "results", "newdata_allen_sections.json")
MIN_CELLS = 20000; MIN_FRAC = 0.01; QUANTILES = (0.25, 0.50, 0.75)
P = lambda rel: os.path.join(ROOT, rel)


def download():
    from download_new_datasets import fetch_resume, verify_or_record
    for rel, url in FILES.items():
        if not os.path.exists(P(rel)):
            print("download", url, flush=True); fetch_resume(url, P(rel))
    if not verify_or_record(list(FILES)):
        raise SystemExit("checksum problem")


def divisions():
    """parcellation_index -> (division acronym, division name) from the CCF term-set membership."""
    m = pd.read_csv(P("data/Allen/parcellation_membership.csv"), usecols=["parcellation_index", "parcellation_term_set_name", "parcellation_term_acronym", "parcellation_term_name"])
    d = m[m.parcellation_term_set_name == "division"].drop_duplicates("parcellation_index")
    # CCF divisions named "unassigned" / "brain-unassigned" / "fiber tracts-unassigned" are placeholders for voxels without an anatomical
    # assignment, not domains: they get no label (None -> "NA", kept in the data, never scored)
    return {int(r.parcellation_index): (None if "unassigned" in f"{r.parcellation_term_acronym} {r.parcellation_term_name}".lower() else r.parcellation_term_acronym,
                                         r.parcellation_term_name) for r in d.itertuples()}


def select():
    meta = pd.read_csv(P("data/Allen/cell_metadata.csv"), usecols=["cell_label", "brain_section_label"])
    ccf = pd.read_csv(P("data/Allen/ccf_coordinates.csv"), usecols=["cell_label", "x", "parcellation_index"])
    df = meta.merge(ccf, on="cell_label", how="left")
    g = df.groupby("brain_section_label")
    tab = pd.DataFrame({"n_cells": g.size(), "ap_ccf_x_median": g.x.median(), "n_registered": g.parcellation_index.apply(lambda s: int((s.fillna(0) > 0).sum()))})
    tab["section_no"] = [float(s.split(".")[-1]) for s in tab.index]
    cand = tab[tab.n_cells > MIN_CELLS].sort_values("ap_ccf_x_median")
    rho = float(cand[["section_no", "ap_ccf_x_median"]].corr(method="spearman").iloc[0, 1])
    n = len(cand); picked = [cand.index[int(round(q * (n - 1)))] for q in QUANTILES]
    div = divisions(); lab = {}
    for sec in picked:
        sub = df[df.brain_section_label == sec]
        names = sub.parcellation_index.fillna(0).astype(int).map(lambda i: div.get(i, (None, None))[0])
        frac = names.value_counts() / len(sub)
        lab[sec] = {k: round(float(v), 4) for k, v in frac.items() if v >= MIN_FRAC}
    out = {"rule": f"sections with > {MIN_CELLS} cells ordered by median CCF x; 25th/50th/75th percentile by nearest rank; labels = CCF divisions with >= {MIN_FRAC:.0%} of the section's cells",
           "n_candidate_sections": n, "spearman_section_number_vs_ccf_x": rho, "sections": picked,
           "per_section": {s: {"n_cells": int(tab.loc[s, "n_cells"]), "ap_ccf_x_median_mm": float(tab.loc[s, "ap_ccf_x_median"]), "n_registered": int(tab.loc[s, "n_registered"]),
                               "division_fractions_kept": lab[s], "K": len(lab[s])} for s in picked}}
    json.dump(out, open(SEL, "w"), indent=1); print(json.dumps(out, indent=1))


def export():
    import anndata
    sel = json.load(open(SEL)); div = divisions()
    meta = pd.read_csv(P("data/Allen/cell_metadata.csv"), usecols=["cell_label", "brain_section_label", "x", "y"], dtype={"cell_label": str}).set_index("cell_label")
    ccf = pd.read_csv(P("data/Allen/ccf_coordinates.csv"), usecols=["cell_label", "parcellation_index"], dtype={"cell_label": str}).set_index("cell_label")
    a = anndata.read_h5ad(P("data/Allen/Zhuang-ABCA-1-raw.h5ad"), backed="r")
    var = [str(v) for v in a.var_names]
    os.makedirs(P("data/ext/csv"), exist_ok=True)
    for sec in sel["sections"]:
        ids = meta.index[meta.brain_section_label == sec]
        keep_div = set(sel["per_section"][sec]["division_fractions_kept"])
        acr = ccf.reindex(ids)["parcellation_index"].fillna(0).astype(int).map(lambda i: div.get(i, (None, None))[0])   # cells without a CCF row: unlabelled
        z = acr.where(acr.isin(keep_div), "NA")
        pos = [a.obs_names.get_loc(i) for i in ids] if hasattr(a.obs_names, "get_loc") else None
        X = a.X[np.sort(pos)] if pos is not None else None
        order = np.argsort(pos); ids = ids[order]; z = z.iloc[order]              # restore the order of the rows read
        X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
        key = sec.replace("Zhuang-ABCA-1.", "ABCA1-")
        pd.DataFrame(X.astype(np.float32), index=ids.astype(str), columns=var).to_csv(P(f"data/ext/csv/allenmerfish_{key}_counts.csv"))
        pd.DataFrame({"z": z.values, "x": meta.loc[ids, "x"].values, "y": meta.loc[ids, "y"].values}, index=ids.astype(str)).to_csv(P(f"data/ext/csv/allenmerfish_{key}_info.csv"))
        print(sec, "->", key, X.shape, "labels:", z.value_counts().to_dict(), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--download", action="store_true"); ap.add_argument("--select", action="store_true"); ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    if a.download: download()
    if a.select: select()
    if a.export: export()
