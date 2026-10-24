# NAR review, round 3, report 02: benchmark design

**Reviewer focus:** benchmarking methodology, judged against Weber et al. 2019, Mangul et al. 2019 and Sonrel et al. 2023.

**Files read:**
- my round-2 report (`docs/nar_review/round2/02_benchmark_design.md`)
- `paper/main.tex`, `results/paper_macros.tex`
- `paper/supplementary.tex` and every table in `results/supp/`
- `results/stats_cluster_aware.json` and `results/stats_cluster_aware_runner.json`
- `scripts/stats_cluster_aware.py`
- `configs/datasets.yaml`, `results/coverage_matrix.md`, `docs/PROTOCOL.md` (header and §2)
- `docs/figures/nar_fig1_pipeline_v2.png` and `nar_fig2_accuracy.png`

I also ran read-only checks with pandas on `results/benchmark_runs.jsonl` and `results/mclust_seed_summary.csv`.

## Recommendation: minor revision

This is a substantial and honest revision. The points that blocked acceptance in round 2 are now resolved, or are explicitly stated as limits:
- **Ranking over all methods.** The ranking now covers all 16 methods on the 23 sections that every method completed. BASS is ranked first (P = 0.49 against 0.29), and that appears in the abstract.
- **Single-environment check.** A sensitivity analysis that takes every dataset from one execution environment (the standardised runner) has been added. It gives the same picture.
- **Tissue dependence.** The abstract and Discussion now say the baseline's lead comes from brain tissue. The PCA > smoothing result on the new tissues is reported.
- **Missing results and limits.** The memory cap and the missing results are handled by a stated complete-case rule. Annotation provenance, missing technologies and the lack of simulation are listed as limitations.

The remaining items need **no new computation**:
- a sensitivity analysis restricted by label provenance;
- disclosure of HiCAST;
- the scope in the abstract;
- the code/archive deliverables;
- several internal inconsistencies.

**Scope.** In its current form this is a focused benchmark of the clustering step on 24 sections. It is not a comprehensive resource, and the abstract should say so. With the items below fixed, I consider it acceptable within that scope.

---

## Major points from round 2

### M1. Pooled estimand and heterogeneity: mostly resolved

- **Ranking (resolved).** The ranking now covers all 16 methods on the 23 shared sections (`ranking_methods = 16`, `ranking_sections = 23` in both JSON files):
  - BASS P(rank 1) = 0.49 and linear diffusion 0.29 (Table S8); six methods have rank 1 inside their 95 % interval.
  - The 11-method complete ranking (P = 0.74) is now clearly secondary.
  - The abstract says "BASS and it were most likely to rank first".
- **Tissue dependence (resolved).**
  - The abstract and Discussion say the lead came from brain tissue.
  - Results give the counts of comparators ahead of the baseline per dataset (0/16 DLPFC, 1/15 STARmap, 1/15 MERFISH, 13/16 breast cancer, 12/15 Stereo-seq) and the brain vs non-brain mean Δ (+0.172 vs −0.027).
  - The text states that PCA beats smoothing on both new tissues (0.562 vs 0.545; 0.349 vs 0.306).
  - The domain-size explanation is now marked "which we did not test".
  - Per-dataset Δ columns are in Tables S5–S7. Linear diffusion is still labelled as a post-hoc, exploratory reference.
- **Still pooled (partly).**
  - The primary inferential statement is still the pooled 8/16 over 7 groups, 5 of which are brain. The per-dataset results are descriptive only (no intervals).
  - No method × tissue model was fitted.
  - "Slightly ahead" is defensible on average (−0.027). However, single comparisons on the new tissues reach −0.08/−0.09 (BASS, NichePCA, GraphST, SpaGCN, DeepST; Table S6).
  - **Request (text only):** in the abstract, state the brain/non-brain split before the pooled count, or give the pooled count with "(5 of 7 groups brain)".
- **Discussion wording.** "BASS was as likely to rank first" understates BASS in the primary analysis (0.49 vs 0.29). It is only true in the runner analysis (0.43 vs 0.44). Reword.

### M2. Mixed execution environments: resolved as a sensitivity analysis

- **Done.**
  - The main text states which datasets come from which environment.
  - Table S7 (`STATS_SOURCE=runner`) repeats the primary analysis with one environment and gives the same picture: 9 comparisons favour the baseline and 7 are unresolved, against 8 and 8.
  - DeepST now has 3 seeds on breast cancer and E9.5. Seeds 1–2 on E10.5_E2S1 hit the cap; this is stated, and `benchmark_runs.jsonl` confirms 12.0 GB kills.
- **Remaining issues.**
  - I would have preferred the runner as the primary analysis. The pipeline numbers (each method's own preprocessing) are defensible, and the agreement table (Table S15) is now explicit, so I accept the authors' choice.
  - "Gave the same picture" hides one change: **HiSTaR moves from unresolved to "baseline higher"** in the runner analysis. Name it in the text.
  - **DeepST seeds in the runner are misreported.** On the 20 brain sections the runner has only **1 seed** per section for DeepST (Table S13: 27 runs). Table S22 and `coverage_matrix.md` give "23/24 / 3". Correct the coverage entry, and note it in the S7 caption.

### M3. Failure and out-of-memory handling: resolved within the stated limits

- **Memory-cap kills are deterministic.** All E10.5_E1S1 kills peak at 12.00–12.25 GB, consistently across all three seeds of each method (`benchmark_runs.jsonl`), so they are not caused by machine load. The Supplementary Note states that each new-dataset job ran alone.
- **The uneven cap is disclosed.** The Methods now say the first three datasets ran without a cap, and give BayesSpace's 12.5 GB.
- **Missing data handled.** The complete-case (23-section) rule addresses round-2 request 4. BayesSpace is handled as a separate stratum ("Visium only", not ranked).
- **Reruns on 64 GB (declined).** The authors could not run on 64 GB. The paper now says the failures are "a statement about resource use, not about accuracy", that more memory or a GPU may let these methods run, and why NichePCA failed. **This is adequate.**
- **Minor gaps.**
  - The retry policy for the earlier DLPFC runs that were killed under machine load is still undocumented. The history shows 6 BASS and 1 NichePCA error records on DLPFC, superseded by retries. One sentence in Supplementary Note 6 is enough.
  - GraphST's failure (a dense N×N graph) is not explained, whereas NichePCA's is.

### M4. Annotation provenance: partly resolved

- **Done.**
  - The Limitations now disclose the provenance problems:
    - The MOSTA labels were partly derived by clustering and then curated.
    - The STARmap and MERFISH labels come from the BASS analyses, and BASS is among the top methods on them.
    - The breast cancer labels come from SEDR.
    - None of these was verified independently.
  - The coarse 4-class breast cancer analysis was added (Table S17). It shows that the ordering is unstable: ARI 0.04–0.31, and linear diffusion ranks 11/14.
- **Not done.**
  - `configs/datasets.yaml` still classes Stereo-seq as `algorithm` and STARmap as `unknown`, with every `verified: false`.
  - `docs/PROTOCOL.md` §2 still says such datasets are "excluded from the primary ranking", yet both are in the primary bootstrap.
  - The requested sensitivity analysis restricted to `expert`/`reference_atlas` labels (DLPFC, MERFISH, breast cancer) was not run. It needs no new runs; the per-section values already exist.
- **Required (cheap).**
  1. Report Table S6 and the ranks without Stereo-seq and STARmap, as a sensitivity analysis.
  2. Bring `PROTOCOL.md` into line with the paper: either amend the rule, with the amendment dated, or mark the protocol as superseded.

### M5. Data breadth: declined (no data, 15 GB machine); limits stated, but not in the abstract (partly adequate)

- **Stated in the Limitations:**
  - three of the five datasets are brain;
  - the non-brain data are one breast cancer section and one embryo study;
  - there are no Slide-seq, Xenium or Visium HD data, nothing above about 20k spots, and no simulation.
- **Missing:** the abstract and title still read as a general benchmark.
- **Required:** put the scope in the abstract, for example: "single sections with the number of domains given, up to 18k observations, one non-brain section per technology".
- **Judgement:** with that change I no longer treat M5 as blocking. The paper then claims what it can support, and the clustering-variance findings do not depend on breadth. The tissue-dependence conclusion rests on n = 1 group per non-brain tissue and should be worded as provisional. The current text ("most methods … were slightly ahead") is acceptable; it does not generalise.

### M6. Method selection and reusable resource: not resolved

- **Method selection.**
  - The inclusion criterion is still one sentence, with no flow table.
  - SpatialPCA and conST were screened in the audit, but no reason is given for not benchmarking them.
  - The "runs on CPU" restriction is not discussed as a source of bias.
- **Reproducibility.**
  - There are still no containers or lock files; `requirements.txt` has 10 lines, and there is no workflow manager.
  - `\todo{GitHub URL and Zenodo DOI}` remains.
  - The `stats_cluster_aware.py` docstring still says the margin was "fixed before looking", while the paper calls the analysis exploratory.
- **Status.** None of these needs computation. A versioned archive with environment files (pip freeze or conda export, the R `sessionInfo`) and per-run results is a condition of NAR acceptance.

### M7. Statistics design: mostly resolved

- **Multiplicity: resolved.** Bonferroni intervals were added (Tables S6/S7), with the result stated: 2 of 16 comparisons survive. **However,** Supplementary Note 4 still says "No correction for multiple comparisons is applied" (new inconsistency N1).
- **Development sections: resolved.** The definitions are now consistent: frozen on the four sections of donor 1; excluded set = those four sections plus the first STARmap and MERFISH sections.
- **Equivalence margin: partly resolved.**
  - It is still justified as "about the seed-to-seed SD", although the baselines' own SDs range from 0.012 to 0.054.
  - The design cannot establish equivalence (interval half-widths about 0.05–0.13).
  - Either drop "no comparator was equivalent" or add one sentence saying the study had no power to show equivalence.
- **Mixed model: not done.** It is acceptable to omit it, given the 7-group caveat now in the text.

### M8. Neutrality: partly resolved

- **Done.**
  - A neutrality paragraph has been added.
  - Results are reported without the development sections ("Test only" columns).
  - The boundary p-value for AnisoST is labelled uncorrected.
  - The HiSTaR and Spatial-MGCN sections are now hedged appropriately: "we report what the released code does", and "not to question the method itself".
- **Developer contact (declined, authors' decision).** Given the hedged wording, I accept this.
- **HiCAST: still undisclosed.**
  - The repository contains `hicast/` and `docs/HiCAST.md`, "the improved model implemented in this repository", described as a successor to HiSTaR.
  - The paper reports non-reproduction of HiSTaR, and its conflict-of-interest statement names only AnisoST.
  - A competing successor model under development is a relevant interest. Add it to the conflict-of-interest and neutrality statements.
- **Dataset choice.** The "home dataset" point (10x breast cancer and MOSTA are the showcase datasets of SEDR, GraphST, STAGATE and Spatial-MGCN) is still not mentioned. One sentence is enough.

---

## Minor points from round 2

| # | Point | Status | Evidence |
|---|---|---|---|
| 1 | Corrupted coverage table | **Resolved** | Table S22 shows "20/24". |
| 2 | Stale Table S13 caption | **Resolved** | "up to 72 = 24 × 3"; the shared preprocessing is explained. BASS leading S13 is now consistent with the main ranking. |
| 3 | Fig. 1 out of date | **Resolved** | Breast cancer and Stereo-seq are in panel A. The caption says "annotation", no longer "expert annotation". |
| 4 | Fig. 2 asterisks / P(best) | **Partly** | P(best) now includes BASS (fine). The asterisked 2-section Stereo-seq means for 5 methods still sit next to linear diffusion's 3-section mean; give the baseline's 2-section value in the caption. |
| 5 | Count over published methods only | **Not resolved** | "8 of 16" includes PCA and AnisoST (the authors' own ablations). Over the 14 published entries it is 7 baseline-higher and 7 unresolved; state this. |
| 6 | Degenerate BIC choice of K | **Resolved** | "BIC did not provide a usable label-free choice … 325 of 332". The text now concedes the lead depends on the true K. |
| 7 | Seed design | **Partly** | The 1-seed pipeline methods are stated in the Limitations. DeepST is fixed on the new data, but has 1 seed on the brain sections in the runner (see M2). |
| 8 | Incomplete R mclust experiment | **Resolved** | No lock files remain. The noise repetitions are skipped on E10.5_E1S1, and this is stated (3 of 10 embeddings there have them; harmless). |
| 9 | CPU-only timing | **Stated limitation** | Acceptable given the hardware. |
| 10 | Usability rubric | **Not resolved** | Optional for a focused paper. |
| 11 | Scope in abstract | **Not resolved** | See M5. |

## Round-1 G-points

| # | Status now | Comment |
|---|---|---|
| G1 Scope | Partly | In the Limitations, not the abstract (M5). |
| G2 Neutrality | Partly | HiCAST undisclosed (M8). |
| G3 Data / simulation | Declined, limits stated | Provenance sensitivity still owed (M4). |
| G4 Inclusion criteria | Open | Minor at this stage, but give the reason SpatialPCA and conST were not benchmarked. |
| G5 Clustering asymmetry | Resolved | Matched clustering is primary. |
| G6 Single pipeline / metrics | Resolved (sensitivity analysis) | Runner analysis is in Table S7; Tables S13 and S15 are explained. |
| G7 Seeds / coverage | Mostly resolved | DeepST coverage entry wrong. |
| G8 Statistics | Mostly resolved | Supplementary Note 4 contradicts the Bonferroni intervals; docstring. |
| G9 Scalability / failures | Resolved within limits | Retry policy still undocumented. |
| G10 Usability | Open (optional) | |
| G11 Containers / archive | Open, condition of acceptance | |
| G12 Overclaims | Largely resolved | Wording of "as likely to rank first" and "slightly". |
| G13 K unknown / multi-section | Partly | K sensitivity analysis is honest now; multi-section is out of scope, as stated. |
| G14 Manuscript readiness | Open | Authors, URLs, funding and CRediT are still `\todo`. |

---

## New problems

1. **Supplementary Note 4 contradicts the main text.** It says "No correction for multiple comparisons is applied", while the main text and Tables S6/S7 report Bonferroni intervals.
2. **Rank intervals are mistypeset.** They print as "1-$-$10" (rendered "1-−10") in Tables S7 and S8. A string-formatting bug in the supplement generator.
3. **The DeepST runner seed count is wrong** in Table S22 and `coverage_matrix.md` ("23/24 / 3"). In fact there is 1 seed on the 20 brain sections, 3 on breast cancer and E9.5, and 1 on E10.5_E2S1 (27 runs).
4. **"Same picture" hides one verdict change.** HiSTaR changes verdict between the primary and the runner analyses; the text calls the two analyses the same picture.
5. **"BASS was as likely to rank first"** (Discussion) is true only in the runner analysis. In the primary analysis BASS is more likely (0.49 vs 0.29).
6. **The repository contradicts the paper.** `PROTOCOL.md` ("DRAFT", label-exclusion rule) and the `stats_cluster_aware.py` docstring ("margin fixed before looking"; "methods with all 20 sections") disagree with what the paper does. They will be public with the code.
7. **The Table S22 column "R mclust perturbation" (20/24) is ambiguous.** It is the older permutation/noise experiment on the first three datasets; the main-text noise experiment covers 23/24. Rename the column, or add the second experiment.

## Actions required for acceptance (no new computation)

1. Run the provenance-restricted sensitivity analysis (drop Stereo-seq and STARmap), and reconcile `PROTOCOL.md` with the paper (M4).
2. Put the scope in the abstract, and lead with the brain/non-brain split (M1, M5).
3. Disclose HiCAST in the conflict-of-interest and neutrality statements (M8).
4. Deliver a code archive with environment and lock files and a Zenodo DOI; remove the remaining `\todo` placeholders (M6, G11, G14).
5. Fix new problems 1–7, and state the published-only count (minor point 5) and the retry policy (M3).
