"""Download the 12 DLPFC Visium sections (spatialLIBD; Maynard et al., Nat Neurosci 2021) in the layout the pipeline reads.

    data/DLPFC/<section>/filtered_feature_bc_matrix.h5   10x Space Ranger filtered counts (spatialLIBD S3 bucket)
    data/DLPFC/<section>/metadata.tsv                     spot metadata with the manual layer annotation
                                                          (column layer_guess_reordered), array row/col and image
                                                          coordinates, as redistributed by JinmiaoChenLab/SEDR_analyses

These are exactly the files read by hicast/data.py::load_dlpfc_adata and spatialbench/data.py::load_section.
The annotation repository is pinned to the commit whose metadata.tsv files are byte-identical (git blob hash)
to the ones used for the paper; the S3 objects have not changed since 2020-03-02 (Last-Modified header).

    python scripts/download_dlpfc.py                    # download missing files, then verify data/CHECKSUMS.sha256
    python scripts/download_dlpfc.py --sections 151673  # one section
    python scripts/download_dlpfc.py --verify-only
    python scripts/download_dlpfc.py --build-cache      # also write results/cache/<section>.npz (HVG + 200 PCs)

STARmap and MERFISH are not downloaded here: see `make data` (clones zhengli09/BASS-Analysis at a fixed commit).
Only the Python standard library is needed for downloading and verifying.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SECTIONS = ["151507", "151508", "151509", "151510", "151669", "151670",
            "151671", "151672", "151673", "151674", "151675", "151676"]
H5_URL = "https://spatial-dlpfc.s3.us-east-2.amazonaws.com/h5/{s}_filtered_feature_bc_matrix.h5"
SEDR_ANALYSES_COMMIT = "00084465fa72cfccf54cee0d5b914cdadaee9961"   # JinmiaoChenLab/SEDR_analyses, 2023-12-04
META_URL = ("https://raw.githubusercontent.com/JinmiaoChenLab/SEDR_analyses/"
            + SEDR_ANALYSES_COMMIT + "/data/DLPFC/{s}/metadata.tsv")
CHECKSUMS = os.path.join(ROOT, "data", "CHECKSUMS.sha256")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url: str, dest: str, retries: int = 3) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
            os.replace(tmp, dest)
            return
        except Exception as e:  # network errors: retry, then give up loudly
            print(f"  attempt {attempt} failed: {e}", file=sys.stderr)
    raise SystemExit(f"could not download {url}")


def expected_sums() -> dict[str, str]:
    """Relative path -> sha256 from data/CHECKSUMS.sha256 (sha256sum format)."""
    out = {}
    if os.path.exists(CHECKSUMS):
        for line in open(CHECKSUMS):
            if line.strip():
                digest, path = line.split(maxsplit=1)
                out[path.strip().lstrip("*")] = digest
    return out


def verify(sections: list[str]) -> bool:
    sums, ok = expected_sums(), True
    for s in sections:
        for name in ("filtered_feature_bc_matrix.h5", "metadata.tsv"):
            rel = f"data/DLPFC/{s}/{name}"
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                print(f"MISSING  {rel}"); ok = False; continue
            if rel not in sums:
                print(f"NO SUM   {rel}"); continue
            good = sha256(path) == sums[rel]
            ok &= good
            print(f"{'OK' if good else 'MISMATCH':<8} {rel}")
    return ok


def build_cache(sections: list[str]) -> None:
    """results/cache/<section>.npz exactly as scripts/benchmark_dlpfc.py writes it (HVG 2000, 200 PCs, seed 0)."""
    sys.path[:0] = [ROOT, os.path.join(ROOT, "scripts")]
    from benchmark_dlpfc import cached_slice
    cache = os.path.join(ROOT, "results", "cache")
    os.makedirs(cache, exist_ok=True)
    for s in sections:
        cached_slice(os.path.join(ROOT, "data", "DLPFC"), cache, s)
        print(f"cache    results/cache/{s}.npz")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sections", nargs="+", default=SECTIONS)
    ap.add_argument("--force", action="store_true", help="re-download files that already exist")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--build-cache", action="store_true", help="also preprocess into results/cache/<section>.npz")
    args = ap.parse_args()
    bad = sorted(set(args.sections) - set(SECTIONS))
    if bad:
        raise SystemExit(f"unknown section(s): {bad}")
    if not args.verify_only:
        for s in args.sections:
            for url, name in ((H5_URL, "filtered_feature_bc_matrix.h5"), (META_URL, "metadata.tsv")):
                dest = os.path.join(ROOT, "data", "DLPFC", s, name)
                if os.path.exists(dest) and not args.force:
                    continue
                print(f"download {url.format(s=s)}")
                fetch(url.format(s=s), dest)
    ok = verify(args.sections)
    if not ok:
        raise SystemExit("checksum verification failed (see above)")
    if args.build_cache:
        build_cache(args.sections)


if __name__ == "__main__":
    main()
