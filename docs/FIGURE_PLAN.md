# Experiment results and figure plan (NAR style: 3-4 experiments per figure, all tables in the supplement)

## 1. All experiment results
| ID | Experiment | What is measured | Coverage now | Source file | In paper now |
|---|---|---|---|---|---|
| E1 | Accuracy | Mean ARI per method and dataset, two clustering protocols | 16 methods x 20 sections (BayesSpace 12) | results/*.jsonl | Table 1, Fig 2a |
| E2 | Cluster-aware comparison | Difference to reference with bootstrap CI, equivalence margin | 16 methods | stats_cluster_aware.json | Table 2, Fig 2b |
| E3 | Rank uncertainty | P(best), rank intervals | 16 methods | stats_cluster_aware.json | Fig 2c |
| E4 | Dev/test sensitivity | Results without the development sections | 16 methods | stats_cluster_aware.json | text only |
| E5 | Clustering protocol | Own clustering vs 20-start best likelihood | 13 methods | stats_cluster_aware.json | Fig 4 |
| E6 | Random-start lottery | ARI spread over 20 single-start fits of one embedding | 10 methods x 20 | clustering_lottery.jsonl | Fig 3a |
| E7 | Likelihood vs ARI | Spearman rho of fit quality and accuracy | 10 methods x 3 datasets | clustering_lottery.jsonl | Fig 3c |
| E8 | R mclust perturbation | ARI change after spot permutation and 1% noise | 10 methods x 20 | mclust_lottery_*.csv | Fig 3b |
| E9 | Seed variability | SD of ARI over training seeds | methods with 3 seeds | paper_numbers_v2.json | text only (HiSTaR) |
| E10 | Metric panel | macro-F1, missed domains, small-domain recall, CHAOS, PAS, Moran I, boundary F1, topology, label-free scores | 13 of 16 methods (running) | benchmark_runs.jsonl | no |
| E11 | Resources | Run time, peak memory, energy estimate | 13 of 16 methods (running) | benchmark_runs.jsonl | Table 3 (7 methods) |
| E12 | HiSTaR reproduction | Reported vs reproduced ARI, mclust vs GMM, deterministic fix | 12 sections | paper_numbers.json | text |
| E13 | Label-selected epoch | Spatial-MGCN inflation per dataset | 20 sections, seed 0 | new_methods.jsonl | text |
| E14 | Code audit | Label-use patterns L1-L5 in 14 repositories | 14 repos | leakage_scan/summary.csv | no |
| E15 | Boundary accuracy | Boundary vs interior accuracy, linear vs edge-preserving diffusion | 12 DLPFC sections | anisost_boundary.jsonl | Supp Fig S2 |
| E16 | Baseline sensitivity | ARI as one hyper-parameter changes | DLPFC | anisost_sweep.jsonl | Supp Fig S1 |
| E17 | Invariance pilot | Consistency under permutation, rotation, scaling, etc. | 3 methods x 2 sections | invariance_pilot.json | no |
| E18 | Data QC | Spots, genes, sparsity, domain sizes and imbalance per section | 20 sections | qc/section_qc.csv | no |
| E19 | Domain maps | Per-spot predictions | 13 methods | results/runs/*.npz | Fig 5 |
| E20 | Coverage | Which method ran in which experiment | all | coverage_matrix.md | no |

## 2. Plot options per result (chosen option in bold)
| ID | Options | Choice and reason |
|---|---|---|
| E1 | heatmap; grouped bars; dot plot; parallel coordinates | **annotated heatmap**: 16x3 values readable at a glance, family colour on the row |
| E2 | forest plot; violin of bootstrap; table | **forest plot with equivalence band**: shows size, uncertainty and margin at once |
| E3 | rank interval plot; rank-probability heatmap; bump chart | **rank interval with P(best)**: compact, aligns with the forest rows |
| E4 | paired dots; slope chart; text | **open/filled marker pair in the forest plot** (no extra panel) |
| E5 | dumbbell per dataset; slope chart; heatmap of change | **dumbbell**: direction and size of the change per method |
| E6 | strip + IQR; violin; box; ridgeline | **strip with median and IQR, coloured by dataset**: every embedding visible |
| E7 | diverging heatmap; dot matrix; bars | **diverging heatmap**: sign change on MERFISH stands out |
| E8 | strip; paired plot; histogram of change | **strip aligned with E6**: same axis, same rows |
| E9 | bar with error; dot plot; part of variance decomposition | **stacked variance share bar (seed vs start vs section)** once all seeds exist; until then dot plot |
| E10 | radar per method; heatmap of ranks across metrics; metric correlation matrix; scatter ARI vs macro-F1 | **rank heatmap across metric families + ARI vs macro-F1 scatter**: shows that rankings change with the metric |
| E11 | scatter time vs ARI (size = memory); bars; Pareto front | **accuracy-cost scatter with Pareto front, log time axis** |
| E12 | paired bars reported vs reproduced; per-section dots | **per-section dots with the reported value as a line** |
| E13 | paired dots final vs label-selected epoch; bars | **paired dots (slope) per section** |
| E14 | tile matrix repo x leakage type; bars | **tile matrix**: one look shows where label use occurs |
| E15 | paired dots boundary vs interior | **paired dots** (supplement) |
| E16 | line plot per parameter | **small-multiple lines** (supplement) |
| E17 | heatmap transform x method | **heatmap** (supplement, labelled pilot) |
| E18 | small-multiple bars; heatmap of QC metrics | **QC heatmap** (supplement) |
| E19 | grid of spatial maps | **map grid**, best and typical methods |
| E20 | tile matrix | **tile matrix** (supplement) |

## 3. Main figures (no main tables)
| Figure | Message | Panels |
|---|---|---|
| Fig 1 | Study design | schematic (done) |
| Fig 2 | Accuracy depends on the method family but differences are small | a E1 heatmap, b E2 forest (+E4 markers), c E3 ranks, d E19 maps |
| Fig 3 | The clustering step is a large source of variance | a E6 lottery strip, b E8 mclust strip, c E7 rho heatmap, d E5 dumbbell |
| Fig 4 | One score is not enough | a E10 rank heatmap across metrics, b ARI vs macro-F1 scatter, c small-domain recall, d E11 accuracy-cost scatter |
| Fig 5 | Reproducibility and label use | a E12 HiSTaR reported vs reproduced, b E13 label-selected epoch, c E14 audit tile matrix, d E9 seed variability |
| Supplement | everything else | Tables 1-3, E15-E18, E20, NMI/AMI tables |
