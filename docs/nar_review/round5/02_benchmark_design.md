# NAR review, round 5 (final), report 02: benchmark design

**Role:** benchmark-design reviewer. **Read:** my round-4 report, `paper/main.tex`, `paper/main.pdf` and `paper/supplementary.pdf` (text), `configs/methods.yaml`, `configs/datasets.yaml`, `docs/PROTOCOL.md`, `results/paper_macros.tex`, `results/benchmark_runs*.jsonl` (read-only), `scripts/run_r_method.R`, `scripts/adapters.py`, `scripts/stats_cluster_aware.py`, `docs/BIGMEM_RERUN.md`. I did not re-open the figures.

## Verdict: minor revision (accept after text and file edits; no new computation needed)

The design is sound for a descriptive benchmark and the claims are now, with two exceptions below, scoped to the evidence. The rerun is handled openly (threads, host/seed confound for DeepST on E10.5_E2S1, GraphST memory, 20 records for 17 jobs are all now in the text). The main remaining problems are (a) the shipped registry and protocol files contradict the paper on label provenance and on which datasets enter the primary ranking, and (b) the sentence "settings were the same on every dataset" and "official code" are not literally true. Both are fixable by wording and file edits.

---

## A. Status of round-4 required items

| # | Round-4 item | Status |
|---|---|---|
| 1 | Thread count for reruns; host and seed confounded for DeepST/E2S1 | **Done** (Methods: ARI 0.35/0.40/0.40, "confounded"; Limitations). Small leftover: Supp. Note 6 says "the same one-thread limit" while main text says DeepST and NichePCA "used several cores" on the 125 GB server (see C4). |
| 1 | GraphST memory correction, failed first attempts | **Done** ("reaching or exceeding the cap"; 3 failed GraphST jobs explained). Verified against `benchmark_runs_bigmem.jsonl`: 20 records, GraphST failures at 13.2 GB, successes at 11.7-11.8 GB. |
| 2 | "BASS ahead" only in primary analysis | **Done** (Discussion: "in the primary analysis; the order reversed in the runner ... intervals overlap"). The expert-only tie (0.37 vs 0.37) is in Results. |
| 2 | Name SEDR as the expert-analysis verdict change; MERFISH stays in "expert" subset | **Not done.** Results still say the expert-only analysis "gave the same picture" (7 baseline-higher / 9 unresolved, against 8 / 8). Supp. Table S8 caption still calls the subset "expert annotation" without saying that MERFISH labels come from the BASS analyses. |
| 3 | Soften "smoothing gave no gain over PCA"; give per-section values or SD next to gaps | **Partly.** Results now say "did not help on these tissues" (fine); the Discussion still reads "smoothing gave no gain over PCA alone" and the abstract "slightly ahead". The brca gap is on n = 1 section (0.017). Add "(single section; Stereo-seq three sections of one study; no interval)". |
| 4 | Published-only count (7 of 14 baseline-higher, 7 unresolved); BayesSpace borderline and four groups | **Not done.** I re-derived from Supp. Table S6: dropping PCA and AnisoST gives 7 baseline-higher (Spatial-MGCN, CCST, SpaGCN, SpaceFlow, DeepST, SEDR, BayesSpace) and 7 unresolved. BayesSpace has lower bound +0.000 and uses four groups only; not flagged. |
| 5 | Stale captions S7, S9, S14 | **Mostly done.** Table S15 caption correct. Table S7 caption still says "sections completed by every method" (now trivially all 24; harmless, but reword). Table numbering was shifted in the PDF; check the `\ST...` labels once more. |
| 6 | Finish R mclust experiment; docstring | **Experiment done** (no R process or lock directory remains; coverage 24/24). **Docstring not fixed**: `scripts/stats_cluster_aware.py` line 6 "margin fixed before looking" and line 130 "methods with all 20 sections". |
| 7 | Retry policy; home-dataset sentence; reason SpatialPCA/conST not benchmarked; abstract scope clause | **Not done** (retry: `--retry-errors` in `scripts/rerun_memory_failures.sh` and "up to 5 restarts" in `docs/BIGMEM_RERUN.md` are not described; no home-dataset sentence; Table S22 only says "screened but not benchmarked"; abstract has no "K given / single sections" clause). All one-liners. |
| 8 | Placeholders, code URL/DOI | Known author-side; still open. |

---

## B. New findings, ranked

### B1 (moderate-major). Registry and protocol contradict the paper on provenance and on primary-ranking eligibility
- `docs/PROTOCOL.md` section 2: datasets whose labels came from a clustering algorithm "are reported but **excluded from the primary ranking**", and "`unknown` provenance must be resolved before ranking". `configs/datasets.yaml` classes Stereo-seq (MOSTA) as `algorithm` and STARmap as `unknown`. Both are in the primary analysis (2 of the 7 groups, 6 of 24 sections). Only section 8 of the protocol carries a "superseded for the paper" note; section 2 does not, and Amendments say "(none yet)", while the header still says "DRAFT ... to be frozen". The paper never calls the protocol pre-registered (good), but the repository will be public and a reader will find a stated rule that the paper broke.
- Every dataset entry, including DLPFC, has `verified: false`, and the file header says such fields were "filled from memory ... MUST be confirmed ... before submission". `methods.yaml` has the same warning for publication fields ("written from memory and are NOT verified"; CCST "volume and pages to verify"). Supp. Note 1 sends readers to this file for "splits and label provenance". All licences are `to_check`.
- Main text, Evaluation: "ARI against the **manual annotation**" is wrong for Stereo-seq (the paper itself says the MOSTA labels are partly clustering-derived).
- **Fix:** (i) add an amendment list to PROTOCOL.md and a "superseded for the paper" note to section 2: STARmap and MOSTA kept in the primary analysis because dropping them would leave n = 5 groups; the expert-only analysis is the check required by the rule; (ii) verify and flip `verified`, or reword the headers; resolve `to_check` licences or state them in DATA_AND_LICENCES; (iii) say "against the reference annotation (manual for DLPFC and breast cancer; see Limitations for the others)". Round-4 B point on MERFISH (reference_atlas in yaml, "expert" in the paper) belongs here: the yaml calls it `reference_atlas`, Table S8 calls it expert annotation. Use one term.

### B2 (moderate). "Settings were the same on every dataset by design" and "official code" are not literally true
- Limitations: "Settings were the same on every dataset by design". The code and Supp. Table S2 show technology-specific tutorial settings: GraphST `datatype='Stereo'` only on Stereo-seq (`scripts/adapters.py` line 105; stated in Methods) and hvg 3000 vs all genes; BASS DLPFC/brca/stereo branch (sparkx 3000 genes, `scaleFeature=FALSE`, C = 20) versus STARmap/MERFISH (all genes, `scaleFeature=TRUE`, C = 15 or 20) in `scripts/run_r_method.R` lines 15-21; CCST lambda_I 0.3 vs 0.8; STAGATE radius vs 6-NN. The BASS branch used for breast cancer and Stereo-seq (the DLPFC branch) and its `scaleFeature` difference are not in `methods.yaml` or Table S2, which list only DLPFC, STARmap and MERFISH.
  Only GraphST received a Stereo-seq-specific setting, while the SEDR and Spatial-MGCN Stereo/breast settings were deliberately not used (disclosed). The result is an uneven treatment that is small but real.
- Methods: "Every method was run with its official code". CCST was re-implemented (`methods.yaml`: "re-implemented in scripts/new_methods.py because of PyTorch 1.7 pins"; Table S2 only). CCST is the second-largest baseline margin in the primary analysis (+0.175, Bonferroni-significant), so this matters for the headline. HiSTaR is a port (disclosed in main text).
- **Fix:** replace with "same settings on every dataset except where the tutorial prescribes technology-specific values (listed in Table S2)"; add BASS brca/Stereo settings to Table S2; state in Methods that CCST and HiSTaR are re-implementations, and add one sentence that CCST was not validated against the original on its own dataset (or give the check if one exists).

### B3 (moderate). Matched clustering coincides with the baselines' native clustering; the primary protocol is not neutral to this
The "matched" clustering (20-start tied-covariance GMM, best likelihood) is also what the three baselines and HiSTaR/BANKSY use by default (3-start version). Methods designed for k-means, Leiden or mclust-on-20-PC (SpaceFlow, NichePCA, CCST, Spatial-MGCN, DeepST) are scored on a clusterer they were not designed for, and SpaGCN/BASS/BayesSpace keep their own clustering in the same ranking. The paper reports both protocols (default: 9 baseline-higher in Table S5 against 8 in S6), which is the right mitigation, and the matched-versus-default gain table (S14) shows which methods benefit. Add one sentence to Methods or Discussion that the matched protocol coincides with the baselines' own clustering step and that the direction of the effect differs by method (S14); this guards against reading the primary result as protocol-free.

### B4 (moderate). Development-set asymmetry is described only one way
The baselines were fixed on DLPFC donor 1; the Discussion offers "a fixed amount of smoothing tuned on cortex blurs [tumour/embryo domains]" as one (untested) explanation. The same applies to many published methods, whose tutorials and default hyper-parameters were also developed on DLPFC (SpaGCN, STAGATE, GraphST, SEDR, SpaceFlow). The dev-section-free analysis handles the baselines' side but not this. Add one clause: "most published defaults were also set on DLPFC or similar brain data, so the brain/non-brain pattern is not specific to the baseline". Also, the left-out sections test pipeline-level overfitting only for donors 2 and 3 plus later sections of the same studies, not for any new tissue; the paper's brain/non-brain framing already says this.

### B5 (minor-moderate). Abstract wording about HiSTaR
"HiSTaR's published accuracy was not reproduced" is in the abstract, but the result is from the authors' own PyTorch port with the shared 200-PC input, without the per-section loss-weight tuning (`methods.yaml` deviations). The Results body is careful ("our PyTorch port ... not to question the method itself"); the abstract is not. Use "A PyTorch port of HiSTaR with its published defaults did not reproduce its published DLPFC accuracy". Same neutrality point for "released code of one method selects its reported epoch using the labels": the Results add "We do not know whether the published numbers were obtained with these scripts"; add "released test scripts" to the abstract.

### B6 (minor). Fairness of rerun: remaining small points
- Supp. Note 6 says the rerun used "the same one-thread limit" on a 20-thread server, while the main text says DeepST and NichePCA "used several cores" and peak memory was "measured with 20 threads". Reconcile (one thread requested, observed cores more).
- The retry policy is in scripts (`--retry-errors`, up to 5 restarts in `docs/BIGMEM_RERUN.md`) but not in the paper; state "failed jobs were retried with unchanged settings, never different ones" to match PROTOCOL section 5 ("never re-run with different settings"), and note that the GraphST rerun did change one thing (the mclust wrapper), so the protocol sentence is not literally met.
- The wrapper check covers two embeddings; it is adequately disclosed. The Stereo-seq GraphST values (E10.5_E1S1, 3 seeds) rest on it; the matched analysis does not.

### B7 (minor). Statements to tighten
- "Taking all datasets from the runner ... a different verdict only for HiSTaR and STAGATE" is correct (macro `listRunnerFlip`); add "borderline" (HiSTaR lower limit +0.004, STAGATE +0.001 in Table S7).
- Primary-analysis count: "8 of 16" includes PCA and BayesSpace; give "7 of the 14 published entries" (B-table above).
- No leave-one-group-out analysis. With seven groups, and the equal-weight mean, one group (breast cancer, one section) carries 1/7. The per-dataset deltas in S6 show the baseline-higher verdicts for CCST, Spatial-MGCN, SpaGCN, DeepST are driven by STARmap and MERFISH (+0.2 to +0.47), so removing any single non-brain group cannot flip them, but verdicts for SEDR, STAGATE, HiSTaR could. One sentence suffices, or add a column.
- Home-dataset point (round 3 and 4): 10x breast cancer and MOSTA/BRCA annotations are the showcase data of SEDR/GraphST/STAGATE/Spatial-MGCN. The Limitations mention the provenance of the annotation but not this; one sentence.

---

## C. Does the evidence support the claims? (checked)
- Tissue dependence (0/16, 1/15, 1/15, 13/16, 11/15 comparators ahead): matches `paper_macros.tex` and S6 per-dataset columns. Descriptive only; the paper says so.
- P(rank 1): BASS 0.49 vs 0.32 (primary), 0.41 vs 0.49 (runner), 0.37 vs 0.37 (expert); Discussion now consistent.
- Memory and rerun counts: 5 methods x 3 seeds + 2 DeepST seeds = 17 jobs; 20 records (3 failed GraphST); consistent with `benchmark_runs_bigmem.jsonl`.
- K given to all methods: stated in Methods, Fig. 1, Limitations; K-robustness reported (S12). The sentence that the lead "depends on giving every method the true K" is supported by the BIC analysis.
- Abstract scope: "four technologies ... three tissues" is stated; add "K given; one non-brain technology section count: one breast cancer section" for scope.

## D. Actions for acceptance (text and file edits only)
1. PROTOCOL.md: supersession note on section 2, amendment list, status line; `datasets.yaml`/`methods.yaml`: verify or reword `verified:false` and "from memory" headers; fix "manual annotation" for Stereo-seq (B1).
2. Replace "same settings on every dataset" by the accurate statement; list BASS brca/Stereo settings; disclose CCST re-implementation in the main text (B2).
3. One sentence on the matched protocol coinciding with the baselines' own clustering (B3); one clause on DLPFC-derived published defaults (B4).
4. Abstract: "port of HiSTaR"; "released test scripts" (B5).
5. Round-4 leftovers: SEDR in the expert-analysis flip; MERFISH in the "expert" subset caption; published-only 7/7 count; BayesSpace flag; PCA wording in the Discussion; retry policy; threads wording; fix docstring lines 6 and 130 of `scripts/stats_cluster_aware.py`.
6. Author-side: `\todo` placeholders, code URL and Zenodo DOI.
