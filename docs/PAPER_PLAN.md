# CIPHER: plan for a Cell Press methods paper

Target journals, in order: **Cell Reports Methods** (methods + benchmark + biological use case),
**Cell Genomics** (needs a stronger biological finding, e.g. GWAS link as in LLCB), **Cell Systems**.

Working title: *CIPHER predicts genetic interactions of unseen perturbation pairs from a
nonlinear cyclic regulatory network learned from single-cell CRISPR screens.*

---

## 0. Honest status (read first)

| Item | Status |
|---|---|
| Core claim | On one dataset (Norman 2019), CIPHER ties additive baselines on overall accuracy (median) and halves the error on the non-additive (interaction) part. Mean overall accuracy is slightly *worse* (0.79 vs 0.82). |
| Leakage 1 | The dev split (seed 100) and test splits 0-2 are independent random halves of the same 131 doubles, so tuning used doubles that are later test pairs. **All test numbers so far are not publishable.** |
| Leakage 2 | HVGs were selected on all cells, including held-out doubles. |
| Novelty | Not yet checked against the closest methods (SAMS-VAE, sVAE+, DCD-FG, NODAGS-Flow, GEARS, CPA, biolord, scGPT, GenePert). |
| Baselines | Only simple ones so far. No deep-learning competitors yet. |
| Datasets | One for the main task. Reviewers will expect at least 3. |

Phase 1 fixes this before anything else.

---

## Phase 1: Fix the evaluation protocol (week 1, GPU)

1. **Frozen splits.** Write `results/splits/norman_splits.json` once and never change it:
   * GEARS-style categories for doubles: *seen 2/2* (both singles trained), *seen 1/2*, *seen 0/2*
     (needs gene embeddings, Phase 3). Single perturbation holdout: *unseen single*.
   * 5 outer test folds. Inside each fold's training set, a validation subset for tuning and
     early stopping. **Hyperparameters are chosen on validation only, then frozen for all folds.**
2. **Train-only preprocessing.** HVGs from training cells only (or a fixed gene list chosen
   from control cells only). Keep all 105 target genes.
3. **Full data.** No subsampling to 400 cells per condition on GPU.
4. **Metrics** (report all, per condition, with median, mean and 95% bootstrap CI):
   * Pearson and MSE of predicted vs true expression change, on top-20 DE genes and on all genes
     (GEARS standard).
   * Same metrics after removing systematic variation (subtract the mean training-perturbation
     effect; Vinas Torne et al. 2025, "Systema"). This guards against metrics inflated by
     perturbation-unspecific shifts.
   * Interaction part: correlation and MSE of the residual `delta_AB - delta_A - delta_B` on
     its top-20 genes.
   * Direction-of-change accuracy on DE genes.
   * Distributional metric (energy distance or MMD between predicted and observed cells), since
     CIPHER is generative. Mean-only baselines get N/A.
5. **Statistics.** Paired one-sided Wilcoxon signed-rank test per metric across test conditions,
   CIPHER vs each baseline, Benjamini-Hochberg across comparisons, effect sizes reported.
6. **Seeds.** 5 seeds per fold for every learned method.

Baselines on Norman (all with identical splits and preprocessing):

| Baseline | Why | Code |
|---|---|---|
| no change, mean training perturbation | trivial; the second is the "Systema" baseline | ours |
| additive (log and linear), scaled additive | GLiMMIRS / MIMOSCA nulls | ours |
| linear model with PCA gene embeddings | Ahlmann-Eltze et al. 2025 showed it beats deep models | their code |
| GenePert (ridge on GenePT embeddings) | strong simple embedding baseline | their code |
| CPA | additive latent model with adversary | `cpa-tools` |
| GEARS | GNN, the standard combinatorial benchmark | `cell-gears` |
| biolord | disentangled VAE | `biolord` |
| scGPT fine-tuned | foundation model, reviewers will ask | scGPT repo (GPU) |
| SAMS-VAE / sVAE+ | closest generative competitors (sparse mechanism shift) | authors' code |

---

## Phase 2: Simulation with ground truth (Fig. 1 and 2, CPU or GPU)

Simulator: GLiMMIRS-sim style NB counts plus a known cyclic nonlinear regulatory network, with
controlled guide efficacy, MOI, cells per perturbation, fraction of interacting pairs, and
interaction type. Also a purely multiplicative simulator with **no** interactions (null).

| Question | Readout | Compared with |
|---|---|---|
| Recovers guide efficacy? | corr / MAE vs true rho_k | indicator GLM, Mixscape (pertpy), MIMOSCA-style EM |
| Finds escaped cells? | per-cell AUROC | Mixscape |
| Unbiased effect sizes? | slope vs truth as a function of efficacy | GLiMMIRS-base indicator and probability models |
| Hallucinates interactions under the null? | interaction magnitude and false-positive rate under shuffled-guide and no-interaction nulls | GLiMMIRS-int |
| Detects real interactions? | power curves vs effect size, MOI, cells (mirror GLiMMIRS Fig. 2) | GLiMMIRS-int |
| Recovers the network? | AUPRC of edges, sign accuracy | LLCB (official code), DCD-FG, NODAGS-Flow, GENIE3 |
| Which interaction types can the model express? | synergy, buffering, suppression, epistasis, dominance (Norman's categories); theory + empirical | linear SCM (can express none) |

Add a short theory section in STAR Methods: existence/uniqueness of the steady state when
||W||_2 < 1, and a first-order expansion showing interaction terms appear only through the
curvature of the activation (so the linear model is exactly additive).

---

## Phase 3: Main benchmark across datasets (Fig. 3)

| Dataset | Type | Task |
|---|---|---|
| Norman 2019 (K562, CRISPRa) | 105 singles, 131 doubles | seen 2/2, 1/2, 0/2 doubles; unseen singles |
| Wessels 2023 (Cas13 RNA-targeting, combinatorial) | combinatorial knockdowns | unseen pairs, second modality of perturbation |
| combosciplex (CPA paper) | drug pairs | unseen drug combinations |
| Replogle 2022 K562 essential, RPE1 | singles at scale | unseen singles; cross cell line transfer |
| Adamson 2016 (UPR) | singles + a few combos | small-data regime |

Extension needed for unseen genes: make perturbation effects a function of a gene embedding,
`a_k = f(e_k)`, with e_k from GO graph (as GEARS), GenePT text embeddings, or ESM protein
embeddings. Compare which prior works best.

Additional analyses:
* Data efficiency: down-sample cells per perturbation (25, 50, 100, 200, all) and fraction of
  training doubles (0%, 25%, 50%, 75%).
* Uncertainty: deep ensemble (5 models). Show that predicted uncertainty correlates with error
  and that 90% intervals cover ~90% of held-out expression changes.
* Runtime and memory vs number of cells (up to the 2.5M-cell Replogle genome-wide screen).

---

## Phase 4: Genetic interaction discovery (Fig. 4)

1. Recompute Norman's GI metrics for every measured pair (their linear model: coefficients c1,
   c2, magnitude, model fit, equality, dcor) and their categories (synergy, suppression,
   buffering, epistasis, neomorphic).
2. For held-out pairs, predict the category from CIPHER's predicted profile. AUROC per
   category vs baselines (additive cannot predict any).
3. Rank all **untested** pairs among the 105 genes (about 5,400 pairs) by predicted
   interaction strength. Release as a resource table.
4. Mechanism: decompose each predicted interaction through the network (which regulatory
   nodes saturate or feed back), and link nodes to gene programs.
5. **Experimental validation (strongly recommended):** test 10-20 top predicted synergistic or
   buffering pairs plus 5 predicted-additive controls in K562 CRISPRa with dual guides;
   readout by small Perturb-seq or qPCR panel of predicted genes. If not possible in the lab,
   use a dataset released after training as prospective validation.

---

## Phase 5: Guide efficacy on real data (Fig. 5)

* **Replogle CRISPRi**: the target gene's own expression gives a per-cell knockdown readout.
  Correlate CIPHER's posterior P(guide worked) with observed target knockdown for well-expressed
  targets (held out from the cis term for this test). Compare with Mixscape.
* **Dixit 2016**: concordance of effect profiles between guides targeting the same gene, with
  vs without the efficacy model; compare to MIMOSCA's EM.
* **Gasperini 2019 enhancer screen** (GLiMMIRS data): reproduce the multiplicative finding, then
  test enhancer-pair interactions with CIPHER and compare calls and calibration with GLiMMIRS-int
  (including Cook's distance outlier checks). Negative controls: shuffled guides, distal genes.

---

## Phase 6: Network and programs (Fig. 6)

* Gene-level effects: total effect = Jacobian of predicted log-expression w.r.t. each
  perturbation; split into direct (cis and direct gene term) and network-mediated parts, the
  analogue of LLCB's direct vs total effects.
* **CausalBench** (Chevalley et al.) on Replogle K562 and RPE1: standard statistical and
  biological evaluation of inferred networks; compare with DCD-FG, NOTEARS-style, GENIE3, LLCB.
* Validate TF -> target edges against ENCODE K562 ChIP-seq, CollecTRI / DoRothEA, and ABC
  enhancer-gene links (as LLCB did).
* Programs (rows of V): GO/KEGG enrichment; compare module quality with scBC, NMF, and Norman's
  programs.
* **Disease link (for Cell Genomics):** S-LDSC heritability enrichment of SNPs linked (ABC) to
  CIPHER programs for blood cell traits (Vuckovic 2020) and immune traits, as LLCB did.

---

## Phase 7: Multi-omic and drug x gene extension (Fig. 7)

CAT-ATAC (GSE288996): 20 CRISPRi perturbations x {DMSO, dasatinib}, RNA + ATAC + guide.
* Add an ATAC decoder (peak-level Bernoulli or Poisson) sharing the same regulatory state.
* Treat dasatinib as one more perturbation unit, so drug x gene interactions come from the
  same network.
* Tasks: (i) predict held-out perturbation x drug profiles in RNA and ATAC; (ii) check that the
  model recovers the paper's HIC2 -> ZFPM2 -> TCF4 / WNT axis without being told;
  (iii) compare with Pando GRN used in the paper.

---

## Phase 8: Robustness, ablations, reproducibility (Supplement)

* Ablations on all main datasets: no efficacy model, linear network, no direct term, cell
  state on, adversary on, d_h in {16, 32, 64, 128}, gamma in {0.5, 0.9, 0.99}.
* Sensitivity to every hyperparameter around the chosen value.
* Separate repository `CIPHER` with: pip-installable package, unit tests, a tutorial notebook
  reproducing Fig. 3 on Norman, config files for every figure, Zenodo DOI for code and results.

---

## Cell Press submission checklist

* Highlights (3-4 bullets, max 85 characters each), eTOC blurb, graphical abstract.
* Cell Reports Methods: "Motivation" box. Cell Genomics: "In brief".
* STAR Methods with Key Resources Table, Resource Availability (lead contact, materials, data
  and code availability with accession numbers and DOIs), Quantification and Statistical
  Analysis (tests, n, what n is, error bars).
* "Limitations of the study" section.
* Declaration of generative AI use in the writing process (Cell Press policy): AI tools must be
  disclosed and cannot be listed as authors; authors take responsibility for all content.
* Source data for every figure panel.

---

## Order of work and compute

| Phase | Where | Rough GPU time |
|---|---|---|
| 1 protocol fix + Norman rerun with baselines | lab GPU | 1-2 days |
| 0 literature search (novelty) | here | - |
| 2 simulation | here (CPU) or GPU | hours |
| 3 multi-dataset benchmark | lab GPU | 1-2 weeks incl. baselines |
| 4 interactions | GPU + wet lab | days (+ experiments) |
| 5 guide efficacy | GPU | days |
| 6 network, CausalBench, LDSC | GPU + CPU | 1 week |
| 7 CAT-ATAC | GPU | 1 week |
| 8 robustness, packaging | GPU | 1 week |

**Go / no-go after Phase 1:** if, on the clean protocol, CIPHER does not beat the scaled additive
baseline on interaction metrics with p < 0.05 across folds, revisit the model before spending
time on Phases 3-8.
