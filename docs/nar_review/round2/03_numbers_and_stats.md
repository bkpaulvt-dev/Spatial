# 03 (round 2): Numbers and statistics audit of paper/main.tex and paper/supplementary.tex

**Reviewer role:** statistical reviewer.

**How the checks were done**
- Macros were resolved against `results/paper_macros.tex`, generated 2026-10-23 13:59. `stats_cluster_aware.json` is from 13:58 and `benchmark_runs.jsonl` from 13:27, so the macros are current with the data.
- The analyses were re-implemented read-only from the raw files: `benchmark_runs.jsonl` (deduplicated by id), `baselines_3start.jsonl`, the pipeline jsonl files, `clustering_lottery.jsonl`, `k_sensitivity.jsonl` and `mclust_seed_g*.csv`. The scratch bootstrap is in the session scratchpad (`boot.py`), not in the repo. No output-writing script was run.
- `scripts/check_paper_numbers.py` passes: 8/8 hand-typed claims and 105/105 macros defined. It checks only 8 hand-typed strings, and several unchecked hand-typed numbers are wrong (see A1, A5, A6, A7).

**Bottom line**
- Every macro value in main.tex reproduces from the result files. This includes:
  - all 32 bootstrap Δ/CI values (within Monte-Carlo error of ±0.005);
  - the verdict counts and method lists;
  - nAhead\*, dBrain/dOther, lottery, ρ, K-sensitivity, mclust-seed and gain values.
- The breast cancer and Stereo-seq mapping (runner `metrics` → own clustering, `metrics_matched` → matched clustering) is correct for every method **except AnisoST**. The runner's AnisoST "own" clustering is the 20-start GMM, but it is filed as the 3-start `anisost_single_gmm` (A2).
- Several hand-typed statements and supplement captions are stale or wrong.
- The headline ranking result depends on excluding BASS (S-A).

---

## A. Discrepancies (claimed → correct, with how verified)

| # | Location | Claim | Correct value / problem | Verification |
|---|---|---|---|---|
| A1 | main.tex:155–156; supplementary.tex:17 (Supp Note 1) | Breast cancer and Stereo-seq were run "with three seeds for every method (two for CCST on the largest Stereo-seq section)" | **DeepST: 1 seed** on breast cancer and on both smaller Stereo-seq sections (seeds 1–2 were never attempted). **BayesSpace: 1 seed** on breast cancer. S8 (`seeds.tex`) itself shows DeepST "3/3/3/1/1" and BayesSpace "…/1/0". | `benchmark_runs.jsonl`, last record per id, status ok, grouped by method/section |
| A2 | `stats_cluster_aware.py:32,38–39`; `paper_v2.py:49`; `make_supplement.py:48` (OWN_KEY `anisost→anisost_single_gmm`) | For breast cancer and Stereo-seq, AnisoST's "default" clustering is described as the 3-start GMM. S3 caption: "training-free baselines, HiSTaR and BANKSY use a 3-start Gaussian mixture as default". | In the runner, `adapters._train_free` returns `robust_gmm(Z,k)` (20 starts) as the labels. `metrics.ARI` ≡ `metrics_matched.ARI` for all 12 AnisoST runs (verified identical). So the "default" AnisoST value on the four new sections is the 20-start fit, while LD and PCA defaults come from the 3-start `baselines_3start.jsonl`. This affects: S3 AnisoST Breast/Stereo default = matched (0.544/0.544, 0.346/0.346); `stdDAniso` (+0.038; per-dataset brca +0.002 and stereo −0.040 compare 3-start LD with 20-start AnisoST); gainAniso (+0.017, 14/24, p=0.020, which includes 4 zero-difference sections); S8 AnisoST Breast/Stereo SDs; S11 AnisoST row. | Runner records compared directly; `scripts/adapters.py:23-30` |
| A3 | `make_supplement.py:183–195` → S14 (`agree.tex`); main.tex:190–191 | S14 compares "each method's default clustering in its published pipeline and in the standardised runner" | For LD, PCA and AnisoST the pipeline column is now the 3-start fit (`*_single_gmm`), but the runner's default for these three is the 20-start fit. The listed differences are protocol differences, not pipeline differences: LD +0.026/+0.025/+0.016, AnisoST +0.028/+0.057/−0.013, PCA +0.029/+0.025/−0.021. Like-for-like (20-start in both), LD is +0.011/+0.028/0.000, as in round 1. | `agree.tex` against `ari.tex` and runner records |
| A4 | supplementary.tex:91 (S12 caption) | "mean over the five datasets … Runs: 60 per method (20 sections, 3 seeds), except DeepST (20, seed 0) and BayesSpace (12 Visium sections, seed 0)" | Stale. The `metrics.tex` Runs column shows 72 for most methods (24×3); 69 for BASS, GraphST, NichePCA and Spatial-MGCN; 71 for CCST; 23 for DeepST; 13 for BayesSpace. The caption also does not say that the five memory-capped methods average 2 rather than 3 Stereo-seq sections. "Values differ slightly from S3 because the preprocessing is shared" is also false for breast cancer and Stereo-seq, where the two tables come from the same runs. | `results/supp/metrics.tex` |
| A5 | main.tex:228–229 | Seed SD "0.003–0.04 for the training-free baselines (Supplementary Table S8)" | S8 (default clustering) gives LD 0.012–0.054, AnisoST 0.015–0.045 and PCA 0.015–0.027, so the range is **0.012–0.054**. The value 0.003 is the 20-start (matched) LD SD on STARmap. Even with matched clustering the range is 0.003–0.045. The comparison with HiSTaR (0.047/0.18, default clustering) should use the same protocol. | `paper_numbers_v2.json` `seed_sd`; `seeds.tex` |
| A6 | main.tex:229–230 | "median time per section … to about 40 min for CCST" | `timeMedCcst` is 2789 s = **46.5 min** (S13). 40 min is roughly the old pilot value (`timePilotCcst` 2490 s = 41.5 min). Also, S13 reports the median per *job*, pooled over all seeds and datasets, not per section. "More than 5 h" on E10.5_E1S1 is correct (max 19,578 s = 5.4 h). | runner `resources.wall_s` |
| A7 | main.tex:157 | "Every job had a memory cap of 12 GB; runs that exceeded it are reported as failures." | BayesSpace peaked at **12.5 GB** (DLPFC 151509) and is recorded as ok (`memMaxBayesspace` 12.5 in S13). Supp Note 6 says the cap applied only to the breast cancer and Stereo-seq runs. Main text and S13 contradict each other. | runner `peak_rss_gb` |
| A8 | main.tex:154, 375–376 | "one for STAGATE, CCST, Spatial-MGCN and BASS in the published pipelines"; "Four methods were run with one seed" | **GraphST on DLPFC also has 1 seed** in the pipeline. GraphST MERFISH has 12 of 15 runs (incomplete seeds). So five methods have one seed on at least one dataset. S20 (`coverage.tex`) still reports GraphST as "20/24 / 3". This is round-1 I-10, unresolved. | `graphst.jsonl` (DLPFC 12 runs, 1 seed; MERFISH 12 runs) |
| A9 | main.tex:351–352 (Discussion) | "on the embryo sections every method reached a much lower ARI than on brain tissue" | False against MERFISH, which is brain. Matched Stereo vs MERFISH means: SpaGCN 0.388 vs 0.151, PCA 0.349 vs 0.130, DeepST 0.365 vs 0.163, Spatial-MGCN 0.280 vs 0.133, CCST 0.271 vs 0.157, HiSTaR 0.307 vs 0.264, BANKSY λ=0.2 0.341 vs 0.222, GraphST 0.315 vs 0.254, SpaceFlow 0.323 vs 0.260, SEDR 0.241 vs 0.167. In total 10 of 16 methods were higher on Stereo-seq than on MERFISH. The claim holds only against DLPFC (and STARmap). | `stats_cluster_aware.json` `means_robust` |
| A10 | main.tex:295 (section title) | "Selecting fits by likelihood helps on cortex but not on single-cell data" | STARmap is single-cell, and it is where selection helped (best-LL − mean +0.026; ρ̃ = 0.41). Selection also did not help on breast cancer (−0.002) and Stereo-seq (−0.010), which are spot/bin data. The data support "helps on cortex (DLPFC, STARmap) but not on MERFISH, breast cancer or Stereo-seq". The abstract's "helped only on cortex" is consistent with this. | `clustering_lottery.jsonl`, mean (best-LL − mean single) per dataset |
| A11 | main.tex:222–223 | "Misspecifying K by one changed ARI by \kOneMean{} (0.09) on average (up to 0.49)" | The macro is the mean over embeddings of the *larger* of \|ΔK−1\| and \|ΔK+1\|. The mean absolute change is 0.067 for K−1 and 0.057 for K+1 (0.062 pooled). The maximum, 0.49, is an *increase* (CCST, DLPFC: 0.14 → 0.63 at K+1), i.e. a degenerate fit at the true K. Reword ("the larger of the two changes averaged 0.09") or report 0.06. | `k_sensitivity.jsonl` recomputed |
| A12 | main.tex:224–225 | "\kTopBic (BANKSY λ=0.8, 0.487) moved ahead of linear diffusion (0.462, rank 3)" | Rank 3 means two methods moved ahead. **NichePCA (0.472)** is also ahead but not named. These are section-pooled means (DLPFC is 51 % of the 331 embeddings), and memory-capped methods are averaged over different section sets. | `k_sensitivity.jsonl` |
| A13 | supplementary.tex:121 (S18 caption) | "the 14 repositories are the benchmarked methods with released code plus SPARK, SpatialPCA and conST" | The table lists 11 benchmarked repositories + 3. **HiSTaR and NichePCA**, both with released code (main.tex:134 uses HiSTaR's "official code"), were not screened. Main text:334 "released repositories of 14 methods" is numerically right but includes 3 non-benchmarked methods. | `results/supp/audit.tex` |
| A14 | main.tex:154–155 vs 160 vs 188 | "settings were frozen on four development sections" (l.160) and "fixed on DLPFC donor 1" (l.152), but "without the development sections (DLPFC donor 1 and the first section of STARmap and MERFISH)" (l.188) | `configs/datasets.yaml` marks 6 sections as `split: dev`. Use one definition: 4 tuning sections, 6 excluded in the test-only analysis. | datasets.yaml |
| A15 | main.tex:296–297 | "best-likelihood fit beat the average single start for \lotBLUp (10) of 14 methods and was worse for 3" | Correct under the ±0.005 threshold, but one method (BANKSY λ=0.8, +0.0048) is "neutral" and unmentioned. SpaceFlow (+0.0054) is counted as "beat", although S9 prints both as +0.005. Minor: mention the neutral method or the threshold. | lottery recomputed |
| A16 | Fig 2 caption (main.tex:240–248) | Panel A rows "ordered by the mean over datasets"; panel C "probability of ranking first" | Panel A orders by the dataset-equal mean, using 2-section Stereo means for memory-capped methods. BASS (0.552) sorts above LD (0.522), while panel C gives LD P(best) = 0.73 with BASS excluded (see S-A). This is round-1 I-7, still present. | `make_figures_nar.py:97–98`, `means_robust` |

All other numerical claims in main.tex were reproduced, including:
- abstract counts 8/16 and 8;
- `listRobBetter` / `listRobUnres` / `listStdUnres`;
- BASS and BANKSY Δ/CI;
- `nRobBetterTest` 6; `pBestLin` 0.73; `pBestSecond` BANKSY λ=0.8 0.11; rank interval 1–5 of 11;
- `nAhead` 0/1/1/13/16/12/15; BASS "in both cases"; `overallBass` 0.594 vs `overallLin` 0.587 (three brain datasets, equal weight);
- `dBrain` 0.172 / `dOther` −0.025;
- best per dataset (LD 0.558, BANKSY 0.740, BASS 0.582, BASS 0.624, SpaGCN 0.388);
- lottery 331 / 14 / 0.17 / 0.60 (SEDR 151672) / 0.18 / 0.09 SpaceFlow / 0.22 BANKSY / 0.07;
- ρ medians 0.38 / 0.41 / −0.11 (10 of 14) / −0.13 / 0.00;
- gain counts 8 / 5 / 1 of 14 and the four quoted gains with p-values;
- mclust seed values: 280 embeddings >2000, 0.11, 0.46, 49 %, 0.08, 0.59, 14 %;
- K-sensitivity 324/331, ρ = 0.93;
- MGCN leak values; HiSTaR 0.509 / 0.491 / 0.454–0.525 / 0.449 / 0.487;
- data counts (3798; 5913/12, 8494/18, 18,408/13; 1049–1088 cells and 166 genes; 5488–5926 cells and 155 genes);
- 24 sections, 7 groups, 5 memory-capped methods (BASS, DeepST, GraphST, NichePCA, Spatial-MGCN), CCST >5 h.

## B. Mapping of the two new datasets (task item)

**Correct**
- `metrics.ARI` → own clustering and `metrics_matched.ARI` → `+robust` for all embedding methods.
- LD and PCA "own" taken from `baselines_3start.jsonl` (3-start, seeds 0–2, 4 new sections present).
- SpaGCN, BASS and BayesSpace keep their own clustering under both protocols.
- paper_v2.py, stats_cluster_aware.py and make_supplement.py use identical mappings, and the supplement tables S3, S5, S6, S7, S8 and S11 agree with the macros.

**Wrong:** AnisoST (A2), and S14's protocol mix (A3).

**Fragile**
1. The three scripts do not deduplicate `benchmark_runs.jsonl` by id. Today's 8 duplicate ids are error → ok pairs, so nothing is double-counted, but an ok → ok rerun would be weighted twice.
2. The LD/PCA 3-start runs use the seed-0 cached PCs (`prepare_new_datasets.py`, `preprocess(..., seed=0)`), while the runner recomputes PCs with `random_state=seed`. Within-dataset LD default vs matched therefore differ slightly in preprocessing for seeds 1–2. The effect is probably negligible but undocumented.
3. The per-dataset Stereo-seq Δ for the 5 memory-capped methods is on 2 sections. This is handled correctly as a paired difference.

## C. Partial `mclust_seed_g6.csv`

- `mclust_seed.R` writes all 16 rows of an embedding in one `write.table` after claiming a lock. The current file has 1 complete embedding (banksy_l0.2, E10.5_E1S1); AnisoST and BANKSY λ=0.8 are locked/in progress.
- The paper_v2.py handling is correct for the current snapshot:
  - 322 embeddings, each with exactly 10 seed, 1 full and 5 full_jit rows;
  - the 160 duplicate rows (g2 vs g5/g6) are byte-identical, so `drop_duplicates` is harmless even though `glob` order is unsorted.
- Macros reproduce: mcsN 322, NBig 280, SeedMeanBig 0.114, Max 0.455, Gt 48.6 %, JitMean 0.083, JitMax 0.591, FullOutside 14.3 %.
- **Provisional:** 9 of the 10 E10.5_E1S1 embeddings are still missing, so N will become 331/289, and `mcsSeedMeanStereo` currently rests on 2 of 3 sections.
- **Robustness gap:** there is no completeness filter. A torn read during a write would enter an embedding with fewer than 10 seeds (understated range), and a missing `full` (NaN) would be counted as "not outside" in `mcsFullOutside`, deflating the percentage. Suggest keeping only groups with 10/1/5 rows and sorting the glob. S20 already shows "23/24" for R mclust seeds; the main text should state the final N once the run finishes.

## D. Statistical concerns (new and carried over)

| ID | Concern | Evidence | Recommendation |
|---|---|---|---|
| S-A (new, high) | **The P(best) / rank claim depends on excluding BASS.** The ranking keeps only methods with all 24 sections, so the 5 memory-capped methods are dropped, including BASS, the comparator with the smallest Δ (−0.004). Re-running the same hierarchical bootstrap on the 23 sections common to all 16 non-BayesSpace methods gives **BASS P(best) = 0.51, LD 0.29**; LD's rank interval becomes 1–8. "LD ranked first in 73 %" (main.tex:207) is therefore an artefact of a memory failure on one section. | Scratch bootstrap, 5000 resamples, same scheme | Rank on the common 23 sections (or impute nothing and say so). At minimum, state next to 0.73 that BASS, the closest competitor, is not ranked. |
| S-B (high, carried S2) | Multiplicity. 16 + 16 interval verdicts are reported with no correction (acknowledged). | Bonferroni over 16 (two-sided 99.69 % percentile interval): only **SpaceFlow, CCST and Spatial-MGCN** stay above zero (PCA lower bound −0.001). A t-interval on the 7 cluster means (df = 6) keeps 4/16 (SpaceFlow, CCST, MGCN, PCA). BayesSpace (lower +0.002, only 4 groups) and SEDR (+0.005) are fragile. | Report the adjusted count ("3–4 of 16 after Bonferroni") alongside 8/16. Treat BayesSpace (4 groups) separately. |
| S-C (high, carried S1) | The bootstrap has 7 groups, three of them single-study datasets and one (breast cancer) a single section with zero within-group variance. Percentile intervals with 7 clusters under-cover. | — | Add the t-based or random-effects sensitivity analysis; keep per-dataset Δ as primary. |
| S-D (medium, carried S5/I-7) | **Mixed estimands.** The accuracy comparison is cluster-weighted (5/7 brain). Lottery, ρ, gain, K-sensitivity and MGCN leak are section-pooled (DLPFC 51–60 %). Fig 2A is dataset-weighted. | Dataset-equal Δ: BASS −0.035 (BASS ahead); BANKSY λ=0.8 +0.017; NichePCA +0.019. "Best-likelihood beat … 10 of 14" is driven by DLPFC: per dataset it holds for 10/10/4/6/4 methods on DLPFC/STARmap/MERFISH/breast/Stereo-seq. | State the weighting for each pooled number; give per-dataset counts for the likelihood-selection result. |
| S-E (medium, carried S12/I-5) | The gain and boundary Wilcoxon tests treat 23–24 (or 12) nested sections as independent, contrary to the paper's own unit-of-analysis argument. AnisoST gain p=0.020 includes 4 artefactual zero differences (A2). | — | Use the hierarchical bootstrap for these contrasts, or label them "section-level, descriptive". |
| S-F (medium, carried S7) | Seed imbalance. Pipeline methods with 1 seed (STAGATE, CCST, MGCN, BASS, GraphST-DLPFC) and runner methods with 1 seed (DeepST, BayesSpace) are compared with 3-seed means. Seed variance is not propagated into the bootstrap. | S8 | Run 3 seeds or add a seed level to the bootstrap; flag 1-seed cells in Fig 2. |
| S-G (low, carried S8) | Equivalence (±0.03) is unattainable with 90 % CI widths of 0.08–0.25. "No method was shown to be equivalent to it" (Discussion) is uninformative. | ci90 widths in JSON | Say the design had no power for equivalence, or drop the sentence. |
| S-H (low) | "The clustering step was a larger source of variation than most differences between methods" compares a range over 20 draws (an extreme, grows with the number of draws) with differences of means. It holds numerically (96 % of pairwise \|Δ\| among 17 methods < 0.165; median pairwise \|Δ\| 0.067 ≈ lotOracle 0.07). | `stats_cluster_aware.json` | Compare like with like, e.g. the SD across starts (S9 "Mean SD" 0.03–0.07) or best-minus-mean, with the pairwise Δ distribution. |
| S-I (low) | `nAhead` counts any negative per-dataset Δ, including −0.001 (HiSTaR, Stereo-seq) and −0.003 (MGCN). "Most methods were slightly ahead" (abstract) is descriptive only: breast cancer is 1 section, Stereo-seq 3 sections from one study. | per_dataset | Add "(differences mostly < 0.04, single study per dataset)". |
| S-J (low, carried S11) | One lottery ρ is NaN (constant ARI); `median` silently drops it. | — | Note n. |

## E. Status of round-1 points (docs/nar_review/03_numbers_and_stats.md)

| ID | Status |
|---|---|
| I-1 "matched or outperformed every deep encoder" | **Resolved**: now "higher than 8 of 16 … could not be separated from the rest" |
| I-2 "differences small" | **Resolved / reworded** |
| I-3 asymmetric standard protocol | **Resolved** for LD and PCA (`baselines_3start.jsonl`, used as the standard reference); matched is now primary. **New instance:** AnisoST on breast/Stereo (A2) and S14 (A3) |
| I-4 "AnisoST matched LD" | **Resolved**: "did not improve on linear diffusion overall" |
| I-5 "Edge preservation helps" | **Partly**: heading removed and "uncorrected" added, but still stated as a fact from a section-level Wilcoxon (S-E) |
| I-6 gain wording | **Resolved** (">0.005 upwards for 8 of 14 … all uncorrected") |
| I-7 mixed estimands | **Partly**: brain-only equal-weight comparison now disclosed; Fig 2A vs 2C conflict and section-pooled numbers remain (S-D, A16) |
| I-8 BASS also ahead on STARmap | **Resolved** ("BASS in both cases") |
| I-9 "14 plus 3" | **Resolved** |
| I-10 GraphST seeds in coverage | **Unresolved** (A8) |
| I-11 S12 "still running" | Sentence removed, but the **caption is stale** (A4) |
| I-12 six vs five patterns | **Resolved** |
| I-13 median (S9) vs mean (text) | **Unresolved**: text gives mean ranges (SpaceFlow 0.09, BANKSY 0.22), S9 gives medians (0.07, 0.19) |
| I-14 "exploratory" in abstract | **Unresolved** |
| I-15 unsupported "gap between methods" | **Resolved** (rephrased) |
| I-16 MGCN leak section-weighted | **Partly** ("20 sections" is now stated in the sentence) |
| I-17 HiSTaR median/CI | **Partly** ("CI over sections" stated; how the median was formed is still not stated) |
| I-18 "margin fixed before" | **Resolved** in the paper; the docstring of `stats_cluster_aware.py:6` still says "fixed before looking" |
| I-19 BayesSpace 50 min | Removed; **new timing error** for CCST (A6) |
| S1 few clusters | Open (S-C); now 7 groups, acknowledged |
| S2 multiplicity | Open (S-B); acknowledged |
| S3 exploratory reference | Partly: the test-only analysis is reported (6/8) |
| S4 asymmetric clustering | Resolved except A2 |
| S5 estimands | Open (S-D) |
| S6 mclust vs sklearn log-likelihood | Moot: `mcLLfrac` is no longer used in the text |
| S7 seeds | Open (S-F); worse for DeepST on the new data |
| S8 equivalence power | Open (S-G) |
| S9 ties | Open, minor (LD 0.558 vs SEDR/AnisoST 0.551 on DLPFC) |
| S10 extremes | Partly: S9 now gives median and IQR |
| S11 ρ NaN | Open, minor |
| S12 section-level Wilcoxon | Open (S-E) |

## F. Suggested additions to `scripts/check_paper_numbers.py`

- Assert the seed-SD range (A5) and the CCST median time (A6) from the JSON.
- Assert that the "three seeds" sentence matches the runner coverage (A1).
- Assert `metrics.ARI != metrics_matched.ARI` wherever a method's default is declared to be 3-start (A2).
- Assert that the S12 run counts match `metrics.tex` (A4).
- Assert the GraphST DLPFC seed count (A8).
