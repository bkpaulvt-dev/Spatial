# Benchmark protocol (pre-registration draft v0.1)

**Status: DRAFT (this file was not frozen before the analyses; it is the working protocol, and the manuscript and its supplement are the authoritative description; deviations are listed under Amendments).** To be frozen (tagged in git and archived on Zenodo with its hash) *before* any
result on the held-out test sections of newly added datasets is generated. After freezing, any change
is recorded in a dated amendment list at the end of this file and reported in the paper.

Companion documents: `docs/BENCHMARK_PLAN.md` (all analyses), `configs/datasets.yaml` (data),
`configs/methods.yaml` (methods and settings), `docs/LEAKAGE_AUDIT.md`.

## 1. Question
How accurate, reproducible, robust and costly are spatial domain identification methods, and how much
of the progress reported in the literature exceeds what chance, clustering initialisation and evaluation
practice alone can produce?

## 2. Data
* Every public dataset with domain annotations that passes the inclusion rules below.
* **Inclusion**: raw counts available; per-spot/cell coordinates; annotation of at least 2 domains on
  at least 50% of spots; a documented label source; licence permits redistribution of derived files
  (otherwise a download script is provided).
* **Label provenance** (`configs/datasets.yaml`): expert / reference_atlas / marker / algorithm / unknown.
  Datasets whose labels were produced by a clustering algorithm are reported but **excluded from the
  primary ranking** (circularity). `unknown` provenance must be resolved before ranking.
  *Superseded for the paper (see Amendments):* STARmap (`unknown`) and Stereo-seq (`algorithm`) are kept in the primary
  analysis because dropping them would leave five groups; the analysis restricted to datasets whose annotation is not known to be
  clustering-derived is reported as the check this rule calls for.
* **Split**: for every dataset one or more *development* sections (fixed in the registry before any
  run); all remaining sections are *test*. Development sections are the only data usable for tuning
  (Arm B) or for choosing preprocessing rules.

## 3. Quality control (identical for every method; applied before any method runs)
`spatialbench.qc.FLAG_RULES` define flags (few spots, low annotation, tiny domain, duplicate coordinates,
few genes, single domain). **No section is dropped silently**: flagged sections are listed in the paper;
a section is excluded from the primary ranking only for *few spots*, *low annotation* or
*single domain*, and the effect of excluding the others is reported as a sensitivity analysis.
No QC threshold may depend on any method's output.

## 4. Tasks
T1 (K given) is primary. T2 (K unknown), T3 (multi-section), T5 (cross-technology), T6 (multi-scale),
T7 (small domains), T8 (boundaries), T9 (markers), T10 (scalability) are secondary; see the plan.

## 5. Methods and settings
* **Arm A (primary)**: settings recorded in `configs/methods.yaml` (source: tutorial > paper > package
  default; documented unit-free rules otherwise; never tuned on test sections).
* **Arm B (secondary)**: the same budget (20 configurations drawn from the ranges declared by the
  authors) for every method, selected on development sections only, then frozen.
* All methods receive the same inputs (raw counts, coordinates), the true K in T1, and at least 3
  training seeds (1 for methods above 30 min per section, reported as such).
* A method that fails (crash, out of memory, timeout) is reported as a failure with its resource
  limit; it is never silently dropped or re-run with different settings.
* Developers are invited to review their configuration before submission.

## 6. Clustering and selection rules (leakage-free)
* No quantity derived from the annotation (ARI, NMI, per-domain scores) may be used to select a run,
  epoch, seed, resolution, hyper-parameter or K, except K in T1 and Arm B tuning on development sections.
* Methods that select by labels in their released code are reported twice: as released (flagged) and
  with a label-free rule (final epoch / best internal objective). The primary ranking uses the label-free rule.
* Matched clustering: every embedding is additionally clustered with the same 20-start GMM; the primary
  comparison of embeddings uses it, and method-specific clustering is reported alongside.

## 7. Metrics
Panel 3A-3M of the plan. **Primary**: ARI, macro-F1, boundary F1, runtime. Overall scores use weights
fixed here: equal weight to the perspectives agreement (3A), per-domain (3B), spatial (3C) and
stability (3G); rankings under random weights are reported (3M).

## 8. Statistics
Unit of analysis = section; paired tests (Wilcoxon signed-rank) with Holm correction within each
family of comparisons; bootstrap confidence intervals over sections; variance components by
mixed-effects models; rank uncertainty by bootstrap. The families of tests are listed in
`docs/BENCHMARK_PLAN.md`; additional exploratory tests are labelled as such.

> **Superseded for the paper.** This section is the plan written before the analysis. The manuscript uses the cluster-aware
> analysis of `scripts/stats_cluster_aware.py` instead: sections are nested in groups (three DLPFC donors and one group each for
> STARmap, MERFISH, breast cancer and Stereo-seq), differences to the reference (linear diffusion, chosen after seeing the
> means, so exploratory) are equal-weight means of group means with 95% hierarchical-bootstrap intervals (and Bonferroni
> intervals over the 16 comparisons), an equivalence margin of ±0.03 ARI, bootstrap rank probabilities, and sensitivity analyses
> (standardised runner only; expert-annotated datasets only). The pooled Wilcoxon tests over sections are kept only as a
> secondary table.

## 9. Reporting
Every figure and number is generated by scripts from raw per-run results; per-spot predictions are saved
for every run; `scripts/check_paper_numbers.py` verifies the manuscript against the results; a
reproducibility package (code, configs, container/lock files, results) is archived.

## 10. Amendments
Recorded retrospectively; none of these were pre-registered.
1. Section 2: STARmap and Stereo-seq are in the primary analysis (see the note there); a sensitivity analysis without them is reported.
2. Section 8: the primary comparison uses matched clustering (20-start Gaussian mixture), cluster-aware hierarchical bootstrap over
   groups, an equivalence margin of 0.03 ARI, and a reference baseline (linear diffusion) chosen after the means were seen (exploratory).
3. Section 5: HiSTaR was run as a PyTorch port and CCST as a re-implementation; GraphST uses its Stereo-seq mode; BASS keeps its DLPFC
   settings on breast cancer and Stereo-seq.
4. Section 5 (never re-run with different settings): the GraphST call to R mclust was wrapped (same function, run inside R) on the second
   server because the direct call failed with mclust 6.x; labels were identical to the original function on two test embeddings.
5. Seventeen jobs that exceeded the memory cap of the benchmark machine were rerun with unchanged settings on a second server.

