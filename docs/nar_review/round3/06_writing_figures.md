# NAR editorial review 06, round 3: writing and figures

Reviewer role: scientific editor, *Nucleic Acids Research*.
Material reviewed:
- `paper/main.pdf` (9 pp.) and `paper/main.tex`
- `paper/supplementary.pdf` (18 pp.)
- `docs/figures/nar_fig1_pipeline_v2`, `nar_fig2_accuracy`, `nar_fig3_robustness`, `nar_fig4_protocol`, `nar_fig5_maps` and `nar_graphical_abstract` (PNG viewed; font sizes and clipping measured with pdfplumber on the vector PDFs)
- Supplementary figure pages rendered with pdftoppm (scratchpad `review6r3/`)

Figure numbers are the **printed** numbers: Figure 1 = `nar_fig1_pipeline_v2`, 2 = `nar_fig2_accuracy`, 3 = `nar_fig5_maps`, 4 = `nar_fig3_robustness`, 5 = `nar_fig4_protocol`.

Supplementary tables were renumbered after round 2. Old → new: S8 → S9 (seed SD), S9 → S10 (initialisation), S10 → S11 (R mclust), S12 → S13 (metric panel), S13 → S14 (run time), S18 → S20 (audit), S19 → S21 (invariance), S20 → S22 (which run where).

---

## 0. Verdict

The round-2 changes have been partly applied:
- **Resolved (7):** the graphical abstract, both inaccurate headings, the development-section definition, the hard-coded seed SD and run time, and the Table S11 and S13 counts.
- **Partly resolved (15).**
- **Not resolved (12).**
- **R1 (title):** kept by the authors' choice and not counted as open.

The text now tells the tissue-dependent story consistently: the abstract, the Introduction's preview, the Results, the Discussion and the graphical abstract all say it. **Figures 2 and 3 do not.** Figure 2A has no brain / other split, and Figure 2B/C is still the pooled estimate. Figure 3 still shows only DLPFC, with default clustering. A reader who looks only at the figures still sees "the baseline is among the best".

There are also new problems:
- Figure 1 clips "PAS" at its right edge.
- Several Supplementary tables print ranges as "1-−10".
- Three new text inconsistencies: Supplementary Note 4 against the Bonferroni intervals, "BASS was as likely" in the Discussion, and "helped only on cortex" in the abstract.

**Not ready to submit. One focused revision, mostly to Figure 2, Figure 3 and the captions, would get it there.**

---

## 1. Status of the 35 round-2 required changes

Legend: ✅ resolved · ◐ partly · ❌ not resolved

| # | Point | Status | Evidence (round 3) and remaining fix |
|---|---|---|---|
| R1 | Title | — kept | Authors' choice; not counted. The supplementary title page matches the main title. |
| R2 | Fig. 2 must show the tissue split | ❌ | Panel A has no gap or rule between MERFISH and Breast, and no "Brain / Other tissues" headers. The headers are still "Breast" and "Stereo". Panel B is pooled only. The caption lacks "Five of the seven groups are brain tissue; per-dataset differences in Supplementary Table S6". That sentence appears only in the Methods. The graphical abstract now has the brain/other dumbbell, so Fig. 2 can reuse that design: a two-point (brain/other) panel D, or two offset intervals in B. |
| R3 | Asterisked Stereo-seq cells not comparable | ◐ | The caption gives "*: mean over the two smaller Stereo-seq sections (memory cap exceeded on the largest)". It still lacks linear diffusion's mean on those two sections, so the column cannot be compared. Fig. 5 caption: ✅. Fig. 4C caption ("columns rest on … 3 sections") has no n = 2 note. |
| R4 | BayesSpace placed last despite "rows ordered by the mean" | ❌ | The caption is unchanged. Add "BayesSpace (Visium only) is placed last". |
| R5 | Fig. 3 shows DLPFC only, default clustering; GraphST variant | ❌ | The figure is unchanged ("DLPFC section 151673, default clustering"). No breast or Stereo-seq maps in the main text or the Supplementary. The GraphST variant (with or without refinement) is not stated in Fig. 2 or Fig. 3. |
| R6 | Fig. 1 panel A, caption, panel E, fonts | ◐ | ✅ Panel A is now "Tissue and technology" with breast cancer and Stereo-seq thumbnails, and the caption lists all five datasets. ✅ 6.5-pt text is down from 773 to 74 characters. ❌ 74 characters are still at 6.5–6.8 pt, all in panel E ("vs", "Agreement", "Domain and spatial quality", "Cost", "Bootstrap over donors and datasets"). ❌ Panel E and the caption still say "Bootstrap over donors and datasets" rather than "… donor and dataset groups (7)". **New:** "PAS" is clipped (see N1). |
| R7 | Graphical abstract stale | ✅ | "24 sections · 4 technologies, 3 tissues · 16 methods". Breast and embryo thumbnails added. Headline "Smoothing baseline: ahead on brain, not elsewhere". Brain/other dumbbells. Direction "baseline ahead →" matches Fig. 2B. Take-home "Include baselines and several tissues". The values match Table S6. For example, GraphST is +0.16 on brain and −0.06 on the other tissues. Wording polish: N11. |
| R8 | Heading "…single-cell data" | ✅ | The heading is now "…helps on cortex but not on the other tissues", and the text gives ρ for breast (−0.13) and Stereo-seq (0.06). |
| R9 | "hidden" seed; manuscript-history sentence | ✅ | The heading is now "The default fit of R mclust depends on its random seed". The history sentence is gone. |
| R10 | Abstract wording | ◐ | ✅ "HiSTaR's published accuracy was not reproduced". ✅ The last recommendation adds tissues. ✅ 199 words. ❌ "helped only on cortex" is unchanged and is now also inconsistent (N6). ❌ "BASS and it were most likely to rank first" is new and awkward (N10). |
| R11 | Seeds: Methods vs Supplementary | ◐ | The Methods now say "…and for GraphST on DLPFC" and explain the DeepST and CCST exceptions, matching Table S9. Remaining: (i) Table S22 lists GraphST "20/24 / 3" in the paper pipeline, but S9 has 1/3/3/3/3. (ii) The Limitations say "Four methods were run with one seed in the published pipelines", which omits GraphST on DLPFC. (iii) Table S13 gives DeepST "27" runs, while S22 says "23/24 / 3" (N8). |
| R12 | Development sections defined three ways | ✅ | The Neutrality paragraph defines four DLPFC donor-1 sections for settings and six for the robustness check. The Baselines and Statistics paragraphs are consistent with it. |
| R13 | Seed SD range; CCST time | ✅ | "0.012–0.054" and "about 46 min", both matching Tables S9 and S14. |
| R14 | Sign of the "difference from the baseline" | ◐ | The second sentence was rewritten ("the methods were close to each other … PCA without any smoothing was also ahead"). The first is unchanged: "the difference from the baseline was 0.172 … and −0.027". Write "linear diffusion exceeded the comparators by 0.172 ARI on the three brain datasets and trailed them by 0.027 on the other two". |
| R15 | Numerals at sentence start | ◐ | The Results is fixed ("In our runs BASS, DeepST … exceeded"). The Limitations still begin a sentence with "5 methods exceeded the 12 GB memory cap": write "Five methods". |
| R16 | Discussion overstatements | ◐ | ✅ The tumour/embryo sentence is now hedged ("a possible explanation, which we did not test") and cites PCA without smoothing. ❌ "which explains why likelihood and ARI disagree there" → "which may explain". ❌ Results "the best-fitting mixture can separate cell types" → "may". ❌ "the default fit of R mclust, used by several widely used methods" → "the final step of GraphST, STAGATE and SEDR". |
| R17 | Split Results 3.1 | ❌ | One subsection still holds the pooled accuracy, the tissue dependence, breast K = 4, the memory cap, K misspecification, seed SD, run time and AnisoST. Its heading "…most accurate methods on brain tissue" now introduces the non-brain result too. Split as proposed: 3.1 brain accuracy; 3.2 "The ranking depends on the tissue"; 3.3 K, seeds and cost. |
| R18 | Naming drift for the reference baseline | ◐ | ✅ The Methods now define it ("Linear diffusion is standard neighbourhood smoothing (graph Laplacian smoothing)"). ❌ The Discussion's first paragraph still has "standard neighbourhood smoothing had a higher mean ARI…". ❌ The Results heading says "A training-free smoothing baseline". Use "linear diffusion" in both. |
| R19 | Dataset labels mix tissue and technology | ◐ | Fig. 1 now gives "mouse mPFC" and "mouse hypothal." (write "hypothalamus"). Not done: the Fig. 2 headers are still "Breast" and "Stereo". The Fig. 2 caption still lacks "STARmap: mouse mPFC (cortex); MERFISH: mouse hypothalamus". Fig. 4C still hyphenates "STAR-map", "MER-FISH" and "Stereo-seq". The graphical abstract mixes "Breast"/"Embryo" with "STARmap"/"MERFISH". |
| R20 | "released repositories of 14 methods" | ◐ | The Table S20 caption now explains the composition (11 benchmarked + SPARK, SpatialPCA, conST). Main text p. 5 still says "of 14 methods". Write "14 released repositories (11 benchmarked methods and three further spatial methods)". |
| R21 | HiSTaR / Spatial-MGCN author contact | ❌ | No mention of contact in either subsection. |
| R22 | Placeholders | ❌ (author-side) | Authors, affiliations, email, CRediT, Funding, Acknowledgements wording and the GitHub/Zenodo identifiers are still red TODOs. "doi: DOI HERE" and "Advance Access … Day Month Year" are still printed. No spatialLIBD version is given. |
| R23 | Fig. 2 caption: filled/open applies to B only; n of ranked methods | ❌ | The caption still says "Filled symbols: interval above zero; open symbols: unresolved" without restricting it to B. Panel C dots are always filled, which contradicts the shared legend. Add "(B) … ; in C all dots are filled". (C) still has no n: add "16 methods ranked; BayesSpace not ranked". |
| R24 | Fig. 4 caption and panel C | ◐ | ✅ "In A and B, bars: interquartile range; open circle: median" now precedes (C). ❌ Row order not stated: add "Rows ordered by median range in A; C shares the rows of A". ❌ Whether STARmap zeros enter B's median is not stated. ❌ "−0.0" is still printed four times in C. ❌ The text quotes **mean** ranges (0.18, 0.09, 0.22) citing Table S10, which gives **medians** (0.18, 0.07, 0.19): quote the medians or add a mean column. |
| R25 | Fig. 5 caption | ◐ | ✅ "ordered by the matched-clustering mean over the five datasets". ✅ Stereo-seq n = 2 note. ❌ No statement that default values come from the published pipelines (A–C) and the runner (D–E). ❌ The x axes still show only 0.2 and 0.6 (optional). |
| R26 | Fig. 3 caption: GraphST variant; colours | ❌ | Unchanged. |
| R27 | Table S20 (now S22) broken | ◐ | ✅ "2not run / 3" fixed. ❌ The header still says "Lottery (20 starts)". ❌ "Standardised runner + metric panel + resources (sections / seeds)" still wraps over four justified lines. ❌ "Invariance tests (sec- tions)" is hyphenated. Use `\raggedright` p-columns and short headers ("Runner (sections / seeds)", "Initialisation (20 starts)", "Invariance (sections)"). |
| R28 | Table S12 (now S13) run counts | ✅ | The caption now reads "Runs: last column (successful runs; up to 72 = 24 sections × 3 seeds)". DeepST's 27 needs a footnote (N8). |
| R29 | Table S10 (now S11) denominators | ✅ | The column is now "Embeddings (n > 2000): 21 of 24 / 20 of 23", and the percentages match (71% = 15/21). |
| R30 | "10 of 14 … worse for 3" threshold | ❌ | Table S10 has 11 positive and 3 negative "best-likelihood minus mean" values. Two are exactly +0.005, so only 9 exceed 0.005. Neither reading gives 10. Recount and state the threshold. |
| R31 | Table S2 formatting | ◐ | ✅ Truncation fixed (CCST, BayesSpace). ❌ Justified narrow columns are still there ("contrastive au- toencoder", "Linear diffu- sion", "convolu- tional"). ❌ Internal identifiers remain ("lambda_sim", "graphst vs graphst_refined", "’deterministic’", "same as linear_diffusion"). ❌ Shouting remains ("NOT", "LEAKAGE"). ❌ The baselines have empty Code/Commit cells. |
| R32 | Minus signs and symbols | ◐ | ✅ Tables S5 and S6 now use U+2212. ❌ "−0.00"/"−0.000" remain (S6 Spatial-MGCN, SpaceFlow, HiSTaR; S7; S15 BANKSY λ = 0.2; S10 HiSTaR "−0.00"). ❌ Table S21 still has "x100", "x0.01" and "x2". **New regression:** ranges print as "1-−10", "0.05-−0.10" and "0.454-−0.525" in Tables S7, S8, S10 and S18 (N4). |
| R33 | "95% CI" vs "95% interval"; "Test only" | ❌ | Main text: "95% bootstrap CI over sections" (HiSTaR). Supplementary: "95% CI" in Tables S5–S7 and S18. "Test only" remains in S5 and S6. |
| R34 | "Supplementary Fig." | ❌ | Three instances remain in `main.tex` (l. 155, 250, 284). |
| R35 | Supplementary figures | ❌ | Fig. S1: tick labels about 5 pt. The caption does not say brain only. MERFISH is still ordered −0.24…−0.04. Fig. S3: still "Linear"/"Anisotropic", "p = 1.000" and the hyphen in "Δ = -0.003". |

**Tally:** 7 ✅ (R7, R8, R9, R12, R13, R28, R29) · 15 ◐ (R3, R6, R10, R11, R14, R15, R16, R18, R19, R20, R24, R25, R27, R31, R32) · 12 ❌ (R2, R4, R5, R17, R21, R22, R23, R26, R30, R33, R34, R35) · R1 kept by choice.

---

## 2. Figure check (round 3)

| Figure | Size | Smallest font | Overlap / clipping | Caption–figure match |
|---|---|---|---|---|
| 1 | 17.5 × 9.8 cm | **6.5 pt** (2 chars), **6.8 pt** (72 chars), all in panel E | **"macro-F1, CHAOS and PA[S]" is clipped at the right edge.** The "S" lies outside the page box in the PDF and is missing in the PNG. Panel C's footnote "Output is an embedding or domain labels" ends about 1 mm from panel D's "ARI 0.23". The embryo thumbnail touches the bottom edge. | (E) "bootstrap over donors and datasets" (R6). Otherwise matches. |
| 2 | 17.5 × 11.4 cm | 7.0 pt | ✅ The legend overlap from round 2 is gone. "P(best)" still sits against the panel C title; put it on its own line. About 1.5 cm of empty space remains between the axes and the legends. "reference" in B is crossed by the zero line and the grey band. "STARmap" and "MERFISH" headers almost touch. | R2, R3, R4, R23 above. |
| 3 | 17.5 × 8.4 cm | 7.0 pt | No problems. | GraphST variant missing (R5, R26). Default clustering, while Fig. 2 uses matched; say why or switch. |
| 4 | 17.5 × 10.4 cm | 7.0 pt | ✅ The noise crosses are now offset from the seed markers. ✅ Breast is a filled diamond, so it no longer looks like the open MERFISH square. B is still dense but readable. C headers hyphenated (R19). "−0.0" ×4 (R24). | Row order and n = 2 not stated (R24, R3). |
| 5 | 17.5 × 8.6 cm | 7.0 pt | No problems. | Default-source sentence missing (R25). Order matches Fig. 2 minus the internal-clustering methods ✅. |
| GA | 25.4 × 10.2 cm | 9.5 pt | No problems. No x scale on the dumbbell (acceptable for a GA; a "0" tick would help). | Matches Table S6 and Fig. 2B direction ✅. |
| S1 | – | about 5 pt | – | Brain only, not said; MERFISH order reversed (R35). |
| S3 | – | – | – | "Anisotropic", "p = 1.000" (R35). |

---

## 3. Story consistency

| Element | Tissue-dependent message? | Comment |
|---|---|---|
| Title | — (kept) | Authors' choice. |
| Abstract | ✅ | "Its lead came from brain tissue: on breast cancer and embryo most methods … were slightly ahead". But see N6 and N10. |
| Introduction | ✅ | The preview names "on brain tissue but not on the other tissues". |
| Results | ✅ in text | It sits inside a section headed "…on brain tissue" (R17). |
| Discussion | ✅ | But "BASS was as likely to rank first" (N5) and "standard neighbourhood smoothing" (R18). |
| Fig. 1 | ✅ | All five datasets shown. |
| **Fig. 2** | ❌ | Pooled only (R2). |
| **Fig. 3** | ❌ | DLPFC only (R5). |
| Fig. 4 / 5 | ✅ | Per-dataset columns and panels. |
| Graphical abstract | ✅ | Brain vs other is the headline. |

---

## 4. New required changes

**N1. Figure 1, clipped text.** "PAS" in panel E is cut at the right edge. Shorten to "macro-F1, CHAOS, PAS", or move the panel E text block left by about 2 mm. Raise the 74 characters at 6.5–6.8 pt in panel E to 7 pt in the same pass. Add 1–2 mm between panel C's italic footnote and "ARI 0.23", for example by ending the C footnote at the C column. Write "hypothalamus" in full in panel A.

**N2. Supplementary ranges "1-−10".** The minus-sign replacement turned the en dash in ranges into "-−":
- Table S7 and S8 rank intervals
- Table S10 IQR
- Table S18 CI

Fix the generator to emit "1–10" and "0.454–0.525". Replace minus signs only at the start of a number, not after a range separator.

**N3. Supplementary Note 4 contradicts the paper.** It says "No correction for multiple comparisons is applied", but Tables S5–S7 and the main text report Bonferroni intervals. Write instead: "Intervals are uncorrected; Bonferroni-corrected intervals over the 16 comparisons are given as a check."

**N4. Discussion, p. 6.** "no method was shown to be equivalent to it, and BASS was as likely to rank first". BASS ranked first in 0.49 of resamples against 0.29 for linear diffusion (and 0.43 vs 0.44 in the runner). Write "…and BASS was at least as likely to rank first".

**N5. Abstract vs Results on likelihood.** The abstract says "Keeping the most likely of 20 fits helped only on cortex". The Results say the best-likelihood fit beat the average single start for "10 of 14 methods" pooled over datasets, and the cortex statement concerns the likelihood–ARI correlation. Write instead: "Likelihood tracked ARI only on the two cortex datasets, so keeping the most likely of 20 fits is not a reliable fix."

**N6. Abstract syntax.** "BASS and it were most likely to rank first" → "BASS and the baseline were the most likely to rank first".

**N7. Run counts in the Supplementary.** Table S13 lists DeepST with 27 runs, which implies seed 0 only on the first three datasets in the runner. Table S22 says "23/24 / 3". Reconcile them and add a footnote to S13: "DeepST: one seed on DLPFC, STARmap and MERFISH (memory)".

**N8. Graphical abstract wording.** "not elsewhere" generalises from one breast section and one embryo study. Write "ahead on brain, not on breast cancer or embryo". The brain point is the equal-weight mean of the three brain datasets, which is not the group-weighted estimate in Fig. 2B; say so in the GA legend or alt text.

---

## 5. Fixes in priority order

1. **Figure 2:** brain/other split in A (rule plus headers) and in B (two offset intervals or a brain/other dumbbell panel as in the GA). Rename the columns "Breast cancer" and "Stereo-seq". Update the caption (R2, R3, R4, R19, R23).
2. **Figure 3:** add a breast cancer and Stereo-seq row (or Supplementary Figure S4) with matched clustering. Add the GraphST variant and the "colours = matched layers" note to the caption (R5, R26).
3. **Figure 1:** fix the "PAS" clipping, the 6.5–6.8 pt text and "groups (7)" (N1, R6).
4. **Text:** split Results 3.1 (R17); fix the one-line items R10, R14, R15, R16, R18, R20, N4, N5 and N6. Add the author-contact sentences (R21).
5. **Supplementary:**
   - Range "-−" bug (N2), "−0.00" values and "x100" (R32)
   - "95% interval" and "Without development sections" (R33)
   - Table S2 formatting (R31)
   - Table S22 header (R27)
   - Note 4 (N3)
   - DeepST runs (N7)
   - R30 recount
   - Figures S1 and S3 (R35)
   - "Supplementary Figure" in the main text (R34)
6. **Before upload:** clear all TODOs, DOI and date placeholders (R22). Rename the figure files to their printed numbers (round-2 optional 8, still open).
