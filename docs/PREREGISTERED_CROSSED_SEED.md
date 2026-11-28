# Pre-registration: crossed training-seed x clustering-seed experiment (revision item 2)

Written and committed on 2026-11-28, **before any run of this experiment** (revision plan `SP-Ben_V1_Revision_Plan.md`, section 2).
Code: `scripts/review_stage_cs.sh` (embeddings), `scripts/cs_analysis.py` (clustering and analysis), committed with this file.

## Question
How much of the variation in ARI comes from the training seed of a method, and how much from the random start of the clustering step on
a fixed embedding? Does likelihood selection over more starts help, and do the findings hold for a second common clusterer (k-means)?

## Subset (fixed here; chosen by assay, feasibility and independent sample coverage, not by results)
Sections (7; one per DLPFC donor, one per other dataset; 7 independent groups):
DLPFC 151507 (Br5292), 151669 (Br5595), 151673 (Br8100); STARmap 20180419_BZ9_control (targeted, single cell); MERFISH -0.14
(targeted, single cell); breast cancer block_a_1 (non-brain, Visium); Stereo-seq E9.5_E1S1 (non-brain, bin50).
Methods (9): training-free linear diffusion, AnisoST, PCA; neighbourhood BANKSY lambda 0.8, NichePCA; learned HiSTaR (our port),
GraphST, STAGATE, SpaceFlow. Excluded for cost or because they return no embedding: CCST, DeepST, Spatial-MGCN (cost), SEDR (fails in R
mclust on the second server before an embedding is returned), SpaGCN, BASS, BayesSpace (internal clustering, no embedding).
Training seeds: 0, 1, 2, 3, 4. Settings: the benchmark settings, unchanged (`configs/methods.yaml`); the annotated K is given.
Runs: 7 x 9 x 5 = 315 jobs through `scripts/review_queue.py` (30 GB cap, 24 h limit, failure rules as for every review stage); the
embedding of every seed is saved. Seeds 0-2 repeat existing benchmark jobs: their ARI is compared with the existing record (agreement
check, reported; a difference does not change the analysis).

## Clustering of each saved embedding (no labels used in any choice)
- GMM: 20 single-start fits, `GaussianMixture(K, covariance_type="tied", n_init=1, reg_covar=1e-5, random_state=r)`, r = 0..19, on the
  embedding as returned (no rescaling; as in the initialisation experiment); default tolerance 1e-3 and max_iter 100.
- k-means: 20 single-start fits, `KMeans(K, n_init=1, random_state=r)` (k-means++ seeding), r = 0..19, same embedding.
- Likelihood (GMM) or inertia (k-means) selection over the first 1, 3 and 20 starts of the same fits.
Embedding dimension and whether the method scales it are recorded per method.

## Quantities (per section and method)
- Within-embedding variation: for each trained embedding, SD and range (max - min) of ARI over the 20 starts; averaged over the 5 seeds.
- Between-training-seed variation: SD over the 5 seeds of the restart-averaged ARI (mean over 20 starts). Training variance component
  = var(restart means) - mean(within variance)/20 (finite-restart correction; truncated at 0), reported with the uncorrected value.
- Ratio of the two SDs. Summaries per dataset and over the 7 groups (equal weight per group), with interquartile ranges over sections.
- Selection: ARI of the best-likelihood fit among 1, 3, 20 starts, mean over seeds.
- Second clusterer: the same quantities for k-means; per dataset, whether (i) within-embedding variation exceeds 0.03 ARI and (ii) the
  method ordering by mean ARI agrees with the GMM ordering (Spearman rho) - "persists" if both hold as for GMM.

## Reporting rule
All quantities are descriptive (7 groups); no significance test. The manuscript claim that the clustering step varies more than training
is revised to whatever these estimates show, per method and dataset, including where the order reverses.
