# Independent review round (4 simulated NAR reviewers) and combined plan

Reviewers: (1) spatial-omics benchmarker, (2) statistician, (3) reproducibility/software/leakage, (4) handling editor.
These are model-generated reviews of the manuscript and repository; treat them as a checklist, not as facts.
Verdicts: R1 reject-in-current-form (resubmission possible), R2 major revision, R3 major revision, R4 major changes first.

## Tier A: minimum for accept; CPU-only; existing data (do first)
1. Cluster-aware statistics: mixed model with dataset/donor/section structure or hierarchical bootstrap; per-dataset estimates as primary;
   pre-specified comparison family; equivalence test (TOST, margin fixed before looking, e.g. ARI 0.03); rank uncertainty (P(best), rank intervals).
   Remove "statistically indistinguishable", "not significantly different from the best methods", "significantly better than 17 of 24".
2. Fair design: exclude development sections (DLPFC 151507-510, STARmap BZ5, MERFISH -0.04) or leave-donor-out; report with and without donor 1;
   drop "official code" wording for the HiSTaR port.
3. Variance reporting: SD/IQR instead of range or maxima; permutation null for the best-of-20 gain; factorial clustering experiment
   (algorithm x number of starts) on saved embeddings; NMI/AMI tables shown.
4. Every number in the text a generated macro; checker fails on numeric literals; fix coverage_matrix seed counting.
5. Finish the missing runs (CCST, DeepST, BayesSpace, Spatial-MGCN; lottery for linear diffusion, PCA, BANKSY; invariance for all methods).
6. Writing: abstract leads with medians/IQR, not maxima; no winner claim; unit of analysis and single-seed limits stated; settings table;
   reporting checklist; neutral wording for the Spatial-MGCN finding (file:line, commit, authors' reply); move AnisoST/boundary analysis to supplement;
   remove template/TODO placeholders; declare AnisoST is the authors' own method and was developed on DLPFC.

## Tier B: needs CPU time but no new data
- At least 5 seeds for every method (GraphST, STAGATE, CCST, Spatial-MGCN, BASS, BayesSpace are the costly ones).
- Equal-tuning arm (plan section 15.2): same budget per method including baselines, tuned on dev sections only, then frozen. Most important missing experiment.
- Unknown-K (or K+-2) runs; label-independent metrics (CHAOS, PAS, marker enrichment); more methods that run on CPU.
- Full leakage audit with two independent readers over all 14 repositories; reproducible environment (lockfile/container), data-fetch scripts with checksums.

## Tier C: needs outside help
- Contact Spatial-MGCN and HiSTaR authors (exact commit, file:line, numbers; ~4 weeks; log dates); verify HiSTaR's published numbers.
- Verify label provenance and licences (STARmap provenance is 'unknown'); public repository and Zenodo DOI.
- More datasets (whole-transcriptome, other technologies, independent ground truth) and a GPU for scaling: required for a strong accept.

## Honest expectation (from the reviewers)
- Tier A (+ author contact): realistic path to accept after major revision for a focused paper.
- Strong accept for a NAR benchmark: needs Tier B and Tier C, roughly months of work; the editor-reviewer judged NAR unlikely for the CPU-only version
  and suggested a focused paper first (clustering variance + reporting protocol + audit) and a broad benchmark later.
- Risk: the "simple diffusion baseline wins" headline may not survive cluster-aware statistics, the tuning arm and dev-section exclusion;
  with ~5 independent clusters, no analysis of the current data can give a confident global ranking.
