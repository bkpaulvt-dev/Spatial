# Benchmark status (generated 2026-10-14; per-method counts come from `scripts/coverage_matrix.py` → `results/coverage_matrix.md`)

## Totals
| | Done | Yet to run / not done |
|---|---|---|
| Datasets | 3 datasets, 3 technologies (Visium, STARmap, MERFISH), 20 sections | All public annotated datasets across ~12 technologies (inventory not done; blocked by network access) |
| Methods | 16 of 16 run in at least one experiment (13 published + 3 training-free baselines) | Same 16 in the experiments marked below |
| Metrics | 40 per-run metrics implemented (families 3A–3E) | 8 of 13 planned families (3A–3M) incomplete |

## Methods x experiments (sections completed; seeds for accuracy)
See `results/coverage_matrix.md` for the live version. At the time of writing: all 16 methods have accuracy for all
sections (BayesSpace: 12 Visium sections); the full metric panel / time / memory covers all methods except CCST (0/20),
Spatial-MGCN (5/20), DeepST (0/20) and BayesSpace (0/12); the lottery and R-mclust tests cover 10 methods
(not linear diffusion, PCA, BANKSY; n/a for SpaGCN, BASS, BayesSpace); invariance tests cover 3 methods on 2 sections.

## Metric families (plan 3A–3M)
| Family | Status |
|---|---|
| 3A agreement with labels | done |
| 3B per-domain / class-balanced | implemented; standardised runner only |
| 3C spatial structure | implemented (no Geary's C, compactness) |
| 3D tissue topology | implemented; not analysed |
| 3E label-free internal quality | implemented; not analysed |
| 3F biological validity | not implemented |
| 3G stability | lottery + mclust for 10 methods; invariance for 3 |
| 3H multi-section integration | not implemented |
| 3I number-of-domains estimation | code exists; not run (K was given) |
| 3J metric meta-analysis | not done |
| 3K uncertainty | ARI only |
| 3L efficiency | 8 methods; scaling not run |
| 3M aggregation / ranking robustness | not done |

## Plan items not run
37 tracked plan items: 4 done, 14 partial, 19 not started. Most important for NAR: variance decomposition, rank
stability, equal-tuning arm, dataset difficulty indices, leakage-inflation simulation for all methods, invariance for
all methods, more datasets and technologies.
