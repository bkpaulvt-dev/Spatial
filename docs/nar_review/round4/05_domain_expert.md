# Referee report, round 4 (final): Reviewer 2 (spatial domain method developer)

Material: paper/main.tex + results/paper_macros.tex, paper/supplementary.tex and results/supp tables, scripts/adapters.py, scripts/new_methods.py, newest record per id in results/benchmark_runs.jsonl (1124 ids, all status ok), configs/methods.yaml, datasets.yaml, brca_coarse.json, nar_fig2_accuracy.png. Light checks only; nothing re-run.

## Recommendation: minor revision (accept after text/table fixes). No conclusion changes.

## A. The five reruns (new since round 3)
- Completeness verified: every method has results on all 4 Stereo-seq/breast sections (17 records tagged host deepmed2; all other Stereo/brca records have no host tag). Three seeds each, including DeepST E10.5_E2S1 seeds 1-2. Good.
- Fairness: acceptable.
  - GraphST: datatype='Stereo' on Stereo-seq, 20 threads CPU. The mclust wrapper (R function calling Mclust(x,G,m) after the same set.seed) is equivalent to GraphST's own call; the identical-labels test is on only two embeddings, which is thin but sufficient. Matched ARI on E10.5_E1S1 is 0.38-0.39, so GraphST was not handicapped.
  - NichePCA default workflow: defensible and stated. It still omits the `backend="sparse"` option I raised in round 3.
  - Spatial-MGCN default config (radius 4.1 bin spacings, k=14, dense graphs): a fair "default on every dataset" treatment, but it is not tuned for bin50, which should be conceded in one clause.
  - BASS keeps its DLPFC settings (C=20) on E10.5_E1S1 (K=13), and BASS returned 13 domains there. Fine.
- Memory statements: mostly correct, with two defects.
  1. Results l.238-240 says the five "needed 12-28 GB ... more than the 12 GB cap". GraphST's recorded peak is 11.8 GB, which is below the cap (it was stopped earlier at 12.05-12.18 GB or by the system-memory rule). Write "reached or exceeded the cap in the first attempt (peak on the larger server 11.8-27.6 GB)".
  2. The reruns used 20 threads and a 125 GB host, but Methods says "one CPU thread". Peaks (e.g. torch/BLAS buffers) can depend on threads and allocator behaviour. The limitation text ("not the methods in general") is right, but add "with 20 threads" next to the memory figures.
  - Intrinsic or workflow-caused failure: the text now says "implementations on this section"; I would still name which are dense n x n (GraphST, Spatial-MGCN, DeepST) and which workflow-dependent (NichePCA).
- Ranking: wording needs care. BASS 0.50 vs linear diffusion 0.32 in the primary analysis is reported neutrally in Results. The runner sensitivity reverses it (linear diffusion 0.49, BASS 0.40, Table S7) and the default-clustering ranks give BASS 0.58. The Discussion sentence "BASS ranked first more often (0.50 against 0.32)" omits this. Add "in the primary analysis; the order reversed in the runner sensitivity analysis and the intervals overlap". The abstract's "BASS and the baseline were the most likely to rank first" is neutral, as is the Results sentence.
- Stale text: Table S9 caption and the final block "Methods with every section" is now redundant (all 16 methods have every section; values differ by bootstrap noise, e.g. 0.49 vs 0.50). Remove the block and the "excludes methods stopped at the cap" wording. Table S14 caption still says DeepST has one seed on E10.5 E2S1 "(memory)". Table S7 caption "sections completed by every method" is now trivial. Figure 2 has no asterisks and matches the table (good).

## B. Round-3 points
- M1.1 GraphST Stereo: resolved. Data l.117 "without changing any setting" is still not literally true (GraphST mode, MGCN NaN patch). Not resolved on wording.
- M1.2 NichePCA: partly. The Limitations sentence and S2 row are present and honest; `sparse` backend still unmentioned.
- M1.3/M1.4 MGCN breast config, SEDR Stereo tutorial: partly. The Limitations name them. S2 now lists both (MGCN "default settings on every dataset", SEDR "the same 12-NN graph") - resolved there. The Spatial-MGCN NaN patch (new_methods.py l.238) is still not listed.
- M1.5 bin50 scale: partly (stated; no sensitivity run). The Discussion still offers only the "blurring" hypothesis; the alternative that annotation is expression-clustering-derived/low-count Cavity class is not named. Not resolved.
- M1.6 ties on square lattice: partly. A Limitations sentence now exists; S2 has none, which is acceptable.
- M1.7 BayesSpace: not resolved in main text (l.147-148) and S2 ("needs a hexagonal spot lattice"); only the docstring is correct. The adapter still raises "requires a Visium spot lattice".
- M2 memory/seeds: partly. The reruns solve the substance. Remaining: the DeepST E10.5_E1S1 single-attempt statement is moot (now run); the NaN patch; Table S23 coverage now consistent (DeepST 24/24, 1-3 seeds) - resolved; GraphST DLPFC "1-3" consistent with Methods.
- M3 ranking: resolved on the core; "more likely" fixed (Discussion l.375 now "ranked first more often" - fine). Interval typesetting now "1--10": resolved.
- M4.1 PCA vs smoothing: resolved. Tissue dependence: resolved (counts 0/1/1 and 13/16, 11/15 consistent with macros; brain equal-weight 0.594 vs 0.587 correct). "d" direction ambiguity: Results says "exceeded ... by 0.172 ... trailed by 0.023": resolved.
- M4.5 "no method stood out": resolved; now "methods were close to each other" - still slightly strong given Stereo-seq range 0.24-0.39, but acceptable with the tissue-dependence wording. Mention the range.
- M4.2 MOSTA provenance: partly (Limitations; datasets.yaml still verified:false, class algorithm). M4.3 Cavity: not resolved (no mention, no ARI without Cavity).
- M4.4 coarse breast: partly. Text says "the order changed (NichePCA and SpaceFlow highest; linear diffusion 0.19)" and the macro `brcaCoarseLinRank` is not used - good - but still says nothing that ten of 14 sit within 0.18-0.21 (my check: 0.18-0.21 for most). Add "most methods 0.18-0.21".
- M5 HiSTaR: partly to mostly resolved. Intro l.78 says "released code": resolved. Results/Methods say "PyTorch port": resolved. Table S19 row says "PyTorch port": resolved. Shared-PC input named as a possible cause: resolved. Remaining: "official code" in Methods l.131 and l.350 ("port of the official code") is acceptable; 0.718 for 151673 not in S19; author-contact sentence absent.
- M6 Spatial-MGCN: partly. The text now gives DLPFC and breast values through macros (mgcnLeakDlpfc 0.13, brca 0.03) and restricts "looks competitive" to DLPFC, and states the breast configuration is the one the repository provides. Resolved in substance. Remaining: the pooled +0.147 and Table S20 still lack the breast row and mix in STARmap/MERFISH (which the scripts never target); say "in-scope: DLPFC +0.13, breast +0.03". Note a subtlety: the text says "the inflation was smaller" on breast while the Spatial-MGCN breast default (0.575) is above linear diffusion (0.545) - the sentence is correct but add that value. LEAKAGE_AUDIT.md still says "authors not yet contacted; do not publish a claim..." - unresolved; either contact the authors or edit that line before release.
- M7 prior work: partly. The four references are correct and cited in the Introduction; CellCharter/MENDER are not placed in the Discussion as published versions of the baseline.
- Minor points 1-4, 7, 10 (HiSTaR default clustering note, SEDR matched collapse, k_found, BASS domain count, development-section clause, verified:false/to_check/"written from memory" header in methods.yaml): not resolved; item 10 must be cleared before code release.
- Supplementary notes: Note 2 now says "HiSTaR: a port" - resolved; Note 4 now mentions Bonferroni - resolved; Note 6 documents the rerun host - resolved.

## C. Domain claims
- "Smoothing ... did not help on these tissues" and "PCA ahead" are correct. The explanation "domains are smaller, interleaved and defined partly by cell composition" is stated as untested; keep it, but a second explanation (annotation derived from expression clustering) must sit next to it.
- Linear diffusion = "standard neighbourhood smoothing" (CellCharter/MENDER-like): fine once cited.
- "On MERFISH the best-fitting mixture may separate cell types": plausible, flagged as speculative; fine.
- Nothing in the abstract overclaims. "BASS and the baseline were most likely to rank first" is neutral given the runner reversal; add "in the primary analysis" only if space permits.

## Required before acceptance
1. Fix the GraphST "more than the cap" statement (11.8 GB) and add the 20-thread caveat to the memory figures.
2. Add the runner-reversal caveat to the Discussion ranking sentence; remove the redundant ranks block and stale captions (S9, S14, S7).
3. BayesSpace reason (main text + S2); NichePCA `sparse` backend; Spatial-MGCN NaN patch in S2.
4. Name the clustering-derived annotation/Cavity alternative next to the blurring hypothesis; cite CellCharter/MENDER there.
5. Table S20: add the breast row and report in-scope inflation; resolve the LEAKAGE_AUDIT contact statement; clear methods.yaml/datasets.yaml verified/licence flags.
