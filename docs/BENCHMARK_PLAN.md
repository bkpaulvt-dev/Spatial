# A leakage-free benchmark of spatial domain identification: full analysis plan

Target journal: *Nucleic Acids Research* (benchmark article; model: Zhong et al., NAR 2025,
53(1):gkae1316). Working title: **"How much of the progress in spatial domain identification is real?
A leakage-free, multi-technology benchmark and audit."**

Priority tags: **[C] core** (must be in the paper), **[E] extended** (strongly recommended),
**[O] optional** (if time and compute allow). Status: ✅ done (pilot), 🔶 partial, ⬜ to do.

---

## 0. What is novel (one paragraph for the cover letter)
Existing benchmarks (Yuan et al., Nat Methods 2024; NAR 2025 gkaf303; iMeta 2025; Genome Biol 2024;
the 2026 explanatory benchmark) rank methods by accuracy. None of them (to our knowledge; to be
re-verified with a full literature search) (i) audits released code for evaluation leakage, (ii) compares
reported with reproduced results, (iii) measures the noise floor that published improvements must exceed,
(iv) tests whether methods are invariant to transformations that should not change the answer, or
(v) checks whether the "ground truths" are themselves derived from algorithms. We provide all five, on a
standardized, QC-checked, leakage-free data resource spanning ten years of spatial technologies.

---

## 1. Data resource and quality control
| # | Analysis | Pri | Status |
|---|---|---|---|
| 1.1 | Inventory of every public dataset with domain annotations, from ST (2016) to Visium, Slide-seqV2, Stereo-seq, Visium HD, osmFISH, seqFISH+, STARmap(PLUS), MERFISH/MERSCOPE, BaristaSeq, Xenium, CosMx | C | 🔶 (3 technologies) |
| 1.2 | Uniform format (AnnData): raw counts, coordinates in µm, labels, metadata, licence, citation | C | 🔶 |
| 1.3 | Per-section QC: counts and genes per spot/cell, sparsity, tissue coverage, spot/cell density, gene-panel size, annotation completeness | C | ⬜ |
| 1.4 | **Label provenance audit**: expert-drawn / marker-based / histology-based / algorithm-derived (circular) labels; algorithm-derived labels are excluded from accuracy ranking or analysed separately | C | ⬜ |
| 1.5 | Label quality: spatial coherence of labels (Moran's I, label-boundary length), granularity, inter-annotator agreement where available | E | ⬜ |
| 1.6 | **Dataset difficulty indices**: domain separability in expression space, boundary fraction, domain-size imbalance, cell-type heterogeneity within domains, spatial autocorrelation | C | ⬜ |
| 1.7 | Diversity map: where datasets sit in technology × resolution × size × tissue × species space; redundancy | E | ⬜ |
| 1.8 | Frozen development/test split (by donor/section) used for every hyper-parameter choice | C | 🔶 (DLPFC donor 1) |

## 2. Tasks
| # | Task | Pri | Status |
|---|---|---|---|
| T1 | Domain identification, true number of domains K given | C | 🔶 |
| T2 | Unknown K: accuracy of K estimation and of the resulting partition | C | ⬜ |
| T3 | Multi-section joint analysis / batch integration (accuracy, iLISI, cross-section label consistency) | E | ⬜ |
| T4 | 3D / serial-section consistency | O | ⬜ |
| T5 | Cross-resolution and cross-technology consistency on the same tissue (Visium vs Visium HD bins vs Xenium) | E | ⬜ |
| T6 | Multi-scale / hierarchical domains (consistency across granularities) | E | ⬜ |
| T7 | Small and rare domain detection (recall as a function of domain size) | C | ⬜ |
| T8 | Boundary accuracy (boundary F1, Hausdorff distance) | C | 🔶 (DLPFC) |
| T9 | Downstream: recovery of domain marker genes / domain-specific spatially variable genes | E | ⬜ |
| T10 | Scalability task: up to 10^6 cells (see §11) | C | ⬜ |

## 3. Metrics: a comprehensive, multi-perspective panel
No single score is reported alone. Metrics are grouped into perspectives; each perspective is
summarised separately, and any overall score is shown with its sensitivity to the weights.

**3A. Partition agreement with the annotation (label-based, global)** [C]
ARI, AMI, NMI, Fowlkes–Mallows, V-measure, homogeneity, completeness, purity, Jaccard (pair-counting).
ARI and NMI behave differently with unbalanced domains, so both are always shown.

**3B. Per-domain and class-balanced accuracy** [C]
Hungarian-matched accuracy, balanced accuracy, macro- and weighted-F1, per-domain precision/recall,
**recall as a function of domain size** (are small and rare domains found?), count of missed and
spurious domains, over- and under-segmentation (split/merge counts).

**3C. Spatial structure and shape** [C]
CHAOS (spatial chaos), PAS (fraction of isolated spots), label Moran's I / Geary's C, number of
connected components per domain (fragmentation), domain compactness, boundary F1 and boundary
displacement (mean and Hausdorff distance), area error per domain.

**3D. Tissue topology** [E]
For layered tissues, preservation of layer order (rank correlation of predicted vs true laminar order);
for all tissues, similarity between the predicted and true domain-adjacency graphs (which domains touch
which).

**3E. Label-free internal quality** [E]
Expression silhouette, Davies–Bouldin, Calinski–Harabasz, spatial silhouette, within-domain expression
homogeneity. Used for **3J** (can they select good models without labels?).

**3F. Biological validity** [E]
Recovery of known domain markers (precision@k against curated marker lists), enrichment of
domain-specific spatially variable genes, pathway coherence of domain markers, consistency with
cell-type composition from deconvolution, agreement with histology where available [O].

**3G. Stability and consistency** [C]
Pairwise ARI between runs over training seeds, over clustering starts and over input permutations
(self-consistency); agreement between adjacent serial sections; invariance-violation rate (§6);
robustness curves under perturbations (§7), summarised as area under the degradation curve.

**3H. Multi-section integration** (task T3) [E]
iLISI and batch ASW (mixing), cLISI and label ASW (conservation), kBET, cross-section label consistency.

**3I. Model-selection metrics** (task T2) [C]
|K̂ − K|, fraction of sections with the correct K, accuracy at the estimated K.

**3J. Metric meta-analysis** [C]
Correlation and redundancy between metrics; cases where metrics disagree on the ranking; bias of each
metric towards many/few or large/small domains (tested on simulated partitions); how well label-free
metrics (3E) predict label-based ones (3A–3C).

**3K. Uncertainty-aware reporting** [C]
Every metric with bootstrap confidence intervals; differences reported relative to the noise floor (§4.6);
probability of superiority between methods (§4.7).

**3L. Efficiency and practicality** (detailed in §11) [C]
Runtime, peak memory, energy, cloud cost, scaling exponent, failure rate, installability.

**3M. Aggregation** [C]
Per-perspective scores (min–max or rank normalised per dataset); overall score as a weighted mean with
weights stated in advance; **ranking robustness to weight choice** (rankings under many random weight
vectors, reported as rank distributions); separate leaderboards per perspective so that readers can
choose what matters for them.

## 4. Reproducibility and variance (the "noise floor")
| # | Analysis | Pri | Status |
|---|---|---|---|
| 4.1 | Training-seed variance (≥3 seeds; 10 on a subset) | C | 🔶 |
| 4.2 | Clustering-initialisation variance on fixed embeddings (random-start GMM lottery) | C | ✅ |
| 4.3 | R mclust sensitivity to spot order and 1% noise | C | ✅ |
| 4.4 | Hardware/software non-determinism: CPU vs GPU, thread count, package versions | E | ⬜ |
| 4.5 | **Variance decomposition** (mixed-effects model): dataset, method, training seed, clustering start, input order, preprocessing | C | ⬜ |
| 4.6 | **Minimum detectable difference** on DLPFC and per technology | C | ⬜ |
| 4.7 | **Rank uncertainty**: bootstrap / Bayesian (Bradley–Terry) probability that method A beats B; rank confidence intervals | C | ⬜ |
| 4.8 | Rank stability across datasets, technologies and metrics (Kendall τ) | C | ⬜ |
| 4.9 | **Reported vs reproduced**: each method's published numbers vs official code (its own protocol) vs our leakage-free protocol | C | 🔶 (HiSTaR) |
| 4.10 | **Meta-analysis of claimed gains**: improvements claimed in 30–50 DLPFC papers vs the noise floor | C | ⬜ |

## 5. Evaluation-leakage audit
| # | Analysis | Pri | Status |
|---|---|---|---|
| 5.1 | Code and tutorial audit of every method; taxonomy: label-based epoch/seed/run selection, per-section hyper-parameter tuning on test labels, dropping unannotated spots, tuning on the reported sections, post-hoc K choice | C | 🔶 (Spatial-MGCN) |
| 5.2 | Measured inflation per leakage type (oracle-epoch, oracle-seed, oracle-hyper-parameter, NA-spot removal) | C | 🔶 (+0.15 ARI, Spatial-MGCN) |
| 5.3 | **Is the field over-fitting DLPFC?** Relation between publication year and performance on DLPFC vs other datasets | C | ⬜ |
| 5.4 | Author contact: share leakage findings with authors before submission | C | ⬜ |

## 6. Invariance ("metamorphic") tests: answers that should not change
| # | Transformation | Pri | Status |
|---|---|---|---|
| 6.1 | Spot/cell order permutation | C | 🔶 (mclust) |
| 6.2 | Coordinate rescaling (pixels vs µm), translation, rotation, reflection | C | 🔶 (STAGATE radius) |
| 6.3 | Gene order permutation; duplicated or renamed genes | E | ⬜ |
| 6.4 | Report invariance violations as a reliability score per method | C | ⬜ |

## 7. Robustness and stress tests
| # | Perturbation | Pri |
|---|---|---|
| 7.1 | UMI/read downsampling (sequencing depth) | C |
| 7.2 | Gene-panel reduction (simulate targeted panels from whole-transcriptome data) | C |
| 7.3 | Spot/cell dropout and tissue holes; cropping to sub-regions | E |
| 7.4 | Spatial jitter; simulated spot swapping / transcript diffusion | E |
| 7.5 | Wrong K (K ± 1, ± 2) | C |
| 7.6 | Hyper-parameter sensitivity around official defaults | C |
| 7.7 | Preprocessing factorial: HVG number, normalisation, PCs, graph type and size | E |
| 7.8 | Simulated batch effects between sections | E |

## 8. Clustering-stage analyses
| # | Analysis | Pri | Status |
|---|---|---|---|
| 8.1 | Matched clustering: same embedding clustered with mclust, GMM (multi-start), k-means, Leiden | C | 🔶 |
| 8.2 | Likelihood vs accuracy: is "best fit" a valid selection rule? | C | ✅ |
| 8.3 | Effect of each method's refinement/post-processing step | E | 🔶 |
| 8.4 | Degenerate clustering detection (mclust collapse) | E | ✅ |

## 9. What drives performance (component analysis)
| # | Analysis | Pri |
|---|---|---|
| 9.1 | Decompose methods into components: graph construction, encoder type, objective, clustering, refinement | E |
| 9.2 | Modular re-combination on a shared code base to estimate each component's contribution | O |
| 9.3 | Regression of performance on dataset difficulty indices (§1.6) and method components: which method for which data | C |

## 10. Embedding and biological analyses
| # | Analysis | Pri |
|---|---|---|
| 10.1 | Linear-probe upper bound: how separable are domains in each embedding (trained on dev sections) | E |
| 10.2 | Over-smoothing: boundary blur vs interior accuracy | E |
| 10.3 | Domain marker recovery vs known markers (DLPFC layer markers, hypothalamus region markers) | E |
| 10.4 | Method similarity (which methods give similar partitions) and consensus/ensemble performance | E |
| 10.5 | Spatial foundation models (e.g. Nicheformer): zero-shot vs fine-tuned vs task-specific methods | E |

## 11. Cost, runtime and usability
| # | Analysis | Pri | Status |
|---|---|---|---|
| 11.1 | Wall-clock time per stage (preprocess / train / cluster), peak RAM and GPU memory (including R subprocesses), CPU/GPU utilisation | C | 🔶 (time only) |
| 11.2 | Energy (kWh) and carbon (CO₂e) | C | ⬜ |
| 11.3 | Failures as outcomes: out-of-memory, timeout, crash rates | C | 🔶 |
| 11.4 | **Scaling curves** 10^3 to 10^6 cells under fixed time/memory limits; fitted exponents; practical size limit | C | ⬜ |
| 11.5 | Standard hardware profiles (CPU-only, single GPU); cloud cost per section and per million cells | C | ⬜ |
| 11.6 | **Accuracy–cost Pareto front** and efficiency score | C | ⬜ |
| 11.7 | **Software usability and decay**: installability on a current Python/R, dependency age and pins, fixes needed, documentation, tutorial reproducibility, maintenance activity | C | 🔶 (documented fixes for 9 methods) |

## 12. Statistics (applies to everything)
- Paired designs (same sections, seeds and clustering); Wilcoxon signed-rank tests with Holm / Benjamini–Hochberg correction; effect sizes with bootstrap confidence intervals
- Mixed-effects models for variance decomposition; Bayesian ranking for rank uncertainty
- Every number in the manuscript generated by scripts and checked automatically (`check_paper_numbers.py`)

## 13. Deliverables
1. Curated, QC-checked, leakage-free dataset resource (Zenodo DOI; uniform AnnData; label provenance)
2. Open benchmark package: any new method can be evaluated under the same protocol in one command
3. Leaderboard with confidence intervals and cost columns
4. Decision guide: method recommendations by data size, technology and hardware
5. Reporting checklist for method papers (seeds, clustering protocol, no label-based selection, noise floor)

## 14. Requirements and phases
- **Data access**: allow GEO/NCBI FTP, Zenodo, figshare, 10x Genomics, Dryad, Google Drive, Bioconductor/CRAN, Hugging Face in the environment's network settings
- **Compute**: the full run (about 30 methods × 100+ sections × seeds, up to 10^6 cells, GPU methods) must run on a GPU cluster; this environment (4 CPU cores, 15 GB, no GPU) is used to build and pilot the pipeline
- **Phases**: (1) protocol, registry, QC and audit tooling, pilot on current data; (2) data download and standardisation; (3) full runs on the cluster; (4) analyses, figures and manuscript

## 15. Hyper-parameters and fairness (pre-registered)
| # | Rule | Pri |
|---|---|---|
| 15.1 | **Arm A, "as published" (primary)**: each method runs with its authors' recommended settings, sourced in order of preference from (1) official tutorial/README for that technology, (2) settings stated in the paper, (3) package defaults. When no setting exists for a technology, a documented unit-free rule is used (e.g. radius in spot spacings), never a value tuned on test data | C |
| 15.2 | **Arm B, "equal tuning budget"**: every method, including our baselines, gets the same budget (e.g. 20 configurations sampled from the ranges the authors declare), tuned on the frozen development sections only; the selected configuration is frozen and applied to all test sections | C |
| 15.3 | Report both arms; the A-vs-B gap is reported as tuning sensitivity, and rank changes between arms are reported | C |
| 15.4 | Flag published settings that were themselves tuned on the benchmark's test sections (e.g. on DLPFC) | C |
| 15.5 | One configuration file per method (every parameter, its source, every deviation), released with the paper | C |
| 15.6 | Pre-registration: protocol, QC rules and configuration files are committed/archived with a timestamp before test results are generated | C |
| 15.7 | Author review: method developers are invited to check their configuration before submission; responses are reported | C |
| 15.8 | QC thresholds and preprocessing rules are identical for every method and fixed before any method is run | C |

## 16. Implementation notes (Phase 1 findings)
- **Save per-spot predictions for every run** (not only scores). Needed for 3B/3C/3D, the invariance tests, consensus analysis and error maps; the first benchmark runs did not keep them.
- Pilot finding for 3B (macro-F1 / missed domains): the AnisoST baseline recovers **no spot of annotated Layer 4 in 12 of 12 DLPFC sections** (Layer 4 = 6-9% of spots), although ARI is 0.44-0.76 (151672: ARI 0.76 with one layer missed). Global ARI hides missed thin domains; to be measured for all methods.
- Spatial-coherence metrics are unit free (distances divided by the median spot spacing); CHAOS is close to 1.0 for any smooth partition on a lattice, so it mainly flags isolated spots and has little discriminative power otherwise.
