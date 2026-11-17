# World models for cytopathology: literature scan and proposal

Status: proposal only. Nothing here has been implemented or run. Literature was
searched on 2026-11-17; claims marked *(search summary)* come from search-result
abstracts and were not checked against the full paper.

---

## 1. Summary

* No published work was found that builds a **world model** (a latent state plus an
  action-conditioned predictor of what will be observed next) for cytology, or for
  microscopy slides of any kind. Six searches turned up cytology foundation models,
  slide-navigation agents and world models in other medical modalities, but not the
  combination.
* Cytology is a better fit for the idea than histology, because the microscope has a
  real third action. A histology section is about 4 µm thick and effectively flat. A
  cytology preparation contains three-dimensional cell clusters, and cytologists
  focus up and down through them. Pan, zoom and **focus** are genuine actions with
  observable consequences.
* Proposed first step: a small **focal world model** on a public z-stack dataset
  (CCCID, 230 MB), which predicts the embedding of another focal plane from the
  current one and the focus step. It has explicit baselines and a stop criterion
  (§5), so a negative result is cheap.

## 2. What "world model" means here

A world model has three parts: an encoder that maps an observation to a latent state
`s_t`, a predictor `s_{t+1} = f(s_t, a_t)` conditioned on an action, and optionally a
head that reads out reward or task belief. Prediction is usually done in latent
space (JEPA-style) rather than in pixels.

For a glass slide the tissue does not change, so the "dynamics" are the dynamics of
*observation*:

| Action | Meaning | Why it is non-trivial in cytology |
|---|---|---|
| Δz | change focal plane | cells overlap in depth; nuclei of a cluster come into focus at different planes |
| Δx, Δy | pan | diagnostic cells are rare and scattered over an empty-looking slide |
| Δmag | zoom | low-power cues (cluster shape, cellularity) decide where to look at high power |

A model that predicts these well must encode 3D cluster structure and slide-level
context, neither of which a single-patch encoder is trained to capture.

## 3. Related work

### Cytology foundation models (encoders, no predictive model)
* **CytoFM**: ViT-B trained with iBOT on about 1.4 M patches from breast, cervical
  and thyroid cytology; beats a histology encoder (UNI) on 2 of 3 tasks
  *(search summary)*. [arXiv 2504.13402](https://arxiv.org/abs/2504.13402)
* **UniCAS**: DINOv2 pretraining on 48,532 cervical WSIs, over 80 M patches
  *(search summary)*. [Cell Reports Medicine](https://www.cell.com/cell-reports-medicine/fulltext/S2666-3791(25)00643-3)
* **DINOv3 cervical study (2026)**: a cytology-trained extractor matches or exceeds
  large histology encoders with less data *(search summary)*.
  [Springer](https://link.springer.com/article/10.1186/s42047-026-00241-8)
* **Huang et al.**: parameter-efficient adaptation of a large encoder for cervical
  WSI screening with slide labels only. [arXiv 2407.11486](https://arxiv.org/abs/2407.11486)
* **Cyto-SSL (AAAI 2026)**: nucleus-centred perturbations with self-distillation
  *(search summary)*. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/38289/42251)

All of these treat a patch as a flat, single-plane image.

### Sequential slide examination (actions, but no learned dynamics)
* **WSI-Lab** (NeurIPS 2026): a Gymnasium environment that frames WSI review as a
  partially observable decision problem, with viewport, slide context, history and
  a diagnostic-belief estimate as state. The abstract mentions no learned dynamics
  model, no cytology and no focus action. [NeurIPS page](https://neurips.cc/virtual/2026/161745)
* **Pathology-CoT**: records pathologists' viewer navigation and trains an agent on
  it; reports that unguided vision-language models navigate poorly
  *(search summary)*. [arXiv 2510.04587](https://arxiv.org/abs/2510.04587)
* **PathFound**: reinforcement learning for multi-turn evidence seeking
  *(search summary)*. [arXiv 2512.23545](https://arxiv.org/abs/2512.23545)
* **Mohamad et al.** (BIOIMAGING 2025): goal-conditioned RL navigation on histology
  *(search summary)*. [SciTePress](https://www.scitepress.org/PublishedPapers/2025/133009)

### World models in neighbouring medical fields
* **Robotic neck ultrasound**: a latent diffusion model predicts future frames from
  context frames and probe motion; a policy trained against it reaches 70.0 %
  (carotid) and 65.0 % (thyroid) success in closed loop.
  [arXiv 2607.21918](https://arxiv.org/abs/2607.21918). This is the closest
  structural analogue: probe motion there, stage and focus motion here.
* **Cardiac action-conditioned JEPA**: disease onset as the action; helps in
  low-label regimes *(search summary)*. [arXiv 2604.22618](https://arxiv.org/abs/2604.22618)
* **"Towards World Models in Biomedical Research"**: a position paper defining
  biomedical world models as latent states plus intervention-conditioned dynamics.
  Its abstract does not mention pathology, microscopy or cytology.
  [arXiv 2606.05925](https://arxiv.org/abs/2606.05925)

### Evidence against the idea
* **"Pretext Matters"** compares SSL objectives on ultrasound and histopathology and
  finds that on histopathology, where the signal is spatially localised, plain
  joint-embedding methods beat predictive (JEPA) ones; JEPA wins on liver
  ultrasound, where the signal is global anatomy.
  [arXiv 2603.22649](https://arxiv.org/abs/2603.22649). Cytology signal is even more
  localised (single cells), so a spatial masked-prediction JEPA may well lose to
  DINO-style training. The proposal below therefore predicts across *focus*, where
  the views are physically different observations of the same cells, and treats
  DINO-style encoders as the baseline to beat.

### Multi-focus cytology
* Focus selection per cell is a known step in oral-cancer screening pipelines on
  multi-focus WSIs. [arXiv 1910.10549](https://arxiv.org/abs/1910.10549)
* Most public cytology sets (Herlev, SIPaKMeD, CRIC) are single-plane.

## 4. Data

| Dataset | Content | Access | Checked |
|---|---|---|---|
| **CCCID** | 639 fields of view × 11 focal planes at 1.0 µm (7,029 images, 384 × 384, 20×), SurePath cervical LBC, Pap stain. Classes: NILM 273, LSIL 93, HSIL 69, SCC etc. 204, agreed by six cytotechnologists | [Zenodo 10.5281/zenodo.18904734](https://doi.org/10.5281/zenodo.18904734), 5 archives, 230 MB, reachable from this environment | data note read; Zenodo record queried |
| Cervix93 | 93 image stacks at 40×, cervical | [GitHub](https://github.com/parham-ap/cytology_dataset), [arXiv 1811.09651](https://arxiv.org/abs/1811.09651) | search summary only |
| Breast FNAC | 321 patients, 470 WSIs, patch labels C1–C5 | [Zenodo](https://zenodo.org/records/20763900) | search summary only |
| HiCervix | 40,229 cells from 4,496 WSIs, 29 classes | paper | search summary only |
| UFSC Multi-Cyto | 17,422 patches from 28 WSIs, three stains | [Mendeley](https://data.mendeley.com/datasets/b8bygdxr7r) | search summary only |

Two caveats on CCCID:

1. **Licence mismatch.** The F1000Research data note states CC BY 4.0; the Zenodo
   record metadata says CC BY-NC 4.0. Treat it as non-commercial until resolved.
2. **No specimen identifiers.** The data note does not say how many slides or
   patients the 639 fields come from. Fields from the same slide can land in both
   train and test, which inflates any classification number. Results on CCCID can
   support a comparison between methods under the same split, but not a claim about
   diagnostic accuracy.

No public cytology dataset with recorded cytologist navigation was found.

## 5. Proposal

### Stage 0: focal world model on CCCID (pilot)

* **Encoder** `E`: a small ViT, or a frozen DINOv2 / CytoFM backbone with a trainable
  projection.
* **Predictor** `P(E(x_z), Δz) → ŝ_{z+Δz}`, trained to match a stop-gradient or EMA
  target `E'(x_{z+Δz})`, with a variance/covariance regulariser against collapse.
  Δz ranges over −10…+10 µm.
* **Questions and baselines**

  | Question | Metric | Baseline that must be beaten |
  |---|---|---|
  | Does the predictor use the action? | latent prediction error on held-out fields | copy predictor (`ŝ = s_z`) and a predictor with Δz shuffled |
  | Does it learn depth structure? | linear probe: regress a field's best-focus offset from one off-focus plane | same probe on frozen DINOv2 / CytoFM features |
  | Are the features more useful? | 4-class linear probe from the centre plane and from planes ±3–5 µm off focus | same probe on frozen DINOv2 / CytoFM; DINO-style training across focal planes as views with no action input |

* **Protocol**, fixed before any run, following the lessons of `docs/HiCAST.md` §6
  (a configuration tuned on one donor did not transfer): one stratified split by
  field of view into train / validation / test; all tuning on validation; test
  evaluated once per method with 3 seeds; all baselines get the same tuning budget.
* **Stop criterion.** If the action-conditioned predictor does not beat the copy and
  shuffled-action baselines, or the off-focus probes do not improve over the
  action-free DINO-style baseline, stop and write up the negative result.
* **Cost.** 7,029 small images; feasible on a single GPU in hours. This environment
  has no GPU, so only a reduced CPU version could be run here.

### Stage 1: pan and zoom on whole slides
Extend the action to (Δx, Δy, Δmag) using WSI data (breast FNAC, a cervical WSI
set). The predictor takes a low-power view and a target location and predicts the
high-power embedding. Evaluation: prediction error against a copy-nearest-neighbour
baseline, and whether predicted embeddings rank regions containing abnormal cells
above random regions.

### Stage 2: screening as planning
Use the Stage 1 model inside a WSI-Lab-style environment: maintain a slide-level
belief, choose the next view by expected information gain computed in latent space,
stop when the belief is confident. The clinically relevant metric is sensitivity
for abnormal slides at a fixed number of high-power fields read, compared with
exhaustive tiling and with attention-based multiple-instance learning.

### Stage 3 (speculative)
Virtual refocusing: scan one plane and predict the embeddings of others, to recover
part of the benefit of z-stack scanning without its 5–10× cost in time and storage.

## 6. Risks

| Risk | Consequence | Mitigation |
|---|---|---|
| Predictive objectives underperform DINO-style ones on localised signal (Pretext Matters) | no representation gain | Stage 0 compares directly and has a stop criterion |
| Focus prediction is solved by a blur shortcut | predictor learns optics, not cell structure | best-focus-offset probe plus class probe; check error on thick clusters vs single cells |
| CCCID is small, single-site, single-scanner, no specimen IDs | results do not generalise; leakage | use only for method comparison; confirm on Cervix93 (different magnification and source) |
| No z-stack WSI data in public | Stages 1–2 cannot include focus | keep focus and pan/zoom as separate models until such data exists |
| No navigation logs for cytology | cannot compare with human search | evaluate against exhaustive tiling instead |

## 7. Sources

Listed inline above. Searches run: world model + cytopathology; JEPA + pathology;
cytology foundation models; slide-navigation agents; world models in
pathology/microscopy; z-stack cytology datasets; public cytology WSI datasets.
