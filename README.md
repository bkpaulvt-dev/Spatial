# Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods

Code, configuration, environment and per-run results for a benchmark of spatial domain identification
methods, submitted to *Nucleic Acids Research* (manuscript: `paper/main.tex`, supplement: `paper/supplementary.tex`).

## Overview

* **Methods (16, 17 configurations):** 13 published methods — HiSTaR, GraphST, BANKSY (λ = 0.2 and 0.8), SpaGCN,
  STAGATE, SEDR, SpaceFlow, NichePCA, CCST, Spatial-MGCN, DeepST, BASS, BayesSpace — and three training-free
  baselines: linear diffusion (standard neighbourhood smoothing of PCs on the spatial k-NN graph), AnisoST
  (edge-preserving diffusion) and PCA without spatial information. Versions, commits, settings and every
  deviation from the authors' tutorials: `configs/methods.yaml` (Supplementary Table S2).
* **Data (24 sections, 4 technologies):** 12 human DLPFC sections (10x Visium, spatialLIBD), 3 mouse mPFC
  sections (STARmap), 5 mouse hypothalamus sections (MERFISH animal 1), 1 human breast cancer section (10x Visium,
  Block A Section 1) and 3 mouse embryo sections (Stereo-seq MOSTA, bin50; `scripts/download_new_datasets.py`,
  `scripts/prepare_new_datasets.py`). Registry, label provenance and the
  frozen development/test split: `configs/datasets.yaml`.
* **Experiments:** accuracy (ARI, NMI and other metrics) with each method's official clustering and with one
  matched clustering for all; seed-to-seed variability (seeds 0–2); the *clustering initialisation* experiment
  (20 single-start Gaussian mixture fits on each fixed embedding); R mclust sensitivity to its random seed
  (random initialisation subset) and to 1 % noise; sensitivity to the number of domains K; time and memory; cluster-aware statistics (hierarchical bootstrap,
  equivalence margin, rank intervals).

## Repository layout

| Path | Contents |
|---|---|
| `scripts/bench_queue.py`, `scripts/bench_run.py`, `scripts/adapters.py` | unified, resumable benchmark runner; one adapter per method |
| `scripts/run_r_method.R` | R methods (BASS, BayesSpace) called by the runner |
| `scripts/clustering_lottery.py`, `scripts/mclust_lottery.R`, `scripts/mclust_seed.R` | clustering-initialisation experiments (Python GMM and R mclust) |
| `scripts/baselines_3start.py` | baselines with the same 3-start GMM as the methods they are compared with |
| `scripts/benchmark_*.py`, `scripts/boundary_analysis.py` | earlier per-family pipelines whose result files the paper also reads |
| `scripts/stats_cluster_aware.py`, `scripts/paper_numbers.py`, `scripts/paper_v2.py`, `scripts/coverage_matrix.py` | statistics, numbers (`results/paper_macros.tex`) and tables |
| `scripts/make_supplement.py`, `scripts/make_figures_nar.py`, `scripts/make_fig1_pipeline_v2.py`, `scripts/make_figures.py` | supplement and figures |
| `scripts/check_paper_numbers.py` | checks numbers quoted in `paper/main.tex` against the result files |
| `scripts/download_dlpfc.py`, `scripts/prepare_extra.py`, `scripts/export_bass_data.R` | data download and conversion |
| `spatialbench/` | metric panel, data loading, preprocessing, resource measurement (unit-tested in `tests/`) |
| `anisost/` | linear diffusion and AnisoST baselines |
| `hicast/` | HiSTaR port (`histar.py`, MIT, see `LICENSE`), data loading and clustering helpers |
| `configs/` | dataset registry and method cards |
| `results/` | all raw per-run results (`*.jsonl`, `*.csv`), generated numbers, tables (`results/supp/`) |
| `docs/` | protocol, evidence map, leakage audit, figures, data and licence table |
| `environment/` | exact Python and R environment |
| `paper/` | manuscript and supplement sources |

## Installation

Tested on Linux x86_64 (Ubuntu 24.04), CPU only.

```bash
# Python 3.13.16 + R 4.3.3 in one conda environment
conda env create -f environment/environment.yml && conda activate spatialbench
# or, with an existing Python 3.13:  pip install -r environment/requirements-lock.txt   (== make env)
```

`environment/requirements-lock.txt` pins every Python package (torch 2.14.1, torch-geometric 2.8.0.post1,
torch_sparse 0.6.18, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.0.5, scanpy 1.12.4, anndata 0.13.4,
GraphST 1.1.1, pybanksy 1.3.5, SpaGCN 1.2.7, SpaceFlow 1.0.4, nichepca 0.1.0, STAGATE_pyG and SEDR at their
recorded commits, rpy2 3.5.17, leidenalg 0.12.0, igraph 1.0.0). `torch_sparse`/`torch_scatter` are built from
source against torch.

R packages (versions in `environment/R-packages.txt`, `environment/R-sessionInfo.txt`): mclust 6.0.1,
BASS 1.1.0.017 (`zhengli09/BASS@5c2690f`), BayesSpace 1.5.1 (`edward130603/BayesSpace@ba8b422`), SPARK 1.1.1
(`xzhoulab/SPARK@a8b4bf2`), Bioconductor 3.18 (SingleCellExperiment 1.24.0, scater 1.30.1, scran 1.30.2).

```bash
Rscript -e 'remotes::install_github("zhengli09/BASS@5c2690fddcdeb12461a69106ff4681777d0a8822")'
Rscript -e 'remotes::install_github("edward130603/BayesSpace@ba8b42211ef1581d31a659766559bd6e42be3acc")'
Rscript -e 'remotes::install_github("xzhoulab/SPARK@a8b4bf27b804604dfda53da42992f100b8e4e727")'
# without CRAN/Bioconductor access: scripts/install_r_pkg.sh <pkg> ...  (apt, then github.com/cran mirrors)
```

Methods used from a clone (DeepST, Spatial-MGCN, CCST reference code) are cloned into `data/ext/methods/<name>`
at the commit in `configs/methods.yaml`, e.g.
`git clone https://github.com/JiangBioLab/DeepST data/ext/methods/DeepST && git -C data/ext/methods/DeepST checkout e37997f`.

## Data

```bash
make data     # = download + verify + convert + preprocess
```

* **DLPFC:** `scripts/download_dlpfc.py` downloads `<id>_filtered_feature_bc_matrix.h5` for the 12 sections from
  the spatialLIBD S3 bucket (`https://spatial-dlpfc.s3.us-east-2.amazonaws.com/h5/`) and the layer annotation
  `metadata.tsv` from `JinmiaoChenLab/SEDR_analyses` at commit `0008446`, into `data/DLPFC/<id>/`, and verifies
  them against `data/CHECKSUMS.sha256`. `--build-cache` writes `results/cache/<id>.npz` (2,000 HVGs, 200 PCs).
* **STARmap and MERFISH:** cloned from `zhengli09/BASS-Analysis` at commit `81dfe73`, exported to CSV with
  `scripts/export_bass_data.R` and preprocessed by `scripts/prepare_extra.py` (all genes, 50 PCs).

Sources, licences and citations: `docs/DATA_AND_LICENCES.md`. No data are redistributed in this repository.

## Reproducing the paper

Three tiers. Tier 1 needs no data and no method packages.

| Tier | Command | Time | Needs |
|---|---|---|---|
| 1. Numbers, tables, supplement, checks | `make numbers supplement check` | ~2 min | committed `results/` |
| 2. Figures and PDFs | `make figures paper` | ~5 min | Figures 1 and 5 also need `results/cache`, `results/runs`, `results/emb` (below) |
| 3. Everything from raw data | `make data benchmark benchmark-legacy robustness all` | ~150 CPU-hours benchmark + ~1 day robustness | full environment and data |

`make all` = `numbers supplement figures paper check`; it does not rerun the benchmark.

### Individual experiments

```bash
export OMP_NUM_THREADS=1
# benchmark: every (method, dataset, section, seed); finished jobs are skipped, failures kept as records
python scripts/bench_queue.py --dry-run                        # list jobs
python scripts/bench_queue.py --methods linear_diffusion nichepca --datasets starmap --seeds 0 1 2 --workers 2
python scripts/bench_run.py --method graphst --dataset dlpfc --section 151673 --seed 0   # one job
python scripts/baselines_3start.py                             # baselines with the 3-start GMM

# clustering initialisation: 20 single-start GMM fits per fixed seed-0 embedding (also exports CSV for R)
METHODS="histar anisost graphst" WORKERS=4 python scripts/clustering_lottery.py
Rscript scripts/mclust_lottery.R results/emb/csv results/mclust_lottery_<method>.csv '__<method>__k'
Rscript scripts/mclust_seed.R    results/emb/csv results/mclust_seed_g1.csv '__(histar|anisost)__k'

# statistics, numbers, supplement, figures
python scripts/stats_cluster_aware.py && python scripts/paper_numbers.py && python scripts/paper_v2.py
python scripts/coverage_matrix.py && python scripts/make_supplement.py
python scripts/make_figures_nar.py && python scripts/make_fig1_pipeline_v2.py
python scripts/check_paper_numbers.py && python -m pytest tests
make paper                                                     # pdflatex + bibtex in paper/
```

The make targets (`make help`) chain these in the right order; `make -n <target>` prints the commands.
Mapping of every claim, figure and table to its evidence: `docs/EVIDENCE_MAP.md`.

### Where results live

* `results/benchmark_runs.jsonl`: one record per run (metrics with official and matched clustering, per-domain
  scores, wall time, CPU time, peak memory, errors). Per-run predictions: `results/runs/<dataset>__<section>__<method>__s<seed>.json|npz`.
* Earlier pipelines: `results/{dlpfc_main,anisost_main,baselines,extra,graphst,new_methods,baselines_3start}.jsonl`.
* Clustering initialisation: `results/clustering_lottery.jsonl`, `results/mclust_lottery_*.csv`, `results/mclust_seed_g*.csv`.
* Generated: `results/paper_macros.tex`, `results/paper_numbers*.json`, `results/stats_cluster_aware.json`,
  `results/table_*.tex`, `results/supp/*.tex`, `docs/figures/nar_fig*.pdf|png`.

### Large intermediates

`results/runs/` (138 MB), `results/emb/` (1.1 GB, seed-0 embeddings) and `results/cache/` (45 MB) are not in git.
`results/cache/` is rebuilt by `make data`; `results/runs/` and `results/emb/` are rebuilt by the benchmark and
will be archived on Zenodo (DOI to be added). Only the Figure 1 and Figure 5 scripts and the robustness
experiments need them.

## Compute

All runs were CPU-only, one thread per job (`OMP_NUM_THREADS=1`), on a 4-core Intel Xeon (2.1 GHz) container
with 15 GB RAM. The unified benchmark took about 150 CPU-hours (CCST ≈ 52 h, Spatial-MGCN ≈ 21 h, GraphST ≈ 19 h,
SpaceFlow ≈ 16 h, STAGATE ≈ 15 h; training-free baselines < 0.5 h each). Peak memory per job was below 3 GB for
most methods, but up to 12.5 GB for BayesSpace, 9.2 GB for DeepST and 7.2 GB for NichePCA, so these run one at a
time. Runtime and memory comparisons are specific to this machine.

The breast cancer and Stereo-seq runs (`make benchmark-new`) ran one job at a time with a per-job cap of 12 GB resident
memory (`SPATIALBENCH_MAX_RSS_GB`, enforced by `spatialbench/resources.py`; a job above the cap, or leaving less than
0.8 GB free, is stopped and recorded as out of memory). On the 18,408-bin Stereo-seq section BASS, DeepST, Spatial-MGCN
and NichePCA (default workflow) exceeded it; CCST took about 5.5 h per run. One R mclust fit on that section uses about
5 GB, so run at most two `mclust_seed.R` workers at a time on a 16 GB machine; workers can share one output file (each
embedding is claimed with a lock directory `<out>.lock_*`; delete stale lock directories after a crash).
Embeddings of these runs are exported with `scripts/export_runner_emb.py`; the coarse-class breast cancer analysis is
`scripts/brca_coarse.py`; `scripts/make_submission.sh` copies the figures under their printed numbers for upload.

## Neutrality

The authors developed AnisoST, one of the baselines; it is reported as a baseline, not as a proposed method,
and its settings were fixed on DLPFC donor 1 before any other data were analysed (as for linear diffusion).
Linear diffusion is standard neighbourhood smoothing on the spatial k-NN graph, not a new method. All published
methods were run with the settings of their own tutorials or papers (`configs/methods.yaml`), and every deviation
is recorded there.

## Licence and citation

Code: MIT (`LICENSE`), which also reproduces the HiSTaR MIT notice for `hicast/histar.py`. **The licence choice
must be confirmed by the authors before the repository is made public.** Third-party method code is not
redistributed (except the HiSTaR port and the CCST re-implementation, see `docs/DATA_AND_LICENCES.md`).
Citation metadata: `CITATION.cff` and `.zenodo.json` (DOI to be added after the Zenodo deposit).

## History

This repository started as an analysis of HiSTaR and a proposed successor, HiCAST (`docs/HiCAST.md`, `hicast/`),
and then the AnisoST baseline (`docs/AnisoST.md`). HiCAST did not beat HiSTaR and is not part of the benchmark.

Maintainer-only scripts that are not part of the reproduction: `scripts/push_overleaf.sh` and
`scripts/package_overleaf.sh` (push to the authors' Overleaf project; contain a private project ID) and the
git/Overleaf lines of `scripts/run_fill_v2.sh`. Remove them, or take the project ID from an environment variable
with no default, before the public release.
