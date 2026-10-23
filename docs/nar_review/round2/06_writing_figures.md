# NAR editorial review 06, round 2: writing and figures

Reviewer role: scientific editor, *Nucleic Acids Research*.
Material reviewed:
- `paper/main.pdf` (9 pp.) and `paper/main.tex`
- `paper/supplementary.pdf` (16 pp.)
- `docs/figures/nar_fig1_pipeline_v2`, `nar_fig2_accuracy`, `nar_fig3_robustness`, `nar_fig4_protocol`, `nar_fig5_maps` and `nar_graphical_abstract` (PNG and PDF; font sizes measured with pdfplumber on the vector PDFs)

Figure numbers below are the **printed** numbers:

| Printed | File | Content |
|---|---|---|
| Figure 1 | `nar_fig1` | design |
| Figure 2 | `nar_fig2` | accuracy |
| Figure 3 | `nar_fig5_maps` | maps |
| Figure 4 | `nar_fig3_robustness` | robustness |
| Figure 5 | `nar_fig4_protocol` | protocol |

Line numbers refer to `paper/main.tex`.

---

## 0. Verdict

The revision fixed most of round 1:
- The journal shell, the protocol naming ("default" and "matched"), the family names, "groups", the count mismatches and the three overclaims are resolved.
- The figure order now follows the citations, and Figures 2–5 are exported at 17.5 cm with text of at least 7 pt.

The new tissue-dependent result is reported honestly in the abstract, in the Results and in the Discussion. However, **the paper's frame has not caught up with it**:
- The title is still generic.
- Figure 2B/C, the headline statistic, is a pooled estimate in which 5 of 7 groups are brain.
- Figure 3 (maps) shows only DLPFC.
- Figure 1A and the graphical abstract still describe a three-dataset, brain-only study. The graphical abstract also contradicts Figure 2.

A reader who looks only at the figures would come away with the round-1 message ("smoothing is among the best").

There are also several new internal inconsistencies, mostly from the dataset extension: seeds per method, development sections, Table S10 counts, Table S12 caption, and the broken Table S20. Two new heading and claim problems also need fixing: "single-cell data" and "hidden" seed.

The rest is polish. **Not yet ready to submit, but close.**

---

## 1. Required changes

### 1.1 Frame: title, figures and graphical abstract must carry the tissue-dependent message

**R1. Title (l. 22).** "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods" does not reflect either main finding. Options:
- **A (recommended):** "Tissue type and the clustering step, more than the encoder, shape benchmark rankings of spatial domain identification methods". The text supports the encoder half only indirectly; if the authors prefer not to claim it, use B.
- **B:** "Benchmarking spatial domain identification across tissues reveals tissue-dependent rankings and an unstable clustering step"
- **C (neutral):** "Accuracy, robustness and reproducibility of spatial domain identification across tissues and technologies"

Update the supplementary title page (`supplementary.pdf` p. 1) to match.

**R2. Figure 2 does not show the result stated in its section heading.**
- The heading of Results 3.1 says "…on brain tissue".
- Panels B and C show one pooled bootstrap that the Methods admit "weights brain data most".
- The breast and Stereo-seq reversal is visible only as a few slightly darker cells in panel A.

Required changes:
- Panel A: put a vertical gap or rule between MERFISH and Breast, and add group headers "Brain" | "Other tissues". Rename the columns "Breast cancer" and "Stereo-seq"; "Stereo" is used nowhere else.
- Panel B: plot two intervals per method, brain groups (5) and non-brain groups (2), offset vertically. Alternatively, add a narrow panel D giving the per-dataset Δ as a diverging heat strip; the values are already in Table S6. The caption then gains: "(B) … filled/open as above; dark: five brain groups; light: breast cancer and Stereo-seq."
- If the authors keep the pooled estimate only, the caption must say: "Five of the seven groups are brain tissue; per-dataset differences are in Supplementary Table S6."

**R3. Figure 2A asterisked cells are not comparable within their column.**
- BASS 0.35\*, NichePCA 0.36\*, GraphST 0.32\*, DeepST 0.37\* and Spatial-MGCN 0.28\* are means over 2 Stereo-seq sections.
- Linear diffusion's 0.31 is a mean over 3 sections, and the text compares them "on the remaining sections".

Caption fix: "\*: mean over the two smaller Stereo-seq sections (memory cap exceeded on the largest); on these two sections linear diffusion has a mean ARI of X." Give the same value in panel B's caption, since those Δ values are computed on 2 sections.

Figure 5E and Figure 4C have the same problem: their "n = 3" is 2 for five methods. Add "(n = 2 for the five methods that exceeded the memory cap)".

**R4. Figure 2 row order.** The caption says "rows ordered by the mean over datasets", but BayesSpace, whose two-dataset mean is about 0.50, is placed last. Add: "BayesSpace (Visium only) is placed last."

**R5. Figure 3 (maps).** The figure shows only DLPFC, with default clustering. This illustrates only the half of the story in which the baseline wins, and with a protocol that is not the primary one.
- Add a second block, or Supplementary Figure S4, with the breast cancer section and one Stereo-seq section: annotation plus 4–5 methods, matched clustering.
- Alternatively, switch the DLPFC row to matched clustering so that it matches Figure 2. Keep "default" only if the authors say why in the caption.
- State which GraphST variant is shown. The Methods (l. ~133) say it was run "with and without its label refinement", and the same applies to Figure 2 and Tables S3–S6. Add to the Fig. 2 and Fig. 3 captions: "GraphST without refinement" (or with).

**R6. Figure 1 must be updated** (panel A and caption l. 85–87).
- Panel A shows only DLPFC, STARmap and MERFISH. Add thumbnails for Visium breast cancer (block A section 1) and Stereo-seq E9.5 embryo. There is room if the large brain icon is removed.
- Alternatively, add a text block "Human breast cancer, 10x Visium, 1 section; Mouse embryo, Stereo-seq, 3 sections (bin50)".
- Retitle panel A "Tissues and technologies".
- Caption (A): "…human DLPFC and breast cancer on 10x Visium, mouse mPFC (STARmap), hypothalamus (MERFISH) and E9.5–E10.5 embryos (Stereo-seq; Supplementary Table S1)".
- Panel E: "Bootstrap over donors and datasets" → "Bootstrap over donor and dataset groups (7)".
- **Font size.** 773 characters (all secondary text, the method names and the "HiSTaR on DLPFC section 151669" caption) are set at **6.5 pt**, below the 7 pt minimum. Raise them to 7 pt. The 20-start dot strip in D is still too small to read: enlarge it or drop it.

**R7. The graphical abstract (`nar_graphical_abstract`) is out of date and contradicts Figure 2.**
- It says "20 sections · 3 technologies · 16 methods" and shows only brain thumbnails. Change to "24 sections · 4 technologies · 3 tissues · 16 methods", with breast and embryo thumbnails added.
- The headline "Training-free smoothing is among the best" omits the tissue dependence. Change it to "Smoothing baseline: top tier on brain, not on tumour or embryo", or show two mini forests (brain / other).
- GraphST is drawn **filled** (interval excludes zero); in the current Figure 2B it is **open** (unresolved). Regenerate the plot from the current Table S6.
- The sign convention is the reverse of Figure 2B: method − baseline, with "← worse / better →", whereas Figure 2B plots baseline − method. Use the same direction as Figure 2B, or label the axis "ARI relative to linear diffusion".
- Add a fourth take-home item: "Test more than one tissue".

### 1.2 Text: consistency and accuracy

**R8. Heading of Results 3.5 (l. 295).** "Selecting fits by likelihood helps on cortex but not on single-cell data" is now inaccurate. Breast cancer (Visium spots, ρ = −0.13) and Stereo-seq (bin50, ρ = 0.00) are not single-cell, and likelihood fails there too.
- Rewrite: "Selecting fits by likelihood helps on cortex but not on the other tissues".
- The following text explains only MERFISH. Add one clause: "…; on breast cancer and Stereo-seq, where domains are small and interleaved, likelihood and ARI were also unrelated."

**R9. Heading of Results 3.4 (l. 283).** "…depends on a hidden random seed" is loaded: the seed is documented R behaviour.
- Rewrite: "The default fit of R mclust depends on the R random seed".
- l. ~292: delete "An earlier version of this experiment attributed the variation to the order of the spots; permuting the rows changes which observations are sampled, so it is the same effect." This sentence is manuscript history and belongs in the response letter. If the spot-order link is worth keeping, write: "Permuting the rows has the same effect, because it changes which observations are sampled."

**R10. Abstract (l. 33–46).** It is 195 words and within NAR's 200-word limit, but three phrases need fixing:
- "HiSTaR did not reproduce its published accuracy": a method does not reproduce. Write "HiSTaR's published accuracy was not reproduced with its official code".
- "helped only on cortex": STARmap is mPFC, but readers think in datasets. Write "helped only on the two cortex datasets".
- "its lead came from brain tissue, while on breast cancer and embryo most methods were slightly ahead" is fine. The last recommendation should add the tissue lesson.

Suggested replacement (≈199 words; recount after the macros expand):
> Spatial domain identification methods are usually compared by small differences in adjusted Rand index (ARI), mostly on one tissue and from a single run. We benchmarked \nMethodsPub{} published methods and three training-free baselines on \nSections{} annotated sections of brain, breast cancer and mouse embryo from four technologies, separating each learned embedding from its clustering step. With the same clustering for every embedding, a neighbourhood-smoothing baseline had a higher mean ARI than \nRobBetter{} of \nRobTot{} comparators and could not be separated from the other \nRobUnres{}, but this lead was confined to brain tissue: on breast cancer and embryo most methods scored slightly higher. On fixed embeddings, refitting the same Gaussian mixture from different random starts changed ARI by \lotMean{} on average (up to \lotMax), and the default fit of R mclust depended on its random seed (up to \mcsSeedMax). Keeping the most likely of 20 fits helped only on the two cortex datasets. HiSTaR's published accuracy was not reproduced with its official code, and the released code of one method selects its reported epoch using the labels. We recommend reporting the clustering protocol and its variance, never selecting runs with labels, including training-free baselines and testing more than one tissue.

**R11. Seeds: the Methods contradict the Supplementary tables.**
- l. 154–156 say "three per section for most methods; one for STAGATE, CCST, Spatial-MGCN and BASS" and, for breast and Stereo-seq, "three seeds for every method (two for CCST…)".
- Table S8 shows GraphST with **1** seed on DLPFC, and DeepST with **1** seed on breast cancer and Stereo-seq. Tables S12 and S20 confirm DeepST at 1 seed.

Rewrite: "…; one for STAGATE, CCST, Spatial-MGCN and BASS, and for GraphST on DLPFC, in the published pipelines … with three seeds for every method except DeepST (one seed, memory) and CCST on the largest Stereo-seq section (two)."

**R12. The development sections are described in three incompatible ways:**
- l. 150: "fixed on DLPFC donor 1" (4 sections)
- l. 160: "frozen on four development sections"
- l. 187: "without the development sections (DLPFC donor 1 and the first section of STARmap and MERFISH)" (6 sections)

State one definition in the Neutrality paragraph and reuse it, for example: "Baseline settings were frozen on DLPFC donor 1 (four sections); the robustness check additionally excludes the first STARmap and MERFISH sections, which were inspected during development (six sections in total)."

**R13. Seed SD for the baselines (l. 229).** "0.003–0.04 for the training-free baselines" is hard-coded and wrong against Table S8, where the range is 0.012–0.054: linear diffusion MERFISH 0.054, AnisoST breast 0.045. Use a macro.

Separately, "about 40 min for CCST" does not match Table S13 (2789 s = 46 min). Write "about 45 min".

**R14. Sign of "difference from the baseline" (l. ~216).** "Averaged over comparators, the difference from the baseline was 0.172 ARI on the three brain datasets and −0.025 on the other two" leaves the direction to the reader. Rewrite:
> "On average, linear diffusion exceeded the comparators by 0.172 ARI on the three brain datasets and trailed them by 0.025 on the other two."

Also rewrite the next sentence, which is convoluted: "…so the gap between published methods and the baseline seen on brain data did not reappear in the opposite direction; rather, no method stood out." Replace it with:
> "On these two datasets the methods were within a few hundredths of each other (Figure 2A); the baseline's deficit there is small, whereas its lead on brain tissue is large."

**R15. Numerals at sentence start.** `\nOom{} methods (…)` (l. 219) and "5 methods exceeded" in the Limitations print as "5 methods". Write "Five methods" in both places, or rephrase as "The memory cap was exceeded by \nOom{} methods…".

**R16. Discussion overstates explanations.**
- l. ~350–352: "In tumour and embryo sections, domains are smaller, interleaved and defined partly by cell composition, so a fixed amount of smoothing blurs them." This is presented as fact. Hedge it and cite the evidence that supports it: on breast cancer and Stereo-seq, **PCA without smoothing** (0.56, 0.35) scored at or above linear diffusion (0.55, 0.31; Table S3).
  > "In tumour and embryo sections, domains are smaller and interleaved and partly defined by cell composition; there smoothing gave no advantage (PCA without smoothing scored as high as linear diffusion; Supplementary Table S3), consistent with a fixed amount of smoothing blurring small domains."
- "…which explains why likelihood and ARI disagree there" → "…which may explain why…". The same hedge is needed in Results ("On MERFISH the best-fitting mixture can separate cell types" → "may separate").
- "the default fit of R mclust, used by several widely used methods": the repetition "used … used" reads poorly. Write "the default fit of R mclust, the final step of GraphST, STAGATE and SEDR,".

**R17. Results 3.1 is now a catch-all.** One subsection holds the pooled accuracy, the tissue dependence, K misspecification, the seed SD, run time and AnisoST. Split it:
- 3.1 "A training-free smoothing baseline is among the most accurate methods on brain tissue": the first paragraph.
- 3.2 "The ranking depends on the tissue": the tissue paragraph plus the memory-cap note.
- 3.3 "Sensitivity to the number of domains, seeds and cost": K, seed SD, run time.
- Move AnisoST to the end of 3.2, or to the Supplementary, as round 1 suggested.

The tissue result is the paper's main new finding and deserves its own heading.

**R18. Naming drift for the reference baseline.** The same method is called:
- "training-free neighbourhood-smoothing baseline" (abstract)
- "standard neighbourhood-smoothing baseline" (Introduction)
- "training-free smoothing baseline" (heading)
- "standard neighbourhood smoothing" (Discussion)
- "linear diffusion" (Results and figures)

Define it once in the Methods ("linear diffusion, i.e. standard graph-Laplacian neighbourhood smoothing") and use "linear diffusion" in the Results and Discussion, so that readers can map the text onto the figures. The abstract may keep the descriptive phrase.

**R19. Dataset naming mixes tissue and technology.** The figure columns are "DLPFC" (tissue), "STARmap" and "MERFISH" (technology), "Breast" (tissue) and "Stereo-seq" (technology). The argument is now about tissue, so the reader has to remember that STARmap is cortex (needed for "helped only on cortex") and that MERFISH is hypothalamus. Either:
- label the columns and legends "DLPFC", "mPFC (STARmap)", "Hypothalamus (MERFISH)", "Breast cancer", "Embryo (Stereo-seq)"; or
- keep the short names and add one sentence to the Fig. 2 caption: "STARmap: mouse mPFC (cortex); MERFISH: mouse hypothalamus."

Whichever is chosen, use the same five labels, in the same order, in Figures 2, 4 and 5, in the Supplementary tables and in the text. Figure 4C currently hyphenates "STAR-map" and "MER-FISH" across lines; widen the columns or use a smaller header.

**R20. Released-code screen (l. ~334).** "An automated screen of the released repositories of 14 methods" is inaccurate. Table S18 lists 14 repositories: 11 benchmarked methods plus SPARK, SpatialPCA and conST, which were not benchmarked. Write:
> "An automated screen of 14 released repositories (11 benchmarked methods and three further spatial methods; Supplementary Table S18)".

**R21. HiSTaR and Spatial-MGCN author contact.** The round-1 TODOs were deleted, but the outcome is not reported. NAR reviewers will ask. Add one sentence to each subsection, for example: "We contacted the authors on [date]; [response/no response by submission]."

**R22. Remaining placeholders.**
- Authors, affiliations, email, CRediT, Funding, the Acknowledgements wording and the GitHub/Zenodo identifiers are still red TODOs.
- The "doi: DOI HERE" and "Advance Access … Day Month Year" lines are template material. Remove them, or confirm that the class does this at submission.
- Data availability lacks a spatialLIBD version or accession.

### 1.3 Captions

**R23. Figure 2 caption** (l. 240–248), in addition to R2–R4:
- "Filled symbols: interval above zero; open symbols: unresolved" applies to B only; panel C dots are always filled. Write "(B) … filled: interval above zero; open: unresolved."
- Add "n = 11 ranked methods" to (C).

**R24. Figure 4 caption** (l. 273–279).
- "Bars: interquartile range; open circle: median" sits after (C), as if it described the heat map. Move it into the opening sentence: "…shape and grey level: dataset; black bar and open circle: interquartile range and median over sections."
- State the row order: "Rows ordered by the median range in A".
- (C): add "rows as in A".
- (B): say whether the median and IQR include the STARmap zeros.
- Replace "−0.0" with "0.0" in panel C (HiSTaR breast, linear diffusion MERFISH, CCST DLPFC, GraphST MERFISH).
- The text (l. ~265) quotes **means** (0.18, 0.09, 0.22) while the figure orders by and draws **medians**. Table S9 gives medians only, so the text's means appear nowhere in the paper. Quote the medians (0.18, 0.07, 0.19), or add a mean column to Table S9.

**R25. Figure 5 caption** (l. 311–314).
- "Rows are ordered by the matched mean" → "Rows are ordered by mean ARI with matched clustering, averaged over datasets (as in Figure 2)".
- Add: "Default clustering values are from the published pipelines for A–C and from the standardised runner for D–E (Methods)."
- Add the Stereo-seq n = 2 note from R3.
- Optional: the x axes show only 0.2 and 0.6; add 0.4.

**R26. Figure 3 caption.** Add the GraphST variant (R5). Also note: "Colours are matched layers, not method families."

### 1.4 Figure legibility (17.5 cm; measured)

| Figure | Width | Smallest font | Issues |
|---|---|---|---|
| 1 | 17.5 cm | **6.5 pt** (773 chars) | below 7 pt (R6); D dot strip too small |
| 2 | 17.5 cm | 7.0 pt | **legend overlap**: "Statistical and neighbourhood methods" runs into the grey "±0.03 equivalence margin" swatch (bottom row). Move the second legend column right or wrap the label. About 1.5 cm of empty space between the axes and the legend; tighten it. "P(best)" is crowded against the panel C title; put it on its own line above the numbers. |
| 3 | 17.5 cm | 7.0 pt | OK. Layer colours repeat the family hues (L1 blue, L2 orange, L3 green); acceptable given R26. No scale bar (optional). |
| 4 | 17.5 cm | 7.0 pt | Panel B: the "×" (noise) markers overplot the seed markers, and the open square (MERFISH) and open inverted triangle (Stereo-seq) are hard to tell apart at print size. Offset the noise crosses on a sub-row (y + 0.25) or move them to a separate small panel, and use a filled marker for one of the two open shapes. The panel C purple–brown diverging map is colour-blind safe. |
| 5 | 17.5 cm | 7.0 pt | When the default–matched difference is small, the family-coloured segment is invisible; this is acceptable because the family dot is shown at left. |
| GA | 25.4 × 10.2 cm | 10 pt | content stale (R7) |

Colour use is now consistent: family colours appear only in Figures 1, 2 and 5, and dataset is encoded by grey and shape in Figure 4. The dataset **order** is the same in every figure.

### 1.5 Supplementary tables (formatting and consistency)

**R27. Table S20 is broken.**
- The "ARI, paper pipeline" and "R mclust perturbation" columns print "**2not run / 3**". The generator evidently replaced the substring "0/20" inside "20/20" with "not run". Fix the replacement so it matches whole cells only.
- The header still says "Lottery (20 starts)". Write "Initialisation experiment (20 starts)".
- The header "Standardised runner + metric panel + resources (sections / seeds)" wraps across four lines with justified spacing. Use `\raggedright` p-columns and shorter headers, for example "Runner (sections / seeds)".

**R28. Table S12 caption is stale.** "Runs: 60 per method (20 sections, 3 seeds), except DeepST (20, seed 0) and BayesSpace (12 Visium sections, seed 0)" does not match the Runs column, which shows 72, 69, 71, 23 and 13. Write: "Runs: 72 per method (24 sections × 3 seeds) unless fewer completed (memory cap); DeepST one seed; BayesSpace Visium sections only."

**R29. Table S10 counts.**
- The "Embeddings" column says 23 per method.
- The caption says only sections with more than 2000 cells are included; there are at most 21 such sections.
- The text says "280 embeddings".
- The "Range > 0.1" percentages are fractions of 20 (75% = 15/20; 37% = 7/19), not of 23.

So the column counts STARmap sections that the statistics exclude. Report the denominator actually used (20 / 19 / 21), or add a column "of which > 2000 cells".

**R30. Table S9 vs text.**
- The text "beat the average single start for 10 of 14 methods and was worse for 3" uses an unstated threshold. The table has 11 positive values, two of them +0.005. State "by more than 0.005".
- The text quotes mean ranges that are absent from the table (R24).

**R31. Table S2.**
- Text is truncated in cells: CCST "…scripts/new_methods.py bec"; BayesSpace "tag v1.5.1 (older release; newer one".
- Justified narrow columns produce "deep graph contrastive au- toencoder" with wide gaps; use ragged-right p-columns.
- Internal identifiers remain: "linear_diffusion", "graphst vs graphst_refined", "lambda_sim", "’deterministic’" (wrong quote mark).
- Upper-case "NOT" and "LEAKAGE" read as shouting; use plain case and refer to Supplementary Note 5.
- The linear diffusion, AnisoST and PCA rows have empty Code and Commit cells: give this repository's commit.

**R32. Minus signs and symbols throughout the Supplementary.**
- Tables S5, S6, S9, S10, S14, S15 and S19 print hyphen-minus ("-0.01", "-0.000", "MERFISH -0.14"). Use `$-$` / U+2212.
- Replace "-0.00" and "-0.000" with "0.00" and "0.000".
- Table S19: "x100" → "×100", "x0.01" → "×0.01", "x2" → "×2".

**R33. "95% CI" vs "95% interval".** The main text uses "interval" except l. 319 ("95% bootstrap CI over sections"). Tables S5, S6 and S16 use "95% CI", and Table S5/S6 also use "Test only".
- Use "95% interval" everywhere.
- Rename "Test only" → "Without development sections".

**R34. Figure-reference style.** The main text cites "Supplementary Fig. S1/S2/S3" (macros `\SF…`), but NAR style and the rest of the paper use "Figure". Write "Supplementary Figure S1".

**R35. Supplementary figures.**
- Fig. S1: tick labels about 5 pt. It covers only the brain datasets, which the caption should say ("on DLPFC, STARmap and MERFISH"). The MERFISH sections are ordered −0.24 … −0.04, the reverse of Table S1.
- Fig. S3: still labelled "Linear" and "Anisotropic" (the caption admits this; relabel to "Linear diffusion" and "AnisoST"). "p = 1.000" → "p > 0.99". "Δ = -0.003" uses a hyphen. The font differs from the house font.

---

## 2. Optional suggestions

1. **Recommendations as a box** (round-1 suggestion). The seven inline items (l. ~360–368) are hard to scan. A numbered box with one evidence pointer each would also give the graphical abstract a source. Fix "(Figure 2A, Figure 5)" → "(Figures 2A and 5)".
2. **"Clustering step varies more than most differences between methods"** (Introduction and Discussion). After the tissue result, between-tissue differences are also large. Consider "…more than most differences between methods on the same dataset".
3. **Introduction.** One sentence would set up the tissue result as a question rather than an afterthought: "Whether a method's advantage on cortex transfers to tissues with smaller, interleaved domains, such as tumours or embryos, is rarely tested."
4. **"Matched clustering"** is defined as "the mclust EEE model" fitted with scikit-learn. Say "equivalent to the mclust EEE model" to avoid implying R mclust.
5. **`\pBestLin`** prints "0.73 of the resamples". "73% of the resamples" reads better.
6. **Figure 1 caption** (about 150 words). It can be cut to about 100 by moving procedural detail (the 20-start example) into panel D's in-figure label.
7. **Spatial-MGCN label leakage** is a headline claim with no figure. A 3-bar inset (final vs label-selected epoch per dataset) could go in the Supplementary.
8. **File names.** Rename the figure files to their printed numbers before upload (`nar_fig5_maps` → `Figure3`, and so on). NAR's upload system and the production editor will otherwise be confused.
9. **Figure 3.** A 500 µm scale bar.

---

## 3. Status of round-1 points (`docs/nar_review/06_writing_figures.md`)

Legend: ✅ resolved · ◐ partly · ❌ open · — superseded

### §0 headline items
| # | Point | Status |
|---|---|---|
| 1 | Bioinformatics Advances shell, VERIFY references, TODOs | ✅ NAR shell, "Computational Biology"; 0 VERIFY in refs/bbl; Table S2 commit given. ◐ author, funding, CRediT and URL TODOs remain (R22) |
| 2 | "Standard/own" contradiction for baselines, HiSTaR, BANKSY | ✅ Default = 3-start GMM for HiSTaR, BANKSY and baselines in main l. 163–167, Table S2 and the Table S3 caption; matched clustering is the primary analysis for all |
| 3 | Figure numbering; colour semantics | ✅ printed order follows the citations; dataset is grey/shape in Fig. 4; Fig. 5 uses family colours; the Fig. 1 caption names Figures 1, 2 and 5. ◐ file names still differ from printed numbers (opt. 8) |
| 4 | Count mismatches (6/12, six patterns, S12 "still running", "every fit", "invariant") | ✅ 8/14 vs S11; "five patterns"; "three representative methods"; invariance claim moved to the S19 caption. ❌ S12 run counts now stale (R28) |
| 5 | Three overclaims | ✅ all softened. New: "single-cell" heading (R8), "hidden" seed (R9) |
| 6 | NAR format (abstract length, GA, panel letters, "Figure", width/fonts) | ✅ abstract 195 words; uppercase letters; "Figure"; all figures 17.5 cm. ◐ Fig. 1 at 6.5 pt; "Supplementary Fig." (R34). ❌ GA exists but is stale (R7) |

### §1 Title and abstract
- Declarative title: ❌ not adopted. It now matters more (R1).
- Abstract: ✅ length, finding stated, "8 of 16" explained, HiSTaR numbers removed, code line moved to Data availability. ◐ wording (R10).

### §2 Journal format
- ✅ journal title, article type, "Materials and Methods", "Conflict of interest statement", section order, uppercase panels, "Figure" in the main text.
- ◐ CRediT TODO, Data availability identifiers (GitHub/Zenodo, spatialLIBD version).

### §3 Terminology
- 3.1 Protocol names: ✅ "default clustering" / "matched clustering" used consistently (equivalent to the proposed BL20).
- 3.2: ✅
- 3.3 Families: ✅ the three families are named identically in Figs 1, 2 and 5 and in the Methods; NichePCA clause added.
- 3.4 BANKSY λ: ✅ roles explained in the Methods; "BANKSY" capitalised in S2.
- 3.5 "cluster" → "group": ✅
- 3.6 Other naming: ◐
  - "Lottery" survives in the Table S20 header (R27).
  - "Anisotropic" survives in Fig. S3 (R35).
  - Naming drift for linear diffusion (R18).
  - ✅ `\lotWorstSection` now prints "DLPFC section 151672"; GraphST "20-PC projection" fixed.

### §4 Line-level edits
- **Introduction:** ✅ all five (ARI defined and cited; GraphST/STAGATE/SEDR named; "can also be"; gap statement; preview of findings).
- **Methods:**
  - ✅ BASS annotation caveat (now in the Limitations); missing verb; heading; NMI "same ranking"; "Initialisation experiment" wording; `\mcNMethods` phrasing.
  - ◐ "default settings" sentence still in both the Methods and the Limitations (acceptable).
  - New inconsistencies: R11, R12.
- **Results 3.1:**
  - ✅ heading, figure citations, equal-weight average stated, run time from Table S13, concrete examples of protocol re-ranking (now in 3.5).
  - ❌ 0.003–0.04 still hard-coded and now wrong (R13); "about 40 min" vs 46 min.
  - ◐ P(best) as a fraction (opt. 5).
- **Results 3.2 (edge):** ✅ test named; invariance sentence corrected and moved; shortened into 3.1. Should move with R17.
- **Results 3.3:**
  - ✅ heading; inflation sentence; "three representative methods".
  - ❌ means in the text vs medians in the figure and Table S9 (R24).
- **Results 3.4:** ✅ reframed around the R seed; STARmap explained. New: R9.
- **Results 3.5:** ✅ heading softened; like-for-like count added; Figure 4C cited. New: R8, R30.
- **Results 3.6:**
  - ✅ heading; resampling unit stated.
  - ◐ "CI" (R33).
  - ❌ author-contact outcome not reported (R21).
- **Results 3.7:** ✅ heading. ❌ "14 methods" vs 14 repositories (R20); ❌ author contact (R21).
- **Discussion:** ✅ "matched or outperformed" removed; "both by"; "14 methods across four technologies"; interpretation paragraph added. New overstatement: R16.
- **Recommendations:**
  - ✅ evidence pointers; (6) and (7) added; R-seed wording.
  - ◐ not a box (opt. 1).
- **Limitations:** ✅ all six proposed additions are present, plus memory-cap and annotation-provenance caveats.
- **Other TODOs:** ◐ (R22).

### §5 Supplementary
| Item | Status |
|---|---|
| Note 1 order | ✅ |
| Note 5 "five" | ✅ |
| Table S2 | ◐ BANKSY, commit and default clustering fixed; truncation, internal names and justification remain (R31) |
| Table S9 | ✅ renamed |
| Table S10 | ✅ mean columns added; ❌ embeddings denominator (R29) |
| Table S11 | ✅ |
| Table S12 | ◐ "still running" removed but run counts stale (R28) |
| Table S16 (now S18) | ✅ explained in the caption |
| Table S17 (now S19) | ✅ labels; ◐ "x100" and hyphens (R32) |
| Table S18 (now S20) | ◐ "Method" header and "not run" added, but the replacement broke the table; "Lottery" remains (R27) |
| Fig. S1 | ◐ text fixed; fonts still ~5 pt |
| Fig. S2 | ✅ |
| Fig. S3 | ◐ test and n named; "Anisotropic" and p = 1.000 remain (R35) |

### §6 Figures
- **Fig. 1:**
  - ✅ A–E caption; commas; neuron icon removed; graph statement in the caption and panel; grey bootstrap tree; BANKSY λ shown; family names.
  - ◐ font 6.5 pt (was 4.7–5.5); D strip still small; caption long.
  - ❌ panel A lacks the new datasets (R6).
- **Fig. 2:** ✅ all eight (baseline caption, BayesSpace row, colour bar, panel B title, P(best) note, uniform line widths, family names, n). New: R2–R4, R23, legend overlap.
- **Robustness (now Fig. 4):**
  - ✅ renumbered; grey/shape palette; STARmap note; colour bar; n per column; full n.
  - ❌ row labels in C and ordering statement (R24).
- **Protocol (now Fig. 5):** ✅ panel letters, colours, order, baselines shown, width. ◐ n of seeds not stated; new R25.
- **Maps (now Fig. 3):**
  - ✅ protocol stated; selection justified (donor 3, accuracy range); L6 brown; "L1…L6" labels.
  - ❌ GraphST variant (R5).
  - Scale bar not added (optional).

### §7 Order and placement
✅ The order is 1 design, 2 accuracy, 3 maps, 4 robustness, 5 protocol, with the first citation of each figure preceding it. The Spatial-MGCN figure was not added (optional).

### §8 Evidence pointers
✅ All eight now have pointers or were removed.

### §9 Graphical abstract
◐ It has been produced, with a three-column layout as proposed, but is now out of date and inconsistent with Figure 2 (R7).
