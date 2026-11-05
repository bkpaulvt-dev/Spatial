# Pre-registration A9: Spatial-MGCN with label-free stopping rules (written 2026-11-04, before any A9 result exists)

**Question.** The paper's Spatial-MGCN result uses the epoch of the authors' schedule without label selection; the authors' script instead keeps the epoch with the best ARI against the
annotation (label use). How much does the choice of stopping epoch matter when no label is used? (Runbook `docs/DEEPMED2_NEXT.md`, R3 / A9; no contact with the authors.)

**Data and runs.** The 24 original sections (`configs/datasets.yaml`), seeds 0, 1, 2, K given. Method: the repository's model, graph code and loss exactly as `scripts/new_methods.py::spatial_mgcn`
(same preprocessing, radius 4.1 spacings, k = 14, hidden 128/64, loss weights 1/10/0.1, Adam lr 1e-3, weight decay 5e-4, k-means with n_init 10 and random_state = seed on the embedding, `nan_to_num` as there).
One training run per section and seed, **401 epochs (0..400)**, the embedding of every epoch >= 100 kept in memory; k-means is run only on the three selected epochs. No label enters any selection.

**The three label-free rules (fixed now).**
1. **F (primary, fixed epoch count of the paper):** the embedding of epoch 200 = the end of the authors' configured schedule (config: epochs 200, loop 0..200). By construction this equals the existing label-free
   Spatial-MGCN value (same seed, same code), so F also checks reproducibility against the existing records (expected to agree up to numerical nondeterminism).
2. **P (loss plateau):** the first epoch t >= 100 for which the total training loss improved by less than 0.1% over the previous 50 epochs: (L[t-50] - L[t]) / |L[t-50]| < 0.001. If no epoch qualifies, t = 400.
3. **L (final-epoch check):** the embedding of epoch 400 (the end of the extended run).

**Reported** per section and seed: ARI of F, P and L (primary clustering = k-means as the method's own; matched clustering by the runner for the primary F), the plateau epoch, and next to them the existing label-selected-epoch value
(`extra.ARI_label_selected_epoch` of the existing records). The ARIs of P and L are computed against the annotation for reporting only. Summary: mean over sections and the paired difference to F with the cluster-aware
(section-level) bootstrap used elsewhere; no rule is chosen by its result; F stays the headline. Anything else is exploratory.

**Deviations / notes.** Extended schedule (401 instead of 201 epochs) is needed to give P and L a meaning distinct from F. CPU, one thread; cost about the same as the existing run (no per-epoch k-means).
