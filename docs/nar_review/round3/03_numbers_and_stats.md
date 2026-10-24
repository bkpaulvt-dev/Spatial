# 03 (round 3): Numbers and statistics re-audit

**Reviewer role:** statistical reviewer.

**Inputs checked**
- `paper/main.tex`, `results/paper_macros.tex` (01:55), `paper/supplementary.tex` and `results/supp/*.tex` (02:08).
- `stats_cluster_aware.json` and `stats_cluster_aware_runner.json` (01:53/01:55), `benchmark_runs.jsonl` (00:51, newest record per id), `brca_coarse.json` (02:08).
- The macros are current with the data. The brca_coarse macros equal the JSON values even though the JSON is 13 min newer.

**How the checks were done**
- Everything was recomputed with read-only Python from the raw jsonl/csv files. No output-writing script was run.
- `scripts/check_paper_numbers.py` passes: **7/7 hand-typed claims, 115/115 macros defined.**

**Bottom line**
- Every macro value and every new claim I checked reproduces (37 items, section C).
- The major round-2 problems are fixed: A1, A2, A3, A5, A6, A7, A9–A12, A14 and S-A.
- What remains is one wrong sentence in the Discussion, a contradiction in Supplementary Note 4, a LaTeX rendering bug in four supplementary tables, the screening-caption error (A13), the coverage table (A8), and several minor wording points.

---

## A. Status of round-2 points

| # | Status | Evidence |
|---|---|---|
| A1 seeds on new data | **Resolved** | main.tex:158–161 and Supp Note 1 now state 3 seeds; 2 for CCST on E10.5_E1S1; 1 for BayesSpace; DeepST seeds 1–2 OOM on E10.5_E2S1. Runner (latest per id): DeepST brca 3, E9.5 3, E2S1 1 (seeds 1–2 "killed (out of memory)", 12.0 GB), E1S1 0; BayesSpace brca 1; CCST E1S1 seeds 0,1. All match. |
| A2 AnisoST "own" = 20-start on new data | **Resolved** | stats_cluster_aware.py:42, paper_v2.py:47 and make_supplement.py:48 no longer take AnisoST's own ARI from the runner. `anisost_single_gmm` on brca/stereo now comes from `baselines_3start.jsonl` (3+9 runs) and differs from the runner value, e.g. block_a_1 s0: 0.543 vs 0.501. stdDAniso is now +0.033 (brca −0.022, stereo −0.051). gainAniso +0.014, 14/24, p=0.121 (was p=0.020). `OWN_KEY` in stats_cluster_aware.py:36 is now dead code. |
| A3 S14/S15 protocol mix | **Resolved** | make_supplement.py:206 compares baselines like with like (20-start both sides); the S15 caption says so. LD +0.011/+0.028/0.000. |
| A4 S12 (now S13) caption | **Partly** | The run counts are now right ("up to 72"; DeepST 27, BayesSpace 13, CCST 71). supplementary.tex:96 still says "Values differ slightly from S3 because the preprocessing is shared". For breast cancer and Stereo-seq both tables come from the same runs. The caption also does not say that memory-capped methods average 2 Stereo-seq sections. |
| A5 seed-SD range | **Resolved** | main.tex:245 \sdBaseLo–\sdBaseHi = 0.012–0.054, which equals the S9 min/max over the LD/AnisoST/PCA cells. |
| A6 CCST time | **Resolved (number)** | 2789 s → "about 46 min". Minor: main.tex:245 says "per section"; S14 reports the median *per job*. |
| A7 memory cap | **Resolved** | main.tex:161–163: the cap applied only to the new datasets; BayesSpace on DLPFC reached 12.5 GB (runner 151509: 12.54 GB). |
| A8 GraphST DLPFC 1 seed | **Partly** | main.tex:157 now names GraphST on DLPFC. Limitations main.tex:392 still says "Four methods were run with one seed in the published pipelines" (five, counting GraphST-DLPFC). S22 (`coverage.tex`) still gives GraphST pipeline "/ 3". It also gives DeepST runner "/ 3", but the runner has DeepST seed 0 only on DLPFC/STARmap/MERFISH and E10.5_E2S1. Cause: coverage_matrix.py:50–52 counts distinct seeds over all datasets. GraphST MERFISH has 12/15 runs. |
| A9 embryo < brain | **Resolved** | The sentence was removed; Discussion l.358 now matches the data. |
| A10 section title | **Resolved** | "helps on cortex but not on the other tissues" (l.310). |
| A11 K±1 | **Resolved** | l.238: 0.06 average, larger direction 0.09, up to 0.49. Recomputed: 0.061 / 0.093 / 0.485. The maximum, CCST 151672, is an increase (0.14→0.63), which the wording now permits. |
| A12 rank-3 at BIC | **Resolved** | \kAboveLinBic = BANKSY λ=0.8 (0.487) and NichePCA (0.472); LD 0.462. |
| A13 audit caption | **Not resolved** | supplementary.tex:131 still says "the benchmarked methods with released code plus SPARK, SpatialPCA and conST". `audit.tex` has 11 benchmarked repositories + 3, and **HiSTaR and NichePCA were not screened**. |
| A14 development sections | **Resolved** | l.155, 166–168 and 194–195 are consistent: 4 tuning sections, 6 excluded. |
| A15 neutral method in lottery | **Not resolved (minor)** | l.311–312: "10 of 14 … worse for 3". The 14th, BANKSY λ=0.8 (+0.0048), is not mentioned, and SpaceFlow (+0.0054) is counted as "beat". |
| A16 Fig 2A vs 2C | **Resolved** | Panel C now ranks on the 23 shared sections with BASS included (P=0.49), so it agrees with panel A's dataset-mean ordering (BASS 0.552 > LD 0.522). |

### Fragility points (round-2 §B, §C)
- **Deduplication by id:** now done in all three scripts (stats:39, paper_v2:45, make_supplement:45). Resolved.
- **mclust completeness:** all 332 embeddings now have 10 seeds and 1 full fit.
  - 4 brca embeddings (BANKSY ×2, CCST, GraphST) appear in both g2 and g5. The rows differ only in `seconds`, so they survive `drop_duplicates()`, but paper_v2.py:343 deduplicates on key. Correct.
- **Seed-0 cached PCs for the 3-start baselines:** still undocumented (minor).

### Statistical concerns (round-2 §D)

| ID | Status |
|---|---|
| S-A ranking excluded BASS | **Resolved.** Ranks now use the 23 shared sections: BASS 0.49, LD 0.29, BANKSY λ=0.8 0.06. The complete-method ranking (LD 0.74, 11 methods) is labelled as excluding BASS. Both reproduce from the JSON. |
| S-B multiplicity | **Partly.** Bonferroni intervals are reported (l.196, 215; Bonferroni column in S5–S7). Two caveats remain. (i) **supplementary.tex:26 still says "No correction for multiple comparisons is applied"**, which contradicts that. (ii) The 2-method Bonferroni list (CCST, Spatial-MGCN) is fragile: SpaceFlow's lower bound is −0.003, BayesSpace's −0.021 and PCA's −0.007. The 0.156 % tail rests on about 8 of 5000 draws. In the runner analysis SpaceFlow is also above zero (3 methods). Suggest "2–3 of 16". |
| S-C 7 clusters / percentile under-coverage | **Not resolved.** No t-based or random-effects sensitivity analysis. Acknowledged in the text ("intervals are wide"). |
| S-D mixed estimands | **Partly.** The weighting is stated for the overall comparison (l.188–189). Lottery, ρ, K-sensitivity and MGCN leak remain section-pooled without saying so. ρ medians are pooled over embeddings (e.g. DLPFC 0.38), whereas the median of per-method medians would be 0.24. Fig 3C's caption says "median" without saying over what. |
| S-E section-level Wilcoxon | **Partly.** Labelled "uncorrected" (l.249, 316) but still treated as independent sections. |
| S-F seed imbalance | **Partly.** Better disclosed (DeepST now 3 seeds on breast cancer and E9.5). Not propagated into the bootstrap. |
| S-G equivalence power | **Not resolved.** l.357 "no method was shown to be equivalent to it": the 90 % CI widths of 0.08–0.25 make equivalence within ±0.03 impossible. |
| S-H range vs mean difference | **Not resolved** (l.359–360, l.80–81). |
| S-I nAhead counts tiny Δ | **Not resolved.** The breast cancer count of 13 includes SpaceFlow (−0.001). The Stereo-seq count of 12 includes HiSTaR (−0.001) and Spatial-MGCN (−0.003). |
| S-J ρ NaN | **Not resolved (minor).** One constant-ARI embedding is dropped silently by `nanmedian`. |

---

## B. New problems found in this round

| # | Location | Problem | Evidence / fix |
|---|---|---|---|
| N1 | **main.tex:357** | "BASS was as likely to rank first" | BASS P(best) = 0.49 against 0.29 for LD (l.216–217 and S8). Write "BASS was more likely to rank first", as in the abstract. |
| N2 | **make_supplement.py:27** (`MINUS` regex) → `ranks.tex` (27×), `stats_runner.tex` (16×), `lottery.tex` (14×), `histar.tex` (2×) | Ranges written as `1--10` are rewritten to `1-$-$10`, which renders as "1-−10" (hyphen plus minus) in S7, S8, S10 and S18. | Exclude a `-` that is preceded by `-`: lookbehind `(?<![\w$\\-])`. |
| N3 | **supplementary.tex:26** (Supp Note 4) | "No correction for multiple comparisons is applied" contradicts main.tex:196/215 and the Bonferroni CI columns of S5–S7. The note also does not describe the shared-section ranking. | Update the note. |
| N4 | **main.tex:307–308** | "fell outside the range of the ten seeded fits for 14 % of the embeddings" uses all 332 embeddings. That includes 42 STARmap embeddings, which are deterministic and cannot fall outside. Over the 290 embeddings with n > 2000 (the set the paragraph is about) the figure is **16 % (47/290)**. | paper_v2.py:367: use `big`. |
| N5 | **main.tex:306; supplementary.tex:86** | "noise … not run on the 18,408-bin Stereo-seq section" | The noise repetitions *were* run there for AnisoST and both BANKSY settings (3 of 10 embeddings; 325 of 332 embeddings have noise rows). Say "not run for most methods on …". |
| N6 | main.tex:184 | "NMI gave the same ranking of methods" | Dataset-mean ranks agree at Spearman ρ = 0.97 but are not identical. SEDR is 16th of 17 by ARI and 12th by NMI; BayesSpace is 4th by NMI. Write "nearly the same ranking (ρ = 0.97)". |
| N7 | main.tex:233–234 | "every method reached a low ARI (0.04–0.31)" | Only the 14 embedding methods were scored (S17 excludes SpaGCN, BASS and BayesSpace). Write "every embedding method". |
| N8 | stats_cluster_aware.py (runner mode) | Latent bug, not used in the paper. With `STATS_SOURCE=runner`, `standard/anisost` has only 4 sections, and `ranking_own` in the runner JSON is computed on the brca/stereo sections only (LD median rank 12). The paper cites only the matched-clustering runner results, which are correct (9 better / 7 unresolved, P(best) BASS 0.43 / LD 0.44). | Do not publish `ranking_own` from the runner JSON, or add AnisoST pipeline own fits. |
| N9 | stats_cluster_aware.py:6, :124 | Stale comments: "fixed before looking" (I-18) and "methods with all 20 sections". | Cosmetic. |

---

## C. Numbers and claims re-verified against the data (37)

| # | Claim (main.tex line) | Recomputed | OK |
|---|---|---|---|
| 1 | LD matched means 0.558/0.705/0.497/0.545/0.306 (206–207) | means_robust LD 0.5580/0.7054/0.4970/0.5446/0.3061 | ✓ |
| 2 | Best per dataset: LD 0.558, BANKSY λ=0.8 0.740, BASS 0.582, BASS 0.624, SpaGCN 0.388 (208–210) | max over both protocols | ✓ |
| 3 | 8/16 better, 8 unresolved, both lists (211–213) | robust categories | ✓ |
| 4 | 5 of these hold test-only (212) | test_only ci95 lower > 0: SpaGCN, SpaceFlow, CCST, MGCN, PCA | ✓ |
| 5 | BASS −0.004 (−0.063, 0.061); BANKSY λ=0.8 +0.024 (−0.020, 0.069) | JSON | ✓ |
| 6 | Bonferroni: 2 (CCST, Spatial-MGCN) (215) | ci_bonf lower 0.018 and 0.015; next is SpaceFlow −0.003 | ✓ (fragile, S-B) |
| 7 | Rank on 23 shared sections: BASS 0.49, LD 0.29, BANKSY λ=0.8 0.06 (216–217) | ranking (16 methods, 23 sections) 0.495 / 0.290 / 0.057 | ✓ |
| 8 | 6 methods with rank 1 in their 95 % interval (217) | BASS, LD, BANKSY λ=0.8, NichePCA, AnisoST, HiSTaR | ✓ |
| 9 | 11 complete methods, LD 0.74 (218–219) | ranking_complete 0.738, 11 methods | ✓ |
| 10 | Runner: 9 better / 7 unresolved; BASS 0.43, LD 0.44 (220–221) | runner JSON robust | ✓ |
| 11 | Default clustering: 11 better, 5 unresolved and list (222–223) | standard categories | ✓ |
| 12 | nAhead 0/1/1, 13 of 16, 12 of 15 (226–229) | per_dataset negatives | ✓ |
| 13 | BASS 0.594 vs LD 0.587, three brain datasets (228) | (0.484+0.716+0.582)/3; (0.558+0.705+0.497)/3 | ✓ |
| 14 | dBrain 0.172, dOther −0.027 (230) | 0.1717, −0.0267 | ✓ |
| 15 | PCA vs LD: 0.562 vs 0.545 breast cancer, 0.349 vs 0.306 Stereo-seq (231–232) | means_robust; the default protocol has the same sign | ✓ |
| 16 | Coarse breast cancer classes 0.04–0.31; NichePCA and SpaceFlow first; LD 0.19, rank 11 of 14 (233–235) | brca_coarse.json: MGCN 0.041, NichePCA 0.308, SpaceFlow 0.300, LD 0.186 (11th) | ✓ (wording N7) |
| 17 | Memory-cap list BASS, DeepST, GraphST, NichePCA, Spatial-MGCN on E10.5_E1S1 (235) | runner errors, all "killed (out of memory)" at about 12.0–12.3 GB | ✓ |
| 18 | K±1: 0.06 / 0.09 / 0.49; BIC at edge 325 of 332; ρ = 0.93 (238–240) | 0.061 / 0.093 / 0.485; 325/332; 0.930 | ✓ |
| 19 | BIC: BANKSY λ=0.8 and NichePCA ahead of LD 0.462, rank 3 (241) | 0.487 / 0.472 / 0.462 | ✓ |
| 20 | HiSTaR SD 0.047 / 0.180; baselines 0.012–0.054 (244–245) | seed SD per section, averaged | ✓ |
| 21 | Median times: baselines and BANKSY < 30 s; CCST about 46 min; > 5 h (245–246) | 23–26 s; 2789 s; 18,856 and 19,578 s | ✓ |
| 22 | AnisoST MERFISH 0.363 vs 0.497; boundary 0.025, 9/12, p=0.034 (248–249) | check script | ✓ |
| 23 | Lottery: 332 embeddings, 14 methods, mean range 0.16, max 0.60 (SEDR 151672), LD 0.18, SpaceFlow 0.09, BANKSY λ=0.8 0.22, oracle 0.07 (279–282) | 0.165 / 0.600 / 0.182 / 0.089 / 0.215 / 0.072 | ✓ |
| 24 | mclust: 290 embeddings, mean 0.11, max 0.46, > 0.1 for 48 % (303–304) | 0.113 / 0.455 / 48.3 % | ✓ |
| 25 | Noise 0.08 mean, max 0.59 (306) | 0.083 / 0.591 over 325 embeddings | ✓ (N5) |
| 26 | Full fit outside the seeded range 14 % (308) | 47/332 = 14 %; 47/290 = 16 % | denominator (N4) |
| 27 | Best-likelihood better 10, worse 3 (311–312) | ±0.005 threshold | ✓ (A15) |
| 28 | Gain counts 8 / 5 of 14; HiSTaR +0.042 (p=0.006), NichePCA +0.077 (0.023), SEDR −0.077 (0.074), CCST −0.059 (0.010) (313–316) | recomputed Wilcoxon | ✓ |
| 29 | ρ medians DLPFC 0.38, STARmap 0.41, MERFISH −0.11 (negative for 10/14), breast cancer −0.13, Stereo-seq 0.06 (317–319) | pooled over embeddings | ✓ (S-D) |
| 30 | MGCN leak: 0.551/0.687/0.221 vs 0.418/0.303/0.182, 0.147, 20 sections (344–347) | section-weighted (12·0.133 + 3·0.384 + 5·0.039)/20 = 0.147 | ✓ |
| 31 | HiSTaR 0.509 / 0.491 / 0.454–0.525 / 0.449 / 0.487 (334–337) | check script | ✓ |
| 32 | DeepST seeds and BayesSpace single run (158–161) | runner | ✓ |
| 33 | BayesSpace on DLPFC 12.5 GB (163) | 12.54 GB | ✓ |
| 34 | mclust per dataset: brca 0.07, Stereo-seq 0.07, DLPFC 0.13, MERFISH 0.11 (macros) | 0.069 / 0.073 / 0.128 / 0.108 | ✓ |
| 35 | "BASS was as likely to rank first" (357) | 0.49 vs 0.29 | ✗ (N1) |
| 36 | "NMI gave the same ranking" (184) | ρ = 0.97 | overstated (N6) |
| 37 | S20 caption: "benchmarked methods with released code" | HiSTaR and NichePCA missing | ✗ (A13) |

---

## D. Suggested additions to `check_paper_numbers.py`
- Assert that the wording next to \pBestBass/\pBestLin matches their order (N1).
- Assert that no `results/supp/*.tex` contains `-$-$` (N2).
- Assert that the audit-table repository set includes every benchmarked method or that the caption names the missing ones (A13).
- Compute mcsFullOutside over the n > 2000 set (N4).
