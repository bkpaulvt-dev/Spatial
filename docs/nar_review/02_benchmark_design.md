# NAR review 02: benchmark design against established guidelines

Reviewer focus: benchmarking methodology. Files read: `paper/main.tex`, `paper/supplementary.tex`,
`results/supp/*.tex`, `results/coverage_matrix.md`, `configs/methods.yaml`, `configs/datasets.yaml`,
`docs/EVIDENCE_MAP.md`, `docs/PROTOCOL.md`, `README.md`, `docs/AnisoST.md`, `docs/HiCAST.md`, `requirements.txt`.

## Reference standards (checked by web search, 2026-10-18)

| Source | What it asks for (relevant parts) |
|---|---|
| Weber et al. 2019 *Genome Biol* 20:125 | State the purpose and whether the benchmark is **neutral** or a method-development comparison. Use explicit **inclusion criteria** and ideally include all available methods. Use a **diverse set of datasets**, both **simulated** (known ground truth) and real. Avoid pitfalls such as too few datasets or simulation scenarios, overly simple simulations and subjective dataset choice. Treat **parameters equally**: no method should gain an edge from more tuning, and every method should use the same strategy (defaults, published settings or a systematic search). Report several metrics plus **secondary measures**: runtime, scalability, memory and user-friendliness/documentation. Publish code, containers and results so that others can reproduce and **extend** the benchmark. |
| Mangul et al. 2019 *Nat Commun* 10:1393 | A **gold standard** with known provenance. **Archive the tools, versions and parameters**. **Share raw outputs**, documentation and installation notes, and use containers. Address overfitting and the incentives behind a study. |
| Sonrel et al. 2023 *Genome Biol* 24:119 | A meta-analysis of 62 single-cell benchmarks scored on scope, **neutrality**, code and data availability, and **extensibility**. Most benchmarks can in principle be reproduced but are hard to extend. Recommends **containerisation and workflow systems**, reusable intermediate results, and continuous or living benchmarks (OpenEBench, Open Problems). |
| Yuan et al. 2024 *Nat Methods* (doi 10.1038/s41592-024-02215-8) | 13 methods on 34 SRT datasets in 7 collections. Scored on accuracy, spatial continuity, marker-gene detection, **scalability** and **robustness**. |
| Hu et al. 2024 *Genome Biol* 25:212 | 16 clustering, 5 alignment and 5 integration methods on real **and simulated** data of varying size, technology and species. 8 clustering metrics. Code on GitHub with a reproducibility site. |
| Chen et al. 2025 *iMeta* (doi 10.1002/imt2.70084) | 14 clustering methods on about **600 datasets**, real and **simulated** (adjacent-slice and neighbourhood-disruption simulations). |
| SACCELERATOR (2025/26, community framework) | 22 methods on 15 datasets from 9 technologies. It notes that existing benchmarks are undermined by a "narrow focus on Visium and brain tissue datasets". |
| `nar2025bench` (cited as NAR 53(7) gkaf303) | **I could not verify that this paper exists under the cited title.** The bib entry has `author = {VERIFY}`. It must be verified or removed (see also `explanatory2026`, `do2026graphbg`). |

**Positioning.** Weber's terms make this a *method-development / non-neutral* benchmark (details in G2). It also covers less than the recent spatial-domain benchmarks: 3 datasets and 1 brain region per technology, against 7–600 dataset collections. Its distinctive contribution is the **robustness analysis on fixed embeddings** (clustering lottery, mclust order/noise sensitivity, label-selected epochs). That contribution is well executed and well supported. The paper should be framed around it, not around an accuracy ranking.

---

## Item-by-item assessment

Severity is for NAR acceptance: **B** = blocker, **M** = major, **m** = minor.

### G1. Purpose and scope statement — m
* **What the paper does:** The Introduction poses three questions (accuracy, robustness, reproducibility).
* **Gap:** The title and abstract present a general benchmark of "spatial domain identification methods", but the design (3 brain tissues, ≤6k cells, K given, single section) covers a narrow use case. Multi-slice analysis, K unknown, large single-cell platforms and non-brain tissue are all out of scope.
* **Fix:** State the scope explicitly in the abstract and Introduction: single-section, K-known, small datasets. Alternatively, broaden the scope (see G3).

### G2. Neutrality — **B**
* **What the paper does:** Competing interests are declared as "none".
* **Gap 1:** The repository grew out of the authors' own method work. `README.md` and `docs/HiCAST.md` describe HiCAST, a HiSTaR successor that failed. `docs/AnisoST.md` was drafted as a method paper titled "*… with a training-free edge-preserving baseline*". Two of the three baselines (linear diffusion, AnisoST) are the authors' own. A full Results subsection ("Edge preservation helps at boundaries…") is method development.
* **Gap 2:** The headline reference (linear diffusion) was chosen *after seeing the means*. The paper admits this.
* **Gap 3:** The baseline settings were fixed on DLPFC donor 1, which is part of the evaluated data, while competitors got no tuning.
* **Gap 4:** Under Weber et al. and Sonrel et al., a reader must be told that this is not a neutral benchmark.
* **Fix:**
  1. Add a neutrality statement saying that the authors developed HiCAST (unpublished, not benchmarked) and the two diffusion baselines, and have no affiliation with the benchmarked methods.
  2. Move the AnisoST subsection to the Supplement, or label it as an ablation.
  3. Pre-specify the reference comparator in a frozen protocol, or use a reference-free summary such as rank intervals across all methods. Report headline numbers with the development sections excluded.
  4. Invite method developers to review their configurations. `PROTOCOL.md` §5 promises this, but it has not been done.

### G3. Datasets: number, diversity, ground truth — **B**
* **What the paper does:** It uses 20 sections from 3 technologies. In practice this is **3 datasets and 5 statistical clusters**: 12 DLPFC sections from 3 donors, 3 STARmap sections from 1 experiment, and 5 MERFISH sections from 1 animal.
  * All are brain tissue.
  * The largest section has about 5.9k cells. STARmap has about 1k cells and 166 genes.
  * There are no simulated data.
* **Gaps:**
  1. **Diversity.** There is no non-brain tissue (tumour, breast cancer, mouse embryo, kidney, liver). There are no high-resolution or large platforms (Stereo-seq, Slide-seqV2, Visium HD, Xenium, CosMx, MERSCOPE). Yuan et al. used 34 datasets, Hu et al. used real and simulated data across many technologies, and SACCELERATOR used 9 technologies. NAR readers will see 3 datasets as insufficient for any ranking claim.
  2. **Annotation validity.** STARmap label provenance is `class: unknown` in `configs/datasets.yaml`. `PROTOCOL.md` §2 says "`unknown` provenance must be resolved before ranking", yet STARmap is ranked. MERFISH provenance is "believed to" be atlas-based, and every provenance field is `verified: false`.
  3. **Possible circularity.** The STARmap and MERFISH labels are taken from the **BASS analysis repository**, and BASS ranks first on MERFISH and second overall. This must be checked and discussed.
  4. **No simulation.** The paper notes that annotations are coarse and may themselves be method-derived. Simulation with known domains is the standard remedy (Weber; Hu; Chen et al. iMeta). Examples include SRTsim, scDesign3, or domain-structured simulations with controlled boundary sharpness, domain size, noise and cell-type mixing. Without it, the robustness claims (lottery, mclust order) cannot be separated from label noise.
* **Fix (minimum for NAR):**
  * Add **≥4–6 further annotated real datasets**, covering at least one tumour or non-brain Visium dataset (e.g. human breast cancer), one Stereo-seq or Slide-seq dataset, one Xenium or MERSCOPE/CosMx dataset with ≥50k cells, and the mouse embryo or olfactory bulb if labels exist.
  * Add a **simulation arm** with known domains that varies domain number, size and imbalance, boundary sharpness and noise.
  * Resolve and report label provenance for every dataset. Exclude `unknown` or algorithm-derived labels from the primary ranking, as the protocol already requires.

### G4. Method selection and inclusion criteria — M (borderline B)
* **What the paper does:** It runs 13 published methods (BANKSY in two settings) and 3 baselines. It gives **no inclusion criteria** and no literature search; HiSTaR is included because the project started from it.
* **Missing widely used or benchmarked methods:**

  | Method | Why it is expected |
  |---|---|
  | **SpatialPCA** | Its repository was screened in the leakage audit (Table S16) but the method was never run. |
  | **conST** | Also audited but not run. |
  | stLearn | Widely used. |
  | **CellCharter** and **MENDER** | Scalable, single-cell-resolution niche methods. These are the natural competitors on MERFISH. |
  | Giotto HMRF / smfishHmrf | Widely used statistical method. |
  | DR-SC, SC-MEB, PRECAST | Statistical, Visium. |
  | ADEPT, SiGra, spaVAE, stGCL, SpaGFT | Recent deep or graph methods. Hu et al. found ADEPT among the top performers. |
  | GraphST variants | The official alternative clustering options, and GraphST with a GPU. |
  | Non-spatial Leiden/Louvain on PCA | Standard reference. |
  | Multi-slice methods (STAligner, PRECAST, BASS multi-sample) | Run per section here, which deviates from BASS's own analyses. |

  SpatialGlue is a multi-omics integration method and is reasonably out of scope; say so explicitly.
* **Fix:**
  1. State the inclusion criteria: peer-reviewed, open code, installable, Python or R, outputs per-spot labels, published before a cut-off date.
  2. Report a PRISMA-style table of identified, eligible, run and failed methods, with failure reasons.
  3. Add at least SpatialPCA, stLearn, CellCharter, MENDER, conST, DR-SC/PRECAST, Giotto HMRF and a Leiden reference. Reaching about 20 published methods would match Yuan et al. and Hu et al.

### G5. Parameter settings and tuning fairness — **B** (because of the clustering asymmetry)
* **What the paper does:** It uses "default or published settings; none tuned". Arm B (equal tuning budget) is defined in `PROTOCOL.md` but was never run, and the paper says it is "future work".
* **Gap 1 (critical): asymmetric clustering in the headline comparison.**
  * Under the "standard" protocol, the training-free baselines are clustered with the **20-start best-likelihood GMM**, while competitors use their own (often single-fit) clustering. See the Fig. 2a caption and Table S3: "Training-free baselines are clustered only with the 20-start mixture".
  * The headline claim, "linear diffusion higher than 14 of 16 methods", comes from this unequal comparison. The paper's own Fig. 3 shows that clustering alone moves ARI by about 0.05–0.2.
  * `PROTOCOL.md` §6 states that "the primary comparison of embeddings uses [matched 20-start clustering]", so the paper inverted its own protocol.
  * Under matched clustering (Table S6), HiSTaR, STAGATE, SEDR, AnisoST and BANKSY λ=0.8 are **unresolved**.
* **Gap 2:** HiSTaR's per-section loss-weight tuning (from its supplement) is not applied, but its non-reproduction is still reported. Similarly, SpaGCN and DeepST ran without histology, which disadvantages methods designed to use it.
* **Gap 3:** The baseline hyper-parameters were chosen on development data (DLPFC donor 1), which is evaluated in the headline numbers. The sensitivity analysis (Fig. S2) covers only linear diffusion and only DLPFC.
* **Fix:**
  1. Make the matched-clustering comparison (every embedding gets the same 20-start GMM, and the internal-clustering methods are reported separately) the **primary** analysis, as pre-specified.
  2. Run the baselines' "own" clustering as the same single-fit protocol the competitors get, so that the "standard" comparison is symmetric.
  3. Run Arm B, an equal tuning budget on the development sections, for at least the top 6 methods, or report a per-method sensitivity analysis.
  4. Run SpaGCN and DeepST with histology on DLPFC as a sensitivity analysis.

### G6. Metrics — M
* **What the paper does:** ARI is the primary metric. NMI is reported and a panel of further metrics is in Table S12: macro-F1, missed domains, small-domain recall, CHAOS, PAS, boundary F1 and label-free scores.
* **Gaps:**
  1. `PROTOCOL.md` §7 names ARI, macro-F1, boundary F1 and runtime as primary and promises an equal-weight overall score with a random-weight sensitivity check. Neither appears.
  2. Table S12 comes from a *different* pipeline (shared preprocessing) and gives different numbers. For example, linear diffusion has mean ARI 0.600 there against 0.587 (the mean of 0.558, 0.705 and 0.497) in Table S3, and the method order changes (STAGATE, GraphST). The paper does not say which pipeline is authoritative.
  3. The Table S12 caption says "CCST, DeepST and BayesSpace are still running and are not yet included", yet they appear in the table. The caption is stale.
  4. No marker or biological-coherence metric is used (Yuan et al. use marker-gene detection).
* **Fix:**
  * Choose one pipeline for the headline.
  * Report a multi-metric summary heatmap (accuracy, spatial continuity, per-domain, stability, cost) with the pre-registered weights and a weight-sensitivity analysis.
  * Add a label-independent biological metric, such as domain-marker enrichment or spatial coherence.

### G7. Robustness and seeds — M
* **What the paper does:** It runs 3 seeds for most methods. The lottery and mclust experiments are run thoroughly.
* **Gap 1:** STAGATE, CCST, Spatial-MGCN and BASS have **1 seed** in the paper pipeline, and BayesSpace has 1 run.
* **Gap 2:** The main text says GraphST was run with one seed on DLPFC. Table S8 says 1/3/3, but `coverage_matrix.md` and Table S18 say "20/20 / 3". The coverage matrix contradicts the text.
* **Gap 3:** The STAGATE seed counts differ between the paper pipeline (1) and the runner (3). The DeepST counts are reversed (3 against 1).
* **Gap 4:** The lottery and mclust experiments use one embedding per section and method, so training variance and clustering variance are not separated.
* **Fix:**
  * Use ≥3 seeds for every stochastic method (≥5 is better).
  * Decompose the variance into training seed × clustering start with a mixed model, as `PROTOCOL.md` §8 promises.
  * Regenerate the coverage table from the actual run logs.

### G8. Statistics — M
* **What the paper does:** It runs a hierarchical bootstrap over **5 clusters** with percentile intervals, an equivalence margin of 0.03, and an analysis excluding the development sections.
* **Gaps:**
  1. Percentile bootstrap intervals are unreliable with only 5 top-level units, and 2 of the 5 are single-experiment datasets.
  2. With 16 comparisons there is no multiplicity correction. `PROTOCOL.md` §8 specified Holm-corrected Wilcoxon tests.
  3. The protocol is labelled "DRAFT … to be frozen" and was never frozen. The paper should not imply pre-registration (it says "a margin fixed before the analysis").
* **Fix:**
  * Increase the number of independent datasets (G3).
  * Add a mixed-effects model with dataset and donor random effects, or a Bayesian hierarchical model, as a sensitivity check.
  * Apply Holm correction within each family.
  * Either freeze and archive the protocol with a hash before the new datasets are run, or describe the current analysis as not pre-registered.

### G9. Scalability and computational cost — M
* **What the paper does:** It measures time and peak memory on **one CPU thread** of a 4-core Xeon with 15 GB of memory (Table S13). Datasets are at most about 6k cells.
* **Gaps:**
  1. There is no scaling curve.
  2. There is no GPU run. Most deep methods are designed for GPUs, so single-thread CPU timings exaggerate their cost by 1–2 orders of magnitude.
  3. There are no large datasets (10⁵–10⁶ cells).
  4. The text gives no failure, timeout or out-of-memory reporting, and the 15 GB memory limit may have constrained BayesSpace and DeepST.
* **Fix:**
  1. Run a scalability experiment that subsamples or tiles a large Xenium, Stereo-seq or MERFISH whole-brain dataset at 5k, 10k, 50k, 100k, 500k and 1M cells.
  2. Measure time and memory on CPU (multi-thread) and on GPU, with a fixed timeout, and report failures.
  3. This is where training-free baselines, MENDER and CellCharter would show their real advantage.

### G10. Usability, documentation and installability — M
* **What the paper does:** Nothing is scored.
* **Gap:** The project already documents substantial usability problems:
  * CCST was re-implemented because of PyTorch 1.7 pins.
  * BayesSpace had to be pinned to an old release.
  * torch_sparse needed a stub.
  * SEDR hard-codes R_HOME.
  * SpaceFlow needed a networkx shim and broke under pandas 3.
  * HiSTaR applies masking at inference.

  Weber et al., Yuan et al. and similar benchmarks (e.g. Saelens et al. 2019) score user-friendliness. This information is valuable and currently hidden in Table S2.
* **Fix:** Add a usability table scored with a fixed rubric for every method:
  * installation (pip/conda/Bioconductor, dependency pins, GPU requirement);
  * documentation and tutorials;
  * test coverage and CI;
  * maintenance (last commit, issue response);
  * licence;
  * input/output standards (AnnData, SpatialExperiment);
  * whether the tutorial runs unmodified.

### G11. Reproducibility, extensibility and resources — **B** for NAR
* **What the paper does:**
  * Scripts and configs exist, and numbers are generated by script (`check_paper_numbers.py`), which is good.
  * But `requirements.txt` holds 10 unpinned Python packages and no R or method environments.
  * There is **no container or lock file**, and no workflow manager (only ad-hoc `run_fill_*.sh` and `bench_queue.py`).
  * GitHub and Zenodo are `\todo`.
  * There is no results browser.
  * Method commits are recorded, but HiSTaR's is "TO RECORD".
  * Dataset licences are "to_check".
* **Gap:** The paper fails Sonrel et al.'s extensibility criteria and Mangul's archiving and containers criteria. NAR benchmark papers are expected to release a reusable resource.
* **Fix:**
  1. Provide one container per method (Docker or Apptainer) with pinned environments.
  2. Use a workflow (Snakemake, Nextflow or Omnibenchmark) with a documented "add a method / add a dataset" interface and a CI test on a toy dataset.
  3. Archive the per-spot predictions, embeddings and all run logs on Zenodo with a DOI.
  4. Release an interactive results website (per-section ARI, maps, lottery distributions), ideally submitted to an open benchmarking platform.
  5. Record every commit and licence.

### G12. Interpretation and claims — M
* **What the paper does:** Some of the language is appropriately cautious ("exploratory"), but several statements overreach.

| Claim | Support | Verdict |
|---|---|---|
| "a training-free diffusion baseline had a higher mean ARI than 14 of 16 methods" (abstract) | Table S5 under the asymmetric protocol. The 16 include the authors' own PCA and AnisoST, so the count for published method entries is 12 of 14 (BANKSY counted twice). | **Not adequately supported.** Restate it under matched clustering (Table S6), where 8 of 13 comparisons favour the baseline and 5 are unresolved, and separate the published methods from the authors' own baselines. |
| "matched or outperformed every deep encoder we tested" (Discussion) | No equivalence was shown for any method, and HiSTaR, STAGATE and SEDR are unresolved under matched clustering. | **Overclaim.** Say instead that no deep encoder was significantly better. |
| Clustering lottery: about 0.2 ARI range on fixed embeddings | Tables S9/S10, Fig. 3, 20 sections × 14 methods | Supported. This is the core contribution; it would gain from simulation and more datasets. |
| mclust is sensitive to spot order | Table S10 | Supported. Add the mclust version and a minimal reproducible example. |
| Best-likelihood selection is "not a remedy" | Table S11, ρ by dataset | Supported, but it rests mainly on one MERFISH dataset. Temper the claim to "not consistently". |
| HiSTaR does not reproduce (0.51 vs 0.65) | Table S14 | **Incomplete.** The reported value is unverified (`\todo`), per-section tuning was not applied, and the authors have not been contacted. |
| Spatial-MGCN selects its epoch with labels (+0.147 ARI) | Table S15, code audit | Supported technically, but the authors have **not been contacted** (`\todo`). Contact them before submission as a matter of fairness. |
| Edge preservation helps at Visium boundaries | One test with uncorrected p = 0.034 on 12 sections | Weak; this is method development. Move it to the Supplement. |

### G13. Task design (K given, single section) — m
* **What the paper does:** The true K is given to every method, and each section is analysed separately.
* **Gap:** Real users rarely know K. The authors' protocol defines T2 (K unknown) and T3 (multi-section) but runs neither. BASS was run per section, unlike its published multi-sample use.
* **Fix:** Add T2, using each method's own K-selection or a stability criterion, at least on the existing datasets. Run BASS multi-sample as a sensitivity analysis, or state the limitation clearly.

### G14. Manuscript readiness — **B** (administrative)
* The template and `\journaltitle` say *Bioinformatics Advances*, not NAR.
* Several `\todo`s remain: authors, URLs, HiSTaR values, author contact.
* Three bib entries are marked `VERIFY`, and the method citations in `configs/methods.yaml` are flagged as unverified.
* These must all be resolved before submission.

---

## Prioritised action list

1. **(B) Fix the headline comparison.** Make matched 20-start clustering primary, as the protocol requires. Make the "own clustering" arm symmetric. Separate the published methods from the authors' baselines, and rewrite the abstract and Discussion claims to match.
2. **(B) Broaden the data.** Add ≥4–6 annotated datasets beyond brain and beyond ≤6k cells (non-brain Visium, Stereo-seq or Slide-seq, Xenium or MERSCOPE) and a **simulation arm**. Resolve label provenance, including the STARmap labels of `unknown` provenance and the BASS-sourced annotations.
3. **(B) Address neutrality.** Write a neutrality and competing-interest statement (HiCAST, AnisoST). Demote the AnisoST section. Invite developer review and report the HiSTaR and Spatial-MGCN author responses.
4. **(B) Build a reusable resource.** Provide containers, a workflow, Zenodo archives of predictions and an interactive results browser (Sonrel and Mangul criteria; NAR expectation).
5. **(M) Add missing methods** with explicit inclusion criteria: SpatialPCA, stLearn, CellCharter, MENDER, conST, DR-SC/PRECAST, Giotto HMRF and a Leiden reference.
6. **(M) Scalability:** run a scaling curve up to 10⁵–10⁶ cells on multi-thread CPU and on GPU, with failures reported.
7. **(M) Usability rubric** table.
8. **(M) Statistics and seeds:** use ≥3 seeds for every method, a mixed model alongside the 5-cluster bootstrap, Holm correction, and a frozen protocol (or drop the pre-registration language). Reconcile Table S12 with Table S3, and Table S18 with the main text.
9. **(M) Arm B tuning** (equal budget on the development sections), or a sensitivity analysis for the top methods. Run histology-enabled SpaGCN and DeepST.
10. **(m) K-unknown task**, a scope statement, and NAR formatting.
