# NAR submission requirements audit, round 3 (final version)

**Manuscript:** *Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods* (NAR, Computational Biology)
**Checked:** `paper/main.tex` (440 lines) with `results/paper_macros.tex` and `paper/supp_labels.tex`; `paper/main.pdf` (9 pp., built 2026-10-24 02:09); `paper/supplementary.pdf` (18 pp.); `paper/refs.bib` and `main.bbl` (32 references); `paper/cover_letter.md`; `paper/figure_alt_text.md`; `scripts/make_submission.sh` and `paper/submission/`; `docs/figures/nar_fig*.png/pdf` and `nar_graphical_abstract.{png,pdf,tif}` (all dated 2026-10-24 02:08).
**Previous round:** `docs/nar_review/round2/01_journal_requirements.md`.
**Audit date:** 2026-10-24. Only this report was written.

## Verdict

**Ready to submit once three small consistency fixes and the author placeholders are done.**
- All five data-integration problems from round 2 are fixed: the graphical abstract, Fig. 1A, the corrupted coverage table, the stale run-count caption and the Fig. 5 caption.
- The development-set definition, the Fig. 4 legend and the figure upload names are fixed too.
- What remains is small:
  - one stale number (0.17 instead of 0.16) in the cover letter and in the alt text;
  - stale Fig. 1 alt text;
  - one stale column in Supplementary Table S22;
  - a generic 10x URL.

**Tally of round-2 required fixes:** 7 resolved, 3 partly resolved, 0 not resolved.

## Rendered abstract word count

I extracted the abstract with `pdftotext paper/main.pdf` (text between "Abstract" and "Key words") and counted with `wc -w`. Result: **198 words, so it passes the 200-word limit**. pdftotext joins the line-broken "neighbourhood-smoothing" into one token, which matches the source, where it is one hyphenated word.

The headroom fell from 5 words to 2. Any further edit must be offset by a cut; round-2 suggestion 1 ("With matched clustering") would save 5 words. The abstract has no URL, citation or figure reference.

## Status of round-2 required fixes

| # | Round-2 problem | Status | Evidence |
|---|---|---|---|
| R1 | Graphical abstract out of date | **Resolved** | `nar_graphical_abstract.png` (6000×2400 px, 600 dpi, 254×101.6 mm, 5:2; TIFF and PDF too) now reads "24 sections / 4 technologies, 3 tissues / 16 methods" and shows DLPFC, STARmap, MERFISH, breast cancer and embryo thumbnails. The headline is "Smoothing baseline: ahead on brain, not elsewhere", with a brain vs breast-and-embryo dumbbell plot, consistent with main.tex l. 226–236. Minor remaining risk: the HiSTaR 151669 worst/best maps (ARI 0.23/0.67) still duplicate Fig. 1D (see N6). |
| R2 | Fig. 1A shows only three datasets | **Resolved** | Panel A of `nar_fig1_pipeline_v2.png` adds "10x Visium breast cancer, 1" and "Stereo-seq mouse embryo, 3". The caption at main.tex l. 86–88 names both. Cosmetic: the embryo thumbnail touches the bottom edge of the figure (non-white pixels on the last pixel row); add about 1 mm of margin. |
| R3 | Supplementary coverage table corrupted ("2not run") | **Partly resolved** | Now Table S22 (supplementary.pdf p. 15). "2not run" is gone: the cells read "20/24 / 3" and "not run" is used only for 0/n, via a regex in `scripts/make_supplement.py` l. 267. **Still wrong:** (a) the header still reads "Lottery (20 starts)" because `.replace("lottery", …)` at l. 268 runs after the first letter is capitalised; use `.replace("Lottery", "Initialisation experiment")`, or rename the column in `results/coverage_matrix.csv`. (b) **New inconsistency:** the column "R mclust perturbation" reads 20/24 for every method, but `results/mclust_seed_summary.csv` has noise repetitions (`jrng`) for 23 sections for most methods and for all 24 for AnisoST and BANKSY λ=0.2/0.8. Main text l. 306 and the S11 caption say the noise repetitions were "not run on the 18,408-bin Stereo-seq section". `coverage_matrix.csv` is stale; regenerate it, then reconcile the three AnisoST/BANKSY E10.5 E1S1 runs with the wording at l. 306 (say "not run for most methods", or drop those runs). |
| R4 | Stale caption run counts (old S12) | **Resolved** | The runs column now sits in Table S13 (p. 10), with the caption "Runs: … up to 72 = 24 sections × 3 seeds". The values are 69/72 and match the table. The old "60 per method" text is gone. |
| R5 | Fig. 5 (protocol) caption inaccurate | **Resolved** | main.tex l. 327–329: "Rows are ordered by the matched-clustering mean over the five datasets" (one global order, matching the figure), and "Stereo-seq values of methods stopped at the memory cap are means over the two smaller sections". The figure itself has no "*" marker, unlike Fig. 2A; the caption note is sufficient. Optional: add "*" to the panel E labels for parity with Fig. 2. |
| R6 | Alt text missing | **Partly resolved** | `paper/figure_alt_text.md` now gives alt text for the graphical abstract and Figs 1–5, and `make_submission.sh` copies it into `paper/submission/`. **Stale content:** (a) **Figure 1** reads "example tissue sections from 10x Visium, STARmap and MERFISH". It must add breast cancer (Visium) and Stereo-seq mouse embryo. (b) **Figure 4** reads "mean about 0.17"; the value is now 0.16 (`\lotMean`; abstract l. 42). The other entries match: Fig. 2 "eight of which lie above zero" = `\nRobBetter` 8; Fig. 4 "14 methods" = `\lotNMethods`; Fig. 3 "nine methods". Placement: OUP asks for alt text in the submission system or under each legend. Pasting it from this file is acceptable; confirm on the live page that ScholarOne has the field (unverified, as in round 2). |
| R7 | Data Availability lacks URLs and accessions | **Partly resolved** | main.tex l. 410–418 now gives spatialLIBD (http://spatial.libd.org/spatialLIBD), SEDR_analyses (GitHub), BASS-Analysis (GitHub), MOSTA STDS0000058 (https://db.cngb.org/stomics/mosta/), and a pointer to `configs/datasets.yaml` and `data/CHECKSUMS.sha256` (both exist) for file URLs, commits and checksums. **Remaining:** (a) the breast cancer link and `refs.bib` `tenx2020brca` `howpublished` (l. 277) are still the generic `https://www.10xgenomics.com/datasets`; use `https://www.10xgenomics.com/datasets/human-breast-cancer-block-a-section-1-1-standard-1-1-0` and state CC BY 4.0. (b) Repository commits are given only in `configs/datasets.yaml`, which readers can reach only once the GitHub/Zenodo placeholder is filled. That is acceptable but depends on the author-side placeholder. Optional: the original MERFISH Dryad deposit doi:10.5061/dryad.8t8s248. |
| R8 | Inconsistent development-set definition | **Resolved** | l. 154–155 ("fixed on DLPFC donor 1 before any other data were analysed"), l. 166–168 ("frozen on the four sections of DLPFC donor 1 … without the six development sections (those four and the first STARmap and MERFISH sections, used to test the pipelines)") and l. 194–195 now agree. The "Test only" wording in Supplementary Table S5 matches. |
| R9 | Fig. 4 legend attached to the wrong panel | **Resolved** | main.tex l. 293: "In A and B, bars: interquartile range; open circle: median." The figure legend reads "median and IQR". |
| R10 | Figure file names do not match the figure numbers | **Resolved** | `scripts/make_submission.sh` copies `nar_fig1_pipeline_v2` → Figure1, `fig2_accuracy` → 2, `fig5_maps` → 3, `fig3_robustness` → 4 and `fig4_protocol` → 5, matching the `\includegraphics` order (l. 85, 255, 270, 288, 325). `paper/submission/` contains Figure1–5.pdf, the graphical abstract PDF and TIFF, `manuscript.pdf`, `supplementary_data.pdf`, the alt text and the cover letter. |

### Round-2 optional suggestions (for information)

| # | Suggestion | Status |
|---|---|---|
| 1 | Abstract headroom | Not done; headroom is now 2 words. |
| 2 | AI-use pointer in Methods | Not done. AI use is disclosed in the Acknowledgements (l. 424–426) and the cover letter. |
| 3 | Ethics line for de-identified public human data | Not done. Recommended, given the human tumour section. |
| 4 | Software versions in the main text | Not done; only mclust 6.0.1 is named. |
| 5 | Family terminology | Not done. l. 130–131 still lists "… and Bayesian models" as a third family, while Fig. 1C, Fig. 2 and l. 135–155 use deep / statistical and neighbourhood / training-free. |
| 6 | Hard-coded "Figures 1, 2 and 5" (l. 92) | Still hard-coded; correct as built. |
| 7 | Type 3 fonts | Not done. `main.pdf` still has two Type 3 fonts (F156, F158); `supplementary.pdf` has none. |
| 8 | NAR reference style | Not done (unsrtnat). Acceptable at first submission. |
| 9 | `paper/SUBMISSION_CHECKLIST.md` | Unchanged since Oct 12: still says *Bioinformatics Advances* and 20 sections. Not submitted, but stale. |
| 10 | Template option | Unchanged (`contemporary,large`). |

## New problems introduced by the revision

| # | Problem | Location | Fix | Severity |
|---|---|---|---|---|
| N1 | **The cover letter quotes the old initialisation range.** It says "changes ARI by 0.17 on average", but the manuscript now says 0.16 (`\lotMean`; abstract, l. 42; Discussion, l. 360). | `paper/cover_letter.md`, finding 2 | Change to 0.16. The other cover-letter numbers match the macros: 13 methods, 24 sections, 0.60, 0.65 vs 0.51, and 0.15 (= 0.147). | **Required** |
| N2 | **The alt text is stale for Fig. 1 and Fig. 4.** | `paper/figure_alt_text.md` | See R6. | **Required** |
| N3 | **Table S22 "R mclust perturbation" says 20/24 for every method, which contradicts the data.** The data have 23 sections, or 24 for AnisoST and BANKSY. This also conflicts with main.tex l. 306 and the S11 caption ("not run on the 18,408-bin section"). | `results/coverage_matrix.csv` → `results/supp/coverage.tex`; main.tex l. 306 | See R3(b). | **Required** (internal consistency) |
| N4 | **The 10x breast cancer URL is still generic.** | main.tex l. 414; `refs.bib` l. 277 | See R7. | Recommended |
| N5 | **Table S22 header still reads "Lottery".** This is the only remaining use of the old term. | `make_supplement.py` l. 268 | See R3(a). | Minor |
| N6 | **The graphical abstract reuses the Fig. 1D content.** Both show HiSTaR 151669 at ARI 0.23 and 0.67. NAR asks that the graphical abstract not simply repeat a figure. | `nar_graphical_abstract.*` | Optional: use a different section or method for the "different random start" panel. | Minor |
| N7 | **The embryo thumbnail is clipped at the bottom edge of Fig. 1.** | `nar_fig1_pipeline_v2.*` panel A | Add a small bottom margin. | Cosmetic |
| N8 | **Small layout issues.** `main.log` shows a new 7.9 pt overfull hbox in the Spatial-MGCN paragraph (l. 343–352), probably from `\texttt{DLPFC\_test.py}`. The 253 pt template-header overfull box remains. | `main.log` l. 1118 | Cosmetic; allow a line break or ignore. | Cosmetic |
| N9 | **The cover letter is signed with a real name and affiliation** (Bikash Kumar Paul, Virginia Tech), while the manuscript author block is still `[TODO]`. | `cover_letter.md`; main.tex l. 25–29 | Fill the manuscript author block consistently (author-side). | Author-side |

**No problems found in these areas:**
- **Abstract:** 198 words.
- **References:** 32 entries, numeric in order of appearance, no `??` in the PDF, no BibTeX warnings. `chen2022mosta` and `tenx2020brca` details are correct.
- **End-matter order:** Data availability → Supplementary data → Acknowledgements → Author contributions → Funding → Conflict of interest → References.
- **Figure specifications:** all five main figures are 175 mm wide at 600 dpi, as PNG and as vector PDF with embedded fonts. The graphical abstract is 254×101.6 mm (5:2) at 600 dpi in TIFF and PDF.
- **Length:** 9 pages and 5 figures.
- **Figure numbers:** Fig. 2B has 8 filled and 8 open symbols, matching `\nRobBetter` = `\nRobUnres` = 8 of 16.

## Author-side placeholders (expected; listed once)

- **Author block:** names, `\authormark`, department, university, country and corresponding e-mail (main.tex l. 25–29); ORCIDs in ScholarOne.
- **Acknowledgements:** confirm the AI wording and add thanks (l. 425).
- **CRediT statement** (l. 429).
- **Funding**, including the open-access charge line (l. 432).
- **GitHub URL and Zenodo DOI:** main.tex l. 418; the cover letter's "[GitHub URL]" and "[DOI]"; cite the Zenodo record in the reference list.
- **Preprint statement** in the cover letter.
- **Suggested reviewers** (`paper/suggested_reviewers.md`): confirm e-mails and conflicts.
- **OUP template fields** (`\DOI{DOI HERE}`, the received/revised/accepted dates and the Advance Access date) are filled by OUP.
