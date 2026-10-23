# NAR review, round 2, report 02: benchmark design

**Reviewer focus:** benchmarking methodology, judged against Weber et al. 2019, Mangul et al. 2019 and Sonrel et al. 2023.

**Files read:**
- `paper/main.tex`
- `results/paper_macros.tex`
- `paper/supp_labels.tex`
- `paper/supplementary.tex`
- every table in `results/supp/`
- `configs/datasets.yaml`
- `results/coverage_matrix.md`
- `scripts/stats_cluster_aware.py`
- the header of `scripts/bench_run.py`
- `results/benchmark_runs.jsonl` (read-only pandas summary)
- `docs/figures/nar_fig1_pipeline_v2.png` and `nar_fig2_accuracy.png`
- `docs/PROTOCOL.md` (header only)
- the round-1 report `docs/nar_review/02_benchmark_design.md`

## Recommendation: major revision (not acceptable in its current form)

The revision is a real improvement:
- Matched clustering is now the primary analysis.
- A neutrality paragraph has been added.
- The datasets are clustered by donor and study, and the analysis is repeated without the development sections.
- Two non-brain tissues and a fourth technology have been added.
- The paper reports honestly that the baseline's lead does not carry over to the new tissues.

That last result is the most informative thing in the revision. However, the claims, the figures and the statistics have not caught up with it:
- The abstract and Fig. 2B/C still lead with a pooled ranking. In that ranking 5 of the 7 bootstrap groups are brain tissue.
- The ranking leaves out the strongest competitor (BASS) because of a memory cap.
- The brain datasets and the new datasets come from two different execution environments. The differences between those environments are larger than the equivalence margin.
- The Stereo-seq labels are classed `algorithm` in the authors' own registry. The authors' own protocol says such labels must not enter the primary ranking, yet they do.

These are fixable, and most of the fixes need no new computation, because runner results already exist for all 24 sections. The rest of the design (no simulation, thin non-brain data, few methods, no containers) still falls short of a NAR benchmark resource.

---

## Major points

Points M1–M6 block acceptance.

### M1. The headline claim rests on a pooled estimand that the data show to be heterogeneous

- **The pooled number is mostly a brain number.** The abstract and the Results lead with "higher mean ARI than 8 of 16 comparators … could not be separated from the other 8". That figure is the equal-weight mean over 7 groups, 5 of which are brain (3 DLPFC donors, STARmap, MERFISH). DLPFC alone carries 3/7 of the weight. The two non-brain groups contribute one Visium section and one Stereo-seq study.
- **The tissue effect is large.** The authors themselves report a method × tissue interaction. The mean difference between the baseline and the comparators is +0.172 on brain and −0.025 on non-brain. On the new data, 13 of 16 comparators lead on breast cancer and 12 of 15 lead on Stereo-seq.
- **Pooling over that interaction is not meaningful.** The pooled Δ answers "how does the method do on a tissue mix that is 71 % brain". No user faces that mix.
- **The bootstrap resamples tissues as if they were exchangeable.** It draws the 7 groups with replacement, so about 9.5 % of resamples ((5/7)^7) contain no non-brain group at all. The pooled intervals and the rank distribution therefore over-represent brain-only worlds.
- **The probability of ranking first is misleading.**
  - P(rank 1) = 0.73 and the rank interval 1–5 (Fig. 2C, Table S7) are computed among 11 methods only.
  - Excluded for the memory cap: BASS, GraphST, NichePCA, DeepST and Spatial-MGCN. Also excluded: BayesSpace (Visium only).
  - BASS has the highest dataset mean on MERFISH and breast cancer. It has the highest brain-only average (0.594 against 0.587) and the highest ARI in the runner metric panel (Table S12: 0.549 against 0.530).
  - A "probability of being best" that excludes the method most likely to be best should not be shown.
- **"Slightly" understates the non-brain result.**
  - On breast cancer and Stereo-seq the baseline ranks roughly 13th of 17.
  - The per-dataset differences reach −0.08 (BASS, NichePCA, SpaGCN) and −0.09 (DeepST).
  - Most strikingly, the non-spatial PCA reference beats linear diffusion on both new datasets: 0.562 against 0.545 on breast cancer, and 0.349 against 0.306 on Stereo-seq.
  - The text does not mention this. It matters for interpretation: see M4.
- **The reference is still post hoc.** Linear diffusion is still the exploratory reference chosen after the means were seen. The new datasets were added "without changing any setting", so they are in effect a held-out validation of the brain-derived hypothesis "smoothing ≥ published methods". That hypothesis was not confirmed. The paper should say this explicitly. It is a stronger and more honest message than the pooled 8/16.

**Required:**
1. Make the primary accuracy result **stratified by tissue/dataset**: per-dataset ranks or Δ with intervals, and the brain and non-brain blocks reported separately.
2. Demote the pooled estimand to a secondary analysis, or drop it.
3. Rewrite the abstract's first result accordingly. For example: "on brain tissue a smoothing baseline matched or exceeded most methods; on breast cancer and embryo it was below most methods, including non-spatial PCA."
4. Either compute ranks over all methods, imputing the missing E10.5_E1S1 values under a pre-stated rule (see M3), or rank on the 23 sections that every method completed. Do not drop methods from the ranking.
5. Report the brain/non-brain interaction formally. A mixed model of ARI ~ method × tissue + (1 | group/section) is enough to show that it exists. Note that with one breast cancer section and one embryo study, this interaction cannot be separated from technology, K, domain size or label provenance (see M4).

### M2. Two execution environments are mixed within one comparison

- **What is mixed.** DLPFC, STARmap and MERFISH use the "published pipelines", where each method has its own preprocessing. Breast cancer and Stereo-seq use the "standardised runner", where preprocessing is shared (Table S14 caption).
- **What the agreement table shows.** The runner-minus-pipeline differences in Table S14 are method-specific and reach:
  - +0.071 (STAGATE, STARmap)
  - −0.077 (HiSTaR, STARmap)
  - +0.057 (AnisoST, STARmap)
  - −0.039 (SpaGCN, MERFISH)
  - +0.016 to +0.026 for linear diffusion on all three datasets

  All of these exceed the 0.03 equivalence margin.
- **Why it matters.** The brain-versus-non-brain contrast, the central new finding, is fully confounded with pipeline versus runner. The seed design is confounded with it too:
  - STAGATE, CCST, Spatial-MGCN and BASS have 1 seed on the brain data and 3 on the new data.
  - DeepST is the reverse: 3 seeds on brain and 1 on the new data.
  - GraphST has 1 seed on DLPFC.
- **A second inconsistency.** The "own clustering" values for linear diffusion and PCA on the new datasets come from a separate script (`baselines_3start.jsonl`), while the matched values come from the runner (`stats_cluster_aware.py`, lines 36–41).
- **The fix is cheap.** The coverage matrix shows runner results for 24/24 sections with 3 seeds for every method except DeepST and BayesSpace.

**Required:**
1. Make the runner, with one preprocessing and one code path, the **single source for the primary analysis on all five datasets**.
2. Report the published-pipeline numbers as a sensitivity analysis. They remain useful, for example to show what each method's own preprocessing does.
3. Say in the main text which numbers come from which environment.
4. Give DeepST three seeds on the new datasets. The Methods text claims "three seeds for every method"; `benchmark_runs.jsonl` shows 1 seed for DeepST on breast cancer and Stereo-seq.

### M3. Failure and out-of-memory handling is not neutral, reproducible or pre-specified

- **The cap was not applied uniformly.** It was enforced only on the breast cancer and Stereo-seq runs. BayesSpace peaked at 12.5 GB on DLPFC 151509 (and 12.2 GB on 151510) and was counted as a success. Table S13 lists BayesSpace at 12.5 GB above a "12 GB cap", so the table is internally inconsistent.
- **The out-of-memory status depends on machine load.**
  - The kill rule includes "or leaving less than 0.8 GB of system memory" on a 15 GB machine.
  - In `benchmark_runs.jsonl`, BASS was killed on DLPFC sections 151507–151510 at 5.0–6.8 GB peak RSS, and NichePCA on 151509 at 6.7 GB. That is far below the cap, so these kills were caused by other jobs running at the same time.
  - The runs succeeded on retry. Out-of-memory status is therefore not a deterministic property of the method. The retry policy is not documented.
  - The main text says each new-dataset job "ran alone"; the authors must show this held for the E10.5_E1S1 runs.
- **The cap itself.** 12 GB for 18,408 bins is a hardware limit of the authors' machine, not a pre-registered scalability criterion. Five of 13 published methods lose their result on the largest section.
  - BASS ran for 68–80 min before it was killed at 12.0 GB, perhaps close to finishing.
  - NichePCA (aggregation plus PCA) failing at 18k bins points to an adapter or densification problem, not an inherent limit. In the runner it receives about 25k genes, possibly as a dense matrix.
- **Consequences.** The failed methods are dropped from the ranking (M1). Their Stereo-seq means are computed on the two smaller sections and shown with an asterisk in Fig. 2A, next to full-data means of other methods.

**Required:**
1. Rerun E10.5_E1S1 for the five failed methods on a node with ≥64 GB, so that accuracy is available for every method.
2. Report memory as a *separate, pre-stated* scalability outcome: a fixed cap, a fixed time limit, exclusive node, and a retry policy declared in advance. Apply it to all datasets.
3. Investigate the NichePCA and GraphST failures. GraphST's dense N×N adjacency is a known issue; say so.
4. If reruns are impossible, use a pre-stated rule for missing results (for example worst-observed ARI, or complete-case ranking on 23 sections) and report sensitivity to the rule.
5. Treat "Visium only" BayesSpace explicitly, as a separate stratum.

### M4. Annotation provenance contradicts the authors' own exclusion rule

- **Stereo-seq (MOSTA).**
  - `configs/datasets.yaml` classes the labels as `algorithm` ("obtained by unsupervised clustering of the bin50 expression … circular for clustering methods; confirm … before ranking on this dataset").
  - `PROTOCOL.md` excludes `algorithm` and `unknown` labels from primary rankings.
  - Stereo-seq is nonetheless one of the 7 bootstrap groups in the primary analysis, and it drives half of the non-brain conclusion.
  - The observed pattern is what clustering-derived labels would predict: non-spatial PCA + GMM beats spatial smoothing, and all ARIs are low (about 0.25–0.39).
  - The Discussion's mechanistic story ("domains are smaller, interleaved … smoothing blurs them") is presented as the explanation. Label circularity is an equally plausible explanation, and the paper does not test between the two.
- **STARmap.** The labels are still `class: unknown` and still ranked. This is unchanged from round 1.
- **MERFISH.** The labels are still "believed to" be atlas-registered. As in round 1, the STARmap and MERFISH labels come from the BASS repository, and BASS is the top competitor on both.
- **Breast cancer.**
  - The 20 fine-grained regions (for example IDC_1…IDC_7, Tumor_edge_1…6) come from the SEDR analyses repository, and "whether expression clusters were used" is unconfirmed.
  - The smallest domain is 0.7 % of spots.
  - A 4-class coarse annotation (`annot_type`) is available in the same file but is not used.
- **Status.** Every provenance field is `verified: false`.

**Required:**
1. Confirm the provenance of every dataset from the primary sources and report it in a table.
2. Apply the protocol's own rule. Run the primary analysis with only `expert` or `reference_atlas` labels, and show Stereo-seq (and STARmap, unless resolved) as secondary.
3. For breast cancer, add the coarse 4-class annotation as a sensitivity analysis.
4. Test the "domain size and interleaving" explanation directly, for example per-domain recall against domain size, or an ARI/F1 analysis restricted to large domains, instead of asserting it.

### M5. Data breadth is still below the standard for a NAR benchmark

Round 1 asked for ≥4–6 further annotated datasets, a large single-cell platform and a simulation arm. The revision adds:
- one Visium section (one sample, no biological replicate);
- one Stereo-seq study at bin50, with algorithm-derived labels.

There is still:
- no Xenium, MERSCOPE, CosMx, Slide-seq or Visium HD data;
- nothing above 18k observations;
- **no simulated data with known domains.**

The paper's own pivot makes simulation more necessary, not less. The question is now *why* the ranking flips between tissues. Simulations that vary domain size, interleaving, boundary sharpness and K are the direct way to answer it, and they would also separate method effects from label noise (M4). Recent spatial benchmarks (Hu et al. 2024; Chen et al. 2025 iMeta; SACCELERATOR) set this bar.

**Minimum:**
1. A simulation arm, for example SRTsim or scDesign3 with a controlled domain layout.
2. At least one more expert-annotated non-brain tissue with ≥2 sections or donors, so that a non-brain group has within-group replication.
3. One large imaging dataset (≥50k cells) for scalability.

### M6. Methods panel and resource (largely unchanged)

- **Method selection.**
  - The inclusion criteria are now one sentence ("maintained public code that runs on CPU"). There is still no systematic search and no flow table of identified, eligible, run and failed methods.
  - The "runs on CPU" criterion is not neutral. It removes GPU-oriented methods and penalises methods built for GPU.
  - SpatialPCA and conST were screened in the code audit but not benchmarked, and no reason is given.
  - CellCharter, MENDER, stLearn, DR-SC/PRECAST, Giotto HMRF and a non-spatial Leiden reference are still absent.
- **Reproducibility.**
  - There are no containers or lock files.
  - `requirements.txt` has 10 lines.
  - There is no workflow manager.
  - The GitHub and Zenodo links are still `\todo`.
  - `PROTOCOL.md` still reads "pre-registration draft v0.1, Status: DRAFT", yet `stats_cluster_aware.py` still states the margin was "fixed before looking".

For NAR, a reusable and extensible resource (Sonrel; Mangul) remains a condition of acceptance.

### M7. Statistics design (major, not blocking once M1 is done)

- **Percentile intervals.** Percentile bootstrap intervals with 7 heterogeneous top-level units are not reliable. The breast cancer group has n = 1 section, so it adds no within-group variance and the same weight as a 4-section DLPFC donor. Add a mixed-effects model (random effects for group and section; fixed effect for method, or method × tissue) as a sensitivity check, and report how the conclusions change.
- **Equivalence margin.**
  - The 0.03 ARI margin is justified as "about the seed SD". The seed SDs actually range from 0.005 to 0.18. Linear diffusion's own SD is 0.039 on DLPFC and 0.054 on MERFISH, which is larger than the margin.
  - The 95 % half-widths are about 0.05–0.13, so the design cannot establish equivalence. "No comparator was equivalent" carries no information.
  - Either justify the margin externally (for example as the typical improvement claimed between successive methods, about 0.02–0.05) and give a precision/power statement, or drop the equivalence language.
- **Multiplicity.** None is applied across 16 comparisons × 2 protocols. The paper now says so, which is better, but Holm-adjusted results, or simultaneous (max-t bootstrap) intervals, should accompany the verdict column.
- **Development sections.** The text gives conflicting definitions:
  - "four development sections" (Neutrality paragraph);
  - "DLPFC donor 1" (Methods, baselines);
  - "DLPFC donor 1 and the first section of STARmap and MERFISH" (Statistics).

  The registry has 6 dev sections. Reconcile these.

### M8. Neutrality (partly resolved)

- **Done:** a neutrality paragraph and a conflict-of-interest statement were added, matched clustering became primary, and the analysis is repeated without the development sections.
- **Not done:**
  - HiCAST, the authors' unpublished HiSTaR successor and the origin of the project, is not disclosed.
  - AnisoST remains a Results paragraph that includes a boundary test with uncorrected p = 0.034 on 12 sections.
  - No developer was invited to review their method's configuration. In particular, there is no reported contact with the HiSTaR or Spatial-MGCN authors before claims of non-reproduction or label-based epoch selection.
- **Dataset choice.** The two new datasets (10x breast cancer, MOSTA) are the "home" datasets of several competitors (SEDR, GraphST, STAGATE, Spatial-MGCN's `HBC_test.py`), much as DLPFC is the authors' development data. That cuts both ways and should be stated. Dataset selection still has no stated criteria.

---

## Minor points

1. **Table S20 (`results/supp/coverage.tex`) is corrupted.** Every "20/24" became "2not run": a string replacement of "0/24" → "not run" in `make_supplement.py`. As printed, the table says the pipeline ARI and R mclust perturbation experiments were "not run".
2. **Table S12 caption is stale.** It says "Runs: 60 per method (20 sections, 3 seeds) … DeepST (20 …) BayesSpace (12 Visium sections)"; the table shows 72/69/23/13. The comment in `stats_cluster_aware.py` ("methods with all 20 sections") is also stale. Table S12 ranks BASS first, which contradicts the headline; say why the two differ (it is the runner; see M2).
3. **Fig. 1 is out of date.** Panel A shows only DLPFC, STARmap and MERFISH. Breast cancer and Stereo-seq are missing, and the caption says "expert annotation", which is wrong for MOSTA.
4. **Fig. 2A/B.** Asterisked Stereo-seq means (2 sections) sit beside 3-section means. Show the paired 2-section value for the baseline, or mark both. Fig. 2C should not show P(best) at all until M1 is fixed.
5. **"Comparators" mixes groups.** The 16 comparators include the authors' own ablations (AnisoST, PCA). For published method entries the count is 7 baseline-higher and 7 unresolved, out of 14. State that count, as requested in round 1.
6. **The K-sensitivity analysis is degenerate.** BIC chose the largest K allowed in 324/331 embeddings, so the "label-free K" is effectively K+2. Call it that, or use a stability criterion. This is not a K-unknown task (round-1 G13).
7. **Seed design.**
   - 1 seed for STAGATE, CCST, Spatial-MGCN and BASS on the brain pipeline;
   - 1 seed for GraphST on DLPFC;
   - DeepST at 1 seed on the new data.

   Resolved automatically by M2 except for DeepST.
8. **Incomplete R mclust seed experiment.** It covers 23/24 sections for most methods, and `results/` holds `.lock_stereo_E10.5_E1S1_*` files, so it was still running when the macros were generated. Regenerate once complete, and state n per method.
9. **Single-thread CPU timing** remains the only cost measure (no GPU, no multi-thread, no scaling curve). Keep the caveat, but add the scaling experiment (M5).
10. **Unscored usability.** The installation and patching burden recorded in Table S2 is still not summarised in a usability rubric (round-1 G10).
11. **Scope is not in the abstract.** The abstract should state the task explicitly: single section, K given, ≤18k observations.

---

## Status of round-1 points

| # | Round-1 point | Status | Comment |
|---|---|---|---|
| G1 | Scope statement | **Partly** | Four technologies and three tissues are now described. The single-section, K-given, small-data scope is in the Limitations but not in the abstract or title. |
| G2 | Neutrality | **Partly** | Neutrality paragraph, conflict-of-interest statement and dev-excluded reanalysis added. Not done: HiCAST disclosure, demotion of the AnisoST section, developer review and author contact. The reference is still post hoc; it is labelled exploratory but still drives the headline. |
| G3 | Datasets, diversity, ground truth, simulation | **Partly / still blocking** | Two non-brain datasets added (1 + 3 sections). No simulation, no large single-cell data. STARmap is still `unknown`, Stereo-seq is `algorithm` yet ranked, and all provenance is unverified. |
| G4 | Inclusion criteria and missing methods | **Open** | A one-sentence criterion was added. No search or flow table and no new methods. SpatialPCA and conST were screened but not run. |
| G5 | Clustering asymmetry and tuning | **Resolved (core) / open (rest)** | Matched clustering is now primary; the default-protocol baselines still use 3-start GMM (secondary). No Arm B tuning and no histology-enabled SpaGCN or DeepST. |
| G6 | Metrics and single pipeline | **Open** | Table S12 (runner) and Table S3 (mixed) still disagree, and now BASS leads S12. No aggregate multi-metric score and no biological metric. Caption stale. |
| G7 | Seeds and coverage | **Partly** | The new datasets have 3 seeds (DeepST excepted). The brain pipeline still has 1 seed for 4 methods. The coverage table is now corrupted (minor point 1). |
| G8 | Statistics | **Partly** | Now 7 groups; pre-registration language reduced; no correction acknowledged. Still no Holm correction, no mixed model, and the protocol is not frozen; the script docstring still says "fixed before looking". |
| G9 | Scalability and failures | **Partly** | Out-of-memory runs are reported (welcome). The cap is uneven and load-dependent (M3). No scaling curve, GPU or large data. |
| G10 | Usability rubric | **Open** | |
| G11 | Containers, workflow, archive | **Open / blocking** | |
| G12 | Overclaims | **Partly** | "Matched or outperformed every deep encoder" is gone, and the tissue dependence is stated. The pooled 8/16 headline, P(best) = 0.73 with BASS excluded, and "slightly ahead" still overreach (M1). HiSTaR values are filled in. |
| G13 | K unknown, multi-section | **Partly** | A BIC/K±2 sensitivity analysis was added, but it is degenerate (minor point 6). No multi-section task. |
| G14 | Manuscript readiness | **Partly** | NAR template; the bib `VERIFY` flags are gone. Authors, URLs, funding and CRediT are still `\todo`. |

## Prioritised actions

1. One execution environment (the runner) for all five datasets, with ≥3 seeds per method (M2).
2. Rerun E10.5_E1S1 without the memory constraint, or apply a pre-stated missing-data rule. Rank all methods (M3).
3. Make the stratified per-tissue result primary, and rewrite the abstract around "the baseline wins on brain and does not generalise". Report that PCA beats smoothing on the new tissues (M1).
4. Enforce the label-provenance rule, verify the sources, and add the coarse breast cancer labels (M4).
5. Add a simulation arm and at least one more replicated non-brain dataset plus one large imaging dataset (M5).
6. Provide containers, a workflow and a Zenodo archive; freeze the protocol or remove the pre-registration language (M6, M7).
7. Fix the minor-point items: the coverage table corruption, stale captions, Fig. 1, and the development-section definition.
