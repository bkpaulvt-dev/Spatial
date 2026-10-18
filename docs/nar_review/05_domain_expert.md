# Referee report — Reviewer 2 (spatial domain method developer)

**Manuscript:** "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods"
**Submitted to:** Nucleic Acids Research
**Material reviewed:** main text (`paper/main.tex` with `results/paper_macros.tex`), Supplementary Information (`paper/supplementary.tex`, tables in `results/supp/`), Figures 1–5 (`docs/figures/nar_fig*.png`). I also checked the R mclust 6.0.1 behaviour the manuscript depends on (see Major 1).

---

## 1. Summary of the submission

The authors compare 13 published spatial-domain methods (HiSTaR, GraphST, BANKSY at two λ, SpaGCN, STAGATE, SEDR, SpaceFlow, NichePCA, CCST, Spatial-MGCN, DeepST, BASS, BayesSpace) and three training-free baselines (PCA, linear graph diffusion of PCs, and an edge-preserving variant, "AnisoST") on 20 annotated sections: 12 Visium DLPFC sections, 3 STARmap mPFC sections and 5 MERFISH hypothalamus sections. Every method is given the true number of domains and run with default or tutorial settings on CPU. The paper reports three findings:

1. **Accuracy.** Linear diffusion has the highest pooled mean ARI (0.587, against 0.594 for BASS and 0.554 for BANKSY λ=0.8). A hierarchical bootstrap over five "clusters" (three DLPFC donors, STARmap, MERFISH) puts it above 14 of 16 methods.
2. **Robustness ("clustering lottery").** On a fixed embedding, 20 single-start Gaussian mixture fits differ by 0.18 ARI on average (up to 0.60). Running R mclust on permuted rows changes ARI by 0.10 on average (up to 0.37). Choosing the best of 20 starts by likelihood helps 6 of 12 methods and hurts 5, because likelihood and ARI are not related on MERFISH.
3. **Reproducibility.** A port of HiSTaR gives a median DLPFC ARI of 0.51, not the reported 0.65. Spatial-MGCN's released test scripts pick the reported epoch by ARI against the annotation, which inflates ARI by 0.147 in the authors' runs.

The paper is honest about many of its limitations: the reference was chosen after the means were seen, intervals are wide, and default settings were used. The bootstrap and the equivalence margin are a step up from the usual "bold the best median" tables. The code-audit idea is useful. However, as submitted, the manuscript has four problems that would each block publication. The central mclust "spot order" result appears to be an artefact of mclust's documented random subsampling. The headline comparison gives the baselines a different clustering protocol from the methods they are compared with. The data and annotation base is too narrow and partly circular for a 2026 benchmark. And it names a third-party method for label leakage before the authors of that method have been contacted (the manuscript itself carries a TODO saying so).

---

## 2. Novelty relative to existing benchmarks

The field already has several large benchmarks of spatial domain detection:

- Yuan et al., *Nat Methods* 2024 (SDMBench)
- Hu et al., *Genome Biol* 2024 (clustering/alignment/integration; they also swap each method's clustering step)
- Chen et al., *iMeta* 2025 (14 methods on ~600 real and simulated datasets)
- The NAR 2025 domain/domain-SVG benchmark cited as `nar2025bench`
- 2026 preprints such as spDDB (18 methods, 36 datasets, six technologies) and the "Beyond benchmarking"/SACCELERATOR consensus paper, which argues that manual annotations should not be treated as ground truth and that benchmarks are too focused on Visium brain data

Against these, the manuscript covers fewer technologies, fewer datasets and fewer methods.

**Is the "clustering lottery" new?** Only in part. The facts behind it are already known:
- Single-start EM is unstable. Nobody uses single-start GMM in practice.
- Seed sensitivity of deep methods is documented (cited `nar2025bench`).
- Swapping the clustering step reorders methods (Hu et al. 2024).
- Many pipelines (STAGATE, GraphST, SEDR) hard-code `set.seed()` before calling mclust. The community knows this step is seed-dependent, which is why the seed is fixed.

What is new is a direct, per-method measurement of the variance contributed by the clustering step alone, on fixed embeddings. Two points limit how much that adds:

- **(a) The measured quantity is inflated by design.** Single-start fits are compared, so the 0.18 range overstates what any real pipeline experiences. The realistic quantity is the spread across seeds of the clustering procedure each method actually ships: mclust with its default initialisation, sklearn `n_init` > 1, or Leiden at a matched resolution.
- **(b) The headline mclust "spot order" result is, I believe, mis-attributed** (Major 1).

Once (a) and (b) are corrected, the novelty becomes "a careful variance decomposition plus a code audit." That is a reasonable NAR contribution if it is done thoroughly and on a broader data base. As it stands, it is not enough.

**Bibliography.** Several key references carry `VERIFY` placeholders in `refs.bib`: the NAR 2025 benchmark, the "explanatory benchmark" 2026 preprint, GraphBG, HiSTaR and NichePCA author lists. I could not confirm the title "An explanatory benchmark of spatial domain detection…" in a quick literature search. The novelty claims rest on these citations, so every one must be verified before resubmission. The template header is still Bioinformatics Advances, not NAR.

---

## 3. Major concerns

### Major 1. The mclust "spot-order" result is very likely caused by mclust's random subsampling for initialisation, not by row order

**Concern.** In mclust ≥ 5.4, `mclust.options("subset")` defaults to **2000**. When n > 2000, the model-based hierarchical agglomeration that initialises EM runs on a *random subset* of 2000 observations, drawn with R's RNG.

I checked this in the authors' own environment (mclust 6.0.1, `mclust.options("subset") == 2000`). On a toy 3000 × 5 matrix:
- Two calls to `Mclust(X, G=4, modelNames="EEE")` that differed **only in `set.seed`** (no permutation) gave partitions with ARI 0.11 to each other.
- Forcing `initialization=list(subset=1:n)` made the result identical across seeds (ARI 1.00).

In `scripts/mclust_lottery.R`, each "permute" fit follows `set.seed(r)`, `rnorm(...)` and `sample(...)`. Both the order **and the RNG state** change, so the subset used for initialisation changes too. Three things point to this explanation:
- The data fit it exactly. STARmap sections have about 1050 cells (< 2000) and show a permutation range of **0.00** (`\mcPermMeanStarmap`, and Fig. 3b where the orange dots sit at zero). DLPFC (3500–4800 spots) and MERFISH (~5500 cells) show 0.12 and 0.11.
- The pilot invariance test (Supp. Table S17) shows the same pattern on the authors' own pipeline: "permute spots" is the only transformation that changes the answer, and it changes it most for PCA on MERFISH (0.39).
- For STARmap, the 1% noise perturbation does change results (0.22). That is a genuine sensitivity of hierarchical agglomeration to ties and near-ties on small data, and it should be reported as such.

The abstract's claim that "merely shuffling the order of the spots changed the ARI of R mclust by up to 0.37" is therefore misleading. What the experiment measures is mclust's seed dependence through subsampling. That is still relevant, because published pipelines fix a seed and present a single result as deterministic, but it is a different and less surprising finding.

**Required analysis.** Rerun the mclust experiment with three arms on the same embeddings:
- (i) seed varied, order fixed;
- (ii) order varied, seed fixed and the subset index mapped back to the same spots;
- (iii) `initialization = list(subset = seq_len(n))`, i.e. full-data hierarchical initialisation, with permutation.

Report also the seeds actually hard-coded by STAGATE (2020), SEDR (2023) and GraphST, and what ARI each yields relative to the seed distribution. Rewrite the abstract, Results §"Robustness to spot order" and Fig. 3b accordingly.

**Feasibility:** fully CPU-feasible. It is the same script with an extra argument, about 280 embeddings × 30 fits.

### Major 2. The headline comparison gives baselines and methods different clustering protocols

**Concern.**
- In the "standard" comparison (Fig. 2, Supp. Tables S3/S5, abstract), the training-free baselines are scored **with the 20-start best-likelihood GMM**. Supp. Table S3 lists "Linear diffusion: own —, 20-start 0.558". Fig. 2a's caption confirms this.
- Every published method is scored with its own clustering instead: 3-start GMM, Leiden, k-means, or mclust.
- Methods §"Clustering protocols" contradicts this: it says the baselines use a 3-start GMM with a fixed seed under "Standard". Which is it?

Either way, the claim "linear diffusion had a higher mean ARI than 14 of 16 methods" mixes encoder quality with clustering protocol. That is exactly the confound the paper warns about in Recommendation 4.

Matched comparisons are available, but they are not in the main text. Under the matched 20-start protocol (Supp. Table S6) the result is weaker: 8 of 13 comparisons favour the baseline and 5 are unresolved (SEDR, HiSTaR, STAGATE, AnisoST, BANKSY λ=0.8).

There are further inconsistencies:
- Supp. Table S2 lists HiSTaR's own clustering as R mclust EEE, the main text as a 3-start sklearn GMM, and the reproducibility section reports both.
- BANKSY's own clustering is "Leiden / mclust (package)" in S2 but a GMM in the main text.
- SpaceFlow is "Leiden at a fixed resolution" in S2 but "Leiden with a search for the true number of domains" in the main text.

**Required analysis.**
- (a) Make the matched-protocol comparison (same clusterer, same number of starts, same seed policy for every embedding) the primary analysis in Fig. 2.
- (b) Additionally report a method × clusterer matrix: mclust EEE with full-data initialisation, sklearn GMM tied/full with n_init = 20, k-means with n_init = 100, and Leiden/Louvain with a resolution search to K. Hu et al. 2024 did this for a subset of methods; the authors have all the embeddings needed to do it comprehensively.
- (c) Give the baselines a "default" clustering of the same type as the competitors' (e.g. single mclust call) so the asymmetry can be quantified.
- (d) Reconcile Supp. Table S2 with the main text.

**Feasibility:** CPU-feasible. All embeddings are already saved (`results/emb/csv`), so this needs re-clustering only.

### Major 3. Default-parameter runs: fairness, configuration errors and sanity checks against published numbers

**Concern.** "Default or published settings" is defensible as a scenario. In practice, though, several results look like configuration failures rather than method properties.

- **NichePCA's DLPFC result looks misconfigured.**
  - With its own Leiden clustering it scores 0.321 on DLPFC; the same embedding with a GMM scores 0.506.
  - Its 151673 map (Fig. 5) is a set of four or five large blocks unrelated to the layers. That is a sign of over-smoothing or a Leiden resolution that never reached K.
  - NichePCA's own paper reports competitive DLPFC performance.
  - NichePCA is also essentially the same operation as the authors' linear diffusion (neighbour aggregation of expression followed by PCA). The NichePCA versus linear diffusion gap is therefore mostly a clustering and configuration effect, not a methodological one.
- **SpaceFlow scores 0.312 on DLPFC.**
- **SEDR collapses with the 20-start GMM on STARmap.** It goes from 0.593 to 0.236, and from 0.406 to 0.167 on MERFISH. This suggests the tied-covariance GMM is applied to unscaled or degenerate embeddings, which is a property of the protocol, not of SEDR.
- **GraphST is run with one seed on DLPFC; STAGATE, CCST, Spatial-MGCN and BASS with one seed everywhere.** Yet the Supp. Table S18 coverage table says STAGATE, CCST, Spatial-MGCN and BASS have 3 seeds in the "standardised runner". Which numbers are in Fig. 2?
- **Supp. Table S12 is internally inconsistent.** Its caption says CCST, DeepST and BayesSpace "are still running", yet rows are shown.
- **The HiSTaR "reproduction" uses a PyTorch *port* of the official code, with no recorded commit** ("TO RECORD"). The reported value is itself marked "to be verified". A failure to reproduce with a re-implementation is not evidence about the official code.

**Required analyses.**
- (a) For every method, a **positive-control reproduction** on DLPFC: reproduce the authors' own published DLPFC number, at least on 151673 or the reported median, with their exact script, seed and clustering. Report it beside the benchmark value. Where reproduction fails, say so and contact the authors before attributing the gap.
- (b) For Leiden/Louvain-based methods, report whether the resolution search actually reached K on every section. If it did not, fix it.
- (c) Give every method, including the baselines, a small, equal, **label-free** tuning budget on development sections only, e.g. 3–5 values of the main spatial hyper-parameter selected by a label-free criterion. Report default and tuned results side by side. Calling equal tuning budgets "future work" is not acceptable for the paper's main claim.
- (d) Run the HiSTaR reproduction with the unmodified official repository (recorded commit) as well as the port.

**Feasibility:**
- (a) and (b) are CPU-feasible. The authors already ran every method on all 20 sections, and a 151673 reproduction is about 15–50 CPU-minutes per method.
- (c) is feasible if limited to the development sections and 3–5 settings per method: roughly 3× the current compute, which by Supp. Table S13 is days, not weeks, on 4 cores.
- (d) is feasible if the official code runs on CPU.

### Major 4. Dataset choice, annotation quality and possible circularity

**Concern.**

- **The datasets are too few and too unbalanced for the conclusions drawn.**
  - Three tissues, all brain, with the cortical-layer geometry that smoothing methods are known to favour.
  - The STARmap set is 3 sections × about 1000 cells × 166 genes with 4 layers. It receives the same bootstrap weight as an entire DLPFC donor and as the MERFISH series, and it drives several of the largest effects: HiSTaR seed SD 0.18, Spatial-MGCN leak +0.38, SEDR collapse.
  - The "five clusters" bootstrap has only 126 distinct top-level resamples. Percentile intervals with five top-level units are known to under-cover.
- **The annotations need scrutiny.**
  - The MERFISH hypothalamus regions and the STARmap layers are taken from the **BASS analysis repository**. If the MERFISH region labels were defined by the BASS authors, possibly with reference to cell-type composition or BASS output, then BASS "winning" on MERFISH (0.582) is partly circular. The authors acknowledge this only generically in the Limitations ("Annotations may themselves have been derived with methods similar to the ones evaluated"). They must document how each annotation was produced.
  - DLPFC labels are taken from the SEDR repository rather than directly from spatialLIBD (`layer_guess_reordered`). The authors should confirm they are identical, report the number of NA spots, and note the known boundary uncertainty of the manual DLPFC layers. The 7- versus 5-layer heterogeneity (donor 2) matters for K.
  - ARI against a single coarse annotation is a weak ground truth. Fig. 5 illustrates this: linear diffusion (ARI 0.59) places "Layer 4" as a band hugging the white matter instead of between L3 and L5. A wrong anatomical assignment is not penalised by ARI.
- **Important technologies are missing.**
  - Sequencing-based at high resolution: **Slide-seq V2** (e.g. mouse hippocampus/cerebellum), **Stereo-seq** (MOSTA embryo, or mouse brain), **Visium HD** (8 or 16 µm bins).
  - Imaging-based with large panels: **Xenium** (human breast, with pathologist annotation), **CosMx**, or the **Allen/Zhuang whole-mouse-brain MERFISH**.
  - The last of these is the strongest option. Its CCF registration gives region labels that are *independent of expression clustering*, which directly addresses the circularity issue.
  - A non-brain tissue (tumour, colon, or the human breast cancer Visium set used by Spatial-MGCN) is needed to test the "smoothing is enough" thesis outside laminar cortex.

**Required analyses.**
- (a) Add at least three datasets with independent or high-quality annotation, of which at least two are non-brain or non-laminar:
  - Allen MERFISH sections with CCF labels;
  - Xenium human breast with pathologist regions;
  - Visium HD or Stereo-seq with a published region annotation;
  - Slide-seq V2 hippocampus.
- (b) Document the provenance of every annotation in Supplementary Note 1, and run a leave-one-dataset-out analysis of the main ranking.
- (c) Report annotation-free and anatomy-aware metrics in the main text: missed or merged domains, layer order, and spatial contiguity (already in Supp. Table S12, but not discussed).
- (d) Replace or supplement the five-cluster percentile bootstrap with a mixed model (section nested in donor/dataset) or a dataset-stratified analysis, and state the effective sample size honestly.

**Feasibility:**
- Annotation documentation, the leave-one-out analysis and the mixed model are trivially CPU-feasible.
- New datasets: on CPU, Xenium and Visium HD sections hold 10^5–10^6 cells or bins. Training-free baselines, BANKSY, NichePCA and BASS scale. Several GNN methods (GraphST with dense adjacency, CCST, Spatial-MGCN, DeepST, BayesSpace) will not run in reasonable CPU time or 15 GB of memory. A defensible, CPU-feasible design is:
  - (i) use fields of view or crops of about 5–20k cells for all methods;
  - (ii) run whole sections only for scalable methods;
  - (iii) report infeasibility (time-out or out-of-memory) as a result, as SDMBench did.
- Visium HD at 16 µm bins over a cropped region is on the order of DLPFC size and is fully feasible.

### Major 5. Number of domains given to methods

**Concern.**
- Supplying the true K is common, but it interacts with the paper's own claims. Leiden-based methods (SpaceFlow, NichePCA, DeepST, SpaGCN) must *search* a resolution to hit K, and GMM-based ones receive it directly, so "K given" does not mean the same thing for every method.
- It also hides the most important practical failure mode: how to choose K without labels.
- On MERFISH, where likelihood and ARI are anti-correlated (Fig. 3c), the right K for a likelihood criterion is plausibly larger than the 8 annotated regions. That would explain why "better likelihood ≠ better domains".
- Spatial-MGCN's script also takes K from the labels (audit category L2). The same is true of the benchmark design itself, so the paper should be careful about how strongly it presents L2 as a problem.

**Required analysis.**
- (a) Report ARI at K−2…K+2 for all embedding-producing methods; this needs re-clustering only.
- (b) Add a label-free K-selection arm (BIC for GMM, a stability or silhouette criterion, or each method's recommended rule) and report the accuracy of the selected K.
- (c) Verify and report that the resolution search hit K for every Leiden run.

**Feasibility:** CPU-feasible, re-clustering of saved embeddings only.

### Major 6. Label-leakage claims and the ethics of naming a method before contacting its authors

**Concern.** The manuscript states in Results that "Spatial-MGCN's released test scripts … keep the best epoch for reporting". The main text itself contains `\todo{Contact the Spatial-MGCN authors and report their response before including this subsection.}`, and Supplementary Note 5 states that "the authors of the methods concerned have not yet been contacted." The same applies to HiSTaR (`\todo{Report the outcome of contacting the authors.}`).

Submitting a paper that publicly attributes label leakage to a named method without first giving its authors the chance to respond is not acceptable practice. It risks an unfair accusation:
- It is not shown that the *published* Spatial-MGCN numbers were produced with `DLPFC_test.py`'s best-epoch rule. Demonstration scripts that print the best ARI are common and are not necessarily what produced the paper's table.
- The inflation was estimated with the authors' modified pipeline. That pipeline keeps the unannotated spots and applies the rule to STARmap and MERFISH, where the released script was never used. The largest number (+0.38 on STARmap) comes from exactly that out-of-scope extension.
- The audit (Supp. Table S16) is a regex screen read by **one** author. Candidates in Banksy_py (L1 = 2) and DeepST (L4 = 3) were judged false alarms with no second reader.

The general point is valuable: selecting an epoch, seed or run by labels inflates results, and the paper's own oracle analysis (best-of-20 minus mean = 0.08) quantifies it method-independently. That point does not need a named example to stand.

**Required changes.**
- (a) Contact the Spatial-MGCN and HiSTaR authors, and the authors of any other method mentioned in the audit, before resubmission. Give them a reasonable time to respond, and report the response, or the absence of one, factually.
- (b) Compare the label-selected and final-epoch ARIs on the **DLPFC sections and settings that Spatial-MGCN actually published**, with the unmodified script, against the numbers in their paper. Only claim that published results were affected if they match the label-selected values.
- (c) Restrict the quantitative inflation to the datasets the released script covers, and present the STARmap/MERFISH extension as illustrative.
- (d) Have a second, independent reader adjudicate every audit candidate, report agreement, and publish the full `LEAKAGE_AUDIT.md` judgements as a supplementary file.
- (e) Until (a)–(b) are complete, describe the issue neutrally ("the released test script selects…") and move the named example to the Supplement. I would ask the editor not to accept a version that names the method without documented contact.

**Feasibility:** (b)–(d) are CPU-feasible: one method, 12 sections.

### Major 7. Interpretation of linear diffusion as a baseline

**Concern.** Linear diffusion, $H^{(t+1)} = (1-\alpha)H^{(t)} + \alpha D^{-1}AH^{(t)}$ applied to PCs, is standard neighbourhood smoothing. It is equivalent to a lazy random walk, a truncated personalised-PageRank/APPNP propagation, or SGC-style feature propagation (Wu et al. 2019). It is closely related to:
- BANKSY's neighbour-mean augmentation;
- NichePCA's neighbour aggregation;
- the spatial smoothing in SpatialPCA, PRECAST and MENDER;
- the spectral graph filtering underlying GraphBG.

The manuscript is mostly careful to call it a "baseline". But the abstract says "the highest mean ARI was reached by linear diffusion on DLPFC", and the Discussion says it "matched or outperformed every deep encoder we tested". Together with the separate name "AnisoST" for the edge-preserving variant, this invites readers to treat it as a new method.

Several further problems follow:
- The settings (α = 0.5, T = 10, k = 6, 30 PCs) were chosen on DLPFC donor 1, and the reference was chosen *after* the means were seen. That makes it, in effect, the most-tuned arm of the benchmark, even though the authors excluded the development sections in a sensitivity analysis.
- "Matched" is not supported. No equivalence test was met: zero methods are equivalent within ±0.03. The accurate statement is "was not significantly worse than any method".
- Fig. 1 and Fig. 2 classify BANKSY and NichePCA as "Statistical / Bayesian". They are training-free neighbourhood-aggregation methods, i.e. the same family as linear diffusion. Correctly grouped, the conclusion becomes "neighbourhood smoothing followed by a well-initialised GMM is hard to beat, whichever package implements it". That is a known message (NichePCA, BANKSY, GraphBG), now confirmed across more methods.
- The AnisoST section (edge-preserving diffusion as a negative result on MERFISH) reads as an abandoned method paper embedded in a benchmark. It should be shortened to a sentence or moved to the Supplement.

**Required changes.**
- (a) Describe linear diffusion explicitly as standard feature propagation, with citations, and make no novelty claims.
- (b) Pre-specify or justify the reference choice. Better, report all pairwise comparisons, or compare against a family of smoothing baselines: BANKSY λ = 0.8, NichePCA and linear diffusion, all under the same GMM.
- (c) Fix the family labels in Figs. 1–2.
- (d) Show the sensitivity of the conclusion to T and k on the *test* datasets (currently Supp. Fig. S2 covers only DLPFC). Single-cell data at 6-NN versus Visium spots at 6-NN represent very different physical radii.

**Feasibility:** CPU-trivial.

### Major 8. The recommendations only partly follow from the results

The recommendations are:
- (1) report the clustering protocol;
- (2) never select by labels;
- (3) report distributions over seeds and clustering runs;
- (4) compare encoders under the same clustering and include smoothing baselines;
- (5) report resources.

Recommendations (1), (3) and (5) are supported. (2) is uncontroversial and needs no data. (4) is supported in principle, but the paper does not follow it in its own headline analysis (Major 2).

Missing or unsupported:
- The paper shows that 20-start best-likelihood selection is "not a remedy". It then uses that protocol as its "robust" reference without saying what *should* be done. The data suggest concrete recommendations:
  - report the median over clustering seeds;
  - use full-data mclust initialisation (Major 1);
  - prefer consensus or ensemble clustering;
  - report label-free stability (e.g. ARI between runs) alongside accuracy.

  The authors should test at least one of these, e.g. consensus clustering over 20 starts, and show whether it reduces variance without labels.
- The claim that clustering variance is "about as large as the gap between most published methods" needs a direct comparison. Show the distribution of between-method gaps from published tables next to the within-embedding range on the same sections.
- Practical guidance for users choosing a method by technology (Visium vs. single-cell imaging) is what NAR readers will look for. The per-dataset sign changes (BASS on MERFISH, BANKSY on STARmap) are more informative than the pooled ranking and should drive that guidance.

**Feasibility:** CPU-feasible (re-clustering).

---

## 4. Minor concerns

1. **Unresolved placeholders.** The manuscript contains TODOs: authors, HiSTaR reported values ("verify the reported values"), Spatial-MGCN contact, GitHub/Zenodo, CRediT, funding, AI-use statement, and the HiSTaR commit "TO RECORD". It is not ready for review in this state, and the reproducibility claim against HiSTaR cannot be evaluated without the verified reported value.
2. **Wrong journal template and header.** The template is OUP *Bioinformatics Advances* ("journaltitle{Bioinformatics Advances}", "Original Paper"). Several bibliography entries are marked VERIFY. Use the NAR format and verify every reference.
3. **Inconsistent seed and coverage reporting** across the Methods text, Supp. Table S8 (STAGATE, CCST, MGCN, BASS: 1 seed) and Supp. Table S18 (standardised runner: 3 seeds). State which run set each figure uses.
4. **Supp. Table S12 versus S3.** The main-metric values differ "because preprocessing is shared". Explain why two pipelines exist and which one supports the headline numbers.
5. **Fig. 2a** mixes protocols within one heat map (baselines 20-start, others their own clustering). Mark this in the panel itself, not only the caption.
6. **Fig. 3a** caption: state that each dot is a single-start range and that real pipelines use multi-start or hierarchical initialisation. Add a reference line for the realistic spread under each method's shipped procedure.
7. **Fig. 3c** is a heat map of medians with no indication of uncertainty or the number of sections (3 STARmap sections). Show per-section values or intervals.
8. **Fig. 4.** The colour legend uses blue for "higher" and orange for "lower", which collides with the family colours (orange = deep encoders) used throughout.
9. **Fig. 5.** Hungarian matching is for display only. Still, label colours for unmatched clusters (e.g. NichePCA) should be distinguishable, and the linear-diffusion "Layer 4" misplacement deserves a sentence.
10. **Boundary analysis.** "p = 0.034, uncorrected" on 9/12 sections, with no multiplicity framing, should be stated as exploratory or removed.
11. **Statistical inference.** Wilcoxon p-values in Supp. Table S11 are "unadjusted" over 12 methods. Adjust them, or present effect sizes only.
12. **Resource measurements.** Report CPU model, thread counts and wall time versus CPU time per method. Note that GPU-designed methods run on one CPU thread are disadvantaged in the cost axis, and say so in the text.
13. **ARI alone is insufficient.** Report AMI or NMI and macro-F1 in the main figure; they are already computed.
14. **Supp. Table S2.** BayesSpace is listed as "tag v1.5.1 (older release; newer one …" with truncated text. GraphST with and without refinement is mentioned, but refined values (0.548 on DLPFC) appear only in the macros, not in the figures. Include them, since refinement is the tutorial default.
15. **Annotated fraction and NA handling.** "Unannotated spots were excluded from evaluation". Confirm that they were *included* in training and graph construction for every method; Spatial-MGCN's original script removes them.
16. **The data availability statement** should give exact accessions or URLs and file hashes for the annotation files, since annotation provenance is central (Major 4).

---

## 5. Recommendation

**Major revision.** Without the revisions below I would recommend rejection.

The study is carefully executed in places and its central message is useful to the field: report and control the clustering step, include smoothing baselines, and don't select by labels. However:
- the most striking robustness result (mclust order dependence) appears to be an artefact of mclust's random subset initialisation;
- the headline accuracy comparison uses an asymmetric clustering protocol;
- several methods appear misconfigured, with no positive-control reproductions;
- the data base (3 brain datasets, partly circular annotations, no Slide-seq/Stereo-seq/Xenium/Visium HD) is narrower than existing 2024–2026 benchmarks;
- a named method is accused of label leakage before its authors were contacted.

Nearly all the required analyses are CPU-feasible, because they mostly re-cluster saved embeddings. The exceptions are new datasets, which are feasible with crops and a scalable-method subset.

### Top required changes

1. Redo the mclust perturbation experiment, separating seed, subset and order (including `initialization=list(subset=seq_len(n))`), and correct the abstract and Fig. 3b.
2. Make a matched clustering protocol, identical for baselines and methods, the primary comparison. Add a method × clusterer matrix and reconcile the protocol descriptions.
3. Add positive-control reproductions of each method's published DLPFC result, fix apparent misconfigurations (NichePCA/SpaceFlow Leiden K-search, SEDR GMM collapse), and give all arms an equal label-free tuning budget.
4. Broaden and validate the data: add at least three datasets from missing technologies (Xenium, Visium HD or Stereo-seq, Slide-seq V2, Allen MERFISH with CCF labels), at least two of them non-laminar. Document annotation provenance (especially the BASS-derived MERFISH labels), and add K-sensitivity and label-free K-selection.
5. Contact the Spatial-MGCN and HiSTaR authors before resubmission and report their responses. Verify that published numbers used the label-selected epoch before naming the method, and have the audit adjudicated by two readers. Reframe linear diffusion as standard neighbourhood smoothing, with corrected method families and recommendations that follow from the matched analyses.

---

### Sources consulted for the literature check
- [Hu et al., Benchmarking clustering, alignment, and integration methods for spatial transcriptomics, Genome Biol 2024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11312151/)
- [Chen et al., comprehensive benchmarking of SRT clustering across technologies, organs and replicates, iMeta 2025](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12747554/)
- [SDMBench (Yuan et al., Nat Methods 2024) code](https://gitee.com/shuliping/SDMBench)
- [Beyond benchmarking: an expert-guided consensus approach to spatially aware clustering (SACCELERATOR)](https://research.chalmers.se/en/publication/553890) and [supporting data](https://zenodo.org/records/15487520)
- [spDDB tutorial (2026 preprint benchmark, 18 methods / 36 datasets / 6 technologies)](https://spddb-tutorial.readthedocs.io/en/latest/)
- [Descoeudres thesis: 26 domain methods on 63 slices from five technologies](https://edoc.ub.uni-muenchen.de/36408/1/Descoeudres_Alice.pdf)
- [NichePCA: PCA-based spatial domain identification](https://ouci.dntb.gov.ua/works/lxLrPybG)
- [Li et al., SVG benchmark incl. downstream domain detection, Genome Biol 2025](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12445034/)
- [Systematic benchmarking of subcellular platforms (Stereo-seq, Visium HD, CosMx, Xenium), Nat Commun 2025](https://researchexchange.ocrahope.org/papers/s41467-025-64292-3)
