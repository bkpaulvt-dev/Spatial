# From HiSTaR to HiCAST

This document (1) summarises the paper *"HiSTaR: identifying spatial domains with
hierarchical spatial transcriptomics variational autoencoder"* (Yu et al., J. Transl.
Med. 2025, 23:1416), (2) lists its weaknesses, including ones found by reading the
official code, and (3) describes **HiCAST**, the improved model implemented in this
repository, together with its benchmark results.

---

## 1. The problem

Spatial transcriptomics (10x Visium, Slide-seqV2, Stereo-seq, STARmap) measures the
expression of thousands of genes at thousands of *spots* while keeping each spot's x/y
position in the tissue. A central analysis task is **spatial domain identification**:
partitioning spots into regions with coherent expression that correspond to anatomy
(e.g. the six cortical layers + white matter of the human DLPFC, or tumour vs. tumour
edge in breast cancer).

Why it is hard:

* Expression is high dimensional, sparse and noisy (dropouts, technical noise).
* Non-spatial clustering (Louvain/Leiden) ignores location and gives fragmented,
  salt-and-pepper domains (median ARI ≈ 0.3 on DLPFC).
* Spatial graph methods (SEDR, STAGATE, STMGraph, DeepST) mostly aggregate only
  1-hop neighbours, so they miss **long-range dependencies** and **multi-scale**
  structure (local cell states vs. large functional zones).
* Multi-slice studies add **batch effects** between slices.

## 2. HiSTaR's solution

HiSTaR is a graph variational autoencoder with a hierarchical encoder:

| Stage | What it does |
|---|---|
| Preprocessing | log-normalise → HVGs → PCA; spatial KNN adjacency; randomly mask spots' expression with a learnable token |
| Encoder | 2 fully connected layers → base features **F0** |
| HiSTaR block 1 | multi-hop GCN (1-hop + 2-hop with softmax hop weights + residual) → GCN heads for μ, log σ² → **F1** |
| HiSTaR block 2 | same block applied to F1 → **F2** (wider receptive field, more abstract) |
| Latent | **Z = [F0, F1, F2]** (concatenation) |
| Decoder | GCN decoder reconstructs expression (MSE / masked SCE); inner-product decoder reconstructs the adjacency (BCE) |
| Losses | λ_rec·L_rec + λ_sim·L_sim + λ_DEC·L_DEC + λ_GCN·L_GCN + L_adj, where **L_sim = −cos(F1, F2)** is the *cross-level similarity loss* that keeps the levels consistent, and DEC is a deep-embedded-clustering refinement |
| Clustering | mclust (EEE Gaussian mixture) on Z |

Reported results: median ARI 0.65 (peak 0.76) over the 12 DLPFC slices (0.718 on
#151673), better than STAGATE/STMGraph/DeepST; it handles Visium, Slide-seqV2,
Stereo-seq and STARmap; it integrates two slices without an external tool (iLISI 1.97
on mouse brain); it trains in 27 s on a slice. The ablation (Table 1) shows that both
the multi-hop GCN and L_sim matter, and that two blocks beat three.

## 3. Weaknesses

### Acknowledged by the authors
1. **Hyper-parameter sensitivity.** "The performance of HiSTaR is very sensitive to
   the setting of cross-level similarity loss", so λ_sim is grid-searched per dataset
   (supplementary Tables S5/S6).
2. **Fixed KNN graph.** Discontinuous or irregular tissue "where KNN-based adjacency
   could introduce artifacts"; they suggest adaptive graphs as future work.
3. **Trajectory order deviates** from the expected L1→L6→WM progression.
4. **Expression only.** No histology or other modalities.

### Found by analysis of the method and the official code
5. **L_sim encourages redundancy.** Maximising cos(F1, F2) per spot rewards F2 for
   copying F1, which works against the stated goal of *decoupled* multi-scale levels.
   This is consistent with their own Table 1: without L_sim, mclust fails outright,
   and a third level adds "redundant information" and lowers ARI.
6. **One global hop weight per layer.** `softmax(θ)` is shared by every spot, and in
   the code it is pulled towards a fixed prior `[0.7, 0.3]` by a KL penalty, so the
   "learned" hop mixture is essentially fixed. Spots at domain boundaries and spots
   deep inside a domain get the same receptive field.
7. **Stochastic inference.** In the official code, the masking routine runs inside
   `forward()` even in eval mode, so the embedding used for clustering has a mask
   token added to a random 80 % of spots. Results therefore change from call to call.
8. **The VAE is close to an AE.** The KL term is computed as `-0.5 / N * mean(...)`,
   i.e. divided by N twice, so it has almost no weight.
9. **Concatenation instead of fusion.** Z = [F0, F1, F2] gives every level equal,
   fixed weight for every spot.
10. **Batch correction is incidental.** There is no batch variable in the model.
    Slices are only connected through shared weights, so mixing depends on luck.
11. **Paper vs. code mismatches.** The paper says masked spots are *replaced* by a
    token; the code *adds* it. The paper's adjacency BCE is over the full N×N matrix,
    but the code samples one random node per edge.
12. **Reproducibility.** Clustering requires an R installation (rpy2 + mclust) with
    hard-coded Windows paths in `configure_r_environment`.

---

## 4. HiCAST: the proposed method

HiCAST (**Hi**erarchical **C**ontrastive **A**daptive **S**patial **T**ranscriptomics)
keeps HiSTaR's core idea, a hierarchical graph VAE whose levels see increasingly large
neighbourhoods. It changes the parts listed in §3. Code: `hicast/model.py`.

| # | Component | Addresses | Implementation |
|---|---|---|---|
| 1 | **Expression-aware graph** | weakness 2 | each spatial KNN edge is weighted by `exp(-(1-cos(x_i,x_j))/τ)` on the top-30 PCs, so edges crossing domain boundaries count less (optional refinement from the learned embedding) |
| 2 | **Node-adaptive hop attention** | 6 | `H_k = Â^k XW`, k = 0..K (K = 3 / 6 per level); each spot computes its own softmax attention over hops |
| 3 | **Correct hierarchical VAE** | 7, 8 | proper KL with warm-up; masking (token *replaces* 30 % of spots) only during training; posterior means at inference, so embeddings are deterministic |
| 4 | **Spatial local–global contrast** | (new signal) | DGI-style: a bilinear discriminator separates (spot, neighbourhood-summary) pairs from feature-shuffled corruptions |
| 5 | **Attention fusion of levels** | 9 | per-spot attention over projected F0, F1, F2 instead of concatenation |
| 6 | **Learned loss balancing** | 1 | homoscedastic-uncertainty weighting (Kendall et al., 2018) over the reconstruction, cross-level, local–global and edge losses; no λ grid search |
| 7 | **Batch-aware** | 10 | cross-slice mutual-nearest-neighbour edges + batch-conditional decoder |
| 8 | **Scalable, R-free** | 11, 12 | edge loss with negative sampling, O(\|E\|); clustering with an EEE Gaussian mixture (scikit-learn `tied`), which is the same model as mclust EEE |

The cross-level term ended up being **HiSTaR's own cosine loss**. The two InfoNCE
replacements I designed (instance-level and neighbourhood-level) were both worse in
tuning (§5.2).

## 5. Experiments

### 5.1 Protocol
* **Data:** all 12 human DLPFC Visium slices (spatialLIBD), layer annotations from
  `layer_guess_reordered`; 7 domains (5 for donor 2).
* **Identical preprocessing for every method:** seurat_v3 HVGs (2000) → normalise →
  log1p → scale → PCA (200). Graph: spatial KNN, k = 6.
* **Identical clustering:** EEE Gaussian mixture on the embedding; ARI/NMI/FMS on
  annotated spots.
* **Baseline:** port of the official HiSTaR code with the published defaults
  (λ_sim = 0.3, 200 + 200 epochs). Also tested: the same model with deterministic
  inference (weakness 7 fixed).
* **No test-set tuning:** all HiCAST design choices were made on **donor 1 only**
  (151507–151510, seed 0). Donors 2 and 3 were used only for the final run.
* 3 seeds per (method, slice), CPU only (1 thread per run).

Reproduce: `python scripts/benchmark_dlpfc.py --data <DLPFC dir> --seeds 0 1 2 --methods histar histar_deterministic hicast`

### 5.2 Tuning on donor 1 (seed 0, mean ARI over 4 slices)

| Variant | Mean ARI |
|---|---|
| HiSTaR | 0.492 |
| HiCAST, first design (instance InfoNCE cross-level loss) | 0.40 (151673 only, 2 seeds) |
| HiCAST, neighbourhood InfoNCE cross-level loss | 0.384 |
| … neighbourhood InfoNCE + initial-value-scaled losses | 0.415 |
| **HiCAST, cosine cross-level loss (final)** | **0.528** (seed 1: 0.492) |
| final − adaptive hops | 0.532 |
| final − graph refinement | 0.528 |
| final − expression-aware graph | 0.496 |
| final, 300 epochs | 0.511 |
| final − cross-level loss | 0.447 |
| final, hand-set loss weights | 0.446 |
| final, initial-value-scaled losses | 0.373 |
| final − attention fusion (concatenate) | 0.398 |
| final − local–global contrast | 0.365 |

Raw runs: `results/tuning/*.jsonl`.

### 5.3 Final benchmark (12 slices × 3 seeds)

| Method | Median ARI | Mean ARI | Median NMI | Median FMS | Donor 1 ARI (tuning) | Donors 2+3 ARI (held out) | Train time / slice |
|---|---|---|---|---|---|---|---|
| HiSTaR (official code) | **0.509** | **0.491** | **0.648** | **0.608** | 0.478 | **0.497** | 116 s |
| HiSTaR, deterministic eval | 0.502 | 0.487 | 0.654 | 0.594 | 0.472 | 0.495 | 117 s |
| **HiCAST** | 0.493 | 0.482 | 0.634 | 0.594 | **0.504** | 0.470 | 248 s |

Per slice (mean ± std of ARI over 3 seeds; best in bold):

| Slice | Donor | HiSTaR | HiSTaR (deterministic eval) | HiCAST |
|---|---|---|---|---|
| 151507 | 1 (tuning) | 0.477 ± 0.042 | 0.469 ± 0.052 | **0.574** ± 0.042 |
| 151508 | 1 (tuning) | **0.504** ± 0.028 | 0.453 ± 0.009 | 0.485 ± 0.027 |
| 151509 | 1 (tuning) | 0.414 ± 0.072 | 0.438 ± 0.061 | **0.498** ± 0.018 |
| 151510 | 1 (tuning) | 0.515 ± 0.036 | **0.529** ± 0.033 | 0.459 ± 0.064 |
| 151669 | 2 | **0.411** ± 0.022 | 0.329 ± 0.068 | 0.352 ± 0.032 |
| 151670 | 2 | **0.364** ± 0.052 | 0.364 ± 0.051 | 0.265 ± 0.066 |
| 151671 | 2 | **0.590** ± 0.003 | 0.589 ± 0.003 | 0.529 ± 0.021 |
| 151672 | 2 | 0.525 ± 0.056 | **0.568** ± 0.128 | 0.565 ± 0.009 |
| 151673 | 3 | 0.535 ± 0.027 | **0.555** ± 0.008 | 0.543 ± 0.022 |
| 151674 | 3 | 0.541 ± 0.052 | 0.549 ± 0.052 | **0.630** ± 0.057 |
| 151675 | 3 | **0.523** ± 0.040 | 0.516 ± 0.036 | 0.487 ± 0.035 |
| 151676 | 3 | **0.489** ± 0.035 | 0.488 ± 0.034 | 0.392 ± 0.032 |

HiCAST beats HiSTaR on 5 of 12 slices; Wilcoxon signed-rank p = 0.68. Raw runs:
`results/dlpfc_main.jsonl`.

## 6. Conclusions and lessons

1. **HiCAST does not improve on HiSTaR.** The donor-1 gain (+0.026 ARI) did not
   carry over to new donors (−0.027), and the overall difference is not significant.
   The gain was partly tuning noise: seed-to-seed standard deviation is 0.02–0.07
   ARI for both methods.
2. **HiSTaR's published numbers did not reproduce here.** With the official code
   and defaults, median ARI was 0.509 (paper: 0.65), and 0.535 on #151673 (paper:
   0.718). Likely causes are per-slice λ_sim tuning (Table S6), the unpublished
   preprocessing script, mclust in R versus the equivalent GMM here, and seed
   selection. The ranking against other methods in the paper should be read with
   this in mind.
3. **The inference-masking bug does not matter for accuracy** (0.502 vs 0.509), but
   fixing it makes results reproducible from run to run.
4. **What did help, from the donor-1 ablations:** the local–global contrastive loss
   (+0.16), attention fusion of levels (+0.13), learned loss balancing (+0.08 over
   hand-set weights) and the expression-aware graph (+0.03), all *within* the HiCAST
   architecture.
5. **What did not help:** InfoNCE cross-level losses (they push apart spots that
   belong to the same domain), per-spot hop attention, and graph refinement.
6. **Promising next steps:** (a) select HiCAST's configuration by an unsupervised
   criterion (e.g. silhouette or embedding stability) per slice instead of one
   donor; (b) ensemble over seeds (consensus clustering), since variance is as large
   as the method differences; (c) a count-based (NB/ZINB) decoder on HVGs; (d)
   evaluate the batch-integration path (MNN edges + conditional decoder) on
   multi-slice data, which is implemented but not yet benchmarked.
