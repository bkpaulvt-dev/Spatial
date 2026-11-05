"""D3/D4 data preparation: osmFISH (mouse somatosensory cortex) and BaristaSeq (mouse visual cortex VISp) from the SDMBench collection (Yuan et al., Nat Methods 2024;
Figshare project 163942, CC BY 4.0). Downloads resumably into data/ext/sdmbench/ (md5 checked against the Figshare API), exports the CSV fallback files
data/ext/csv/<ds>_<section>_{counts,info}.csv (targeted panels), and registers both datasets in configs/datasets_newdata.yaml (additive, once).
  python scripts/review_sdmbench.py [--download] [--export] [--register]      (no flag = all three)
Provenance caveats (written into the registry): labels are anatomical names but how SDMBench derived them is not fully documented; the osmFISH matrix is library-size normalised
(every cell sums to 5,328), not raw counts, and is analysed as released."""
import argparse, hashlib, json, os, subprocess, sys, urllib.request
import numpy as np, pandas as pd, scipy.sparse as sp
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DST = os.path.join(ROOT, "data", "ext", "sdmbench"); CSV = os.path.join(ROOT, "data", "ext", "csv")
ARTICLES = {"osmfish": 22565194, "baristaseq": 22550074}
FILES = {"osmfish": {"osmFISH": ("osmfish_remove_excluded.h5ad", "Region")},
         "baristaseq": {f"Slice_{i}": (f"Slice_{i}_removed.h5ad", "layer") for i in (1, 2, 3)}}


def download():
    os.makedirs(DST, exist_ok=True)
    for ds, art in ARTICLES.items():
        meta = json.load(urllib.request.urlopen(f"https://api.figshare.com/v2/articles/{art}", timeout=60))
        for f in meta["files"]:
            p = os.path.join(DST, f["name"])
            def md5(): return hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
            if md5() != f["computed_md5"]:
                subprocess.run(["curl", "-fsSL", "-C", "-", "--retry", "5", "-m", "1800", "-o", p, f["download_url"]], check=True)
            assert md5() == f["computed_md5"], f"md5 mismatch for {f['name']}"
            print("ok", f["name"], f["size"], f["computed_md5"], flush=True)


def export():
    import anndata
    os.makedirs(CSV, exist_ok=True)
    for ds, secs in FILES.items():
        for sec, (fn, lab) in secs.items():
            a = anndata.read_h5ad(os.path.join(DST, fn))
            X = a.X.toarray() if sp.issparse(a.X) else np.asarray(a.X)
            ids = [f"{sec}_{i}" for i in a.obs_names]
            pd.DataFrame(X, index=ids, columns=list(map(str, a.var_names))).to_csv(os.path.join(CSV, f"{ds}_{sec}_counts.csv"))
            xy = np.asarray(a.obsm["spatial"], float)
            pd.DataFrame({"z": a.obs[lab].astype(str).to_numpy(), "x": xy[:, 0], "y": xy[:, 1]}, index=ids).to_csv(os.path.join(CSV, f"{ds}_{sec}_info.csv"))
            print("exported", ds, sec, a.shape, "K =", a.obs[lab].nunique(), flush=True)


ENTRY = '''
  osmfish:
    name: Mouse somatosensory cortex (osmFISH; SDMBench release)
    technology: osmFISH
    generation: imaging, targeted panel (33 genes), single cell
    species: mouse
    tissue: somatosensory cortex (one section, 4,839 cells after SDMBench exclusion)
    resolution: single cell
    n_sections: 1
    n_domains: {"osmFISH": 11}
    label_provenance: {class: unknown, verified: false,
      note: "obs['Region'] of the SDMBench file: 11 anatomical region names (Layer 2-3 medial/lateral, Layer 3-4, 4, 5, 6, White matter, Hippocampus, Ventricle, Pia Layer 1, Internal Capsule Caudoputamen); labels from SDMBench, derivation not fully documented (the region annotation goes back to Codeluppi et al. 2018, Nat Methods, but SDMBench does not state how its file was derived). Reported as a separate, clearly labelled group."}
    settings_note: "targeted-panel path (all 33 genes, 50 PCs capped at n_genes - 1), CSV fallback of spatialbench.data.load_section. The SDMBench matrix is library-size normalised (every cell sums to 5,328), not raw counts: analysed as released (deviation)."
    source: {counts: "https://ndownloader.figshare.com/files/40038577 (osmfish_remove_excluded.h5ad, Figshare article 22565194, md5 b087669928e888619ff003bb2d533a7c)", labels: "same file, obs['Region']",
             citation: "Yuan et al., Nat Methods 2024 (SDMBench); Codeluppi et al., Nat Methods 2018"}
    license: {status: CC-BY-4.0, note: "Figshare licence of the SDMBench deposit (CC BY 4.0); derived CSVs are not committed"}
    sections:
      "osmFISH": {split: test}
  baristaseq:
    name: Mouse primary visual cortex VISp (BaristaSeq; SDMBench release)
    technology: BaristaSeq
    generation: in situ sequencing, targeted panel (79 genes), single cell
    species: mouse
    tissue: primary visual cortex (3 slices; 1,525 / 2,042 / 1,690 cells)
    resolution: single cell
    n_sections: 3
    n_domains: {"Slice_1": 6, "Slice_2": 6, "Slice_3": 6}
    label_provenance: {class: unknown, verified: false,
      note: "obs['layer'] of the SDMBench files: cortical layers VISp_I, II/III, IV, V, VI and white matter; labels from SDMBench, derivation not fully documented (layer assignment probably by distance to pia, columns 'Dist to pia' and 'depth_um' exist, but this is not stated). Reported as a separate, clearly labelled group."}
    settings_note: "targeted-panel path (all 79 genes, 50 PCs capped at n_genes - 1), CSV fallback; integer counts as released."
    source: {counts: "https://ndownloader.figshare.com/files/40017088, 40017172, 40017175 (Slice_1/2/3_removed.h5ad, Figshare article 22550074)", labels: "same files, obs['layer']",
             citation: "Yuan et al., Nat Methods 2024 (SDMBench); Sun et al., 2021 (BaristaSeq VISp)"}
    license: {status: CC-BY-4.0, note: "Figshare licence of the SDMBench deposit (CC BY 4.0); derived CSVs are not committed"}
    sections:
      "Slice_1": {split: test}
      "Slice_2": {split: test}
      "Slice_3": {split: test}
'''


def register():
    p = os.path.join(ROOT, "configs", "datasets_newdata.yaml"); s = open(p).read()
    if "\n  osmfish:" not in s:
        open(p, "w").write(s.rstrip("\n") + "\n" + ENTRY); print("registered osmfish, baristaseq")
    else:
        print("already registered")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--download", action="store_true"); ap.add_argument("--export", action="store_true"); ap.add_argument("--register", action="store_true")
    a = ap.parse_args(); allf = not (a.download or a.export or a.register)
    if a.download or allf: download()
    if a.export or allf: export()
    if a.register or allf: register()
