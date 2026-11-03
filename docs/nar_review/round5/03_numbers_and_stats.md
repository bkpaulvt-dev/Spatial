# 03 (round 5): Numbers and statistics audit

**Reviewer role:** statistical referee, final manuscript (`paper/main.pdf`/`.tex` and `paper/supplementary.pdf`/`.tex` of 3 Nov 22:11; `results/paper_macros.tex` 04:00; stats JSONs 2 Nov 23:39–23:45).

## Verdict

**Every quantitative claim I recomputed from the raw result files reproduces. No conclusion is affected.** I found no wrong main-text number. I found one stale methods statement that contradicts the main text (E1), two undisclosed or loosely worded statistical details (E2, E3) and a handful of cosmetic items. The round-4 errors B1–B7 are fixed: B1 (peak memory vs cap), B2 (threads), B3–B6 (stale captions) and B7 (Bonferroni fragility, now flagged in the text).

Order of the files is consistent: data, then script, then JSON, then macros, then supplement tables (03:59), then `main.tex`, then PDFs. Nothing is stale in that sense. `check_paper_numbers.py` gives 7/7 claims and 122/122 macros defined.

### How the checks were done
- Read-only Python in the scratchpad. The data-assembly part of `scripts/stats_cluster_aware.py` (everything before `def hboot`) was executed in memory.
- My own vectorised hierarchical bootstrap was run **once** with B = 20000 and a different seed (777). It covers 16 comparisons, the test-only (without development sections) variant and the ranking.
- Everything else (lottery, K, mclust, memory, time, epoch, Wilcoxon) was recomputed directly from `clustering_lottery.jsonl`, `k_sensitivity.jsonl`, `mclust_seed_g*.csv`, `benchmark_runs.jsonl`, `new_methods.jsonl` and `anisost_boundary.jsonl`.
- Only resolved points from round 4 were skipped. Round-4 points that are still open are listed in section D.

## A. Bootstrap, margin, Bonferroni and dedup logic

| Item | Finding |
|---|---|
| Hierarchical bootstrap | Correct as written. Groups are drawn with replacement, then sections within each drawn group, fresh for every occurrence. The estimate is the equal-weight mean of group means, with percentile intervals. My independent implementation reproduces the stored intervals to within Monte-Carlo noise of ±0.003 or less. |
| Estimand | 7 groups (3 donors + 4 single-study datasets). Brca is one section, so it contributes no within-group variance. BayesSpace rests on 4 groups (3 donors + brca) and 13 sections. |
| Equivalence margin 0.03 | Implemented as 90 % interval inside ±0.03, which is TOST-like. No comparator qualifies, and none could: the narrowest 90 % interval is about 0.08 wide. The text correctly blames interval width. The stated rationale ("about the seed SD") fits the baselines' per-section SD of 0.012–0.054. HiSTaR is 0.047 on DLPFC and 0.18 on STARmap. The SD is that of a single section, while the margin applies to a group-averaged difference. |
| Bonferroni | Level 0.05/16, so each tail is the 0.156 % quantile. This is correct. The code uses a separate 20000-draw bootstrap, about 31 draws per tail. Stored intervals: CCST (+0.020), Spatial-MGCN (+0.023) and PCA (+0.005) are above zero. SpaceFlow is at −0.004. My re-run: CCST +0.016, MGCN +0.026, PCA +0.000, SpaceFlow −0.002. The membership of the list therefore depends on the seed for PCA. The text already says so for PCA, and "3" is the stored result. |
| Dedup, `benchmark_runs.jsonl` | The newest record per id is the last line of the file, not a timestamp. All three consumers (stats, paper_v2, make_supplement) agree. 1159 lines give 1124 ids, and all 1124 newest records are `ok`. 17 ids are host-tagged `deepmed2`, plus 3 earlier host-tagged GraphST `error` records, which gives the 20 records for 17 jobs quoted in main:164. |
| Host exclusion | Time and energy are `None` for host-tagged records, and peak memory keeps them. Medians reproduce: n = 69 for BASS, GraphST, NichePCA and Spatial-MGCN, 27 for DeepST and 71 for CCST. |
| Superseded non-host records | 6 GraphST Stereo-seq ids (E9.5_E1S1 and E10.5_E2S1, seeds 0–2) have two `ok` records. The older ones are slower (5185 s against 1723 s) and differ in ARI (e.g. 0.396 against 0.383). `scripts/rerun_graphst_stereo.sh` shows the newer ones use `datatype='Stereo'`, and the old analyses were purged. The newest-record rule is the right one here, and accuracy and timing use only the new runs. |
| `new_methods.jsonl` dedup | The script filters `status == ok` and then keeps the last. The rule differs from the runner rule: if an error record were newest, an older ok would survive. In the data the 9 error/ok pairs all have the ok record last, so there is no effect today. |
| Assembled data | 1906 rows with no duplicated (dataset, method, slice, seed), so seed means are not double-counted. mclust CSVs contain 80 duplicated rows across g-files (ARI difference 0.0). All consumers deduplicate them (336 embeddings, 10 seeds and 1 full fit each). |

## B. Numbers independently recomputed (all match unless marked)

| # | Claim (location) | Recomputed | Result |
|---|---|---|---|
| 1 | 24 sections = 12+3+5+1+3; 7 groups; 6 development sections (4+1+1) | `datasets.yaml` | ✓ |
| 2 | LD matched means 0.558 / 0.705 / 0.497 / 0.545 / 0.306 (main:209) | 0.558 / 0.705 / 0.497 / 0.5446 / 0.3061 | ✓ |
| 3 | Best dataset means: LD 0.558, BANKSY λ=0.8 0.740 (default), BASS 0.582, BASS 0.624, SpaGCN 0.388 | Max over both protocols and all methods | ✓ |
| 4 | 8 of 16 better, 8 unresolved; both lists and the order (main:214) | Mine at B = 20000: same 8 better. Lower limits: SpaGCN +0.025, SEDR +0.006, SpaceFlow +0.041, CCST +0.070, MGCN +0.071, DeepST +0.029, PCA +0.048, BayesSpace +0.002 | ✓ |
| 5 | Without development sections 6 of 8 hold (`nRobBetterTest`=6) | Lower limits above zero for SpaGCN, SpaceFlow, CCST, MGCN, DeepST and PCA. SEDR (−0.002) and BayesSpace (−0.019) do not | ✓ |
| 6 | BASS Δ −0.002 (−0.060, +0.065); BANKSY λ=0.8 +0.024 (−0.020, +0.069) | Mine: −0.002 (−0.058, +0.064); +0.024 (−0.021, +0.070) | ✓ |
| 7 | No comparator equivalent | Narrowest 90 % interval is BANKSY λ=0.8, (−0.013, +0.061) | ✓ |
| 8 | Bonferroni: 3 (PCA, CCST, MGCN), PCA borderline | See section A. Stored JSON gives exactly these three. | ✓ (seed-dependent for PCA) |
| 9 | P(rank 1) on 24 sections: BASS 0.49, LD 0.32, BANKSY λ=0.8 0.04 (main:220) | 0.488 / 0.326 / 0.044. JSON 0.495 / 0.316 / 0.043 | ✓ |
| 10 | 6 methods with rank 1 in the 95 % interval | 6 (BASS, LD, BANKSY λ=0.8, NichePCA, AnisoST, HiSTaR). LD rank 1–7, median 2 | ✓ |
| 11 | Runner analysis: 10 better, 6 unresolved; flip only HiSTaR and STAGATE; BASS 0.41, LD 0.49 | Runner JSON categories, 0.414 / 0.489 | ✓ |
| 12 | Default clustering: 11 better, 5 unresolved (list) | JSON | ✓ |
| 13 | Expert-annotation analysis: 7 / 9, BASS 0.37, LD 0.37; SEDR is the flip | JSON (18 sections, 5 groups), 0.367 / 0.373 | ✓ |
| 14 | Comparators ahead: DLPFC 0, STARmap 1, MERFISH 1 (BASS), brca 13 of 16, Stereo-seq 11 of 15 | Recomputed from matched dataset means | ✓ |
| 15 | BASS 0.594 against LD 0.587 on the 3 brain datasets | 0.5943 / 0.5868 | ✓ |
| 16 | dBrain 0.172, dOther −0.023 | 0.1717 / −0.0229 | ✓ |
| 17 | PCA 0.562 / 0.349 against LD 0.545 / 0.306 | 0.5616 / 0.3487 | ✓ |
| 18 | Brca coarse: 0.04–0.31, NichePCA and SpaceFlow first, LD 0.19, rank 11 of 14 | 0.0413 / 0.3080 / 0.1855, rank 11, n = 14 | ✓ |
| 19 | Peak memory on E10.5_E1S1: BASS 22, NichePCA 20, GraphST 12, MGCN 27, DeepST 28 GB | Max over newest ok records: 22.12 / 19.64 / 11.78 / 27.11 / 27.59 | ✓ |
| 20 | 17 rerun jobs; DeepST on E2S1 0.35 / 0.40 / 0.40; 20 records for 17 jobs | 0.347 / 0.403 / 0.405. 17 host `ok` ids, 20 host records | ✓ |
| 21 | Median times: BASS 744, DeepST 920, GraphST 1250, MGCN 1515, CCST 2789 (46 min); CCST > 5 h on the largest section; baselines < 30 s | 744 / 920 / 1250 / 1515 / 2789 s. CCST 18 856 s and 19 578 s. Baselines 23–26 s | ✓ |
| 22 | Peak memory of all methods (S16); BayesSpace 12.5 GB on DLPFC | Max over all ok records incl. host | ✓ |
| 23 | CPU/wall of host runs: DeepST 3.8 (max 6.1), NichePCA 4.5; the others 0.98–1.0 | 3.80 / 6.1 / 4.52; BASS 0.98, GraphST 0.99, MGCN 1.00 | ✓ |
| 24 | K±1: 0.06 average, 0.09 larger direction, 0.49 maximum | 0.0609 / 0.0928 / 0.4853 | ✓ |
| 25 | BIC at the largest K in 329 of 336; ρ = 0.91; BANKSY λ=0.8 and NichePCA ahead of LD (0.462, rank 3) | 329 / 336; 0.9077; 0.487, 0.467 > 0.4616, rank 3 | ✓ |
| 26 | Lottery: 336 embeddings, 14 methods, mean range 0.16, max 0.60 (SEDR, DLPFC 151672) | 0.1638 / 0.5999 SEDR 151672 | ✓ |
| 27 | Lottery per method: LD 0.18, SpaceFlow 0.09, BANKSY λ=0.8 0.22; oracle 0.07 | 0.182 / 0.089 / 0.215 / 0.0713 | ✓ |
| 28 | Best-likelihood fit better for 10 of 14 and worse for 3 (±0.005 threshold) | 10 up, 3 down (CCST, DeepST, MGCN), 1 neutral (BANKSY λ=0.8 +0.0048). SpaceFlow is +0.0054, barely above | ✓ |
| 29 | Matched-clustering gain: 8 up / 5 down of 14; HiSTaR +0.042 (p=0.006), NichePCA +0.078 (0.018), SEDR −0.077 (0.074), CCST −0.059 (0.010) | Recomputed Wilcoxon on 24 sections: identical | ✓ |
| 30 | Median ρ: DLPFC 0.38, STARmap 0.41, MERFISH −0.11 (negative for 10 of 14), brca −0.13, Stereo-seq 0.06 | 0.376 / 0.409 / −0.113 (10) / −0.126 / 0.056 | ✓ |
| 31 | R mclust: 294 embeddings above 2000, mean 0.11, max 0.46, range above 0.1 for 48 % | 294 / 0.1129 / 0.4553 / 47.96 % | ✓ |
| 32 | Per dataset 0.07 / 0.07 / 0.13 / 0.11 / 0.00; STARmap n ≤ 1088 | 0.069 / 0.074 / 0.128 / 0.108 / 0.000; 1088 | ✓ |
| 33 | Noise: 0.08 mean, max 0.59, over 325 embeddings; 3 embeddings on the 18,408-bin section; full fit about 38 min | 0.0829 / 0.5908 / 325; 3; median 38.5 min (27.4–43.9) | ✓ |
| 34 | Full-data fit outside the seeded range: 16 % | 47 / 294 = 15.99 % | ✓ |
| 35 | Seed SD: HiSTaR 0.047 / 0.180; baselines 0.012–0.054 | 0.0474 / 0.1803; 0.0120–0.0538 | ✓ |
| 36 | AnisoST boundary: +0.025, 9 of 12, p = 0.034 | 0.0246 / 9 / 0.0342 | ✓ |
| 37 | Label epoch: 0.551 / 0.687 / 0.221 against 0.418 / 0.303 / 0.182; inflation 0.147 over 20 sections; STARmap 0.38; brca 0.03 over 3 seeds | 0.5514 / 0.6867 / 0.2209; 0.1473; 0.3837; 0.0304 (n = 3). S21 +0.133 / +0.384 / +0.039 | ✓ |
| 38 | MOSTA Cavity: 15–24 % of bins, count ratio 0.5–0.9 | 0.149–0.237; 0.50 / 0.87 / 0.47 | ✓ |
| 39 | HiSTaR 0.509 / 0.491 / 0.454–0.525 / 0.449 / 0.487 | `check_paper_numbers.py` | ✓ |
| 40 | NMI against ARI Spearman 0.97 | 0.9675 including BayesSpace (see E5) | ✓ (caveat) |
| 41 | Tables, captions and text agree: 16 = 8+8 = 11+5 = 7+9 = 10+6; 336 = 14×24 embeddings; 294 = 14×21; `Runs` 72 / 71 (CCST) / 13 (BayesSpace) / 32 (DeepST); coverage table seeds | Checked in S5–S10, S12, S13, S15, S23 and the text | ✓ |

## C. Errors and stale statements, ranked by severity

None changes a result.

**E1 (medium, factual contradiction between supplement and main text).**
- Location: `paper/supplementary.tex` line 32 (Supplementary Note 6, produced by `scripts/make_supplement.py` line 311). It says the 17 jobs were rerun "with the same code and settings and the same one-thread limit on a server with 125 GB RAM and 20 threads".
- Main.tex lines 163–164, 239–240 and 426 correctly say that DeepST and NichePCA used several cores on this server. CPU/wall is 3.8 (max 6.1) for DeepST and 4.5 for NichePCA, and `peak_rss_gb` is not affected by this.
- The note was not updated when B2 was fixed in the main text.
- Fix: replace "and the same one-thread limit" with "(thread count not restricted: DeepST and NichePCA used several cores, CPU time about 4–6 times wall time; the other three methods used one)". Edit `make_supplement.py` line 311 and regenerate.

**E2 (low–medium, undisclosed procedure).**
- Location: main.tex line 197 and line 199, `supplementary.tex` line 26 (Note 4). They state 5000 resamples for the intervals.
- The Bonferroni intervals (S6–S9, stats_*.tex) come from a separate 20000-resample bootstrap with its own random stream (`stats_cluster_aware.py` line 115). Nothing in the manuscript says so.
- Note 4 also says ranks and P(rank 1) "come from the same resamples". They come from a separate loop of 5000 resamples with the same design. The ranking and the interval for the same comparison are therefore not tied to one resample set.
- Fix: in Note 4 write "5000 resamples for the 95 % and 90 % intervals, ranks and P(rank 1) (each from its own loop of the same design); 20000 resamples for the Bonferroni intervals, whose tails sit at the 0.16 % quantile".

**E3 (low, fragile statement correctly hedged but incomplete).**
- Location: main.tex line 219 and 331 of the PDF text: "of these, PCA had a lower limit within 0.01 of zero and could change with the resampling seed".
- My re-bootstrap gives PCA +0.000 and SpaceFlow −0.002, against +0.005 and −0.004 stored. SpaceFlow lies just as near the boundary on the other side, so the list can have 2 to 4 members.
- Also, with 7 groups a percentile interval at the 0.16 % quantile is set by the few resamples that draw one or two groups only. It is not a calibrated Bonferroni interval, and it is labelled "a check", which is right.
- Fix (optional): "(PCA, and just outside it SpaceFlow, had limits within 0.01 of zero ...)" or report the seed range "two to four".

**E4 (low, presentation).** Table S6 prints BayesSpace as "+0.000, +0.179 ... baseline higher". The unrounded limit is +0.0004 (JSON rounds to 0.0). My re-run gives +0.002 and round-4 re-runs gave +0.001 to +0.005. The classification is right but rests on 4 groups. Fix: footnote "limit +0.0004" or print four decimals for that row. The count "8 of 16" depends on this one limit, and the text already says "interval above zero".

**E5 (low, trivial).**
- (a) The "NMI gives nearly identical ranking, ρ = 0.97" value (main:187) includes BayesSpace, whose mean covers only DLPFC and breast cancer. Without it ρ = 0.964 ("0.96"). Either way the wording holds.
- (b) "BANKSY λ=0.8 in 0.04" is given as the third place in P(rank 1). S10 prints NichePCA 0.04 and AnisoST 0.04 as well. The order of the three is within noise (mine 0.044 / 0.037 / 0.035). Fix: "about 0.04 each for BANKSY λ=0.8, NichePCA and AnisoST".

**E6 (low, carried over from round 4, unchanged).**
- S-I: "13 of 16 comparators were ahead on breast cancer and 11 of 15 on Stereo-seq" (main:231–232) counts differences down to −0.001 (SpaceFlow −0.0012, Spatial-MGCN −0.0074, HiSTaR −0.0009). Only 11 and 10 are ahead by more than 0.01. The sentence "the methods were close to each other" covers it. A short parenthesis "(by more than 0.01: 11 and 10)" would remove the objection.
- S-C/S-E/S-F remain as noted in round 4: no small-group check (7 groups), sections treated as independent in the Wilcoxon tests, seed variance not propagated.
- S-H (range over 20 fits compared with differences of means) is unchanged.
- S-J: one embedding with constant ARI (SpaceFlow 151670) gives ρ = NaN and is silently dropped from the median.

**E7 (cosmetic, code only).**
- `stats_cluster_aware.py` line 6 ("fixed before looking"), the comment "methods with all 20 sections" at the ranking function and the dead `OWN_KEY` (line 36) are still stale (N9).
- The `new_methods.jsonl` dedup filters `ok` before keeping the last record (differs from the runner rule, no effect today).
- Table S11 shows GraphST "3" seeds on MERFISH in the published pipeline, while 3 of the 5 sections have 2 (S23 correctly says 1–3).
- Optional additions to `check_paper_numbers.py`: assert `mcsN == lotN == kN` (336 now), assert that the stored Bonferroni list equals the macro, and check the 20000 in `stats_cluster_aware.py`.

## D. What was not changed or needs no action

- The main-text description of the mclust, lottery, K and memory results is now complete (336 embeddings each, 294 big).
- The main text and supplement agree on the sizes: 17 jobs, 20 records, 12 GB cap, 12.5 GB BayesSpace on DLPFC.
- Placeholders (`\todo`: authors, URL, DOI, funding, CRediT) remain in `main.tex` and are outside the statistical audit.
