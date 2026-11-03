# NAR editorial review 06, round 5: writing and figures

Material: `paper/main.pdf` (10 pp.), `paper/supplementary.pdf` (20 pp., landscape), `paper/main.tex`, `docs/figures/nar_fig1_pipeline_v2`, `nar_fig2_accuracy`, `nar_fig3_robustness` (printed Fig. 4), `nar_fig4_protocol` (printed Fig. 5), `nar_fig5_maps` (printed Fig. 3), `nar_figS_maps_new` (Suppl. Fig. S3), `nar_graphical_abstract`, plus all 10 main pages and 20 supplement pages rendered to images. Figure font sizes were measured with pdfplumber. The title is not commented on. TODO placeholders are ignored.

## 0. Verdict

**Minor revision, editorially ready after a short list of small fixes.** The manuscript reads coherently. The abstract, Introduction, Results, Discussion, Figures 1, 2 and 5 and the graphical abstract tell the same tissue-dependent story. Terminology is now stable: "matched" and "default" clustering, "linear diffusion", "standardised runner". All main figures are at least 7 pt (the graphical abstract is at least 9.5 pt), with no overlap and no clipping, except the Fig. 2 title that touches the top edge. The supplementary tables are landscape, at 7–8 pt, with no overflow. Table S2 is a longtable with a repeated header. Table references in the main text match the current table numbering (S11 seed SD, S12 initialisation, S13 R mclust, S14 default against matched, S16 cost). Nothing below is structural. Most open points are cosmetic, and the one numerical item is "10 of 14" (N1).

## 1. Status of round-4 items

| Round-4 item | Status now |
|---|---|
| F2 mean against median range | RESOLVED. The text (0.18, 0.09, 0.22) now matches the new "Mean range" column of Table S12 (LD 0.18, SpaceFlow 0.09, BANKSY λ = 0.8 0.22). The citation points to S12. |
| F3 GraphST memory | RESOLVED. The Results say "reaching or exceeding the 12 GB cap". Residual wording point: N4. |
| R30 / F9 "10 of 14" | NOT RESOLVED. See N1. |
| F1 / R6 Fig. 1 "bootstrap over donors and datasets" | NOT RESOLVED. The text is unchanged in Fig. 1E and its caption. |
| F4 Table S2 | PARTLY. Hyphenation is fixed, there is no truncation, and the longtable header repeats. Still open: the Spatial-MGCN default-clustering cell collides with the next column ("LEAKAGE, see docs/LEAKAGE_AUDIT.md)section"). Internal identifiers remain ("LEAKAGE", "docs/LEAKAGE_AUDIT.md", "docs/BIGMEM_RERUN.md", "hicast/histar.py", "scripts/new_methods.py", "networkx>=3", "n_init=100", "numpy nan_to_num"). The PCA Deviations cell is empty. |
| F5 Results flow (AnisoST paragraph) | NOT CHANGED. See N3. |
| F6 Fig. 2 top edge, "P(best)" | NOT RESOLVED. pdfplumber still flags the "M" of "Mean ARI, matched clustering" at the page edge. "P(best)" still sits on the C title line. "reference" is still crossed by the zero line. |
| F7 symbols | NOT RESOLVED. Table S23 still has "x100", "x0.01", "x2", "1-3" and "2-3". Note 4 still has "1 - 0.05/16". "λ=0.8" without spaces remains in Tables S3–S12 and once in the Results ("BANKSY λ=0.8 in 0.04"). |
| F8 Suppl. Fig. S1 | PARTLY. The caption now says that all datasets are in Fig. 4A. Ticks and legend are still about 5 pt, and MERFISH runs −0.24 to −0.04. |
| F10 dataset names | NOT RESOLVED. The Fig. 2A header still says "Stereo". Fig. 4C still hyphenates "STAR-map", "MER-FISH" and "Stereo-seq". The graphical abstract still uses "Breast" and "Embryo". |
| F11 / R21 author contact | NOT RESOLVED. There is no sentence on the HiSTaR and Spatial-MGCN authors. |
| "BANKSY two λ → 17 entries" note | NOT ADDED. See N5. |
| Softening "starting with a smoothing baseline" | NOT CHANGED. See N6. |
| All other round-4 items | Remain resolved. |

## 2. New findings, ranked

**N1 (moderate): "10 of 14 methods" does not match Table S12.**
- Location: Results, section "Selecting fits by likelihood…" (main p. 5): "beat the average single start by more than 0.005 ARI for 10 of 14 methods and was worse for 3".
- Table S12 gives 9 methods with a printed best-likelihood minus mean strictly above +0.005. Two more (SpaceFlow and BANKSY λ = 0.8) print exactly +0.005, and 3 are negative. The caption says that printed +0.005 values "may fall on either side", so the count cannot be confirmed from the table.
- Fix: print three decimals for those two methods and recount. Alternatively write "by at least 0.005 for 11 of 14 methods", which matches 14 − 3 negatives. Keep "worse for 3".

**N2 (minor to moderate): Suppl. Fig. S1 (suppl. p. 17).**
- The tick labels and legend are about 5 pt, below the 7 pt standard.
- STARmap tick labels read "0417_BZ5" while Table S1 uses "20180417_BZ5_control".
- The MERFISH sections run −0.24 to −0.04, with a hyphen instead of a minus sign.
- The AnisoST row shows open circles at ARI about 0 on all three STARmap sections (R mclust default fit). This is the most striking feature of the panel and is not mentioned in the caption or the text.
- Fix: redraw at 7 pt or larger and use the section names of Table S1. Order the MERFISH sections by Bregma, left to right. Add one caption sentence: "R mclust's default fit collapsed (ARI about 0) for AnisoST on STARmap, which has fewer than 2000 cells", or explain why that happens.
- The image file is still called `v2_fig1_lottery.png`. This is harmless but should be renamed.

**N3 (minor): Results flow.**
- The AnisoST paragraph (MERFISH 0.363 against 0.497, boundary accuracy, Suppl. Fig. S4) sits at the end of "Number of domains, seed variability and cost" and breaks that subsection. Move it to the end of "The lead of the baseline depends on the tissue".
- The seed-variability sentence ("0.047 on DLPFC and 0.180 on STARmap, against 0.012–0.054") is followed directly by cost. Add a transition or a one-line subsection break.
- The "Seeds" paragraph in Methods (about 400 words) mixes seed counts, memory caps, the second-server rerun, the GraphST wrapper and a DeepST confound. Split it into "Seeds" and "Memory-capped jobs and reruns". The 17 jobs and 20 records detail could go to Suppl. Note 6.

**N4 (minor): consistency of the memory statement.**
- Limitations say "Five methods needed more than the 12 GB … (up to 28 GB)". Table S16 lists GraphST at 11.8 GB, and the Results say "12–28 GB … reaching or exceeding the cap".
- Fix: use "reached or exceeded the 12 GB cap" in the Limitations as well.
- The Table S16 caption should state whether peak memory is the median or the maximum over jobs.
- BayesSpace shows 12.5 GB there, which is the DLPFC run without a cap. Say so in a footnote.

**N5 (minor): the "16 methods" count.** The Fig. 2 rows contain 17 entries: 13 published methods, 3 baselines and the second BANKSY λ. The text counts "16 comparators" (correct, since 17 minus the reference is 16), "16 methods ranked" (C) and "16 methods" (graphical abstract). Add to the Fig. 2 caption: "BANKSY was run with two λ values, giving 17 entries; 16 comparators". Use the same wording in the graphical abstract note, or write "17 method variants".

**N6 (minor): tone of the recommendation.**
- Discussion: "the results suggest starting with a smoothing baseline". The evidence is exploratory and tissue-dependent. Write "suggest including a smoothing baseline as a reference".
- In Recommendation (4), "include training-free baselines" is fine.

**N7 (minor): Fig. 1 and its caption.**
- Replace "Bootstrap over donors and datasets" with "Bootstrap over 7 donor and dataset groups" in the panel and the caption.
- The E block ends 1.6 pt from the right edge. Shift it left by about 2 mm.
- The Fig. 1C count "Statistical and neighbourhood methods 4" lists BANKSY once, which agrees with 13. Say "BANKSY (λ = 0.2, 0.8)" is one method in the caption, together with the point in N5.

**N8 (minor): Fig. 2 and Fig. 4 layout.**
- Fig. 2: add about 2 mm of top margin. Put "P(best)" on its own line above the numbers. Move "reference" off the zero line. Change the "Stereo" header to "Stereo-seq" (the column is narrow, so "Stereo-seq" at 7 pt may need a line break). The brain/other triangles are very small and light grey. Enlarge them or darken the filled triangle.
- Fig. 4: panel C has no row labels. The caption says "C uses the same rows", but the panel is three columns away from the labels in A. Repeat the labels, or add a faint guide line. Remove the hyphenation of "STAR-map" and "MER-FISH" (use "STARmap" and "MERFISH", with a smaller header font if needed). The overlapping symbols in A and B are dense but legible. The caption already says so.

**N9 (minor): supplementary symbols and identifiers.**
- Table S23: "x100", "x0.01", "x2" become "×100", "×0.01", "×2". "1-3" and "2-3" become "1–3" and "2–3".
- Note 4: "1 - 0.05/16" becomes "1 − 0.05/16".
- Use "λ = 0.8" with spaces in Tables S3–S12 and in the main text ("BANKSY λ=0.8 in 0.04").
- Table S2: wrap the Spatial-MGCN default-clustering cell (`\raggedright`) and rewrite it as "k-means each epoch; epoch chosen by ARI against the annotation (label use, Suppl. Note 5)". Remove or replace the repository paths and code syntax listed in section 1 with plain wording. Fill the PCA Deviations cell ("same as linear diffusion").
- Note 1 and Note 3 contain `spatialbench/metrics.py`, `scripts/audit_leakage.py` and `docs/LEAKAGE_AUDIT.md`. Keep them only if the repository is released with those paths.

**N10 (minor): dataset naming in the graphical abstract.** The thumbnails mix dataset and technology names ("Breast", "Embryo", "STARmap", "MERFISH"). Use "Breast cancer" and "Mouse embryo", and add "equal-weight mean of datasets" to the legend or alt text. There is no x scale on the dumbbell plot, which is acceptable for a graphical abstract. Fix: "Same embedding" shows two maps without saying which method or section (HiSTaR 151669, as in Fig. 1D). Add that to the caption or alt text.

**N11 (minor): maps and colour.** Fig. 3 and Suppl. Fig. S3 use categorical colours. In S3 the tab20 palette is not colour-blind safe, but the ARI is printed. In Fig. 3 the orange (L2) against the red-brown (L6) and the green (L3) against the blue (L1) differ mainly in hue. Add one caption clause: "colours are not optimised for colour-vision deficiency; ARI is given in each title". The S3 caption should name the GraphST variant for breast cancer (with or without refinement) as Fig. 3 does.

**N12 (minor): writing.**
- Abstract: "mostly on one tissue and one run" is fine. The abstract never says "linear diffusion"; "neighbourhood-smoothing baseline" is used instead, and the first Results heading then introduces "Linear diffusion". Add "(linear diffusion)" once in the abstract.
- Methods: "Neutrality." is a run-in head with a line break in the PDF. Make it a proper run-in paragraph head.
- Results: "the larger of the two directions 0.09, up to 0.49" is unclear. Rewrite as "0.09 in the worse direction".
- Results (long sentence): "Restricting the comparison to the datasets with an expert annotation (…) gave the same picture: 7 comparisons favoured the baseline, 9 were unresolved, and BASS and linear diffusion ranked first in 0.37 and 0.37 of the resamples". Split it, and say "0.37 each".
- Data availability: the long 10x URL runs past the column and is broken mid-word ("...block-a-sectio"). Shorten it with the DOI, or put it in the reference only.
- "Day Month Year", the DOI and the author block are author-side and ignored.
- The Acknowledgements say that a first draft was produced with an AI coding assistant. That is acceptable for NAR if it is stated. Check the journal's policy on AI-use disclosure wording.
- R21: add "The authors of HiSTaR and Spatial-MGCN were informed of these findings before submission" if true, or say they were not contacted.

## 3. Figure legibility summary

| Figure | Size | Smallest text | Comment |
|---|---|---|---|
| 1 | 17.5 × 9.8 cm | 7 pt | No clipping. Right edge margin 1.6 pt. |
| 2 | 17.5 × 11.4 cm | 7 pt | Title at the top edge, "P(best)" crowded. |
| 3 (maps) | 17.5 × 8.4 cm | 7 pt | Fine. |
| 4 | 17.5 × 10.4 cm | 7 pt | C lacks row labels and has hyphenated headers. |
| 5 | 17.5 × 8.6 cm | 7 pt | Fine. |
| S3 maps | 17.5 × 7.6 cm | 7 pt | Fine. |
| Graphical abstract | 25.4 × 10.2 cm | 9.5 pt | Fine. |
| S1 | raster | about 5 pt | Too small (N2). |
| S2, S4 | raster / vector | at least 7 pt | Fine. |

Supplementary tables use 7–8 pt on landscape pages. The widest table text ends at x = 785 of 842 pt, so there are no margin overflows. Tables S5–S8 are dense but readable.
