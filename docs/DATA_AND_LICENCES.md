# Data, method code and third-party licences

Checked 2026-10-18/19 against the local clones in `data/ext/` (commit = `git rev-parse HEAD` of the clone)
and the upstream repositories. "No licence file found" means that the repository at that commit contains no
LICENSE/COPYING file and no licence field in its package metadata. Under copyright law that is "all rights
reserved": the code may be run and cited but not redistributed or adapted without permission.

**This repository's own code** is released under the MIT licence (`LICENSE`); the authors still need to
confirm this choice before the public release.

## 1. Datasets

No raw data are stored in this repository. `make data` downloads them from the sources below and verifies
`data/CHECKSUMS.sha256` (SHA-256 of every raw input file used for the paper).

| Dataset | Files used | Source (exact) | Licence / terms | Citation |
|---|---|---|---|---|
| Human DLPFC, 10x Visium, 12 sections (151507–151676) | `<id>_filtered_feature_bc_matrix.h5` | `https://spatial-dlpfc.s3.us-east-2.amazonaws.com/h5/<id>_filtered_feature_bc_matrix.h5` (LIBD spatialLIBD bucket; objects unchanged since 2020-03-02) | Publicly distributed by the Lieber Institute for Brain Development through spatialLIBD; the spatialLIBD Bioconductor package is Artistic-2.0. No separate data licence is stated for the S3 objects; **to confirm** with LIBD / the spatialLIBD documentation. Not redistributed here. | Maynard et al., *Nat Neurosci* 2021;24:425–436; Pardo et al., *BMC Genomics* 2022 (spatialLIBD) |
| DLPFC layer annotation (`layer_guess_reordered`) | `metadata.tsv` per section | `JinmiaoChenLab/SEDR_analyses` at commit `00084465fa72cfccf54cee0d5b914cdadaee9961`, `data/DLPFC/<id>/metadata.tsv` (git blob hashes identical to the files used) | Annotation is from Maynard et al. 2021 (spatialLIBD). **SEDR_analyses: no licence file found.** Downloaded, not redistributed. | Maynard et al. 2021; Xu et al., *Genome Med* 2024 (SEDR) |
| Mouse mPFC, STARmap, 3 sections | `data/starmap_mpfc.RData` | `zhengli09/BASS-Analysis` at commit `81dfe7353093823eed68f403d9c4033031b73de4` (converted by `scripts/export_bass_data.R`) | **BASS-Analysis: no licence file found** → do not redistribute the `.RData` or the derived CSVs (including on Zenodo). Original data: STARmap resources of Wang et al.; terms not stated, **to confirm**. | Wang et al., *Science* 2018;361:eaat5691; Li & Zhou, *Genome Biol* 2022;23:168 |
| Mouse hypothalamic preoptic region, MERFISH animal 1, 5 sections (Bregma −0.04 to −0.24) | `data/MERFISH_Animal1.RData` | same BASS-Analysis commit as above | BASS-Analysis: no licence file found (as above). Original data: Moffitt et al., Dryad `doi:10.5061/dryad.8t8s248` (Dryad releases data under CC0). | Moffitt et al., *Science* 2018;362:eaau5324; Li & Zhou 2022 |

Derived files (`data/ext/csv/*.csv`, `results/cache/*.npz`) are rebuilt by `make data` and are not checksummed
(they depend on R's CSV writer and on library versions); the raw files above are.

## 2. Benchmarked methods

"Use" = how the code enters this benchmark: *pip* (installed package, only called), *clone* (upstream
repository cloned into `data/ext/methods/`, only called), *ported* (code adapted and included in this repository).

| Method | Repository | Version / commit used | Licence (as stated in the repository at that commit) | Use |
|---|---|---|---|---|
| HiSTaR | https://github.com/Anglejuebi/HiSTaR | `0039a3b` (upstream HEAD, unchanged since 2025-08-03; the port was made on 2026-10-06 — inferred, no vendored copy was kept) | MIT (© 2025 JunHua Yu) | **ported** (`hicast/histar.py`). MIT requires the copyright and permission notice to accompany the code: it is reproduced in `LICENSE` (third-party section); keep it there and reference it from the `histar.py` docstring. |
| GraphST | https://github.com/JinmiaoChenLab/GraphST | pip `GraphST 1.1.1`; tutorials at `d62b0b7` | **Conflicting:** repository `LICENSE.md` is GNU AGPL-3.0; the PyPI package metadata says MIT. Only called, not redistributed. | pip |
| BANKSY (Python) | https://github.com/prabhakarlab/Banksy_py | pip `pybanksy 1.3.5`; clone `9278996` | GPL-3.0 | pip |
| SpaGCN | https://github.com/jianhuupenn/SpaGCN | pip `SpaGCN 1.2.7`; clone `dc7a1c2` | MIT | pip |
| STAGATE (PyG) | https://github.com/QIFEIDKN/STAGATE_pyG | `ae1158c` (installed from the clone) | MIT | clone |
| SEDR | https://github.com/JinmiaoChenLab/SEDR | `ef48360` (installed from the clone) | MIT | clone |
| SpaceFlow | https://github.com/hongleir/SpaceFlow | pip `SpaceFlow 1.0.4`; clone `58d1ab0` | MIT | pip |
| NichePCA | https://github.com/imsb-uke/nichepca | pip `nichepca 0.1.0` (no commit recorded) | MIT (PyPI classifier; repository not cloned) | pip |
| CCST | https://github.com/xiaoyeye/CCST | `890de27` | **No licence file found.** | **ported**: `scripts/new_methods.py` re-implements CCST.py / data_generation_ST.py / CCST_ST_utils.py for current PyTorch. **Action needed:** ask the CCST authors for permission/a licence, or rewrite as an independent implementation from the paper and say so in the docstring, before the repository is made public. |
| Spatial-MGCN | https://github.com/cs-wangbo/Spatial-MGCN | `cf4412d` | **No licence file found.** | clone (modules imported from the clone at run time; nothing vendored — keep it that way) |
| DeepST | https://github.com/JiangBioLab/DeepST | `e37997f` | MIT | clone |
| BASS | https://github.com/zhengli09/BASS | `5c2690f` (R package 1.1.0.017) | GPL-3 (`LICENSE.md`; DESCRIPTION: GPL (>= 3)) | clone (R package) |
| BayesSpace | https://github.com/edward130603/BayesSpace | tag v1.5.1, `ba8b422` | MIT (© 2020 Fred Hutchinson Cancer Research Center) | clone (R package) |
| SPARK (SPARK-X gene selection inside BASS) | https://github.com/xzhoulab/SPARK | `a8b4bf2` (R package 1.1.1) | GPL-3 | clone (R package) |
| conST (screened, not benchmarked) | https://github.com/ys-zong/conST | `a32d747` | MIT | clone (leakage screen only) |
| SpatialPCA (screened, not benchmarked) | https://github.com/shangll123/SpatialPCA | `1d4dbb1` | GPL (>= 3) in DESCRIPTION only; no licence file | clone (leakage screen only) |
| Linear diffusion, AnisoST, PCA | this repository (`anisost/`, `scripts/adapters.py`) | this release | MIT (this repository) | own code |

Exact commits are also in `configs/methods.yaml` (single source of truth, shown as Supplementary Table S2).

**GPL/AGPL note.** BANKSY, BASS, SPARK (GPL-3) and GraphST (AGPL-3 per its repository) are only installed and
called; none of their code is copied into this repository, so the MIT licence of this repository is not
affected. If any of that code is ever vendored, the repository (or that part) must become GPL-3/AGPL-3.

## 3. Software infrastructure

R 4.3.3 with mclust 6.0.1 (GPL (>= 2)), Bioconductor 3.18 packages (SingleCellExperiment 1.24.0, scater 1.30.1,
scran 1.30.2); Python 3.13.16 with PyTorch 2.14.1 (BSD-3), PyTorch Geometric 2.8.0 (MIT), scikit-learn 1.9.1
(BSD-3), scanpy 1.12.4 (BSD-3). Full lists: `environment/`.

## 4. Figure icons

Figure 1 uses icons from Bioicons (https://bioicons.com); file-by-file authors and licences are in
`docs/figures/icons/LICENSES.md`. Most are CC0. Three are **CC BY 3.0 by Servier Medical Art** (`brain-1.svg`,
`glassslide-top.svg`, `clock.svg`) and require the credit "Servier Medical Art, CC BY 3.0" in the figure legend
or acknowledgements.
