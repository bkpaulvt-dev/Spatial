# 03 — Numbers and statistics audit (paper/main.tex, paper/supplementary.tex)

Reviewer role: statistical reviewer. Every macro used in `paper/main.tex` was resolved against
`results/paper_macros.tex`, and the key numbers were recomputed from the raw result files with
independent scratch code (`/tmp/rev/*.py`; not part of the repo). No repo files other than this report were changed.
`scripts/check_paper_numbers.py` passes (9/9 hard-coded claims, 73/73 checked macros defined), but it only checks
string presence. It does not check whether the wording fits the statistics.

**Bottom line.** All 87 macro values used in the manuscript reproduce from the raw files, up to rounding and
bootstrap Monte-Carlo error (±0.003 on CI bounds). No number is arithmetically wrong. The problems are:
(i) some claims say more than the statistics support ("matched or outperformed every deep encoder", "AnisoST matched",
"improved 6 of 12", "Edge preservation helps");
(ii) the reference is compared asymmetrically in the "standard" protocol, and the Methods section describes it incorrectly;
(iii) two different estimands (cluster-weighted and dataset-weighted) are mixed, and they disagree on whether linear
diffusion or BASS is first;
(iv) several stale or incorrect statements in the Methods, supplement and `coverage_matrix.md`;
(v) the mclust-vs-sklearn log-likelihood comparison is not comparable across implementations for three methods.

---

## 1. Macros used in main.tex (resolved)

87 distinct generated macros appear in main.tex. Values (from `results/paper_macros.tex`):

| Macro | Value | Where used |
|---|---|---|
| nMethodsPub | 13 (hard-coded in paper_v2.py, not computed) | Abstract, Intro, Fig 1/2 captions, Discussion |
| nSections | 20 | Abstract, Data, Discussion, Limitations |
| bestDlpfc / Val | linear diffusion / 0.558 | Abstract, Results 1 |
| bestStarmap / Val | BANKSY λ=0.8 / 0.740 | Abstract, Results 1 |
| bestMerfish / Val | BASS / 0.582 | Abstract, Results 1 |
| meanLin{Dlpfc,Starmap,Merfish} | 0.558 / 0.705 / 0.497 | Results 1, Results (MGCN) |
| overallLin / Bass / BanksyHi | 0.587 / 0.594 / 0.554 | Results 1 |
| nStdBetter / nStdTot / nStdBetterTest | 14 / 16 / 12 | Abstract, Results 1 |
| stdDBass (lo, hi) | +0.025 (−0.046, +0.101) | Results 1 |
| stdDBanksyHi (lo, hi) | +0.045 (−0.008, +0.091) | Results 1 |
| nRobBetter / nRobTot / nRobUnres | 8 / 13 / 5 | Results 1 |
| pBestLin / pBestBass | 0.70 / 0.25 | Results 1 |
| rankLoLin–rankHiLin / rankMethods | 1–3 / 16 | Results 1 |
| statMargin / statBoot / statClusters | 0.03 / 5000 / 5 | Abstract, Methods, Results, Fig 2 caption |
| lotN / lotNMethods | 280 / 14 | Methods, Results, Fig 3 caption, Discussion |
| lotMean / lotMax | 0.18 / 0.60 | Abstract, Results, Discussion |
| lotWorstMethod / Section | SEDR / dlpfc 151672 | Results |
| lotLo (Name) / lotHi (Name) | 0.09 (SpaceFlow) / 0.24 (BANKSY λ=0.8) | Results |
| lotMeanHistar / Aniso / Graphst | 0.23 / 0.20 / 0.09 | Results |
| lotOracle | 0.08 | Results |
| mcN / mcNMethods | 280 / 14 | Methods, Results |
| mcPermMean / Max / MeanDlpfc / MeanMerfish | 0.10 / 0.37 / 0.12 / 0.11 | Abstract (Max), Results |
| mcPermFrac / mcPermGt | 26 % / 44 % | Results |
| mcJitMean / Max / MeanStarmap | 0.13 / 0.56 / 0.22 | Results |
| mcDefault / mcBest / mcLLfrac | 0.40 / 0.43 / 34 % | Results |
| nGainPos / nGainNeg / nGainTot | 6 / 5 / 12 | Abstract, Results |
| gainHistar (wins/N, p) | +0.053 (14/20, p=0.004) | Results |
| gainGraphst (wins/N, p) | +0.025 (13/20, p=0.114) | Results |
| gainSedr / gainMgcn | −0.092 / −0.037 | Results |
| rhoDlpfcMed / rhoMerfishMed / rhoNegMerfish | 0.38 / −0.11 / 10 | Results |
| mgcnLeak / mgcnLeakStarmap / mgcnLeakN | 0.147 / 0.38 / 20 | Abstract, Results |
| mgcnOracle{D,S,M} / mgcnFinal{D,S,M} | 0.551, 0.687, 0.221 / 0.418, 0.303, 0.182 | Results |

Hard-coded (non-macro) numbers in main.tex:
- HiSTaR seed SD 0.047 / 0.18; baselines 0.003–0.04.
- AnisoST vs linear diffusion 0.551 vs 0.558 (DLPFC) and 0.363 vs 0.497 (MERFISH).
- Boundary gain 0.025, 9/12, p=0.034.
- HiSTaR median 0.509 (Abstract 0.51), mean 0.491, CI 0.454–0.525, mclust 0.449, deterministic 0.487, reported 0.65.
- BayesSpace about 50 min.

---

## 2. Independent recomputation

Recomputed from `results/{anisost_main,baselines,extra,graphst,new_methods}.jsonl` (paper pipeline),
`clustering_lottery.jsonl`, `mclust_lottery_*.csv`, `anisost_boundary.jsonl`, `dlpfc_main.jsonl`, `benchmark_runs.jsonl`,
`configs/datasets.yaml`. The bootstrap was re-implemented with a different RNG seed (4000 resamples).

| # | Claim | Location | Paper value | Recomputed | OK? |
|---|---|---|---|---|---|
| 1 | Best method DLPFC (both protocols) | Abstract, Res 1 | linear diffusion 0.558 | linear diffusion 0.5580; runner-up SEDR+20-start 0.551, AnisoST 0.551 | OK (margin 0.007) |
| 2 | Best method STARmap | Abstract, Res 1 | BANKSY λ=0.8 0.740 | BANKSY λ=0.8 0.740 (BASS 0.716, LD 0.705) | OK |
| 3 | Best method MERFISH | Abstract, Res 1 | BASS 0.582 | BASS 0.582 (LD 0.497) | OK |
| 4 | Linear diffusion mean ARI D/S/M | Res 1 | 0.558 / 0.705 / 0.497 | 0.558 / 0.7054 / 0.497 | OK |
| 5 | Dataset-average LD / BASS / BANKSY0.8 | Res 1 | 0.587 / 0.594 / 0.554 | 0.587 / 0.594 / 0.554 | OK (note: BASS > LD) |
| 6 | nStdBetter / nStdTot | Abstract, Res 1 | 14 / 16 | 14 / 16 | OK |
| 7 | nStdBetterTest | Res 1 | 12 | 12 (all 12 are among the 14) | OK |
| 8 | BASS Δ (95 % CI) | Res 1 | +0.025 (−0.046, +0.101) | +0.025 (−0.045, +0.103) | OK (MC error) |
| 9 | BANKSY0.8 Δ (95 % CI) | Res 1 | +0.045 (−0.008, +0.091) | +0.045 (−0.009, +0.092) | OK |
| 10 | Sign change per dataset (BASS ahead on MERFISH, BANKSY on STARmap) | Res 1 | — | BASS: +0.074/−0.011/−0.085; BANKSY0.8: +0.064/−0.035/+0.069 | OK (BASS also ahead on STARmap, −0.011) |
| 11 | nRobBetter / nRobTot / nRobUnres | Res 1 | 8 / 13 / 5 | 8 / 13 / 5 | OK |
| 12 | Equivalent comparisons | Abstract | 0 | 0 (no 90 % CI within ±0.03) | OK |
| 13 | pBest LD / BASS; LD rank interval | Res 1 | 0.70 / 0.25; 1–3 of 16 | 0.699 / 0.247; 1–3 (stats JSON) | OK |
| 14 | lotN / lotNMethods | Methods, Res | 280 / 14 | 280 embeddings, 14 methods, 20 fits each, no duplicates | OK |
| 15 | lotMean / lotMax | Abstract, Res | 0.18 / 0.60 | 0.177 / 0.600 (SEDR, DLPFC 151672) | OK |
| 16 | lotLo / lotHi | Res | 0.09 SpaceFlow / 0.24 BANKSY0.8 | 0.091 / 0.240 | OK |
| 17 | lot HiSTaR / AnisoST / GraphST | Res | 0.23 / 0.20 / 0.09 | 0.225 / 0.201 / 0.093 | OK |
| 18 | lotOracle (best-by-ARI minus mean) | Res | 0.08 | 0.076 | OK |
| 19 | mcPermMean / mcPermMax | Abstract, Res | 0.10 / 0.37 | 0.100 / 0.371 (NichePCA, DLPFC 151671) | OK. The range is over the 10 permutations only; including the unpermuted fit, the max is 0.465. |
| 20 | mcPermMean DLPFC / MERFISH (/ STARmap) | Res | 0.12 / 0.11 (STARmap 0.00 not stated) | 0.122 / 0.107 / 0.000 | OK |
| 21 | mcPermFrac / mcPermGt | Res | 26 % / 44 % | 25.5 % / 43.6 % | OK |
| 22 | mcJitMean / Max / STARmap | Res | 0.13 / 0.56 / 0.22 | 0.131 / 0.559 / 0.219 | OK |
| 23 | mcDefault / mcBest / mcLLfrac | Res | 0.40 / 0.43 / 34 % | 0.401 / 0.435 / 33.6 % | Value OK; **comparability questionable** (see S6) |
| 24 | rho median DLPFC / MERFISH | Res | 0.38 / −0.11 | 0.376 / −0.113 (median over embeddings; one DLPFC ρ is NaN, constant ARI) | OK |
| 25 | rhoNegMerfish | Res | 10 of 14 | 10 of 14 | OK |
| 26 | nGainPos / nGainNeg / nGainTot | Abstract, Res | 6 / 5 / 12 | 6 / 5 / 12 (BANKSY0.8 +0.003 is "neutral") | OK, but depends on weighting (see S5) |
| 27 | gain HiSTaR / GraphST / SEDR / MGCN | Res | +0.053 / +0.025 / −0.092 / −0.037 | +0.053 (14/20, p=0.004) / +0.025 (13/20, p=0.114) / −0.092 / −0.037 | OK |
| 28 | mgcnLeak (all) / STARmap | Abstract, Res | 0.147 / 0.38 | 0.147 / 0.384 (DLPFC 0.133, MERFISH 0.039) | OK; section-weighted; dataset-weighted = 0.185 |
| 29 | MGCN oracle / final D,S,M | Res | 0.551, 0.687, 0.221 / 0.418, 0.303, 0.182 | identical | OK |
| 30 | HiSTaR median DLPFC | Abstract, Res | 0.51 / 0.509 | 0.5093 (median of 12 seed-averaged sections); median of 36 single runs = 0.493 | OK |
| 31 | HiSTaR mean / CI | Res | 0.491 / 0.454–0.525 | 0.4906 / 0.454–0.525 (naive section bootstrap) | OK (but ignores donors) |
| 32 | HiSTaR + R mclust | Res | 0.449 | 0.4492 | OK |
| 33 | HiSTaR seed SD DLPFC / STARmap | Res | 0.047 / 0.18 | 0.047 / 0.180 | OK |
| 34 | Baseline seed SD range | Res | 0.003–0.04 | 0.003–0.042 (AnisoST 3-start, STARmap) | OK |
| 35 | AnisoST vs LD DLPFC / MERFISH | Res | 0.551 vs 0.558 / 0.363 vs 0.497 | 0.551 / 0.558; 0.363 / 0.497 | OK (value); wording see I-4 |
| 36 | Boundary gain | Res | 0.025, 9/12, p=0.034 | 0.0246, 9/12, p=0.0342 (interior −0.003, p=1.0) | OK |
| 37 | nSections | Abstract | 20 | 20 | OK |
| 38 | BayesSpace ~50 min | Res | ~50 min | feasibility 2998 s; pilot median 3115 s (52 min); standardised runner median 1839 s (31 min) | OK for the feasibility run; runner median differs |

### 2b. Paper pipeline vs standardised runner (`benchmark_runs.jsonl`), mean ARI, own clustering

Format: paper / runner (runner − paper, on common sections). Seeds differ for some methods:
- Paper pipeline has 1 seed for STAGATE, CCST, Spatial-MGCN, BASS and GraphST on DLPFC; the runner has 3.
- DeepST has 3 seeds in the paper pipeline and 1 in the runner.

| Method | DLPFC | STARmap | MERFISH | mean abs diff |
|---|---|---|---|---|
| Linear diffusion | 0.558 / 0.569 (+0.011) | 0.705 / 0.733 (+0.028) | 0.497 / 0.497 (0) | 0.013 |
| AnisoST (20-start) | 0.551 / 0.554 (+0.004) | 0.622 / 0.621 | 0.363 / 0.363 | 0.002 |
| PCA | 0.409 / 0.417 (+0.007) | 0.294 / 0.295 | 0.130 / 0.130 | 0.003 |
| BANKSY λ=0.2 | 0.514 / 0.514 | 0.502 / 0.502 | 0.211 / 0.211 | 0.000 |
| BANKSY λ=0.8 | 0.494 / 0.494 | 0.740 / 0.740 | 0.428 / 0.428 | 0.000 |
| HiSTaR | 0.491 / 0.497 (+0.006) | **0.593 / 0.515 (−0.077)** | 0.221 / 0.237 (+0.016) | 0.033 |
| GraphST | 0.514 / 0.502 (−0.013) | 0.388 / 0.388 | 0.251 / 0.260 (+0.009) | 0.007 |
| SpaGCN | 0.422 / 0.422 | 0.267 / 0.259 (−0.008) | **0.151 / 0.113 (−0.039)** | 0.016 |
| STAGATE | 0.497 / 0.509 (+0.011) | **0.479 / 0.550 (+0.071)** | **0.368 / 0.331 (−0.037)** | 0.040 |
| SEDR | 0.515 / 0.515 | 0.593 / 0.593 | 0.406 / 0.406 | 0.000 |
| SpaceFlow | 0.312 / 0.312 | 0.628 / 0.628 | 0.389 / 0.389 | 0.000 |
| NichePCA | 0.321 / 0.321 | 0.692 / 0.692 | 0.475 / 0.475 | 0.000 |
| CCST | 0.437 / 0.438 | 0.505 / 0.498 (−0.007) | 0.212 / 0.222 (+0.010) | 0.006 |
| Spatial-MGCN | 0.418 / 0.414 | 0.303 / 0.304 | 0.182 / 0.175 | 0.004 |
| DeepST | 0.459 / 0.456 | 0.368 / 0.343 (−0.025) | 0.231 / 0.220 (−0.011) | 0.013 |
| BASS | 0.484 / 0.490 (+0.005) | 0.716 / 0.718 | 0.582 / 0.561 (−0.022) | 0.009 |
| BayesSpace | 0.437 / 0.437 | — | — | 0.000 |

Seed 0 is identical in both pipelines. Seeds 1–2 differ for some methods: for linear diffusion and HiSTaR, the same
(section, seed) gives different ARI (e.g. HiSTaR STARmap BZ5 seed 2: 0.441 runner vs 0.804 paper). The two pipelines
are therefore not seed-reproducible for these methods. In the runner, linear diffusion's dataset average (0.600) exceeds
BASS (0.590); in the paper pipeline BASS is higher (0.594 vs 0.587). The order of the top two depends on the pipeline.
The supplement (S12 caption) says the values "differ slightly"; differences of 0.04–0.08 for HiSTaR and STAGATE on
STARmap are more than slight.

---

## 3. Inconsistencies and overstatements

| ID | Issue | Location | Evidence | Suggested fix |
|---|---|---|---|---|
| I-1 | **"a training-free diffusion baseline matched or outperformed every deep encoder we tested"** overstates. "Matched" was never established: no comparison met the equivalence criterion. With the 20-start protocol, HiSTaR, STAGATE and SEDR are *unresolved*, not outperformed. The reference is exploratory and the comparisons are uncorrected. | Discussion ¶1 | stats_cluster_aware.json robust/histar (−0.018, +0.163), robust/stagate (−0.001, +0.131), robust/sedr (−0.008, +0.352) | "had a higher mean ARI than most deep encoders under their standard clustering (exploratory); with matched 20-start clustering, 3 of 11 comparisons with deep encoders were unresolved." |
| I-2 | "Accuracy differences between most methods were small" contradicts Results, where 14/16 Δ have CIs above zero and Δ reaches 0.24. | Discussion ¶1 | stdD* macros | Say "small among the top 4–5 methods". |
| I-3 | **Asymmetric "standard" comparison.** Linear diffusion and PCA are always clustered with the 20-start GMM (AnisoST default n_init=20), while the "standard" protocol gives other methods a 3-start GMM, Leiden or mclust. The Methods say "a 3-start GMM … for HiSTaR, BANKSY **and the baselines**", which is false for linear diffusion and PCA. The Fig 2 caption and S3/S8 say 20-start, so the Methods contradict the captions. | Methods, Clustering protocols; Fig 2 caption | `benchmark_anisost.py` METHODS; `anisost/core.py` n_init=20; `benchmark_extra.py` | Correct the Methods. Make the robust (matched) protocol the primary comparison, or state that the reference gets the 20-start clustering in both. |
| I-4 | "AnisoST **matched** linear diffusion in ARI (0.551 vs 0.558)" is not supported. The cluster-aware analysis puts AnisoST below LD (standard Δ +0.071, CI +0.019 to +0.129). Under 20-start it is unresolved, with a 90 % CI (+0.002, +0.096) outside ±0.03, so it is *not* equivalent. | Results "Edge preservation" | S5/S6 | "was close to linear diffusion on DLPFC (0.551 vs 0.558); across datasets it was lower (Δ +0.048, 95 % CI −0.005 to +0.107)". |
| I-5 | Section title "Edge preservation **helps** at boundaries on Visium" rests on one uncorrected Wilcoxon p=0.034 over 12 sections from 3 donors, i.e. nested data. The paper's own argument is that sections are not independent. | Results heading | anisost_boundary.jsonl | Use "may help"; analyse with the donor-level bootstrap; report it as exploratory. |
| I-6 | Abstract "Choosing the best of 20 starts by likelihood **improved** 6 of 12 methods and **worsened** 5". Most changes are not significant (GraphST p=0.11, STAGATE 0.20, BANKSY0.2 0.18, SpaceFlow 0.37, DeepST 0.31, SEDR 0.07). "12 methods" includes AnisoST (a baseline) and BANKSY twice. | Abstract, Results | S11 | "raised the mean ARI of 6 and lowered it for 5 of 12 embeddings-producing configurations (most changes not significant)". |
| I-7 | **Mixed estimands.** Results quote dataset-weighted averages (LD 0.587 < BASS 0.594). The bootstrap, P(best)=0.70 and the rank interval use a cluster-weighted mean, where DLPFC is 3/5 of the weight. LD is ranked first only under the DLPFC-heavy weighting. Fig 2a orders rows by the dataset-weighted mean, which puts BASS above LD, while panel c reports LD as the most likely to rank first. LD's settings were fixed on DLPFC donor 1, and DLPFC dominates the estimand. | Results 1, Fig 2 | overall* macros vs stats JSON | State both estimands explicitly. Report P(best) under dataset-equal weighting as a sensitivity analysis. Avoid implying LD is the overall best. |
| I-8 | "BASS was ahead on MERFISH and BANKSY λ=0.8 on STARmap": BASS was also ahead on STARmap (Δ −0.011). | Results 1 | S5 per-dataset columns | "BASS was ahead on STARmap and MERFISH". |
| I-9 | "mclust perturbations … (\mcNMethods{} methods in the extended set, **plus** HiSTaR, GraphST and AnisoST)" renders as "14 … plus 3" = 17. In fact the 14 already include HiSTaR, GraphST and AnisoST. | Methods, Clustering protocols | mclust CSVs: 14 methods, 280 embeddings | "(14 methods with embeddings, including HiSTaR, GraphST and AnisoST)". |
| I-10 | `coverage_matrix.md` gives GraphST in the paper pipeline as "20/20 / 3" seeds. DLPFC has 1 seed, as main.tex says correctly. The script takes the union of seeds across datasets. S18 (coverage.tex) inherits this. | coverage_matrix.md / S18 | graphst.jsonl | Report seeds per dataset (D/S/M), as S8 does. |
| I-11 | S12 caption: "CCST, DeepST and BayesSpace are still running and are not yet included". They are included (metrics.tex has rows; benchmark_runs complete, 0 errors after dedup). | supplementary.tex S12 | results/supp/metrics.tex | Delete the sentence. |
| I-12 | Supplementary Note 5: "six patterns of label use", but S16 lists five (L1–L5). | supplementary.tex | audit.tex | Make the two match. |
| I-13 | S10 (mclust) reports the *median* range per method, while the main text reports *mean* ranges. S9 reports the median range, while the text's per-method values (0.09 … 0.24) are means. This is not wrong but invites mismatches (e.g. GraphST S9 0.07 vs text 0.09). | Results / S9 / S10 | — | Label "mean" or "median" in the text, or add a mean column to the tables. |
| I-14 | The abstract does not say that the LD reference was chosen post hoc and that the comparisons are exploratory. The Results and Fig 2 caption do. | Abstract | — | Add "(exploratory)" to the abstract claim. |
| I-15 | "would inflate a reported result by about as much as the gap between most published methods" has no evidence pointer or quantity. | Results, Robustness | — | Cite the distribution of pairwise Δs (e.g. median absolute Δ between published methods) or drop. |
| I-16 | Spatial-MGCN leak "0.147 on average" is a section-weighted mean (DLPFC 12/20). The dataset-weighted mean is 0.185. This is a different averaging from the rest of the Results. | Abstract, Results | — | State "mean over 20 sections". |
| I-17 | The HiSTaR median of 0.509 is a median of seed-averaged sections. The reported 0.65 is presumably a median of single runs, whose median here is 0.493. The CI 0.454–0.525 is a plain section bootstrap that ignores donors, unlike the rest of the paper. | Results HiSTaR, S14 | dlpfc_main.jsonl | State how the median was formed; use the donor bootstrap or call the CI approximate. |
| I-18 | "Margin fixed before the analysis": git history shows the margin first appeared on 2026-10-14 (REVIEW_ROADMAP.md and stats_cluster_aware.py, same day), after the per-method means had been committed (2026-10-08 onward). It was fixed before the bootstrap was run, but not before the data were seen. | Methods, Supp Note 4 | git log | "fixed before the bootstrap analysis (after the means were known)" or justify 0.03 externally (≈ seed SD). |
| I-19 | Results: "tens of minutes … about 50 minutes for BayesSpace" comes from the feasibility run. The standardised runner median is 31 min (timeMedBayesspace=1839 s). | Results 1 | macros | Say which measurement is meant. |

No other abstract/results/caption/supplement value mismatches were found. Every macro is rendered identically wherever
it is used, and the supplementary tables (S3, S5–S11, S14, S15) agree with the macros to the printed precision.

---

## 4. Statistical methodology concerns and fixes

| ID | Concern | Severity | Fix |
|---|---|---|---|
| S1 | **Five-cluster hierarchical bootstrap.** With 5 top-level units, the percentile bootstrap has only 5^5 = 3125 distinct cluster resamples (126 distinct multisets). Percentile intervals at n=5 are known to under-cover (often 80–85 % nominal 95 %). STARmap (3 sections) and MERFISH (5 sections) are each one cluster, so between-dataset heterogeneity, the dominant source (e.g. BASS +0.074 / −0.011 / −0.085), is estimated from 5 points. | High | Report as descriptive. Add a sensitivity analysis with a t-based interval on the 5 cluster means (df = 4) or a random-effects model (dataset/donor random effects). Present the per-dataset Δ as primary and the pooled Δ as secondary. |
| S2 | **Multiplicity.** 16 + 13 = 29 interval-based comparisons, each called "baseline higher" at 95 % with no family-wise or FDR control. The earlier pooled Wilcoxon used Holm, but the bootstrap does not. The gain p-values (S11) and the boundary p are explicitly unadjusted. | High | Use simultaneous (max-t / Bonferroni 99.7 %) bootstrap intervals or Holm on bootstrap p-values. At least report how many verdicts survive (e.g. SEDR's lower bound +0.012 and GraphST's +0.010 would probably not). |
| S3 | **Exploratory reference choice** (acknowledged). Choosing the best-looking method as the reference and then testing "reference vs all" biases Δ upward (winner's curse). In addition, the reference's settings were tuned on DLPFC donor 1, which carries 1/5 of the bootstrap weight and is part of DLPFC's 3/5. | High | Keep the test-only analysis (12/16 survive). Add a reference-free analysis: all-pairs comparisons, or the rank intervals as the primary result. Avoid "outperformed". |
| S4 | **Asymmetric clustering in the "standard" protocol** (I-3). The reference always gets the 20-start best-likelihood GMM, which adds +0.02 to +0.05 for several embeddings (S11). | High | Compare under the matched protocol (S6 table) as the primary result. There, 8/13 favour the baseline and 5 are unresolved. |
| S5 | **Section-pooled vs cluster-weighted vs dataset-weighted.** The clustering gain (nGainPos/Neg), mgcnLeak and the HiSTaR stats weight sections equally (DLPFC 60 %). The accuracy comparison weights clusters equally, and "overall" means weight datasets equally. The sign of NichePCA's gain flips with the weighting: +0.080 pooled vs +0.008 dataset-weighted (DLPFC +0.185, STARmap −0.088, MERFISH −0.072). Under dataset weighting the count becomes 6 up / 6 down. | Medium | Pick one estimand (cluster-weighted to match S5) and use it everywhere, or report both. |
| S6 | **mclust vs sklearn log-likelihood not comparable.** For SEDR, Spatial-MGCN and HiSTaR the per-observation log-likelihood from R mclust is +11 to +65 nats higher than the best sklearn fit. This is due to near-singular covariances (sklearn reg_covar=1e-5 caps the likelihood; mclust does not), not a better optimum. Of the 34 % of cases where "mclust ≥ best-of-20", 98 % of those 3 methods' embeddings qualify. Excluding them, the share is 16 %. | Medium | Recompute both likelihoods under the same model and regularisation (e.g. evaluate mclust's partition/parameters in sklearn, or refit mclust from sklearn's best start). Otherwise report 16 % with the three methods excluded and explain. |
| S7 | **Seeds averaged before analysis.** Each (method, section) is a mean over 1 or 3 seeds, so methods with 3 seeds have less within-section noise than 1-seed methods (STAGATE, CCST, MGCN, BASS, GraphST-DLPFC). Seed variance is not propagated into the CIs. For single-seed methods the seed-0 draw may be lucky or unlucky (HiSTaR seed SD 0.18 on STARmap). The runner shows seeds 1–2 are not reproducible between pipelines (§2b). | Medium | Use 3 seeds for every method (the runner already has them for STAGATE/CCST/MGCN/BASS). Add a seed level to the bootstrap (resample seeds within section). Flag single-seed methods in Fig 2. |
| S8 | **Equivalence margin 0.03.** It is roughly the seed SD, so it is a noise-level margin. With 5 clusters, the 90 % CIs are ≥0.09 wide, so equivalence is essentially unattainable (power ≈ 0). "No method was equivalent" is then uninformative, yet it is used rhetorically in the abstract. | Medium | Report the minimal margin each comparison could establish, or the TOST power. Drop the claim from the abstract, or add "(the design had little power to show equivalence)". |
| S9 | **ARI ties and close calls.** The "highest mean ARI" on DLPFC (0.558) is 0.007 above SEDR+20-start and AnisoST. This is well inside the seed SD, and the runner gives a different LD value (0.569). | Low | Use "among the highest" or give the interval. |
| S10 | **Lottery/mclust use one embedding per section** (acknowledged). Ranges are maxima over 20 or 10 draws, so they grow with the number of draws. Abstract "up to 0.60" / "up to 0.37" are single extremes out of 280 embeddings. | Low | Report the SD across starts (S9 has it) and quantiles alongside the extremes. |
| S11 | **Spearman ρ** over 20 fits with ties and one constant case (NaN) on DLPFC. The medians pool all embeddings across methods. | Low | Note n and the NaN; give the per-method distribution (already in S9). |
| S12 | Gain and boundary Wilcoxon tests treat 20 or 12 sections as independent, against the paper's own clustering argument. | Medium | Use the same hierarchical bootstrap for these contrasts. |

---

## 5. Reproduction notes

- Scratch code: `/tmp/rev/load.py`, `r1.py`–`r7.py` (independent loaders; the bootstrap re-implemented with a different seed).
- All recomputed CIs agree with `stats_cluster_aware.json` within ±0.003, which is Monte-Carlo error.
- `scripts/check_paper_numbers.py`: 9/9 OK. It checks hard-coded strings only, not the 87 macros or the wording. Suggested
  addition: assert I-3 (protocol description), I-9 (method count) and the supplement captions (I-11, I-12).
