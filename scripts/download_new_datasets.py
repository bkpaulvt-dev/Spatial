"""Download the two held-out datasets added after the baseline settings were frozen (all sections split "test").

    brca    10x Visium human breast cancer, V1_Breast_Cancer_Block_A_Section_1 (10x Genomics demo data, Space
            Ranger 1.1.0), section key "block_a_1":
              data/BRCA/block_a_1/filtered_feature_bc_matrix.h5   filtered counts
              data/BRCA/block_a_1/spatial/...                     tissue_positions_list.csv, scale factors, images
              data/BRCA/block_a_1/metadata.tsv                    20-region annotation (column fine_annot_type) as
                                                                  redistributed by JinmiaoChenLab/SEDR_analyses
    stereo  Stereo-seq mouse embryo atlas MOSTA (Chen et al., Cell 2022), bin50, sections E9.5_E1S1, E10.5_E2S1,
            E10.5_E1S1:  data/Stereo/<section>.MOSTA.h5ad   (raw counts in .layers['count'], tissue annotation in
            .obs['annotation'], coordinates in .obsm['spatial'])

Downloads resume from a partial `<file>.part` (HTTP Range); sha256 of every new file is appended to
data/CHECKSUMS.sha256 the first time and verified against it afterwards. Standard library only.

    python scripts/download_new_datasets.py                       # both datasets
    python scripts/download_new_datasets.py --datasets brca
    python scripts/download_new_datasets.py --verify-only
"""
from __future__ import annotations

import argparse
import os
import sys
import tarfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from download_dlpfc import CHECKSUMS, ROOT, SEDR_ANALYSES_COMMIT, expected_sums, sha256  # noqa: E402

TENX = "https://cf.10xgenomics.com/samples/spatial-exp/1.1.0/V1_Breast_Cancer_Block_A_Section_1/"
MOSTA = "https://ftp.cngb.org/pub/SciRAID/stomics/STDS0000058/stomics/{s}.MOSTA.h5ad"
STEREO_SECTIONS = ["E9.5_E1S1", "E10.5_E2S1", "E10.5_E1S1"]
FILES = {   # dataset -> [(url, path relative to ROOT)]
    "brca": [(TENX + "V1_Breast_Cancer_Block_A_Section_1_filtered_feature_bc_matrix.h5",
              "data/BRCA/block_a_1/filtered_feature_bc_matrix.h5"),
             (TENX + "V1_Breast_Cancer_Block_A_Section_1_spatial.tar.gz",
              "data/BRCA/block_a_1/spatial.tar.gz"),
             ("https://raw.githubusercontent.com/JinmiaoChenLab/SEDR_analyses/" + SEDR_ANALYSES_COMMIT
              + "/data/BRCA1/metadata.tsv", "data/BRCA/block_a_1/metadata.tsv")],
    "stereo": [(MOSTA.format(s=s), f"data/Stereo/{s}.MOSTA.h5ad") for s in STEREO_SECTIONS],
}


def fetch_resume(url: str, dest: str, retries: int = 5) -> None:
    """Download url to dest, continuing a partial dest + '.part' with an HTTP Range request."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    for attempt in range(1, retries + 1):
        have = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        hdr = {"User-Agent": "curl/8.5.0"}          # cf.10xgenomics.com answers 403 to Python-urllib
        if have:
            hdr["Range"] = f"bytes={have}-"
        req = urllib.request.Request(url, headers=hdr)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                mode = "ab" if have and r.status == 206 else "wb"   # server ignored Range: start over
                total = int(r.headers.get("Content-Length", 0)) + (have if mode == "ab" else 0)
                with open(tmp, mode) as f:
                    while block := r.read(1 << 20):
                        f.write(block)
            if total and os.path.getsize(tmp) != total:
                raise IOError(f"short read: {os.path.getsize(tmp)} of {total} bytes")
            os.replace(tmp, dest)
            return
        except urllib.error.HTTPError as e:
            if e.code == 416:                                         # .part already complete
                os.replace(tmp, dest)
                return
            print(f"  attempt {attempt} failed: {e}", file=sys.stderr)
        except Exception as e:  # network errors: retry (resuming), then give up loudly
            print(f"  attempt {attempt} failed: {e}", file=sys.stderr)
    raise SystemExit(f"could not download {url}")


def verify_or_record(rels: list[str]) -> bool:
    """Check each file against data/CHECKSUMS.sha256; append the sum of files not yet listed."""
    sums, ok = expected_sums(), True
    for rel in rels:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"MISSING  {rel}"); ok = False; continue
        digest = sha256(path)
        if rel not in sums:
            with open(CHECKSUMS, "a") as f:
                f.write(f"{digest}  {rel}\n")
            print(f"ADDED    {rel}")
            continue
        good = digest == sums[rel]
        ok &= good
        print(f"{'OK' if good else 'MISMATCH':<8} {rel}")
    return ok


def extract_spatial(tar_rel: str) -> None:
    """Unpack the Space Ranger spatial/ folder next to the tarball (members are checked to stay inside it)."""
    path = os.path.join(ROOT, tar_rel)
    out = os.path.dirname(path)
    if os.path.exists(os.path.join(out, "spatial", "tissue_positions_list.csv")):
        return
    with tarfile.open(path) as t:
        for m in t.getmembers():
            if not (m.isfile() or m.isdir()) or os.path.isabs(m.name) or ".." in m.name.split("/"):
                raise SystemExit(f"refusing suspicious tar member {m.name}")
        t.extractall(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=list(FILES), choices=list(FILES))
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    rels = [rel for d in args.datasets for _, rel in FILES[d]]
    if not args.verify_only:
        for d in args.datasets:
            for url, rel in FILES[d]:
                if os.path.exists(os.path.join(ROOT, rel)):
                    continue
                print(f"download {url}", flush=True)
                fetch_resume(url, os.path.join(ROOT, rel))
    if not verify_or_record(rels):
        raise SystemExit("checksum verification failed (see above)")
    if "brca" in args.datasets:
        extract_spatial("data/BRCA/block_a_1/spatial.tar.gz")


if __name__ == "__main__":
    main()
