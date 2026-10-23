# Referee report, round 2: Reviewer 2 (spatial domain method developer)

**Manuscript:** "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods" (NAR, revised)

**Material reviewed:**
- `paper/main.tex` with `results/paper_macros.tex`
- `paper/supplementary.tex` and its tables in `results/supp/`
- `configs/methods.yaml` and `configs/datasets.yaml`
- `scripts/adapters.py`, `scripts/new_methods.py` and `scripts/run_r_method.R`
- `scripts/stats_cluster_aware.py` and `scripts/paper_v2.py`
- the run records in `results/benchmark_runs.jsonl` and `results/runs/*.npz`
- Figures `docs/figures/nar_fig*.png`
- the installed method packages (GraphST 1.1.1, nichepca 0.1.0) and the vendored repositories in `data/ext/methods/`

All checks below were light (file reads and small Python on metadata and saved labels). I re-ran no method.

---

## Recommendation

**Minor revision. Before acceptance, the new-data part needs a further major round on four specific points.**

The revision addresses the most serious problems of round 1:
- The mclust result is now correctly attributed to the random 2000-observation subset used for initialisation.
- Matched clustering is now the primary analysis.
- A sensitivity analysis on K and a BIC choice of K were added.
- Two non-brain datasets were added.
- The text on the baseline is more modest: its lead is now said to come from brain tissue.

These are real improvements, and the robustness part (Figs 3–4) is now sound and useful.

The new-tissue part has problems that I verified in the code and data.

**(i) Not every method got its documented settings for the new technologies.** For several methods the "default/tutorial settings, unchanged" rule replaced settings that the method's own package or repository documents for exactly these data types:
- GraphST's `datatype='Stereo'`;
- Spatial-MGCN's breast-cancer configuration;
- SEDR's Stereo-seq tutorial.

**(ii) At least two of the five memory-cap failures come from the adapter or configuration, not from the method.** These are NichePCA and GraphST.

**(iii) Excluding the failed methods distorts the ranking.** BASS and NichePCA are removed from the rank analysis (Fig. 2C) because of that single section. The "P(best) = 0.73" for linear diffusion is therefore computed without its strongest competitor.

**(iv) The interpretation of the embryo and breast results needs more care.** Problems include:
- MOSTA labels derived from Leiden clustering;
- a low-count "Cavity" class that covers 17–24% of bins;
- 20 fine breast regions whose numbered sub-regions are different tumour foci;
- non-spatial PCA beating the smoothing baseline on both non-brain datasets, which the text does not say.

The Spatial-MGCN and HiSTaR sections are more neutral than before. Both still contain a factual problem:
- **HiSTaR:** it is described as run "with its official code", but it was run through a re-implementation.
- **Spatial-MGCN:** the inflation estimate pools in datasets the released script never targets, and the in-scope breast-cancer estimate, which is small, is omitted.

The authors of either method have still not been contacted (`docs/LEAKAGE_AUDIT.md`: "authors not yet contacted").

---

## Major points

### M1. Fairness of the runs on the new technologies (Stereo-seq bin50, Visium breast cancer)

The paper states that the breast and Stereo-seq data were run "without changing any setting" and that every method used "its official code and default or tutorial settings". These two rules conflict whenever a method documents data-type-specific settings. In each such case the benchmark applied its DLPFC/Visium settings instead. I verified the following.

**1. GraphST**

`GraphST.GraphST(..., datatype=...)`:
- The docstring of the installed package says: "Our model supports 10X Visium ('10X'), Stereo-seq ('Stereo'), and Slide-seq/Slide-seqV2 ('Slide')".
- With `'Stereo'`, it builds a KNN graph and a **sparse** normalised adjacency (`preprocess_adj_sparse`).
- The adapter (`scripts/adapters.py::graphst`) never passes `datatype`, so Stereo-seq runs take the `'10X'` path.
- That path calls `construct_interaction`, which materialises a dense n×n float64 distance matrix (stored in `adata.obsm`), a dense n×n interaction matrix and a dense float tensor adjacency.
- At n = 18,408 each dense n×n float64 array is 2.7 GB. The run record (`stereo__E10.5_E1S1__graphst__s0`) shows it was killed at 12.17 GB after 81 s, i.e. during graph construction.
- GraphST's own paper and tutorial analyse the MOSTA E9.5 embryo with `datatype='Stereo'`.

The GraphST failure on the largest section, and arguably its Stereo-seq ARI on the other two sections, therefore reflect a configuration choice, not the method. Rerun with `datatype='Stereo'`. Note that even this path allocates a dense n×n `interaction` array (2.7 GB), so it may still fail at 12 GB. If it does, report that failure as the method's own.

**2. NichePCA (a training-free method that ran out of memory)**

That NichePCA hit the cap should itself have raised suspicion. The adapter passes all ~25,000 genes (25,201 in E10.5_E1S1) to `npc.workflows.nichepca(a, knn=6)`:
- That workflow does no gene selection.
- With the default `backend="pyg"` it densifies the expression matrix (`to_numpy(adata.X)` in `nhood_embedding/_aggr.py`), then copies it to a torch tensor and aggregates it.
- 18,408 × 25,201 is 1.9 GB in float32 per copy (3.7 GB in float64), and several copies coexist.

The run records confirm the pattern:

| Section | NichePCA peak RSS | STAGATE peak RSS |
|---|---|---|
| Breast cancer (3798 spots) | 6.7 GB | 1.7 GB |
| E10.5_E2S1 | 9.1 GB | 2.3 GB |

The package offers `backend="sparse"`, and an HVG pre-selection like every other method's would also fix it. Treating this as "a statement about resource use" is not fair to NichePCA. Rerun it. NichePCA would then also re-enter the ranking (see M3).

**3. Spatial-MGCN**

- The repository ships `config/Human_Breast_Cancer.ini` for **this very section** (V1_Breast_Cancer_Block_A_Section_1, script `HBC_test.py`): spatial kNN with k = 15 (`spatial_construct_graph`) and γ = 1.
- It also ships `config/Mouse_Olfactory.ini` for Stereo-seq: kNN 15, α = 10, β = 1, 300 epochs, R mclust.
- The benchmark instead applies the DLPFC config to every dataset: a radius of 4.1 spot spacings and γ = 0.1.
- On a square bin50 grid a radius of 4.1 spacings gives about 53 neighbours, against about 15 in the authors' Stereo-seq configuration.
- The memory failure comes from `spatial_construct_graph1`, which builds a dense `np.zeros((n, n))` plus `torch.ones(n, n) - A`. The kNN variant used for HBC/MOB also uses dense `euclidean_distances`.

The OOM is probably intrinsic to the released code. Even so, the breast-cancer result is not "the tutorial setting": the authors' own setting for this exact dataset was not used. Run it, or state the deviation explicitly in Supplementary Table S2.

**4. SEDR**

- SEDR's own `docs/Tutorial4_Stereo-seq.ipynb` (vendored in `data/ext/methods/SEDR`) uses a 6-NN graph (`SEDR.graph_construction(adata, 6)`) and no HVG or gene filtering.
- The benchmark uses the DLPFC recipe (12-NN, 2000 HVGs).

SEDR is the lowest method on Stereo-seq (0.24 matched). Either use its Stereo-seq tutorial or list the deviation.

**5. Neighbourhood scale on bin50**

All radii are "expressed in spot spacings so that they transfer across technologies". On bin50 one spacing is about 25 µm, against 100 µm on Visium. So every graph, including the baseline's 6-NN graph with T = 10, covers roughly 1/16 of the physical area it covers on Visium, on bins with far fewer UMIs than a Visium spot. That may well be the right choice, but it is a substantive design decision and needs one sentence of justification and a sensitivity check (k or T ×2–4 on Stereo-seq for the baseline and one GNN).

It also undermines the Discussion's explanation that "a fixed amount of smoothing blurs [small interleaved domains]". On Stereo-seq the physical smoothing is far *smaller* than on Visium.

**6. Ties on the square lattice**

On the bin50 square grid, "6 nearest neighbours" is ill-defined:
- There are 4 neighbours at distance 1 and 4 at √2, so `NearestNeighbors(n_neighbors=7)` (`anisost/core.py::spatial_knn`, also NichePCA and STAGATE) keeps 2 of the 4 diagonals by index order. The graph is therefore anisotropic and depends on row order.
- CCST's "median 6th-neighbour distance" threshold (`new_methods.py::ccst`) equals √2 spacings on this grid, so its radius graph has about 8 neighbours, not the stated 6.

Use 4 or 8 neighbours, or a radius, on square lattices, and state it.

**7. BayesSpace**

BayesSpace has a square-lattice `platform="ST"` mode. Excluding it from Stereo-seq "because it requires a Visium lattice" is therefore not accurate. Run it, or say it was not attempted.

**Required:**
- Rerun GraphST (`datatype='Stereo'`), NichePCA (sparse backend or HVG input), Spatial-MGCN (HBC config on breast cancer) and SEDR (Stereo-seq tutorial) on the new data, or list each of these as a deviation in Supplementary Table S2 and mark the affected cells in Fig. 2A.
- Add the bin50 neighbourhood-scale justification and sensitivity check.

### M2. The memory-cap failures: are they fair and correctly framed?

The paper lists BASS, DeepST, GraphST, NichePCA and Spatial-MGCN as exceeding 12 GB on the 18,408-bin section. It says this is "a statement about resource use, not about accuracy". The framing is reasonable in principle, but:

- **The failures have different causes.** I checked the run records:

  | Method | Killed at | Cause | Assessment |
  |---|---|---|---|
  | GraphST | 81 s | dense graph construction | wrong `datatype`; see M1.1 |
  | NichePCA | 56 s | dense all-gene matrix | adapter; see M1.2 |
  | Spatial-MGCN | 87 s | dense n×n adjacency | released code |
  | DeepST | 106 s | after "Finding adjacent spots" | released code |
  | BASS | 4069 s | during the MCMC | DLPFC settings, `nsample = 10000` |

  Only Spatial-MGCN, DeepST and possibly BASS are plausibly intrinsic. BASS's posterior storage grows with n × nsample; the BASS authors analysed about 25,000 MERFISH cells jointly. The text should say which failures are intrinsic and which come from configuration.
- **DeepST was run once.** It failed with one seed only (seed 0 was attempted because it runs serially). That is fine, but state it.
- **The 12 GB cap is low and arbitrary.** It is lower than a standard 16 GB laptop and far below a GPU node. The claim "methods that exceed 12 GB on an 18k-bin section" should come with the scaling curve already measured (peak RSS on 3.8k, 5.9k, 8.5k and 18.4k observations; Supplementary Table S13). Readers can then see that, for example, GraphST is O(n²) in memory. Better still, rerun the failed methods once without the cap, or with ≥ 32 GB, to separate "needs > 12 GB" from "cannot run".
- **One earlier failure is unreported.** Spatial-MGCN on E9.5_E1S1 seed 0 first failed with "Input X contains NaN": bins with no HVG counts were divided by zero. The adapter was then patched (`np.maximum(..., 1)`). This is harmless but contradicts "without changing any setting". Note it in Supplementary Table S2.

### M3. The ranking excludes the strongest competitor because of the memory cap

Fig. 2C ranks only methods with a result on every section. As a result, BASS, NichePCA, GraphST, DeepST and Spatial-MGCN are "not ranked: memory cap". BASS is the method that:
- is ahead of linear diffusion on STARmap, MERFISH and breast cancer;
- has the higher equal-weight brain mean (0.594 against 0.587).

Its absence is what allows the statement that linear diffusion "ranked first in 0.73 of the resamples" (abstract-level message, Results §1). That statement compares the baseline only with the methods that ran everywhere; the text never says so.

The paired bootstrap deltas (`stats_cluster_aware.py`) correctly use common sections, so Fig. 2B is fine. Fig. 2C and the rank sentence need either:
- (a) a ranking on the common sections (drop E10.5_E1S1 from the rank bootstrap, or rank within each resample over the available sections); or
- (b) an explicit statement that the five strongest-to-middle methods with a missing section are excluded, and that BASS is not ranked.

Also, Fig. 2A mixes 3-section and 2-section means in the Stereo-seq column. On the two common sections, linear diffusion scores 0.277, not 0.306, because its best section is the large one (0.364). Show the 2-section mean for every method, or add the paired value.

### M4. Interpretation of the breast cancer and embryo results

The headline is now that the baseline leads on brain, not on breast cancer or embryo. That is correct, but the supporting text still over-reads or under-reads the data in places.

**1. The non-spatial reference beats the smoothing baseline on both non-brain datasets.** This is not stated.

| Dataset (matched clustering) | PCA, no spatial information | Linear diffusion |
|---|---|---|
| Breast cancer | 0.562 | 0.545 |
| Stereo-seq, 3 sections | 0.349 | 0.306 |
| Stereo-seq, the two common sections | 0.347 | 0.277 |

On these data, the baseline's smoothing step *reduces* agreement with the annotation. This is the most informative single fact about the new data and should be in the Results and Discussion. Either the smoothing scale is wrong for these data (M1.5), or the annotation rewards expression-only structure (points 2–3 below).

**2. Provenance of the MOSTA annotation.**
- GraphST's Fig. 3 legend (Long et al., *Nat Commun* 2023) describes the MOSTA E9.5 reference as "clusters first identified using Leiden clustering from SCANPY and then annotated using differentially expressed genes".
- The text's "derived partly from clustering of the expression data and then curated" is therefore correct in spirit.
- However, `configs/datasets.yaml` still marks it `verified: false`, and the class is `algorithm`, i.e. circular by the authors' own taxonomy.

Please:
- confirm the provenance in Chen et al. (*Cell* 2022, Methods) and cite it specifically;
- report the Stereo-seq results as "agreement with a published clustering-derived annotation", not as accuracy;
- note that GraphST and other method papers used the same reference, which makes it a de facto standard but not ground truth.

**3. The "Cavity" class is mostly a sequencing-depth class.** In the MOSTA files, "Cavity" covers:
- 882 of 5913 bins in E9.5_E1S1 (15%);
- 1413 of 8494 in E10.5_E2S1 (17%);
- 4366 of 18,408 in E10.5_E1S1 (24%).

Its median total counts are about half those of tissue bins (7188 against 14,039 overall in E9.5_E1S1; 5808 against 11,786 in E10.5_E1S1). A domain this large, defined largely by low counts, has a big effect on ARI and favours representations that keep library-size signal. Report Stereo-seq ARI with and without "Cavity" bins. Also comment on the uneven number of domains: 18 annotated tissues in E10.5_E2S1 against 13 in E10.5_E1S1, at the same stage.

**4. Breast cancer: one section, 20 fine regions.**
- The 20 regions (`fine_annot_type`) subdivide 4 histological classes into numbered foci (IDC_1–7, DCIS/LCIS_1–5, Tumor_edge_1–6, Healthy_1–2). These are spatially separate regions of the *same* histology, so with K = 20 the ARI largely rewards cutting spatially disconnected foci apart. That is precisely what spatial-prior methods (BASS, BANKSY λ = 0.8, NichePCA) do. The ranking on this dataset is partly a test of spatial fragmentation, not of tissue-type recognition.
- The coarse 4-class annotation (`annot_type`: Invasive 1663, Tumor 827, Surrounding tumor 823, Healthy 485) is in the same file. As a rough check, I scored the saved K = 20 partitions against it. All methods fall in 0.16–0.21 and the order changes (DeepST and CCST first, linear diffusion last). This check is confounded by K = 20 against 4 classes. The proper analysis is to recluster each embedding at K = 4 and report it alongside the fine result.
- The breast section is one section, which makes it one bootstrap group with the same weight as a DLPFC donor (four sections). Say so where the "13 of 16 ahead" figure is given.
- Several benchmarked methods (SEDR, DeepST, Spatial-MGCN) published results on this exact section with this annotation, so it is the natural place for the positive-control reproductions requested in round 1 (Major 3a). Report each method's published value next to the benchmark value.
- Provenance: the annotation is distributed with SEDR_analyses and widely reused. State who drew it, and when, if the source says so; `datasets.yaml` still has `verified: false`.

**5. "No method stood out" is too strong.** On breast cancer the range is 0.522–0.624 (BASS against SEDR, matched clustering). On Stereo-seq it is 0.241–0.388, and per section 0.21–0.41. These are spreads as large as on DLPFC. A more accurate statement is "the ordering differed from the brain data and the baseline was below the median". Given M1, the ordering on these data should be taken as provisional for GraphST, NichePCA, Spatial-MGCN and SEDR.

### M5. HiSTaR non-reproduction: factual accuracy of "official code"

The abstract ("HiSTaR did not reproduce its published accuracy with its official code"), the Results ("With the official code and defaults") and Supplementary Table S16 ("Official code, 3-start GMM") all say the official code was run. It was not:
- `configs/methods.yaml` lists "PyTorch port of the official code (hicast/histar.py)".
- The commit is "inferred, no vendored copy kept".
- `hicast/histar.py` is a "faithful re-implementation" with at least one change (vectorised negative-edge sampling).
- The adapter feeds HiSTaR the benchmark's shared 200-PC input (`_pcs` in `adapters.py`) rather than HiSTaR's own preprocessing. Yet the text lists "unpublished preprocessing" among the *possible causes*, when the benchmark itself replaced the published preprocessing.

The section is otherwise neutral, and its closing sentence is appropriate. Round 1's request (Major 3d) still stands: run the unmodified upstream repository at a recorded commit on at least the twelve DLPFC sections. Until then, every occurrence of "official code" must read "a re-implementation of the official code", and the abstract sentence should be softened or removed.

Also report the reported per-section values next to yours. 151673 is quoted in the text (0.718) but is not in Table S16.

### M6. Spatial-MGCN label-selected epoch: factual and neutral?

The wording is now largely neutral:
- "released test scripts";
- "we do not know whether the published numbers were obtained with these scripts".

I verified the claim in `DLPFC_test.py` lines 113–127 and `HBC_test.py` lines 112–125 (`ari_max` over epochs). It is factual. Remaining issues:

1. **The inflation estimate uses out-of-scope data.** The headline "+0.147 on average" pools DLPFC (+0.133) with STARmap (+0.384) and MERFISH (+0.039). The released scripts target DLPFC and human breast cancer only. The in-scope estimate on the **breast cancer section, the dataset of `HBC_test.py`**, is available in `results/benchmark_runs.jsonl` (`extra.ARI_label_selected_epoch`) but is not reported:

   | Seed | Final epoch | Label-selected epoch |
   |---|---|---|
   | 0 | 0.543 | 0.587 |
   | 1 | 0.627 | 0.666 |
   | 2 | 0.555 | 0.564 |
   | Mean | 0.575 | 0.606 |

   That is an inflation of about +0.03. Report DLPFC and breast cancer as the in-scope estimate, and STARmap/MERFISH as illustrative (round-1 Major 6c).
2. **Loaded comparison.** "Here it makes the method look competitive with the training-free baselines when its label-free result is not" sets the method against the authors' own baseline, and the claim reverses on breast cancer: Spatial-MGCN's label-free default (0.575) is above linear diffusion (0.545). Delete the sentence, or state it per dataset.
3. **Settings.** The final-epoch value is computed with the DLPFC configuration on every dataset, and with k-means (n_init = 10) rather than the R mclust used by the authors' `MOB_test.py`. State this.
4. **Author contact.** The authors have still not been contacted: `docs/LEAKAGE_AUDIT.md` line 6 says "authors not yet contacted; do not publish a claim about a specific method before…". The round-1 TODO was removed from the manuscript, but the action was not done. The same applies to HiSTaR. I maintain the round-1 request: contact both groups and report the response, or its absence, factually before acceptance. The audit is still adjudicated by one reader (Supplementary Note 5).

### M7. Missing prior work closest to the paper's main message

The paper's practical conclusion is that neighbourhood aggregation of expression followed by a Gaussian mixture is hard to beat on cortex. Several established methods do exactly this and should be cited and discussed, ideally with at least one included as a comparator, because they are what a practitioner would use instead of "linear diffusion":
- **CellCharter:** Varrone M, Tavernari D, Santamaria-Martínez A, Walsh LA, Ciriello G. *Nat Genet* 2024;56:74–84, doi:10.1038/s41588-023-01588-4. Multi-hop neighbour aggregation plus a GMM, with a stability-based choice of K. It is very close to the baseline and addresses the label-free-K problem the paper raises.
- **MENDER:** Yuan Z. *Nat Commun* 2024;15:207, doi:10.1038/s41467-023-44367-9. Training-free multi-range neighbourhood features, scalable to millions of cells. It is directly relevant to the memory-cap discussion.
- **SpatialPCA:** Shang L, Zhou X. *Nat Commun* 2022;13:7203, doi:10.1038/s41467-022-34879-1.
- **PRECAST:** Liu W et al. *Nat Commun* 2023, doi:10.1038/s41467-023-35947-w.

SpatialPCA and PRECAST are spatially smoothed factor models, the statistical counterpart of the baseline.

I verified that these four papers exist. The round-1 suggestion to cite the iMeta 2025 cross-technology benchmark (Chen et al.) is also still open.

---

## Minor points

1. **HiSTaR default clustering.** It is listed as a 3-start scikit-learn GMM in the main text, while `methods.yaml` gives its official clustering as R mclust EEE. The "default clustering" protocol therefore does not use HiSTaR's default. Say so in §Clustering protocols, or use mclust.
2. **SEDR under matched clustering collapses** on STARmap (0.593 to 0.236) and MERFISH (0.406 to 0.167). This was unexplained in round 1 and still is. A tied-covariance GMM on an unscaled DEC embedding is the likely cause. One sentence and a check (standardise the embedding) would help, because it drives SEDR's "baseline better" verdict.
3. **Leiden K search.** The run records show k_found ≠ K for NichePCA on breast cancer (21 against 20, all seeds), NichePCA on MERFISH (2 runs), DeepST on STARmap and MERFISH (all runs) and SpaGCN on Stereo-seq (2 runs). Report this (round-1 Major 5c) and note it in Supplementary Table S3.
4. **BASS on new data** uses the DLPFC settings (C = 20, SPARK-X 3000 genes, nsample = 10000). That is reasonable, but state it, and note that BASS returned 17–19 non-empty domains for K = 20 on breast cancer.
5. **Fig. 2A/C.** Add the 2-section Stereo-seq mean (M3). In Fig. 2C, write "not ranked: missing E10.5_E1S1" rather than "memory cap" until M1 is resolved.
6. **Family labels.** NichePCA and BANKSY are now in "Statistical and neighbourhood methods", together with BASS and BayesSpace. Round 1 asked for them to sit with the smoothing baselines, since they are the same operation. This is partly addressed. Consider a separate "neighbourhood aggregation" family.
7. **Development-section exclusion.** "All comparisons are repeated without the development sections" does not apply to the new datasets, which are all test. Say so.
8. **BayesSpace on Stereo-seq.** See M1.7; correct the sentence in the `new_methods.py` docstring and in the text.
9. **The "Seeds" paragraph** says three seeds for every method on the new data, but DeepST has one seed on E10.5_E1S1 (OOM after the first) and BayesSpace has one. Align the text with Supplementary Table S20.
10. **`configs/methods.yaml`** still opens with "publication fields … written from memory and are NOT verified". `datasets.yaml` has `verified: false` for every label provenance, and every licence is `to_check`. These must be resolved before acceptance, since annotation provenance is now load-bearing (M4).
11. **The AnisoST paragraph** is still in the main Results. Shorten it to a sentence, or move it to the Supplement (round-1 Major 7).
12. **Abstract.** "on breast cancer and embryo most methods were slightly ahead" is correct, but it should add that a non-spatial PCA reference was also ahead (M4.1).

---

## Status of the round-1 points (docs/nar_review/05_domain_expert.md)

| Round-1 point | Status | Comment |
|---|---|---|
| **Major 1:** mclust "spot order" result is subsampling-driven | **Resolved** | Seed arm, full-data initialisation arm and noise arm added. The text now attributes the effect to the 2000-observation subset and states the earlier misattribution. STARmap invariance is explained. Seeds hard-coded by STAGATE/GraphST (2020) and SEDR (2023) are reported. |
| **Major 2:** asymmetric clustering protocol in the headline | **Largely resolved** | Matched 20-start GMM is primary (Fig. 2, Table S6), and the default protocol is secondary. Still open: (b) the method × clusterer matrix (k-means, Leiden, mclust with full initialisation) was not added; HiSTaR's "default" is not its official clustering (Minor 1). |
| **Major 3:** configuration problems, positive controls, tuning budget | **Not resolved** | No positive-control reproduction of any method's published number except HiSTaR, which uses a re-implementation, so (d) is also open. No label-free tuning budget; the limitation is acknowledged. NichePCA's DLPFC gap is now visibly a clustering effect (0.321 own against 0.506 matched). SEDR's collapse is unexplained. New configuration problems on the new data (M1). |
| **Major 4:** datasets, annotation provenance, circularity | **Partly resolved** | Breast cancer Visium and MOSTA Stereo-seq were added, and the per-dataset reporting is good. No Xenium, Visium HD, Slide-seq or CCF-registered Allen MERFISH data. Annotation provenance is discussed in Limitations but not verified (`verified: false` everywhere). The MOSTA labels are clustering-derived, so the circularity problem has grown rather than shrunk. No mixed-model analysis, although the per-dataset breakdown partly substitutes for leave-one-dataset-out. |
| **Major 5:** number of domains | **Resolved** | K±1/±2 and BIC selection reported (Table S15), with the honest conclusion that the baseline's lead depends on the true K. Verification that the Leiden search hit K is still missing (Minor 3). |
| **Major 6:** label-leakage claim; contacting authors | **Partly resolved** | The wording is now neutral, and the analysis is restricted in tone. Still open: authors not contacted (the audit file says so); the inflation estimate still pools STARmap/MERFISH; the in-scope breast-cancer estimate is omitted; single-reader audit (M6). |
| **Major 7:** framing of linear diffusion | **Largely resolved** | It is now "standard neighbourhood smoothing (graph Laplacian smoothing)", the post-hoc reference choice is acknowledged, and "matched" is replaced by "could not be separated". Still open: no citation of the closest existing aggregation+GMM methods (M7); the family grouping is only partly fixed; the AnisoST paragraph is still in the main Results; T/k sensitivity on test datasets is still only on DLPFC (now more important on bin50, M1.5). |
| **Major 8:** recommendations | **Partly resolved** | Recommendations (1)–(7) now follow from the matched analyses. Still open: a tested remedy (consensus clustering or the median over starts); technology-specific guidance. The finding that smoothing hurts on breast and embryo data (M4.1) should feed into recommendation (4). |
| Minor 1: placeholders | Partly | Only author, funding, CRediT and URL TODOs remain, which is acceptable for review. The HiSTaR commit is "inferred". |
| Minor 2: template | Resolved | NAR header. The bibliography entries I checked are now complete. |
| Minor 3: seed and coverage reporting | Mostly resolved | Table S20. See Minor 9 above. |
| Minor 4: two pipelines | Resolved | Table S14 compares them. |
| Minor 5: mixed protocols in Fig. 2a | Resolved | Now uniformly matched. Stereo-seq column: see M3. |
| Minor 6: single-start caveat in Fig. 3a | Resolved | The text and the R mclust panel give the realistic spread. |
| Minor 7: Fig. 3c uncertainty | Resolved | Interquartile range and number of sections shown. |
| Minor 8: Fig. 4 colours | Not re-checked in detail | — |
| Minor 9: Fig. 5 | Partly | Not re-checked in detail. |
| Minor 10: boundary p-value | Resolved | Labelled uncorrected. |
| Minor 11: Wilcoxon multiplicity | Resolved | Labelled uncorrected. |
| Minor 12: hardware and CPU caveat | Resolved | Supplementary Note 6 and Limitations. |
| Minor 13: NMI/AMI | Resolved | Table S4. |
| Minor 14: GraphST refinement values | Partly | Mentioned in methods.yaml; not in the figures. |
| Minor 15: NA spots included in training | Resolved | All spots kept; Spatial-MGCN deviation stated. |
| Minor 16: annotation accessions | Partly | Commit given for SEDR_analyses (breast cancer); no file hashes in the text; licences `to_check`. |

---

### Sources consulted

- [GraphST, Long et al., Nat Commun 2023 (Fig. 3 legend on the MOSTA reference annotation)](https://link.springer.com/10.1038/s41467-023-36796-3)
- [MOSTA dataset STDS0000058, CNGB](https://db.cngb.org/stomics/datasets/STDS0000058/)
- [SemanticST preprint (describes the MOSTA E9.5 annotation as Leiden plus markers)](https://arxiv.org/pdf/2506.11491)
- [CellCharter, Varrone et al., Nat Genet 2024](https://link.springer.com/article/10.1038/s41588-023-01588-4)
- [MENDER, Yuan, Nat Commun 2024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10770058/)
- [SpatialPCA, Shang & Zhou, Nat Commun 2022](https://link.springer.com/10.1038/s41467-022-34879-1)
- [PRECAST, Liu et al., Nat Commun 2023 (CRAN documentation with DOI)](https://anorien.csc.warwick.ac.uk/CRAN/web/packages/PRECAST/PRECAST.pdf)
