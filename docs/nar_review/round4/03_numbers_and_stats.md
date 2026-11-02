# 03 (round 4): Final numbers and statistics audit

**Reviewer role:** statistical reviewer (final audit).

**Inputs checked**
- `paper/main.tex` and `paper/supplementary.tex` (23:21 / 23:25 on 2 Nov), `results/paper_macros.tex` (23:21) and `results/supp/*.tex` (23:25).
- `stats_cluster_aware.json`, `_runner.json` and `_expert.json` (23:12–23:15).
- `benchmark_runs.jsonl` (23:06; newest record per id; 17 latest records carry `host=deepmed2`), `baselines_3start.jsonl`, `clustering_lottery.jsonl` (336 embeddings), `k_sensitivity.jsonl`, `mclust_seed_g1..g6.csv` and `brca_coarse.json`.
- Macros, JSON and figures are in time order (data, then JSON, then macros, then tables and PDFs). Nothing is stale in that sense.

**How the checks were done**
- Read-only Python from the raw files. The only script run was `check_paper_numbers.py`.
- I also executed the data-assembly part of `stats_cluster_aware.py` in memory, cut off before its bootstrap and output code. Nothing was written. I used it for an independent re-bootstrap with different seeds.
- `scripts/check_paper_numbers.py`: **7/7 hand-typed claims match; 119/119 macros defined.**

**Bottom line**
- Every number in the revised main text that I recomputed reproduces (section C, 46 items).
- All 16 round-3 points A1–A16 are resolved. N1–N7 are resolved. Statistical points S-A, S-B and S-G are resolved. S-C to S-J and N8–N9 are unchanged.
- I found **six small errors or stale statements** and one fragile result (section B). None changes a conclusion.
- The R mclust numbers are provisional because four new embeddings are still running (section D). That is not an error.

---

## A. Status of every round-3 point

### A1–A16

| # | Status | Evidence |
|---|---|---|
| A1 seeds on new data | **Resolved** | Runner, latest record per id: every brca/Stereo-seq (method, section) has 3 seeds except BayesSpace on brca (1) and CCST on E10.5_E1S1 (seeds 0, 1). DeepST on E10.5_E2S1 now has 3 (seed 0 original, seeds 1–2 rerun on host deepmed2). DLPFC, STARmap and MERFISH have 3 seeds in the runner for all methods but BayesSpace (1) and DeepST (1). main.tex:157–166 matches. |
| A2 AnisoST own = 20-start | **Resolved** | Unchanged and correct. AnisoST "own" comes from `baselines_3start.jsonl`. stdDAniso +0.033, gainAniso +0.014 (14/24, p=0.121). |
| A3 S14/S15 protocol mix | **Resolved** | Unchanged. |
| A4 S13 caption | **Resolved** | The wording moved to S14 (supp:101). It now reads "for breast cancer and Stereo-seq they are the same runs", and "up to 72 = 24×3" is right. The caveat about memory-capped methods averaging 2 sections no longer applies. A new stale phrase in the same caption is B3. |
| A5 seed-SD range | **Resolved** | 0.012–0.054 equals the min/max over the LD, AnisoST and PCA cells of S10 (seeds.tex). |
| A6 CCST time | **Resolved** | main.tex:255 now says "median time per job". 2789 s gives 46 min. |
| A7 memory cap | **Resolved** | main.tex:160–163. BayesSpace on DLPFC peaked at 12.54 GB. |
| A8 GraphST DLPFC 1 seed, coverage | **Resolved** | main.tex:157 and 410 name GraphST on DLPFC. S23 (coverage.tex) now gives GraphST "1-3" and DeepST runner "1-3". |
| A9 embryo < brain | **Resolved** | Sentence removed. |
| A10 section title | **Resolved** | main.tex:326. |
| A11 K±1 | **Resolved** | 0.061 / 0.093 / 0.485 recomputed from 336 embeddings. |
| A12 rank-3 at BIC | **Resolved** | BANKSY λ=0.8 0.487 and NichePCA 0.472 are ahead of LD 0.462, which is rank 3. |
| A13 audit caption | **Resolved** | supp:136 now says "11 of the benchmarked methods (all except HiSTaR … and NichePCA, a library) plus SPARK, SpatialPCA and conST". audit.tex has exactly those 14 repositories. |
| A14 development sections | **Resolved** | 4 + 1 + 1 = 6 (main.tex:169–171, 197–198). |
| A15 neutral method in lottery | **Resolved** | main.tex:327–328 now states the threshold ("more than 0.005 ARI … 10 of 14 … worse for 3"). The 14th method (BANKSY λ=0.8, +0.0048) is covered by the threshold. |
| A16 Fig 2A vs 2C | **Resolved** | Panel C now ranks on all 24 sections including BASS (rank data below). |

### Fragility points from round 2

| Point | Status | Evidence |
|---|---|---|
| Deduplication by id | **Resolved** | Applied in all three scripts. `merge_bigmem.py` appends, and the analyses take the newest record. |
| mclust completeness | **Resolved for 332 embeddings; 4 pending** | All 332 finished embeddings have 10 seeds and 1 full fit. The 4 new embeddings of E10.5_E1S1 are not yet in any CSV. |
| Seed-0 cached PCs for the 3-start baselines | Unchanged (minor) | Still undocumented. |

### Statistical concerns S-A to S-J

| ID | Status | Evidence |
|---|---|---|
| S-A BASS excluded from ranking | **Resolved** | Ranking is on all 24 sections and 16 methods. No method is excluded now (`rankExcluded` = none). |
| S-B multiplicity | **Resolved in wording; result fragile** | Supp Note 4 (supp:26) now says "Intervals are uncorrected; Bonferroni-corrected intervals … are given as a check". The Bonferroni list is no longer stable under resampling (B7). |
| S-C 7 clusters, percentile under-coverage | **Not resolved** | No t-based or random-effects check. main.tex:198 only says "the intervals are wide". |
| S-D mixed estimands | **Partly** | Weighting is stated for the overall comparison (main.tex:189–192). ρ medians are still pooled over embeddings (DLPFC 0.376 pooled, per-method medians differ). Fig 3C caption (l.309) says "Median Spearman correlation" without saying over what. |
| S-E section-level Wilcoxon | **Partly** | Labelled "uncorrected" (l.259, 332), but sections are still treated as independent. |
| S-F seed imbalance | **Partly** | Better balanced: DeepST now has 3 seeds on every Stereo-seq section. Not propagated into the bootstrap. |
| S-G equivalence power | **Resolved** | main.tex:375 now blames interval width: "the intervals were too wide to show equivalence with any method". |
| S-H range vs mean difference | **Not resolved** | l.376–380 and l.80–81 still compare a max–min over 20 fits (mean 0.16) with differences of means. |
| S-I nAhead counts tiny Δ | **Not resolved** | Breast cancer 13 includes SpaceFlow (−0.001) and MGCN (−0.007). Stereo-seq 11 includes HiSTaR (−0.001). Counting only Δ > 0.01 gives 11 and 10. The text says "ahead" without a margin. |
| S-J ρ NaN | **Not resolved (minor)** | `ConstantInputWarning` still occurs: a constant-ARI embedding is dropped silently. |

### New items N1–N9 from round 3

| # | Status | Evidence |
|---|---|---|
| N1 "as likely to rank first" | **Resolved** | main.tex:375 "BASS ranked first more often (0.50 against 0.32)". |
| N2 `1-$-$10` | **Resolved** | `grep -- '-\$-\$' results/supp/*.tex` finds nothing. The regex at make_supplement.py:27 has the lookbehind. ranks.tex shows `1--10`. |
| N3 Supp Note 4 contradiction | **Resolved** | See S-B. |
| N4 mcsFullOutside denominator | **Resolved** | main.tex:323–324 uses n > 2000: 47/290 = 16.2 %. |
| N5 noise on the 18,408-bin section | **Resolved in main.tex, not in supp** | main.tex:322 now says "only for three embeddings" (true: anisost, banksy×2). supp:91 (S12 caption) still says "Noise repetitions were not run on the 18,408-bin Stereo-seq section" (B5). |
| N6 "same ranking" for NMI | **Resolved** | main.tex:187 "nearly identical ranking (ρ = 0.97)". I recomputed 0.9675. |
| N7 "every method" coarse | **Resolved** | main.tex:237 "every method with an embedding". |
| N8 runner-mode latent bug | **Not fixed, not used** | `stats_cluster_aware_runner.json` still has `standard/anisost` with 4 sections (baseline_worse) and a meaningless `ranking_own` (LD P(best) 0.00). The paper cites only the matched-clustering runner results, which are correct. |
| N9 stale comments | **Not fixed (cosmetic)** | stats_cluster_aware.py:6 "fixed before looking", :128 "all 20 sections", and dead `OWN_KEY` at :36. |

### Suggested additions to `check_paper_numbers.py` from round 3
- Not added: ordering of \pBestBass/\pBestLin, the `-$-$` assertion, and the audit repository set. The script still checks only 7 hand-typed claims. Optional.

---

## B. Remaining errors and stale statements (new this round)

| # | Location | Problem | Evidence and fix |
|---|---|---|---|
| B1 | **main.tex:238–240**, :162–163, :412–413; macros `peakBigMin`=12, `memMaxGraphst`=11.8 | "needed 12–28 GB of RAM … more than the 12 GB cap". GraphST's rerun peaks were 11.78, 11.65 and 11.66 GB, which is **below** the cap. The 12 comes from rounding 11.8. On the capped machine GraphST was killed at 12.04–12.18 GB. The first attempts on deepmed2 (host-tagged `error` records, failed in R mclust) peaked at 13.2 GB. | Reword to "GraphST about 12 GB, the others 20–28 GB". Say that the peak differs between machines and attempts (11.7 versus 13.2 GB for the same job). |
| B2 | **main.tex:426** ("All runs used one CPU thread"), supp:32 ("one CPU thread per job"), supp:106 (S15 "on one CPU thread") | The 20-thread server did not restrict threads. Rerun CPU time over wall time is **3.8 on average for DeepST (max 6.1) and 4.5 for NichePCA**; every other method is 0.98–1.0, on both machines. The records still carry `threads: 1`. Run times are already excluded, but the claim "same settings" and "one thread" is wrong for these 8 runs. | Add "except the reruns on the 125 GB server, where DeepST and NichePCA used several cores". |
| B3 | **supp:101** (S14 caption, written by make_supplement.py:209) | "DeepST: one seed on DLPFC, STARmap and MERFISH **and on Stereo-seq E10.5 E2S1 (memory)**" is stale. DeepST has 3 seeds on E10.5_E2S1 after the rerun, and `metrics.tex` shows 32 runs (20 + 3 + 9). | Drop the Stereo-seq clause. Also supp:17 could say "and were rerun". |
| B4 | **supp:76** (S9 caption) and `ranks.tex` lower block | "…which excludes the methods stopped at the memory cap" is stale. No method is excluded now (16 of 16, 24 of 24). The lower block duplicates the upper block and differs only by Monte-Carlo noise (BASS 0.49 vs 0.50, GraphST 1–10 vs 2–10). | Delete the lower block and the sentence. |
| B5 | **supp:91** (S12 caption) | "Noise repetitions were not run on the 18,408-bin Stereo-seq section" contradicts main.tex:322. Noise fits exist for 3 of the 10 embeddings (AnisoST, BANKSY ×2). | "…were run for only three of its embeddings." |
| B6 | **main.tex:322** and supp:91 ("about 30 min") | The 11 full-data fits on E10.5_E1S1 took 27.5–43.9 min (median 38.9 min; 7 of 11 above 37 min). | "about 40 min". |
| B7 | **main.tex:218** "only 3 comparisons (SpaceFlow, CCST and Spatial-MGCN) remained above zero" | The Bonferroni lower limit is the 0.156 % quantile of 5000 draws (about 8 draws). SpaceFlow's lower limit is +0.003; PCA's is −0.003 and DeepST's −0.004. Five re-bootstraps with other seeds: SpaceFlow −0.011, −0.006, −0.002, −0.006, −0.002 (never positive); PCA −0.002, +0.003, +0.006, −0.009, −0.001. Only CCST and Spatial-MGCN are stable. | Write "two to four of 16 depending on the resampling seed" or raise B to ≥ 50 000. Also relevant to the abstract-level claim "3 of 16". |

Minor notes (no action required):
- **BayesSpace verdict:** the BayesSpace "interval above zero" rests on 4 groups (three donors and breast cancer). The lower limit is +0.000 in S6 (re-bootstraps +0.001 to +0.005). It is consistently positive but only just. A rounded "+0.000" next to "baseline higher" in S6 may confuse readers.
- **Runner flip:** HiSTaR's flip in the runner analysis rests on a lower limit of +0.005 (main.tex:221–222). The statement is correct as worded.
- **S13 p-values:** S13 gives p = 0.240 (BANKSY λ=0.2) and 0.040 (Spatial-MGCN), against 0.241 and 0.039 in the macros. Cause: p is rounded to 4 digits before formatting in `paper_numbers_v2.json` (0.2405 → 0.240). Not used in the text.
- **Energy in S15:** it is a per-job mean (kWh sum over jobs without host), whereas time is a median. The header says only "per job".
- **GPU field:** `peak_gpu_mem_gb` of 9–11 GB appears in 5 host records (GraphST ×3, DeepST s0, MGCN s2) although `device` is `cpu`. It must be the whole-GPU reading of other users' jobs. It is not reported anywhere, but the field contradicts "its two GPUs were not used" if anyone reads the raw file.
- **Times of the five rerun methods:** their medians in S15 exclude the largest section, so they are biased low relative to CCST, whose median includes it. The caption states that run times of the reruns are excluded.

---

## C. Numbers and claims re-verified against the data (46)

| # | Claim (location) | Recomputed | OK |
|---|---|---|---|
| 1 | 24 sections = 12+3+5+1+3 (main:267) | JSON `ranking_sections` 24, 16 methods | ✓ |
| 2 | LD matched means 0.558/0.705/0.497/0.545/0.306 (209–210) | `means_robust` | ✓ |
| 3 | Best means: LD 0.558, BANKSY λ=0.8 0.740, BASS 0.582, BASS 0.624, SpaGCN 0.388 (211–213) | max over both protocols | ✓ |
| 4 | Brca and Stereo-seq per-dataset means, all 15 methods (macros) | Recomputed from raw runner records (latest per id, matched ARI): all equal to 4 decimals | ✓ |
| 5 | 8 of 16 better, 8 unresolved; both lists (214–217) | `category` in JSON | ✓ |
| 6 | 7 of 8 hold without development sections (215) | test_only ci95 lower > 0 for SpaGCN, SEDR, SpaceFlow, CCST, MGCN, DeepST, PCA; BayesSpace −0.019 | ✓ |
| 7 | BASS −0.002 (−0.059, 0.063); BANKSY λ=0.8 +0.024 (−0.020, 0.069) | JSON | ✓ |
| 8 | Bonferroni 3 (SpaceFlow, CCST, MGCN) (218) | `ci_bonf` lower 0.003, 0.015, 0.029 | ✓ (fragile, B7) |
| 9 | Ranking on 24 sections: BASS 0.50, LD 0.32, BANKSY λ=0.8 0.04 (219–220) | 0.498 / 0.323 / 0.044; independent re-bootstrap 0.491 / 0.322 / 0.043 | ✓ |
| 10 | 6 methods with rank 1 in 95 % interval (220) | BASS, LD, BANKSY λ=0.8, NichePCA, AnisoST, HiSTaR; re-bootstrap also 6 | ✓ |
| 11 | Ranks "LD 1–7", median 2 (macros rankLoLin/rankHiLin) | [1, 7] | ✓ |
| 12 | Runner analysis: 9 better, 7 unresolved, BASS 0.40, LD 0.49 (221–224) | runner JSON: 9 / 7, 0.402 / 0.489 | ✓ |
| 13 | Verdict change **only HiSTaR** (221–222) | Category differs from the primary analysis only for HiSTaR (unresolved to better, lower limit +0.005). All 15 others are identical | ✓ |
| 14 | Default clustering: 11 better, 5 unresolved, lists (224–226) | `standard` categories | ✓ |
| 15 | Expert-annotation analysis: 7 better, 9 unresolved, BASS 0.36, LD 0.37 (240–243) | expert JSON (18 sections, 5 groups) | ✓ |
| 16 | Comparators ahead: DLPFC 0, STARmap 1, MERFISH 1 (229–230) | per-dataset deltas < 0: none; BASS −0.011; BASS −0.085 | ✓ |
| 17 | **Breast cancer 13 of 16, Stereo-seq 11 of 15** (231–232) | Brca negatives: 13 (incl. SpaceFlow −0.001, MGCN −0.007). Stereo negatives: 11 (incl. HiSTaR −0.001). MGCN is now +0.017 on Stereo-seq | ✓ (S-I) |
| 18 | BASS 0.594 vs LD 0.587 on three brain datasets (231) | (0.484+0.716+0.582)/3; (0.558+0.705+0.497)/3 | ✓ |
| 19 | dBrain 0.172, dOther 0.023 (232–233) | 0.1717 / −0.0228 over 16 comparators (BayesSpace counted on the datasets it has) | ✓ |
| 20 | PCA vs LD 0.562 vs 0.545, 0.349 vs 0.306 (234–235) | `means_robust` | ✓ |
| 21 | Coarse classes 0.04–0.31, NichePCA and SpaceFlow first, LD 0.19 rank 11 of 14 (236–238) | brca_coarse.json: 0.041 / 0.308 / 0.300 / 0.186, rank 11 | ✓ |
| 22 | **Peak memory of the five reruns on E10.5_E1S1** (239–240): BASS 22, NichePCA 20, GraphST 12, MGCN 27, DeepST 28 | Max over seeds: 22.12 / 19.64 / 11.78 / 27.11 / 27.59 GB | ✓ numbers; ✗ "more than the cap" for GraphST (B1) |
| 23 | **17 rerun jobs** (163) | 15 on E10.5_E1S1 (5 methods × 3 seeds) + 2 on E10.5_E2S1 (DeepST s1, s2) = 17 latest host records; all `ok`. No `error` or `oom` record is the newest for any id | ✓ |
| 24 | **DeepST seeds on E10.5_E2S1** (158–163, supp:17) | seeds 0 (original), 1, 2 (rerun, 12.07 GB peak, so above the cap as claimed) | ✓ |
| 25 | **Timing excluding host-tagged runs** (255–257, S15) | Medians from non-host ok records match all 17 `timeMed*` macros (e.g. BASS 744 n=69, DeepST 920 n=27, GraphST 1250, MGCN 1515, CCST 2789 n=71) | ✓ |
| 26 | Baselines and BANKSY < 30 s; CCST ≈ 46 min; CCST > 5 h on the largest section (255–257) | 23–26 s; 2789 s = 46.5 min; 18 856 and 19 578 s (5.2 and 5.4 h) | ✓ |
| 27 | S15 peak memory for all methods (resources.tex) | Max `peak_rss_gb` over all ok records incl. host: DeepST 27.6, MGCN 27.1, BASS 22.1, NichePCA 19.6, BayesSpace 12.5, GraphST 11.8, SEDR 9.4, SpaGCN 8.5, CCST 5.5 … | ✓ |
| 28 | K±1: 0.06 / 0.09 / 0.49 (248–249) | 0.0609 / 0.0928 / 0.4853 | ✓ |
| 29 | **K-sensitivity**: 336 embeddings, BIC at the edge in 329, ρ = 0.91 (249–251) | 336; 329; Spearman 0.9077 | ✓ |
| 30 | BIC: BANKSY λ=0.8 and NichePCA ahead of LD 0.462, LD rank 3 (251) | 0.4865 / 0.4673 / 0.4616; rank 3 | ✓ |
| 31 | Seed SD: HiSTaR 0.047 / 0.180; baselines 0.012–0.054 (254–255) | seeds.tex S10 | ✓ |
| 32 | **Lottery**: 336 embeddings, 14 methods, mean range 0.16, max 0.60 (SEDR, 151672), LD 0.18, SpaceFlow 0.09, BANKSY λ=0.8 0.22, oracle 0.07 (293–297) | 0.1638 / 0.5999 SEDR 151672 / 0.182 / 0.089 / 0.215 / 0.0713 | ✓ |
| 33 | Best-likelihood better for 10, worse for 3 of 14 (327–328) | ±0.005 on per-method mean: 10 up, 3 down (CCST, DeepST, MGCN), 1 neutral | ✓ |
| 34 | Gain counts 8 / 5 of 14; HiSTaR +0.042 (p=0.006), NichePCA +0.078 (0.018), SEDR −0.077 (0.074), CCST −0.059 (0.010) (329–332) | Recomputed Wilcoxon on 24 sections: identical | ✓ |
| 35 | ρ medians DLPFC 0.38, STARmap 0.41, MERFISH −0.11 (negative for 10 of 14), breast cancer −0.13, Stereo-seq 0.06 (332–335) | 0.376 / 0.409 / −0.113 (10) / −0.126 / 0.056 | ✓ |
| 36 | **R mclust** (provisional): 290 embeddings with n > 2000, mean 0.11, max 0.46, > 0.1 for 48 % (319–320) | 332 complete embeddings; big 290: 0.1134 / 0.4553 / 48.3 % | ✓ |
| 37 | mclust noise 0.08 mean, max 0.59; fits outside the seeded range 16 %; "three embeddings" on the largest section (322–324) | 0.0829 / 0.5908 over 325; 47/290 = 16.2 %; noise fits exist for 3 of 10 on E10.5_E1S1 | ✓ |
| 38 | mclust per dataset: brca 0.07, Stereo-seq 0.07, DLPFC 0.13, MERFISH 0.11, STARmap 0.00; STARmap n ≤ 1088 (macros, 320–321) | 0.069 / 0.073 / 0.128 / 0.108 / 0.000; 1088 | ✓ |
| 39 | MGCN leak 0.551/0.687/0.221 vs 0.418/0.303/0.182; 0.147 over 20 sections; brca 0.03 over 3 seeds (362–367) | (12·0.133+3·0.384+5·0.039)/20 = 0.147; macros match files | ✓ |
| 40 | HiSTaR 0.509 / 0.491 / 0.454–0.525 / 0.449 / 0.487 (350–353) | `check_paper_numbers.py` | ✓ |
| 41 | AnisoST MERFISH 0.363 vs 0.497; boundary 0.025, 9/12, p=0.034 (258–259) | `check_paper_numbers.py` | ✓ |
| 42 | NMI vs ARI Spearman 0.97 (187) | 0.9675 from ari.tex and nmi.tex matched columns | ✓ |
| 43 | Coverage table S23: seeds in published pipelines (LD/AnisoST/PCA/BANKSY/HiSTaR/SpaGCN/SEDR/SpaceFlow/NichePCA/DeepST 3; STAGATE, CCST, MGCN, BASS 1; BayesSpace 1; GraphST 1–3) (main:157, 410) | Matches the coverage text and the runner (checked the runner side) | ✓ |
| 44 | 13 published methods; 11 benchmarked repositories + 3 screened (368) | 13 in `nMethodsPub`; audit.tex has 11 + SPARK, SpatialPCA, conST | ✓ |
| 45 | DeepST SD 0.022 on Stereo-seq (S10) | 3/3/3/3/3 seeds, consistent with 3 seeds on each section | ✓ |
| 46 | `Runs` column S14: 72 for most, CCST 71, BayesSpace 13, DeepST 32 | Counts of latest ok records | ✓ |

---

## D. Provisional items (not errors)

R mclust for four new embeddings of E10.5_E1S1 (GraphST, NichePCA, Spatial-MGCN, DeepST) is still running (`scripts/mclust_seed.R`, lock file `mclust_seed_g6.csv.lock_stereo_E10.5_E1S1_graphst`). When it finishes and `paper_v2.py`, `make_supplement.py` and the PDFs are regenerated, these will change:
- `mcsN` 332 to 336 (it now differs from `lotN` and `kN`, 336).
- `mcsNBig` 290 to 294.
- `mcsSeedMeanBig`, `mcsSeedMax`, `mcsSeedGt` (48), `mcsFullOutside` (16), the per-dataset Stereo-seq mean (0.07) and `mcsStarmapMaxN`.
- S12 and S23 (the "23/24" cells for GraphST, NichePCA, MGCN and DeepST), and Fig 3B.

Probably unchanged: `mcsJitN` (325) and "only for three embeddings" (l.322), unless noise runs are added.

After the final regeneration, re-run `check_paper_numbers.py`. I would also add an assertion that `mcsN == lotN` so that a partial mclust run cannot be published.
