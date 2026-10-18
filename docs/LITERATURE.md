# Literature check for CIPHER (October 2026)

Question: is CIPHER new, and what must it be compared against?

## Short answer

CIPHER's headline idea is **not new on its own**: a nonlinear regulatory network solved to a
steady state, so that two perturbations interact through the network. **CLAMP** (ICML 2026
workshop spotlight) does this on Norman 2019 with Hill kinetics and implicit gradients, and
reports non-additive pair predictions learned from singles. NODAGS-Flow (2023) learns nonlinear
cyclic models from interventions, and SCCVAE (2026) places a learned (linear, acyclic)
regulatory network inside a VAE.

What still looks open, as a combination, and must be the paper's claim:

1. **Guide efficacy and network interactions in one count model.** CLAMP clamps perturbed genes
   to their observed level, so it assumes the edit worked, needs the target measured, and cannot
   handle enhancers or drugs. ContrastiveVI+ models guide efficacy but not combinations or
   interactions. CIPHER marginalises over which guides worked and treats any unit (gene,
   enhancer, drug) as a learned input to the network.
2. **Interaction prediction that holds up under strict evaluation.** Two 2025-2026 benchmarks
   (Ahlmann-Eltze et al., Gao) found that current predictors do not beat the additive baseline
   and do not learn interactions that transfer to unseen pairs; Systema shows standard metrics
   are inflated by systematic variation. If CIPHER beats additive *on the interaction part*
   under these protocols, with calibrated uncertainty, that is a clear contribution.
3. **Multiplicative null built in** (GLiMMIRS), with the network adding only the deviation.

Nothing here is confirmed until the clean benchmark (PAPER_PLAN Phase 1) is done.

## Closest methods

| Method | What it does | Overlap with CIPHER | Difference |
|---|---|---|---|
| **CLAMP** (Gallagher-Syed et al., ICML 2026 GenBio workshop) | Hill-kinetics GRN, perturbation clamps gene, fixed-point solver with implicit gradients, one shared network; k-gene perturbations compositionally; Norman 2019; ChIP-seq validation | Very high: steady-state nonlinear network, pairs from singles, Norman | No guide efficacy, perturbation = clamp of measured gene, no count likelihood stated, workshop paper |
| **NODAGS-Flow** (Sethuraman et al., AISTATS 2023) | Nonlinear cyclic causal model via residual flows; Perturb-CITE-seq, 61 genes | Cyclic, nonlinear, interventional | Network discovery focus, small graphs, no count model, no pair prediction |
| **SCCVAE** (Liu, Zhang, Uhler, PLoS Comput Biol 2026) | VAE with learned linear DAG among latent modules; perturbation = shift intervention | Network inside a VAE, shift interventions | Linear and acyclic (no interactions), singles only, penetrance as a fitted scalar |
| **SAMS-VAE** (Bereket and Karaletsos, NeurIPS 2023) | Sparse additive latent shifts per perturbation | Generative, compositional | Additive by design: no interactions |
| **CPA** (Lotfollahi et al., MSB 2023) | Adversarial basal latent + additive perturbation embeddings | Our first version | Additive in latent space |
| **GEARS** (Roohani et al., Nat Biotechnol 2024) | GNN over GO graph; unseen genes and pairs; GI subtypes | Main pair-prediction competitor | Learned from graph prior, no efficacy model |
| **scLAMBDA** (2024 preprint) | Generative model with language-model gene embeddings; singles and pairs | Pair prediction | Additive-style composition |
| **PerturbNet** (MSB 2025), **biolord**, **scGPT**, **PertSpectra** (PSB 2026), **MechPert**, **Stable-Shift** (2026) | Other predictors, mostly for unseen single genes | Benchmarks | |
| **ContrastiveVI+** (Weinberger et al., NeurIPS 2024 workshop) | Infers which cells were truly edited, separates perturbation from background variation | Guide efficacy / escape | Singles only, no network or interactions |
| **Mixscape** (Papalexi et al. 2021; pertpy) | Classifies perturbed vs escaping cells | Escape detection | LDA + Gaussian mixture, singles |
| **GLiMMIRS** (Zhou et al. 2024) and **SCEPTRE** | NB GLMs with guide-efficiency probability; calibrated tests | Efficacy, multiplicative null | Per-pair statistics, no prediction for unseen pairs |
| **LLCB** (Weinstock et al. 2024), **DCD-FG** (Lopez et al. 2022) | Cyclic linear / factor-graph network inference | Network | Linear, bulk (LLCB) |

## Evaluation papers the paper must follow

* **Ahlmann-Eltze, Huber, Anders, Nat Methods 2025**: no deep model (scGPT, scFoundation, GEARS,
  CPA, ...) beat the additive model on doubles. Use their linear baselines.
* **Systema** (Vinas Torne et al., Nat Biotechnol 2025): remove systematic variation before
  scoring; report perturbation-specific metrics.
* **Gao, arXiv 2610.18880 (NeurIPS 2026 workshop)**: splits each pair prediction into additive
  reference plus interaction correction; current models' corrections do not generalise; larger
  corrections mean larger errors. Uses Norman (GEARS preprocessing) and Joung-Zhang combinatorial
  data. CIPHER must be scored with this decomposition (our "residual" metric is the same idea)
  and on Joung-Zhang as a second combinatorial dataset.
* A counterpoint preprint (bioRxiv 2025.10.20.683304) argues deep models do beat uninformative
  baselines under well-calibrated metrics. Report both kinds of metric.

## Consequences for the plan

* Reposition the claim (title, abstract) from "network-induced interactions" to
  "efficacy-aware generative model whose interaction predictions survive strict evaluation".
* Add baselines: CLAMP (if code is released; otherwise reimplement the clamp idea as an ablation:
  CIPHER with perturbation fixed to observed target expression), SCCVAE, ContrastiveVI+ (escape),
  scLAMBDA.
* Add dataset: Joung-Zhang combinatorial TF screen.
* Add Gao's reliability analysis: does CIPHER's interaction size, and its posterior uncertainty,
  predict its own errors (failure-detection AUROC, selective abstention)?

## Sources

* CLAMP: https://icml.cc/virtual/2026/70834
* NODAGS-Flow: https://arxiv.org/abs/2301.01849
* SCCVAE: https://pmc.ncbi.nlm.nih.gov/articles/PMC12885384/
* SAMS-VAE: https://arxiv.org/abs/2311.02794
* GEARS: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11180609/
* Ahlmann-Eltze et al.: https://github.com/const-ae/linear_perturbation_prediction-Paper
* Systema: https://brbiclab.epfl.ch/projects/systema
* Gao 2026: https://arxiv.org/html/2610.18880
* Calibrated-metrics counterpoint: https://www.biorxiv.org/content/10.1101/2025.10.20.683304v1.full
* ContrastiveVI+: https://arxiv.org/abs/2411.08072
* Mixscape (pertpy): https://pertpy.readthedocs.io/en/1.0.2/tutorials/notebooks/mixscape.html
* PerturbNet: https://link.springer.com/article/10.1038/s44320-025-00131-3
* scLAMBDA: https://www.biorxiv.org/content/10.1101/2024.12.04.626878.full.pdf
* Stable-Shift: https://arxiv.org/abs/2606.24940
* MechPert: https://arxiv.org/pdf/2602.13791
* PertSpectra: https://psb.stanford.edu/psb-online/proceedings/psb26/chang_s.pdf
