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
