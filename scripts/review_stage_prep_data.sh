#!/bin/bash
# Prep stage: the data of the 24 original sections that are not yet on this host (DLPFC 12, STARmap, MERFISH, breast cancer, Stereo-seq E9.5), with the
# project's own resumable downloaders and recorded SHA-256 checksums; one download at a time. Needed by R2, M5, M6 and R3.
set -e
BASE=${BASE:-/mnt/disk/bikashkumar/SpatialBench}; cd "$BASE/Spatial"
source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$BASE/env"; export R_LIBS_USER="$BASE/Rlib"
[ "$(python -c 'import sys;print(sys.prefix)')" = "$BASE/env" ]
python scripts/download_dlpfc.py
BA=data/ext/BASS-Analysis; COMMIT=81dfe7353093823eed68f403d9c4033031b73de4        # as in the Makefile (data-extra)
[ -d $BA/.git ] || git clone https://github.com/zhengli09/BASS-Analysis $BA
git -C $BA checkout -q $COMMIT
sha256sum -c --ignore-missing data/CHECKSUMS.sha256
Rscript scripts/export_bass_data.R $BA/data data/ext/csv
python scripts/download_new_datasets.py --datasets brca
python scripts/download_new_datasets.py --datasets stereo --sections E9.5_E1S1
echo "prep_data finished"
