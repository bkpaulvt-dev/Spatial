# NAR review, round 4 (final), report 02: benchmark design

**Reviewer focus:** benchmarking methodology (Weber et al. 2019, Mangul et al. 2019, Sonrel et al. 2023).

**Read:** my round-3 report, `paper/main.tex`, `results/paper_macros.tex`, `paper/supplementary.tex`, `results/supp/*.tex`, the three `stats_cluster_aware*.json` files, `scripts/stats_cluster_aware.py`, `results/coverage_matrix.md`, `docs/figures/nar_fig2_accuracy.png`. I also checked `results/benchmark_runs.jsonl` and `results/mclust_seed_summary.csv` with read-only Python. I did not open Fig. 1, Figs. 3-5 or the Fig. 1 caption fix.

## Recommendation: minor revision

The rerun is handled openly, and the headline conclusions follow from the evidence. The ranking now uses all 16 methods on all 24 sections, with two sensitivity analyses. What is left is a set of text corrections, a few stale captions and deliverables the authors have not yet supplied (URL/DOI, `\todo`s). One methodological gap is the lack of any cross-host equivalence check for the rerun jobs; I treat it as a disclosure issue, not a blocker.

---

## A. Handling of the rerun (new since round 3)

**Transparent: yes, largely.**
- The main text (Methods, Limitations), Supplementary Note 6 and the Table S15 caption all state:
  - the 17 jobs,
  - the 125 GB CPU-only server with a different processor,
  - that run times and energy are excluded from the timing tables,
  - the GraphST mclust wrapper and its check on two sections.
- Records carry `host=deepmed2`. `results/benchmark_runs_bigmem.jsonl` holds the 20 rerun records, and `environment.deepmed2.yml` is provided.

**Fair: mostly, with these exceptions.**

1. **Primary analysis is largely insulated from the wrapper.** The matched clustering (sklearn GMM) does not call R mclust. Only the default-clustering analyses (Tables S3, S5, S13) depend on the wrapped GraphST call.
   - The wrapper check covers two sections only. The paper does not say whether they have more than 2000 observations, which is where mclust's random-subset initialisation matters.
   - The only real test would be GraphST on E10.5_E1S1 with a fixed R seed against the original function. That could not run on the 15 GB machine, so "identical labels" is weaker evidence for that section.

2. **No cross-host check for the torch methods.**
   - The paper says "same code and settings". Note 6 says "20 threads", while the runner policy is one CPU thread. State how many threads each rerun job used.
   - Only the 20-job set is available. Nothing compares the same job on both hosts, for example a section that fits under the cap (E2S1) rerun on deepmed2 for one method.
   - The one natural overlap is DeepST on E10.5_E2S1. Seed 0 is from the old machine; seeds 1 and 2 are from deepmed2.

   | DeepST on E10.5_E2S1 | seed 0 (old host) | seeds 1 and 2 (deepmed2) |
   |---|---|---|
   | ARI, own clustering | 0.347 | 0.403 and 0.405 |
   | ARI, matched clustering | 0.336 | 0.326 and 0.350 |

   - With n = 1 against n = 2 the own-clustering gap of 0.056 cannot be separated into host effect and seed effect. The matched value is consistent across hosts, which is reassuring for the primary analysis.
   - The paper should state that the E2S1 DeepST mean mixes hosts. The seed SD for DeepST on Stereo-seq (Table S10, 0.022) also mixes hosts.
   - Per-section DeepST ARI differs between hosts or seeds by up to 0.05. Compared with differences of 0.03 to 0.07 between methods on Stereo-seq, this is not negligible for the Stereo-seq column.

3. **GraphST memory figure.**
   - The paper says GraphST "needed 12 GB, more than the cap".
   - In `benchmark_runs.jsonl`, the original kills were at 12.0 to 12.2 GB. The successful rerun peaked at 11.7 to 11.8 GB, which is below the cap (Table S15 lists 11.8).
   - GraphST's first three rerun attempts failed in mclust (peak 13.2 GB) and remain in the data as `error` records. That explains the 20 records against the 17 "jobs".
   - Say that GraphST was at the margin, that its memory differs by stack, and that there were failed first attempts. Memory is stack-dependent, so peak-memory comparisons across hosts are indicative only. This is already partly stated, but "more than the cap" is not accurate for GraphST.

4. **Cap bias.** Under a fixed cap, some jobs were killed and some were not. The reruns of those jobs on 125 GB do not cause a bias in accuracy as such. Table S15 now lists mixed-host peak memory, so peak memory for BASS, NichePCA, Spatial-MGCN and DeepST comes from one host and from the larger section. This is disclosed.

**Net.** The decision to complete the ranking is sound: the previous complete-case rule lost the Stereo-seq section on which the five methods differ. P(rank 1) moved little (BASS 0.49 to 0.50, linear diffusion 0.29 to 0.32), so the conclusion is stable. I do not require a rerun. I do require:
- a threads statement;
- one sentence that host and seed are confounded for DeepST on E2S1;
- the GraphST memory correction.

---

## B. Check of the specific statements

**Tissue dependence: accurate, with one caveat.**
- Verified from `means_robust` (matched clustering): linear diffusion is beaten by 0 of 16 comparators on DLPFC, 1 of 15 on STARmap, 1 of 15 on MERFISH, 13 of 16 on breast cancer and 11 of 15 on Stereo-seq. These match the macros.
- Caveat: the "non-brain" side is n = 1 group (breast cancer, one section) and n = 1 group (Stereo-seq, three sections of one study). The statement is a descriptive pattern, not an inferred interaction. The paper does say that no method × tissue model was fitted and that the explanation was "not tested". Keep it.
- "Slightly ahead": the mean gap is 0.023 across comparators, but individual differences reach -0.08 (BASS on breast cancer) and -0.07 (NichePCA). "Slightly" is acceptable for most methods.

**BASS against linear diffusion: accurate in the primary analysis, but fragile.**
- The primary analysis gives BASS 0.50 and linear diffusion 0.32 (Table S9). The abstract's "BASS and the baseline were the most likely to rank first" is accurate.
- The runner analysis reverses the order (0.40 against 0.49), and the expert-only analysis ties them (0.36 against 0.37).
- The Discussion says "BASS ranked first more often (0.50 against 0.32)". That is true only in the primary analysis. Give the three values or say that the order depends on the analysis.
- Their mean difference is 0.00 (BASS, Δ = -0.002, interval -0.06 to 0.06), and both have median rank 2. This is a tie, not a lead for BASS.
- Provenance: the MERFISH and STARmap labels come with the BASS analyses, and MERFISH is kept in the "expert" subset. The Limitations disclose this, but Supplementary Table S8 and the Results text call this subset "expert annotation" (MERFISH provenance conflicts with the claim). Say that the expert subset still contains MERFISH, where BASS has a provenance advantage.

**PCA ahead of smoothing on breast cancer and embryo: stated more strongly than the evidence.**
- The numbers are 0.562 against 0.545 (breast cancer, n = 1 section) and 0.349 against 0.306 (Stereo-seq, 3 sections).
- A 0.017 gap on one section is well inside the clustering variance the paper itself reports (mean range of 20 single starts is 0.14 for PCA and 0.18 for linear diffusion; seed SD about 0.02). The Stereo-seq gap of 0.043 is on three sections with no interval.
- The Discussion's "smoothing gave no gain over PCA alone" and "smoothing did not help on these tissues" should be softened to "was not better than". Report per-section PCA minus linear diffusion for the three Stereo-seq sections, or the seed SD next to the gap.
- The abstract's "including PCA without smoothing, were slightly ahead" is acceptable only with that caveat; "slightly" does the work.

**Runner-analysis verdict change (HiSTaR): accurate.**
- Verified: the runner analysis has 9 baseline-higher comparisons and 7 unresolved, against 8 and 8; the only change is HiSTaR (interval 0.005 to 0.120). The main text now names HiSTaR (`listRunnerFlip`).
- The HiSTaR margin is marginal (lower bound 0.005; the test-only interval spans zero, -0.003); say it is a borderline verdict.
- The same statement is missing for the expert-only analysis. It also gives "the same picture", but SEDR moves from baseline-higher to unresolved (interval -0.036 to 0.212), and the P(rank 1) order of BASS and linear diffusion reverses. Name SEDR.
- BayesSpace is borderline in the primary analysis (interval 0.000 to 0.177 as stored). It is also computed on four groups only (three DLPFC donors and breast cancer), a different estimand from the other 15 comparisons, and unresolved without the development sections. Flag it in the count, or treat it separately.

**Counts.**
- "8 of 16" includes PCA and AnisoST (the authors' own ablations). Over the 14 published entries (13 methods with BANKSY at two settings) the count is 7 baseline-higher and 7 unresolved. I asked for this in round 3 and the paper still does not give it. This is a one-line fix.
- Bonferroni: 3 of 16 (SpaceFlow, CCST, Spatial-MGCN) remain. Verified in the JSON. Supplementary Note 4 now says Bonferroni intervals are given. The round-3 contradiction is resolved.

**Do the conclusions follow?**
- The robustness conclusions (clustering step variance, R mclust seed dependence, label-selected epochs) do not depend on the ranking and are well supported.
- The accuracy conclusion ("a training-free baseline is competitive with learned methods on brain tissue, not elsewhere") is supported as a descriptive statement. The inferential strength is limited by 7 groups and 5 of them brain, which the paper says.

---

## C. Round-3 report: point by point

### Major points

| # | Point | Status | Evidence |
|---|---|---|---|
| M1 | Ranking over all methods | **Resolved** | 16 methods, 24 sections; BASS 0.50, linear diffusion 0.32. |
| M1 | Tissue dependence | **Resolved** | Per-dataset counts, brain vs other, PCA > smoothing reported; "not tested" explanation. |
| M1 | Still pooled | **Partly** | Abstract: lead "came from brain tissue", but it still gives the pooled count without "(5 of 7 groups brain)". The Methods do say five of seven groups are brain. No per-dataset intervals. Acceptable. |
| M1 | Discussion "as likely to rank first" | **Resolved** | Now "BASS ranked first more often (0.50 against 0.32)". But now the opposite problem (see B): analysis-dependent. |
| M2 | Runner as sensitivity analysis | **Resolved** | Table S7; HiSTaR verdict change now named. |
| M2 | DeepST seed count in the runner | **Partly** | `coverage_matrix.md` now says "24/24 / 1-3", which is correct. The Table S14 caption says one seed on DLPFC, STARmap, MERFISH and E2S1 (memory); but E2S1 now has three seeds (seed 0 old host, seeds 1 and 2 rerun), so that part is stale. The Table S7 caption does not mention it. |
| M3 | Memory-cap handling | **Resolved** | Rerun described; reruns disclosed; GraphST remark (A.3) is the only fix. |
| M3 | Retry policy for DLPFC kills | **Not resolved** | I found no sentence on superseded error records in Note 6. |
| M3 | GraphST failure explanation | **Resolved by the rerun** | It now has results; the reason for the memory use is not given, minor. |
| M4 | Provenance sensitivity | **Resolved** | Expert-only analysis (Table S8), with the caveat on MERFISH above. `PROTOCOL.md` has a "superseded for the paper" note. |
| M4 | `datasets.yaml` labels | **Not checked** | Not re-read this round. |
| M5 | Scope in abstract | **Partly** | The abstract now lists four technologies and three tissues, and says that the lead comes from brain. It does not say "single sections, K given, up to 18k observations, one non-brain section per technology". The Limitations are complete. Acceptable but I would still add one clause. |
| M6 | Method selection criterion | **Partly** | One sentence in Methods; the reason SpatialPCA and conST were not benchmarked is in the Table S21 caption only ("screened but not benchmarked"), not given. |
| M6 | Reproducibility files | **Partly** | Environment files now exist (`environment.yml`, `requirements-lock.txt`, R `sessionInfo`, `environment.deepmed2.yml`). Containers declined by design. The GitHub URL and Zenodo DOI remain `\todo`. Declared as the authors' deliverable; required at acceptance. |
| M6 | Script docstring | **Not resolved** | `stats_cluster_aware.py` still says "margin fixed before looking" and "methods with all 20 sections". The paper calls the analysis exploratory. Will be public. |
| M7 | Multiplicity | **Resolved** | Note 4 consistent. |
| M7 | Development sections | **Resolved** | |
| M7 | Equivalence margin | **Partly** | The paper says "the intervals were too wide to show equivalence". The margin is still justified as "about the seed-to-seed SD" while the baselines' SDs range from 0.011 to 0.054 (Table S10). Minor. |
| M7 | Mixed model | **Declined, acceptable** | |
| M8 | Neutrality paragraph | **Resolved** | |
| M8 | HiCAST disclosure | **Resolved** | The conflict-of-interest statement now names HiCAST ("did not improve ... not part of the benchmark"). |
| M8 | Home-dataset point | **Not resolved** | Still not mentioned: 10x breast cancer and MOSTA are showcase datasets of SEDR, GraphST, STAGATE and Spatial-MGCN. One sentence. |

### Minor points

| # | Status | Evidence |
|---|---|---|
| 1 Coverage table | **Resolved** | 24/24 now. |
| 2 Table S13 caption | **Resolved** | |
| 3 Fig. 1 | **Resolved in round 3** | Not re-examined. |
| 4 Fig. 2 | **Resolved** | Fig. 2 now shows all 24 sections; the asterisks are gone because all methods have all sections; P(best) matches Table S9. |
| 5 Published-only count | **Not resolved** | See B. |
| 6 BIC | **Resolved** | |
| 7 Seed design | **Partly** | One-seed pipeline methods in Limitations; DeepST/E2S1 host confound (A.2). |
| 8 Lock files | **New problem** | See D.2. |
| 9 CPU timing | **Stated limitation** | |
| 10 Usability rubric | **Declined / optional** | |
| 11 Scope in abstract | **Partly** | See M5. |

### New problems from round 3 (7)

| # | Status | Evidence |
|---|---|---|
| 1 Note 4 vs Bonferroni | **Resolved** | |
| 2 Rank-interval typesetting | **Resolved** | Tables now print "1--10". |
| 3 DeepST coverage | **Resolved** | See M2 for the leftover in S14. |
| 4 Verdict change hidden | **Resolved for HiSTaR**, **not** for the expert analysis (SEDR). |
| 5 "As likely to rank first" | **Resolved**, replaced by an analysis-dependence issue (B). |
| 6 Repo contradicts paper | **Partly** | `PROTOCOL.md` fixed; the script docstring is not. |
| 7 Column "R mclust perturbation" | **Resolved** | Renamed "R mclust noise/order (first 3 datasets)". |

### Round-3 actions

1. Provenance-restricted analysis and protocol reconcile: done.
2. Scope and brain/non-brain in the abstract: partly done.
3. HiCAST disclosure: done.
4. Code archive and DOI: environment files present; URL/DOI and all `\todo` placeholders remain (authors, funding, CRediT, acknowledgements wording).
5. Fix new problems and add the published-only count and retry policy: partly done (see above).

---

## D. Remaining issues a demanding referee would raise

1. **Stale captions after the rerun.**
   - Table S7 caption: "ranks on the sections completed by every method". Table S9 caption: the last rows "exclude the methods stopped at the memory cap". Now all 16 methods have all 24 sections, so the "complete-methods" block at the bottom of S9 duplicates the top block. The two give slightly different P(rank 1) (0.49 against 0.50 for BASS; 0.31 against 0.32 for linear diffusion), which is bootstrap noise that a reader will trip over.
   - Remove the block, or state that the difference is Monte Carlo noise.
   - Check the same for `ranking_complete` in the script (docstring "all 20 sections").
   - Table S14: "DeepST one seed ... on E10.5 E2S1 (memory)" is outdated.
2. **R mclust experiment is still running.** An R process (started 23:07) and a lock directory (`mclust_seed_g6.csv.lock_stereo_E10.5_E1S1_graphst`) are present, and the last commit message says four new embeddings (GraphST, NichePCA, Spatial-MGCN and DeepST on E10.5_E1S1) are not finished. `coverage_matrix.md` shows 23/24 for these four. The R-mclust numbers in the text (n = 290 embeddings, 48% with range above 0.1, 16% outside) are therefore a snapshot, and will change. Regenerate the macros after it finishes, or say in the text that the seed experiment covers 23 of 24 sections for four methods.
3. **Bootstrap and the mixed estimand.** The estimate is an equal-weight mean of group means. Seven groups, where Stereo-seq and breast cancer each count as much as a whole DLPFC donor, so one breast-cancer section carries 1/7 of the weight. This is stated; a leave-one-group-out analysis would show how much any single group drives the verdicts. It needs no new runs.
4. **Hyper-parameter budget.** The baseline's settings were tuned on donor 1 (DLPFC) and the others use defaults. The paper says so and says no tuning budget was given to any method; declined by design. Stated adequately.
5. **Simulations, extra breast sections, containers, contacting authors, 64 GB-per-job tuning.** All declined by design. Each is acknowledged in the Limitations, apart from contacting method authors, which is not mentioned. The wording "we report what the released code does" is adequate for the Spatial-MGCN and HiSTaR sections. I judge the statements adequate; I would add that the authors of HiSTaR and Spatial-MGCN were not contacted, in one clause.
6. **Placeholders.** Authors, affiliations, DOI, funding, CRediT, acknowledgement wording and the code URL/DOI are still `\todo` in `main.tex`; the Data availability section is incomplete without them.

## E. Actions for acceptance (all text or file edits; no new computation)

1. State the thread count for the rerun jobs; note that host and seed are confounded for DeepST on E10.5_E2S1; correct the GraphST memory statement and mention the failed first attempts.
2. Say that the "BASS ahead" statement holds only in the primary analysis (0.50 against 0.32; runner 0.40 against 0.49; expert 0.36 against 0.37). Name SEDR as the expert-analysis verdict change. Note that MERFISH stays in the "expert" subset.
3. Soften "smoothing gave no gain over PCA" and give the per-section values or the seed SD next to the gaps (0.017 on one section).
4. Give the published-only count (7 baseline-higher and 7 unresolved) and flag BayesSpace as borderline and computed on four groups.
5. Fix stale captions (S7, S9, S14); remove or explain the duplicate rank block.
6. Finish the R mclust experiment, then regenerate the macros and remove the lock directory. Fix the `stats_cluster_aware.py` docstring.
7. Add the one-sentence retry policy for superseded error records, the "home-dataset" sentence, the reason SpatialPCA and conST were not benchmarked, and one clause of scope in the abstract.
8. Fill in the `\todo` placeholders and give the code URL and Zenodo DOI.
