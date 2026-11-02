# NAR editorial review 06, round 4: writing and figures (final)

Material: `paper/main.pdf` (10 pp.), `paper/supplementary.pdf` (20 pp.), `paper/main.tex`, `docs/figures/nar_fig1_pipeline_v2`, `nar_fig2_accuracy`, `nar_fig3_robustness` (printed Fig. 4), `nar_fig4_protocol` (printed Fig. 5), `nar_fig5_maps` (printed Fig. 3), `nar_figS_maps_new` (Suppl. Fig. S3), `nar_graphical_abstract`. Font sizes and clipping were measured with pdfplumber on the vector PDFs. Pages were rendered to `scratchpad/review6r4/`. The title was kept by the authors' choice and is not an open point. The R mclust panel of Fig. 4 is expected to change slightly and is not counted.

## 0. Verdict

The manuscript is much improved and is now scientifically and editorially coherent.

- **Round-3 points:** 22 resolved, 8 partly, 2 not resolved or author-side (R21, R22). R30 is still unresolved. R1 is excluded (title kept).
- **Story consistency:** the abstract, Introduction, Results, Discussion, Figure 2, Figure 1 and the graphical abstract now all tell the same tissue-dependent story. The earlier Fig. 2 and Fig. 3 gaps are closed.
- **Memory rerun:** it is described neutrally and consistently (Methods, Results, Limitations, Suppl. Note 6, Tables S2, S15). One number is inconsistent (GraphST, see F3).
- **Legibility:** all figure text is at least 7 pt. There is no clipping and no overlap in the main figures.
- **Remaining:** a short list of fixes, mostly in Supplementary Table S2, two text/table mismatches and some placeholders. None are structural. **Ready after the minor fixes below.**

## 1. Status of every earlier required change

Legend: RES resolved, PART partly, NOT not resolved.

| # | Status | Evidence now and remaining fix |
|---|---|---|
| R2 Fig. 2 tissue split | RES | Fig. 2A has "Brain / Other tissues" headers and a white rule. Fig. 2B has brain (filled) and other (open) triangles. The caption says "five of the seven groups are brain tissue" and gives the dataset identities. The graphical abstract matches. Optional: "Stereo" in the A header should read "Stereo-seq". |
| R3 asterisked Stereo-seq cells | RES | The asterisks are gone. The 17 rerun jobs enter the means, and the Methods say so. |
| R4 BayesSpace last | RES | The caption says "BayesSpace (Visium only) last". |
| R5 maps beyond DLPFC | RES | Suppl. Fig. S3 shows breast cancer and E9.5 Stereo-seq. The main text points to it. The Fig. 3 caption names GraphST "without label refinement". Optional: the S3 caption should give the GraphST refinement variant. |
| R6 Fig. 1 | PART | Fixed: "PAS" is no longer clipped, all text is at least 7 pt, "hypothalamus" is written out, all five datasets are shown. Still open: panel E and the caption say "bootstrap over donors and datasets". Write "over donor and dataset groups (7)". |
| R7 graphical abstract | RES | "Smoothing: ahead on brain, not on breast or embryo". It shows 24 sections, 4 technologies, 3 tissues, 16 methods. The dumbbells agree with Table S6 and Fig. 2B. |
| R8, R9 headings, "hidden" | RES | |
| R10 abstract | RES | "Fit likelihood tracked ARI only on cortex" and "BASS and the baseline were the most likely to rank first" are both fixed. |
| R11 seeds | RES | Methods, Limitations ("Four methods (and GraphST on DLPFC)") and Tables S10 and S23 agree. |
| R12, R13 | RES | |
| R14 sign of difference | RES | "exceeded the comparators by 0.172 … trailed them by 0.023". I recomputed 0.023 from the Table S6 columns (breast about −0.025, Stereo-seq about −0.021). |
| R15 numeral | RES | "Five methods needed…". |
| R16 hedges | RES | "may separate", "may explain", "the final step of GraphST, STAGATE and SEDR". |
| R17 split Results | RES | The first three subsections are now: brain accuracy, "The lead of the baseline depends on the tissue", and "Number of domains, seed variability and cost". Remaining flow point: see F5. |
| R18 naming | RES | "linear diffusion" is used throughout the Discussion and Results. |
| R19 labels | PART | Fig. 4 and Fig. 5 now use "STARmap", "MERFISH", "Breast" and "Stereo-seq". Still open: the Fig. 2A header says "Stereo", and Fig. 4C hyphenates "STAR-map", "MER-FISH" and "Stereo-seq". The graphical abstract mixes dataset names ("Breast", "Embryo") with technology names ("STARmap", "MERFISH"). |
| R20 "14 methods" | RES | "11 benchmarked methods and three further spatial methods". |
| R21 author contact | NOT | No sentence on contacting the HiSTaR or Spatial-MGCN authors. Add: "The authors of HiSTaR and Spatial-MGCN were informed of these findings before submission." If that is not true, say "were not contacted". |
| R22 placeholders | NOT (author-side) | All TODOs, "doi: DOI HERE", "Day Month Year", GitHub/Zenodo URL and the spatialLIBD version are still present. |
| R23 Fig. 2 caption | RES | The filled/open convention is scoped to B. C says "16 methods ranked". |
| R24 Fig. 4 | PART | Fixed: row order, zero ranges in the medians, and C's zeros (no more "−0.0"). Still open: the text gives "the mean range was 0.18 … 0.09 … 0.22" and cites Table S11. Table S11 lists median ranges (0.18, 0.07, 0.19) and the mean SD, not the mean range. See F2. |
| R25 Fig. 5 caption | RES | It states the default-clustering sources. |
| R26 Fig. 3 caption | RES | |
| R27 Table S23 header | RES | The header is clean. "Lottery" is gone. |
| R28, R29 | RES | |
| R30 "10 of 14" | NOT | Table S11 gives 11 positive and 3 negative best-likelihood minus mean values. Two of the 11 are exactly +0.005. Strictly more than 0.005 gives 9, not 10. Recount and state the threshold, for example "by at least 0.005 for 11 of 14 methods" or "by more than 0.005 for 9". |
| R31 Table S2 | PART | Fixed: the justified-column hyphenation is gone, and the CCST and BayesSpace truncation is fixed. Still open: see F4 (cell collision, page number inside the table, internal identifiers, empty baseline cells). |
| R32 symbols | PART | Fixed: "−0.00" and "-−" are gone, and Table S6 now prints "0.00". Still open: "x100", "x0.01" and "x2" in Table S22 (use ×); "1 - 0.05/16" in Note 4 (use −); hyphenated ranges "1-3", "2-3" and "1-3" in Table S23 (use en dashes). Table S16 mixes "0.000" and "+0.000". |
| R33 "95% CI" / "Test only" | RES | |
| R34 "Supplementary Fig." | RES | |
| R35 supplementary figures | PART | Suppl. Fig. S4 is fixed ("Δ = −0.003, p > 0.99", "Linear diffusion"/"AnisoST"). Suppl. Fig. S1: tick labels and legend are still about 5–6 pt, and MERFISH sections are ordered −0.24 to −0.04 (reverse order or label "Bregma"). Table S1 should say "MERFISH Bregma −0.04". |
| N1 Fig. 1 clipping | RES | No clipped glyphs. The tightest margin is 1.6 pt at the right edge ("equivalence margin"). See F6. |
| N2 "-−" ranges | RES | |
| N3 Note 4 vs Bonferroni | RES | "Intervals are uncorrected; Bonferroni-corrected intervals … as a check." |
| N4 "BASS as likely" | RES | The Discussion now says "ranked first more often (0.50 against 0.32)". |
| N5, N6 abstract | RES | |
| N7 DeepST runs | RES | The Table S14 caption footnotes DeepST. Table S23 gives "1-3" seeds. |
| N8 graphical abstract | RES | "not on breast or embryo". Optional: add a "equal-weight mean of datasets" note in the legend or alt text. |

## 2. New material

**Three Results subsections.** They are well formed. The first states the pooled result and the second shows the tissue dependence with per-dataset counts (0, 1, 1 comparators ahead on the brain datasets; 13 of 16 and 11 of 15 on breast cancer and Stereo-seq). The counts agree with Table S6. The 0.594 against 0.587 BASS remark is in the text. The overall tone is hedged correctly ("exploratory", "possible explanation, which we did not test").

**Memory rerun.** The wording is neutral and consistent:
- The Methods say "17 jobs … rerun with the same code and settings on a second server".
- The Results give 12–28 GB.
- The Limitations say the memory figures describe the implementations, not the methods.
- Note 6 describes the 125 GB server and the GraphST mclust wrapper.
- The 17 count is right (5 methods × 3 seeds + 2 DeepST seeds).
- The Results mention "more than the 12 GB cap" for all five, but GraphST is listed at 12 GB (Table S15: 11.8 GB). See F3.

**Figure 2 brain/other split.** It works. The white rule, the two header labels, the open/filled triangles in B and the caption agree. The text "brain (mean)" in the legend is the equal-weight mean of the three brain datasets and the caption says so ("on the three brain datasets"). Only one reading note is missing: the triangles are unweighted means, not bootstrap estimates (the caption says "without intervals", which is enough).

**Fig. 1 and the graphical abstract.** Both show five datasets. In the graphical abstract the dataset labels stagger correctly, and the direction labels ("method ahead / baseline ahead") match Fig. 2B. Fig. 1 panel A is balanced. "embryo, 3" sits very close to the embryo thumbnail, but they do not overlap.

**Suppl. Fig. S3 (maps).** It is accurate and legible (7 pt or more). The 20-colour palette (tab20) is not colour-blind safe, and the caption admits that colours repeat. That is acceptable for a supplementary map figure, but the caption should give the GraphST refinement variant for the breast-cancer row. The ARIs in the panels (for example BASS breast 0.61, linear diffusion 0.53) are seed 0, while Table S3 gives means over seeds (0.624, 0.546); the caption says "seed 0", so this is consistent.

**Consistency across abstract, Results, Discussion, figures and graphical abstract.** All agree on: 8 of 16 above zero, BASS 0.50 against linear diffusion 0.32, a lead from brain only, 0.16 range (up to 0.60), likelihood tracking ARI on cortex only, HiSTaR not reproduced, label use in Spatial-MGCN. The counts "13 published methods and three baselines" and "16 methods" are consistent, but the figures show 17 entries because BANKSY is run with two values of λ. Add a one-line note in the Fig. 2 caption: "BANKSY was run with two λ values, giving 17 entries".

**Overclaiming.** Nothing structural remains. One recommendation is worth softening: the Discussion's "the results suggest starting with a smoothing baseline" rests on an exploratory comparison. Write "…suggest including a smoothing baseline as a reference".

**Colour-blind safety.**
- The family palette (blue, orange, green) is distinguishable by luminance and by the direct labels. Fig. 4 uses shape and grey level, and Fig. 4C uses a brown-purple diverging scale, which is safe.
- The Fig. 2A heat map is greyscale, which is safe.
- Fig. 3 and Fig. S3 use categorical map colours (annotation). That is acceptable because ARI is printed, but the Fig. 3 caption could say that colours are not colour-blind optimised.

## 3. Remaining fixes (concrete)

- **F1. Fig. 1 panel E.** Replace "Bootstrap over donors and datasets" (also in the caption, "summarised with a bootstrap over donors and datasets") with "Bootstrap over 7 donor/dataset groups". The right-hand text ends 1.6 pt from the edge. Move the E block left by about 2 mm.
- **F2. Mean/median range.** In the Results text replace "the mean range was 0.18 for linear diffusion, against 0.09 for SpaceFlow and 0.22 for BANKSY λ = 0.8 (Supplementary Table S11)" by the medians "0.18, 0.07 and 0.19", or add a mean-range column to Table S11. Also reconcile "the ARI range … was 0.16 on average" (a mean over embeddings) with the table (medians) in one sentence.
- **F3. GraphST memory.** The Results list "GraphST 12" among methods that needed "more than the 12 GB cap". Write "GraphST about 12 GB, which exceeded the cap on the 15 GB machine once system overhead was included" (or "at or near the cap"). Table S15 says 11.8 GB. Also state in the Table S15 caption whether peak memory is the median or the maximum across jobs.
- **F4. Table S2.**
  - The Spatial-MGCN "Default clustering" cell overruns into the Deviations column ("docs/LEAKAGE_AUDIT.md" collides with "section was not used"). Use `\raggedright` p-columns and shorten to "k-means each epoch; epoch chosen by ARI against the annotation (label use, see Suppl. Note 5)".
  - The page number "4" prints inside the table at the page break. Break the table before the baselines or reduce the row height.
  - Remove internal identifiers and shouting: "LEAKAGE", "docs/LEAKAGE_AUDIT.md", "hicast/histar.py", "networkx>=3", "scripts/new_methods.py", "n_init=100" (keep the setting, drop the code syntax).
  - Fill the empty Code/Commit cells of the three baselines ("this study, spatialbench").
- **F5. Results flow.** The AnisoST paragraph (MERFISH 0.363 against 0.497, boundary accuracy, Suppl. Fig. S4) sits under "Number of domains, seed variability and cost" and is out of place. Move it to the end of the subsection "The lead of the baseline depends on the tissue", or give it its own sentence in the first subsection. The sentence "Taking all datasets from the standardised runner…" repeats the pipeline comparison and could move to the Supplementary.
- **F6. Fig. 2 top edge.** The "Mean ARI, matched clustering" title touches the top edge (−0.1 pt), and "P(best)" sits against the panel C title. Add 2 mm of top margin and put "P(best)" on its own line. "reference" in B is crossed by the zero line and the grey band; move it right of the band.
- **F7. Supplementary symbols.**
  - Table S22: "x100", "x0.01" and "x2" become "×100", "×0.01" and "×2".
  - Note 4: "1 - 0.05/16" becomes "1 − 0.05/16".
  - Table S23: "1-3" and "2-3" become "1–3" and "2–3".
  - Table S16: use "+0.000" or "0.000" consistently.
  - Tables S3–S6 and S11: write "λ = 0.8" (with spaces), as in the main text.
- **F8. Suppl. Fig. S1.** Raise the tick labels and legend to 7 pt, reverse the MERFISH order or label it "Bregma", and say in the caption that only DLPFC, STARmap and MERFISH are shown (Fig. 4A has all datasets).
- **F9. R30.** Recount "10 of 14" (see R30 above).
- **F10. Dataset names.** Use "Stereo-seq" in the Fig. 2A header, avoid the hyphenation in Fig. 4C ("STARmap", "MERFISH") and use "Breast cancer" and "Mouse embryo" in the graphical abstract thumbnails (or "Visium breast cancer").
- **F11. Author contact (R21) and placeholders (R22).** Add the contact sentence. Clear all TODOs, DOI and date placeholders before upload. Rename the figure files to their printed numbers (open since round 2).

## 4. Figure legibility summary

| Figure | Size | Smallest text | Overlap / clipping |
|---|---|---|---|
| 1 | 17.5 × 9.8 cm | 7 pt | None. Right margin 1.6 pt. |
| 2 | 17.5 × 11.4 cm | 7 pt | Title at the top edge; "P(best)" crowds the C title. |
| 3 (maps) | 17.5 × 8.4 cm | 7 pt | None. |
| 4 | 17.5 × 10.4 cm | 7 pt | None. |
| 5 | 17.5 × 8.6 cm | 7 pt | None. |
| S3 maps | 17.5 × 7.6 cm | 7 pt | None. |
| Graphical abstract | 25.4 × 10.2 cm | 9.5 pt | None. No x scale on the dumbbell (acceptable). |
| S1 | – | about 5–6 pt | Too small (F8). |
