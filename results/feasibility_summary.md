# Feasibility of additional methods (seed 0; STARmap section 20180417_BZ5, DLPFC section 151673)

Single CPU thread per run; times are wall-clock. All methods use their official tutorial / published
settings; deviations are documented in `scripts/new_methods.py`.

| Method | Publication | STARmap ARI | time | DLPFC ARI | time | Clustering | Status |
|---|---|---|---|---|---|---|---|
| NichePCA | Bioinformatics 2025 | 0.642 | 32 s | 0.302 | 74 s | Leiden (k search) | works |
| SEDR | Genome Med 2024 | 0.515 | 30 s | 0.521 | 114 s | R mclust | works (mclust called without its hard-coded R path) |
| SpaceFlow | Nat Commun 2022 | 0.792 | 12 min | 0.351 | 10 min | Leiden (k search) | works (networkx-3 alias; all-zero genes dropped) |
| STAGATE | Nat Commun 2022 | 0.421 | 2.4 min | 0.582 | 24 min | R mclust | works (radius in spot spacings: 5.8 neighbours, as in tutorial) |
| BASS | Genome Biol 2022 | 0.815 | 2.3 min | 0.602 | 17 min | own Bayesian model | works (R deps built from GitHub CRAN mirror) |
| DeepST | Nucleic Acids Res 2022 | 0.464 (11 domains found) | 2 min | 0.536 | 11 min | Leiden + refinement | works; needs ~7 GB RAM, run one at a time on DLPFC |
| Spatial-MGCN | Brief Bioinform 2023 | 0.329 (0.685*) | 1 min | 0.417 (0.505*) | 31 min | k-means | works |
| CCST | Nat Comput Sci 2022 | 0.475 | 22 min | 0.323 | 40 min | k-means | works (ported; old PyTorch pins) |
| BayesSpace | Nat Biotechnol 2021 | n/a | n/a | 0.559 | 50 min | own Bayesian model | works on Visium only (needs a spot lattice) |
| conST | Brief Bioinform 2022 | – | – | – | – | – | not feasible: requires histology-image (MAE) features |
| GraphPCA | Genome Biol 2024 | – | – | – | – | – | not available: PyPI "graphpca" is an unrelated package |

\* ARI of the epoch selected by agreement with the ground truth, as in Spatial-MGCN's released
`DLPFC_test.py`; the first value is the label-free result (final epoch) used in the benchmark.

With the four methods already benchmarked (HiSTaR, GraphST, BANKSY, SpaGCN), this gives **13 published
methods** plus the training-free baselines (linear diffusion, AnisoST, PCA).
