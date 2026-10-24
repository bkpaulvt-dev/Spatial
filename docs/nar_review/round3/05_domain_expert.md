# Referee report, round 3: Reviewer 2 (spatial domain method developer)

**Manuscript:** "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods" (NAR, second revision)

**Material reviewed:**
- `paper/main.tex` with `results/paper_macros.tex`
- `paper/supplementary.tex` and the tables it includes from `results/supp/` (methods, ari, ranks, brca_coarse, histar, labelepoch, coverage)
- `scripts/adapters.py` and `scripts/new_methods.py`
- `results/benchmark_runs.jsonl`, using the newest record for each id
- `results/brca_coarse.json`
- `configs/methods.yaml` and `configs/datasets.yaml`
- `docs/figures/nar_fig2_accuracy.png`
- `paper/refs.bib`
- `docs/LEAKAGE_AUDIT.md`
- the installed `nichepca` 0.1.0, signature of its workflow only

All checks were light: file reads and small Python on run metadata. I re-ran no method.

---

## Recommendation

**Minor revision.** The new experiments I asked for no longer block acceptance. The remaining items are corrections to text and tables, and none of them changes a conclusion.

The authors made the important fixes:
- GraphST was rerun with `datatype='Stereo'`. It still exceeds the cap, so that failure now belongs to the method.
- The rank analysis now uses the 23 sections every method completed. BASS is ranked and leads (P(best) 0.49 against 0.29).
- The text now states that PCA without smoothing is ahead of the baseline on both non-brain datasets.
- The breast data are re-scored against the 4 coarse classes at K = 4.
- The HiSTaR results paragraph now says "PyTorch port".
- The four missing references are cited and are correct.

The declined requests are mostly described fairly. Several places still need correcting:
- Leftover "official code" wording.
- An inaccurate sentence in the Discussion about BASS's chance of ranking first.
- Supplementary Table S2 does not list the deviations that the Limitations now admit.
- The Spatial-MGCN inflation estimate is unchanged and still omits the in-scope breast-cancer value.
- Supplementary Notes 2 and 4 contradict the main text.

---

## Status of the round-2 points

### M1. Fairness of the runs on the new technologies

**M1.1 GraphST `datatype='Stereo'`: resolved.**
- `adapters.py::graphst` now passes `datatype="Stereo" if ds == "stereo" else "10X"`, and the Methods state it (main.tex l.138–139).
- The newest records (lines 1130–1138 of the jsonl) are reruns:
  - E10.5_E1S1 is still OOM in all three seeds (12.05–12.18 GB at about 106 s), as I anticipated: the `'Stereo'` path still allocates a dense n×n interaction matrix.
  - On the smaller sections the rerun changed matched ARI noticeably. On E9.5_E1S1 it rose from about 0.23 to about 0.33, and run time fell about 2.6-fold.
- The failure on the largest section is now the method's own. One small leftover: Data §"These two datasets were added … without changing any setting" (l.117) is no longer literally true, because GraphST's setting was changed on Stereo-seq. Write "with the same settings, except GraphST's documented Stereo-seq mode".

**M1.2 NichePCA: declined. The paper states this fairly, with one gap.**
- Limitations (l.395–396): "NichePCA failed there with its default workflow, which aggregates all genes before PCA; its package also offers other orders of these steps." This is accurate. The installed `npc.workflows.nichepca` has `pipeline=('norm','log1p','agg','pca')` as its default and accepts other orders.
- The sentence omits the other documented remedy, `backend="sparse"`. The default `backend="pyg"` densifies the all-gene matrix, and that is the immediate cause of the OOM.
- Keeping the authors' default workflow is defensible. Please:
  - add "or a sparse aggregation backend" to the sentence;
  - put the same note in the NichePCA row of Supplementary Table S2, whose deviation cell is empty.

  Otherwise a reader of the main Results (l.235) sees NichePCA in the same list as the methods whose released code is intrinsically O(n²).

**M1.3 Spatial-MGCN breast-cancer configuration; M1.4 SEDR Stereo-seq tutorial: declined by design. Fair in the Limitations, missing from Supplementary Table S2.**
- The Limitations (l.396–399) now say that dataset-specific tutorial settings were not used and name both examples. That is honest and sufficient for the main text.
- Supplementary Table S2 ("every deviation from the published tutorial") still lists neither.
- Supplementary Note 2 still says "Every method was run from its official code with the settings of its tutorial or paper". The Methods still say "official code and default or tutorial settings" (l.131–132), although HiSTaR and CCST are re-implementations.
- Please align these three places: add the two deviations to Table S2, and say "official code or a documented port".

**M1.5 Neighbourhood scale on bin50: partly resolved.**
- The Limitations now state that radii in bin spacings cover a smaller physical area on bin50 (l.398–399). Good.
- No sensitivity check was added.
- The Discussion hypothesis (l.367–369), that "a fixed amount of smoothing tuned on cortex then blurs them", remains. It is marked "which we did not test", which is acceptable. However, it is the less plausible explanation for Stereo-seq, where the physical smoothing radius is about 1/16 of the Visium area.
- The alternative is that the annotation rewards expression-only structure: it is derived from clustering, and the Cavity class is a low-count class. That is equally consistent with PCA > smoothing and should be named in the same sentence.

**M1.6 Ties on the square lattice: not resolved.**
- `spatial_knn`, NichePCA and STAGATE still use 6-NN on the bin50 grid, which breaks ties by index order.
- CCST's median-6th-neighbour radius still gives about 8 neighbours.
- One sentence in Supplementary Table S2 would suffice.

**M1.7 BayesSpace on Stereo-seq: partly resolved.**
- The docstring (`new_methods.py` l.298–299) is now correct: the `platform="ST"` mode exists but was not used.
- The main text (l.147–148, "requires a spot lattice") and Supplementary Table S2 ("needs a hexagonal spot lattice") still give the old reason. A bin50 grid *is* a spot lattice.
- Write "was run on Visium only; its square-lattice ST mode was not attempted on Stereo-seq".

### M2. Memory-cap failures

**Partly resolved.**
- The run records match the text. The OOM list (`\listOom`: BASS, DeepST, GraphST, NichePCA, Spatial-MGCN) is correct.
- The Seeds paragraph correctly states that DeepST seeds 1–2 exceeded the cap on E10.5_E2S1. I confirmed this: 12.0 GB at about 440 s, while seed 0 succeeded at 10.8 GB.
- "With more memory or a GPU they may run, so this is a statement about resource use, not about accuracy" is neutral and acceptable.
- Still missing:
  - A statement of which failures are intrinsic to the released code (GraphST, Spatial-MGCN and DeepST: dense n×n structures) and which come from the default workflow (NichePCA) or from settings (BASS with `nsample=10000`).
  - That DeepST was attempted only once on E10.5_E1S1.
  - The Spatial-MGCN NaN patch (`np.maximum(…, 1)`, `new_methods.py` l.238), which should be listed as a deviation.
  - A pointer to the peak-RSS scaling across 3.8k–18.4k observations, which is in Supplementary Table S14.
- Coverage table S22 reports DeepST on the runner as "23/24 / 3", but it has 1 seed on E10.5_E2S1. It reports GraphST in the paper pipeline as "/ 3", but Methods l.157–158 and Table S9 say one seed on DLPFC. Please align the tables.

### M3. Ranking without BASS

**Resolved.**
- Ranks now use the 23 sections every method completed.
- BASS P(best) = 0.49, linear diffusion 0.29, BANKSY λ=0.8 0.06.
- 6 methods have rank 1 within their 95% interval. I checked this against `results/supp/ranks.tex`.
- The 11-method "complete sections" ranking (0.74) is explicitly labelled as excluding BASS.
- Fig. 2A marks the 2-section Stereo-seq means with an asterisk.
- The counts "12 of 15 ahead on Stereo-seq" and "13 of 16 on breast" are correct when each method is paired on its available sections. I reproduced 12 of 15. If all methods are compared on the two common sections, linear diffusion (0.277) is behind 14 of 15. Fig. 2A still shows the baseline's 3-section 0.31 beside asterisked 2-section values; consider adding 0.28* in a note.

**New inaccuracy.**
- The Discussion (l.357) says "BASS was as likely to rank first". It was more likely (0.49 against 0.29).
- The abstract's "BASS and it were most likely to rank first" is fine.
- Write "BASS was more likely to rank first".

Typesetting: `ranks.tex` and `histar.tex` print intervals as `1-$-$10` and `0.454-$-$0.525`, which render as a hyphen followed by a minus sign. Use `--`.

### M4. Interpretation of the breast and embryo results

**M4.1 PCA ahead of smoothing: resolved.**
- The new sentence is correct and neutral (Results l.231–233; Discussion l.369; abstract):
  - breast cancer: PCA 0.562 against linear diffusion 0.545;
  - Stereo-seq: 0.349 against 0.306.
- "Smoothing with the settings fixed on DLPFC did not help on these tissues" is accurate. On these data smoothing in fact lowered ARI.

**Tissue-dependence text: correct.**
- I recomputed the equal-weight brain means: BASS (0.484+0.716+0.582)/3 = 0.594 against linear diffusion 0.587.
- "No comparator ahead on DLPFC, 1 on STARmap and MERFISH (BASS)" matches Supplementary Table S3.
- One sign is ambiguous: "the difference from the baseline was 0.172 … and −0.027". State the direction, i.e. "baseline minus comparator".

**"No method stood out" (M4.5): not resolved.**
- On breast cancer the matched range is 0.522–0.624. On Stereo-seq it is 0.241–0.388, a spread comparable with DLPFC (0.326–0.558).
- The data support "no method was consistently ahead, and the ordering differed from the brain data".
- Given one breast section and three embryo sections, the true point is that the differences are not resolved, not that they are absent.

**M4.2 MOSTA provenance: partly resolved.**
- The Limitations say that the annotation "was derived partly from clustering … may favour methods similar to that clustering". Good.
- The source is still not cited specifically, and `datasets.yaml` still has `verified: false` with class `algorithm`.
- The Results still read as accuracy, not as "agreement with a published clustering-derived annotation".

**M4.3 Cavity class: not resolved.** There is no mention of it, and no ARI without Cavity bins. On E10.5_E1S1 Cavity is 24% of bins with about half the median counts. It bears directly on the PCA > smoothing finding.

**M4.4 Coarse breast classes: resolved, with one wording fix.**
- `brca_coarse.json` matches the text:
  - range 0.04 (Spatial-MGCN) to 0.31 (NichePCA);
  - NichePCA 0.308 and SpaceFlow 0.300 first;
  - linear diffusion 0.186, rank 11 of 14.
- The analysis reclusters at K = 4 as I requested.
- Ten of the 14 methods lie within 0.18–0.21 on one section and one seed. "Rank 11 of 14" therefore implies more precision than the data allow. Say "most methods within 0.18–0.21; linear diffusion among them (0.19)".
- Still open:
  - the remark that the single breast section carries the weight of a DLPFC donor;
  - published per-method values on this section (positive controls).

### M5. HiSTaR "official code"

**Partly resolved.**
- The Methods (l.136) and the Results (l.334, "With our PyTorch port of the official code") are now correct.
- The abstract ("HiSTaR's published accuracy was not reproduced") no longer claims official code, and the claim is accurate.
- Remaining:
  1. The Introduction (l.78): "do published results reproduce with the official code (here HiSTaR's DLPFC results)". Change it to "with the released code or a port of it".
  2. Supplementary Table S18 row: "Official code, 3-start GMM". Change it to "PyTorch port".
  3. "Unpublished preprocessing" is still listed as a possible cause (l.338). The benchmark itself fed HiSTaR the shared 200-PC input (`adapters.py::histar`, `_pcs`), so the paper's own preprocessing substitution should be named among the causes.
  4. The reported 151673 value (0.718) is quoted in the text but not in Table S18.
- The closing sentence ("not to question the method itself") is neutral.
- Contacting the HiSTaR authors is the authors' decision. With the wording corrected the section is fair without it. I would still welcome a sentence such as "we have informed the authors".

### M6. Spatial-MGCN label-selected epoch

**Not resolved** (only the wording was already neutral).
- Table S19 and the text still give the pooled +0.147, which includes STARmap (+0.384) and MERFISH, datasets the released scripts never target.
- The in-scope breast-cancer estimate, the dataset of `HBC_test.py`, is still omitted. It is in the run records (`extra.ARI_label_selected_epoch`, seeds 0–2):

  | | Final epoch | Label-selected epoch | Difference |
  |---|---|---|---|
  | Breast cancer, mean over seeds 0–2 | 0.575 | 0.606 | about +0.03 |

- The sentence "here it makes the method look competitive with the training-free baselines … when its label-free result is not" (l.348–349) remains. It is true on DLPFC and false on breast cancer, where Spatial-MGCN's label-free default (0.575) exceeds linear diffusion (0.545/0.546).

Required:
- report DLPFC (+0.13) and breast cancer (+0.03) as the in-scope estimate, with STARmap/MERFISH as illustrative;
- restrict that sentence to DLPFC.

Also not done: stating that the final-epoch value uses the DLPFC configuration and k-means everywhere.

Author contact is the authors' decision. `docs/LEAKAGE_AUDIT.md` still says "authors not yet contacted; do not publish a claim … before they have been given the chance to respond". The manuscript's "We do not know whether the published numbers were obtained with these scripts; we report what the released code does" is fair and factual. However, the authors' own audit file sets contact as a precondition for publication. They should either do it or remove that sentence from the audit file before it is released with the code.

### M7. Missing prior work

**Partly resolved.** I checked the four references in `refs.bib`, and they are correct:
- CellCharter: Varrone et al., *Nat Genet* 2024;56:74–84, doi:10.1038/s41588-023-01588-4.
- MENDER: Yuan, *Nat Commun* 2024;15:207, doi:10.1038/s41467-023-44367-9.
- SpatialPCA: Shang & Zhou, *Nat Commun* 2022;13:7203, doi:10.1038/s41467-022-34879-1.
- PRECAST: Liu et al., *Nat Commun* 2023;14:296, doi:10.1038/s41467-023-35947-w.

They are cited in sensible categories in the Introduction (l.57–59).

They are not mentioned where they matter, in the Discussion of why smoothing does well. CellCharter (aggregation + GMM) and MENDER (training-free multi-range neighbourhood features) are the published versions of the baseline. One sentence there would place the baseline correctly ("standard neighbourhood smoothing, as in CellCharter and MENDER"). Including one of them as a comparator remains desirable but optional. The iMeta 2025 cross-technology benchmark is still not cited.

---

## Minor points (round 2)

| # | Point | Status | Comment |
|---|---|---|---|
| 1 | HiSTaR default clustering is not its official mclust | Partly | Table S18 gives the R mclust value (0.449); §Clustering protocols still lists HiSTaR's "default" as a 3-start GMM without noting that this is not its official clustering. |
| 2 | SEDR collapse under matched clustering | Not resolved | STARmap 0.593 → 0.236 and MERFISH 0.406 → 0.167 are still unexplained. |
| 3 | Leiden K search: k_found ≠ K | Not resolved | Not reported anywhere. New case: DeepST on E10.5_E2S1 seed 0 returned 29 clusters for K = 18. |
| 4 | BASS settings on the new data; BASS returns 17–19 domains | Not resolved | `methods.yaml` lists only the DLPFC, STARmap and MERFISH settings. BASS returns 17–19 of 20 domains on breast cancer and 17 of 18 on E10.5_E2S1. |
| 5 | Fig. 2A/C labelling | Resolved | Asterisk for 2-section means; ranks on common sections. |
| 6 | Neighbourhood-aggregation family | Not changed | Acceptable. |
| 7 | Development-section exclusion does not apply to the new data | Not resolved | Trivial: one clause. |
| 8 | BayesSpace on Stereo-seq | Partly | Docstring fixed; main text and Table S2 not (M1.7). |
| 9 | Seeds paragraph | Partly | DeepST E10.5_E2S1 is now stated. DeepST E10.5_E1S1 single attempt is missing. Table S22 seed counts are inconsistent (M2). |
| 10 | `verified: false`, licences `to_check`, the "written from memory" header in methods.yaml | Not resolved | Must be cleared before release, because provenance is load-bearing. |
| 11 | AnisoST paragraph in Results | Not resolved | Acceptable now that it is four lines. |
| 12 | Abstract mentions PCA | Resolved | |

---

## New inconsistencies found in this round

1. **Supplementary Note 4** says "No correction for multiple comparisons is applied". The main text (l.196, 215) reports Bonferroni-corrected intervals as a check, so the note should mention them.
2. **Supplementary Note 2** ("settings of its tutorial or paper") contradicts the Limitations on dataset-specific tutorial settings (M1.3/4).
3. **Data §** "without changing any setting" (l.117) is contradicted by GraphST's Stereo mode and the Spatial-MGCN NaN patch.
4. **Discussion** l.357: "BASS was as likely to rank first" should read "more likely" (M3).
5. **Interval typesetting** `-$-$` in Tables S8 and S18.

---

## Summary of required changes before acceptance

All of these are text or table changes:
1. List every deviation in Supplementary Table S2:
   - GraphST Stereo mode;
   - NichePCA default all-gene `pyg` workflow (the `sparse` backend not used);
   - Spatial-MGCN HBC configuration not used, and the NaN patch;
   - SEDR Stereo-seq tutorial not used;
   - BASS DLPFC settings on the new data;
   - BayesSpace ST mode not attempted;
   - 6-NN ties on the square lattice.
2. Correct the leftover "official code" wording (Intro l.78, Table S18, Supplementary Note 2) and name the shared-PC input as a possible HiSTaR cause.
3. For Spatial-MGCN, report DLPFC and breast cancer as the in-scope inflation, and restrict the "looks competitive" sentence to DLPFC.
4. Fix "as likely" → "more likely" for BASS. Soften "no method stood out" and "rank 11 of 14" on the coarse breast analysis.
5. Name the alternative explanation for PCA > smoothing (an expression-clustering-derived annotation and the low-count Cavity class) next to the "blurring" hypothesis, and cite CellCharter/MENDER there.
6. Align Supplementary Notes 2 and 4 and Table S22 with the main text.

Recommended but optional:
- ARI without Cavity bins;
- k_found reporting;
- a sentence on SEDR's matched-clustering collapse;
- contacting the HiSTaR and Spatial-MGCN authors, or removing the precondition from `LEAKAGE_AUDIT.md`.
