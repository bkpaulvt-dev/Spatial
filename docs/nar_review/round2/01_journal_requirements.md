# NAR submission requirements audit, round 2

**Manuscript:** *Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods* (NAR, Computational Biology)

**Files checked:**
- `paper/main.tex`, with macros from `results/paper_macros.tex` and `paper/supp_labels.tex`
- `paper/supplementary.tex` and `results/supp/*.tex`
- `paper/refs.bib`, `paper/cover_letter.md`, `paper/suggested_reviewers.md`
- the built `paper/main.pdf` (9 pp., built 2026-10-23 13:59) and `paper/supplementary.pdf` (16 pp.)
- `docs/figures/nar_fig*.pdf/png` and `docs/figures/nar_graphical_abstract.{pdf,png,tif}`

**Previous round:** `docs/nar_review/01_journal_requirements.md` (2026-10-18).

**Audit date:** 2026-10-23. Only this report was written; no other file was modified.

**Source caveat (unchanged from round 1):** `academic.oup.com` still returns HTTP 403 to curl and fails DNS in WebFetch. The NAR rules were therefore checked through web-search extracts of the official pages ([author guidelines](https://academic.oup.com/nar/pages/author-guidelines), [data deposition](https://academic.oup.com/nar/pages/data_deposition_and_standardization), [Database-issue preparation](https://academic.oup.com/nar/pages/Ms_Prep_Database)) and through the Manusights guides ([formatting](https://manusights.com/blog/nucleic-acids-research-formatting-requirements), [submission](https://manusights.com/blog/nucleic-acids-research-submission-guide)). Search extracts confirm four rules:
- a mandatory Data Availability statement; "available on request" is not sufficient;
- code and data must be released as a condition of publication;
- software and data should be cited in the reference list, and a Figshare or similar DOI belongs in the Data Availability statement;
- the abstract is unstructured and at most 200 words.

Three rules could not be re-confirmed from an official page in this round: the alt-text requirement, the 5:2 graphical-abstract specification for the general track, and the exact place where AI use must be disclosed. Check those three in a browser on the live author-guidelines page.

## Verdict

**Close, but not yet ready to submit.** Most format problems from round 1 are fixed:
- article type
- abstract length (now 195 words)
- the URL in the abstract
- end-matter order
- numeric references, with all `VERIFY` flags cleared
- figure widths and fonts
- a graphical abstract now exists
- AI disclosure
- the cover letter, rewritten for NAR
- a reviewer list
- a lock file

Adding the Visium breast cancer and Stereo-seq datasets left several items stale or broken:
- the **graphical abstract** still says 20 sections, 3 technologies and "among the best";
- **Figure 1A** and its caption show only three datasets;
- **Supplementary Table S20** is corrupted ("2not run");
- the **Supplementary Table S12** caption gives the old run counts;
- two figure captions are now inaccurate.

**Alt text** is still missing, and the Data Availability statement still has no URLs or accessions for three of the five datasets.

None of these is hard to fix. The remaining blockers sit with the authors: names, funding, CRediT, and the GitHub URL and Zenodo DOI.

## Abstract word count (rendered text)

The abstract was extracted from `main.pdf` with `pdftotext` and split on whitespace. Hyphenated compounds count as one word. Result: **195 words, so it passes the 200-word limit**, but with only 5 words to spare. Any future edit, such as a new number or a definition, must be offset by a cut. The abstract contains no URL, citation or figure reference. It uses "ARI" (defined) and "R mclust", which is acceptable as a software name.

## Required fixes (prioritised)

| # | Problem | Exact location | Suggested fix |
|---|---|---|---|
| R1 | **The graphical abstract is out of date and partly contradicts the paper.** It reads "20 sections / 3 technologies / 16 methods" and shows only Visium, STARmap and MERFISH. Its headline, "Training-free smoothing is among the best", conflicts with the new tissue-dependent conclusion. Its interval panel shows GraphST as filled (interval above zero), but GraphST is now **unresolved**: an open symbol in Fig. 2B. | `docs/figures/nar_graphical_abstract.{pdf,png,tif}` (dated Oct 19, before the new data) | Regenerate it from the current results. Use 24 sections, 4 technologies, and Visium, STARmap, MERFISH and Stereo-seq thumbnails (plus breast cancer). Make the headline tissue-specific, e.g. "Smoothing baseline leads on brain; methods converge on tumour and embryo". Take the intervals from the current `stats_rob` results. Keep 254×101.6 mm (5:2) at 600 dpi as TIFF plus PDF; the current size and dpi already comply. Optionally replace the HiSTaR 151669 worst/best maps, which duplicate Fig. 1D: NAR asks that the graphical abstract not reuse a figure, and partial reuse is a minor risk. |
| R2 | **Figure 1A and its caption cover only three datasets.** Panel A shows DLPFC, STARmap and MERFISH. The caption says "Examples of the data: human DLPFC … and mouse sections profiled by STARmap … and MERFISH …". Breast cancer (Visium) and Stereo-seq are missing from the study-design figure, while the abstract, Methods and Figs 2–5 include them. | `docs/figures/nar_fig1_pipeline_v2.*` panel A; `main.tex` l. 85–86 | Add a breast cancer Visium thumbnail ("human breast cancer, 1 section") and a Stereo-seq MOSTA thumbnail ("mouse embryo E9.5/E10.5, 3 sections, bin50") to panel A. Update the caption, e.g. "…MERFISH (hypothalamus, Bregma −0.14), human breast cancer (10x Visium) and mouse embryo (Stereo-seq, E9.5 E1S1)…". Panel B's "PCA with 200 or 50 PCs" text is still correct. |
| R3 | **Supplementary Table S20 is corrupted.** The "ARI, paper pipeline" and "R mclust perturbation" columns print **"2not run"** for every method. The cause is a substring replacement: `str(x).replace("0/24","not run")` turns "20/24" into "2not run". The same code fails to rename the "Lottery" column header, because the column is capitalised before `.replace("lottery", …)` runs. | `scripts/make_supplement.py` l. 242–243 → `results/supp/coverage.tex` → supplementary.pdf p. 13 | Replace a cell only when it equals the string exactly, e.g. `"not run" if str(x) in ("0/24","0/13") else str(x)`. Apply the header rename case-insensitively, so the header reads "Initialisation experiment (20 starts)" as in the main text. Then regenerate the supplement. Also check the remaining coverage cells: R mclust seeds is 23/24 for most methods; state which section is missing, or footnote it. |
| R4 | **The Supplementary Table S12 caption is stale.** It says "Runs: 60 per method (20 sections, 3 seeds), except DeepST (20, seed 0) and BayesSpace (12 Visium sections, seed 0)". The table itself shows 72 runs (24×3), 69 or 71 for OOM methods, 23 for DeepST and 13 for BayesSpace. | `scripts/make_supplement.py` (S12 caption string); supplementary.pdf p. 9 | Generate the run counts from the data, e.g. "Runs: up to 72 per method (24 sections × 3 seeds; fewer where a run exceeded the memory cap), DeepST 23 (seed 0), BayesSpace 13 Visium sections (seed 0)". |
| R5 | **The Figure 5 (protocol) caption is inaccurate.** (a) It says Stereo-seq values are "means over … 3 sections", but BASS, DeepST, GraphST, NichePCA and Spatial-MGCN have no result on E10.5 E1S1. Fig. 2 marks these with "*", while Fig. 5 has no marker. (b) "Rows are ordered by the matched mean" is not true per panel: one global order is used, e.g. SEDR (0.55) sits near the bottom of the DLPFC panel. | `main.tex` l. 311–313; `docs/figures/nar_fig4_protocol.*` | Add the same "*" marker and caption note as in Fig. 2 ("*: two smaller Stereo-seq sections; memory cap exceeded on the largest"). Write "Rows are ordered by the mean over datasets with matched clustering (same order in every panel)". |
| R6 | **Alt text is still missing** for all 5 figures (round-1 point #13). OUP and NAR ask for an "Alt text:" line under each legend (secondary source; verify on the live page). | after each `\caption{…}` in `main.tex` (l. 85, 240, 255, 273, 311) | Add one or two plain sentences per figure. For example, Fig. 2: "Alt text: Heat map of mean ARI for 17 methods on five datasets, a forest plot of differences from linear diffusion with bootstrap intervals, and a plot of bootstrap ranks." |
| R7 | **The Data Availability statement has no URLs or accessions for three datasets** (round-1 point #14, partly fixed). MOSTA now has STDS0000058; I verified this is the [MOSTA dataset on CNGB STOmicsDB](https://db.cngb.org/stomics/datasets/STDS0000058/), and the raw reads are CNGB CNP0001543. "spatialLIBD", "SEDR analyses repository" and "BASS-Analysis repository" have no link or commit. The 10x dataset has only a generic URL. NAR requires the data to be accessible without request. | `main.tex` l. 388–394; `refs.bib` `tenx2020brca` | Add the links, checking each one: spatialLIBD (http://spatial.libd.org/spatialLIBD; Bioconductor `spatialLIBD`); SEDR_analyses (https://github.com/JinmiaoChenLab/SEDR_analyses, commit …); BASS-Analysis (https://github.com/zhengli09/BASS-Analysis, commit …); original MERFISH deposit (Dryad doi:10.5061/dryad.8t8s248); 10x breast cancer: https://www.10xgenomics.com/datasets/human-breast-cancer-block-a-section-1-1-standard-1-1-0 (CC BY 4.0). Put the dataset-specific URL in `tenx2020brca` `howpublished`. Optionally add the STOmicsDB mirror STDS0000027 as a second source. |
| R8 | **The development set is described inconsistently.** The Neutrality paragraph says settings were "frozen on **four** development sections", and l. 152 says "fixed on DLPFC donor 1" (4 sections). But l. 187–188 and l. 204 exclude "DLPFC donor 1 **and the first section of STARmap and MERFISH**" (6 sections) as "the development sections". | `main.tex` l. 152, 160, 187–188 | State one definition. For example: "Baseline settings were fixed on DLPFC donor 1 (four sections); for the test-only analysis we also exclude the first STARmap and MERFISH sections, which were inspected during development (six sections in total)." Use the same wording in Supplementary Table S5/S6 captions ("Test only"). |
| R9 | **The Figure 4 (robustness) caption attaches a legend to the wrong panel.** "Bars: interquartile range; open circle: median" comes after (C), which is a heat map. The bars and circles are in A and B. | `main.tex` l. 278–279 | Move the sentence before (C), or write "(A, B) Bars: interquartile range; open circle: median." |
| R10 | **Figure file names do not match the figure numbers** for upload. Figure 3 is `nar_fig5_maps`, Figure 4 is `nar_fig3_robustness` and Figure 5 is `nar_fig4_protocol`. Two Fig. 1 versions exist (`nar_fig1_pipeline` and `_v2`). | `docs/figures/` | When uploading the high-resolution files to ScholarOne, name them `Figure1.pdf` to `Figure5.pdf` in their printed order and upload only `_v2` for Fig. 1. This avoids a figure being swapped during production. |

## Author-side items (not reviewer blockers; listed once)

These are placeholders only the authors can fill:
- Author names, `\authormark`, department, university, town, postcode, country, corresponding e-mail (`main.tex` l. 25–29), and ORCID in ScholarOne.
- Acknowledgements: confirm the AI wording and add thanks (l. 401). Consider naming the model or version.
- CRediT statement (l. 405).
- Funding, including the "Funding for open access charge:" line (l. 408).
- GitHub URL and Zenodo DOI (l. 394; cover letter; supplement paths such as `scripts/…` and `docs/LEAKAGE_AUDIT.md`). Also cite the Zenodo record in the reference list, which NAR recommends for software and data.
- Cover-letter placeholders "[GitHub URL]", "[DOI]" and "[A preprint is / is not posted…]".
- Suggested reviewers (`paper/suggested_reviewers.md`): confirm affiliations and institutional e-mails for all six (L. M. Weber has no affiliation listed) and check conflicts. Six names meet the stated minimum.
- Template placeholders (`\DOI{DOI HERE}`, received/revised/accepted, Advance Access date) are filled by OUP and can stay.
- Optional author decisions: whether to contact the HiSTaR and Spatial-MGCN authors before submission (the TODOs were removed and the text now hedges appropriately), and confirming HiSTaR's published values (0.65 median; 0.718 on 151673) against Yu et al. 2025.

## Optional suggestions

1. **Abstract headroom.** At 195 words, consider trimming "With the same clustering for every embedding" to "With matched clustering" to gain room.
2. **AI disclosure location.** One secondary source says OUP/NAR expects AI use to be disclosed in the Methods. It is currently in the Acknowledgements and the cover letter. Add one sentence at the end of Materials and Methods ("AI assistance: see Acknowledgements") to cover both readings.
3. **Ethics line.** Now that a human tumour section is used, add to Data availability: "Only publicly available, de-identified human data (spatialLIBD; 10x Genomics demonstration data, CC BY 4.0) were used; no ethics approval was required."
4. **Software versions in the main text.** `environment/requirements-lock.txt` and `R-sessionInfo.txt` now exist, which resolves round-1 #15 for reproducibility. The Methods still name only mclust 6.0.1. Add "Python 3.13 (scanpy X, scikit-learn X, PyTorch X) and R 4.3.3; full lock file in the archive". The root `requirements.txt` is still unpinned; point to the lock file in the README.
5. **Family terminology.** Methods l. 128–129 names three families as "deep graph encoders, statistical and neighbourhood methods, and Bayesian models". Fig. 1C, the legends and l. 133–146 use "deep graph encoders / statistical and neighbourhood methods (incl. BASS, BayesSpace) / training-free baselines". Align l. 128–129 with the figures.
6. **Hard-coded figure numbers.** The Fig. 1 caption hard-codes "Figures 1, 2 and 5". It is correct now, but use `\ref{fig:accuracy}` and `\ref{fig:matched}` so it survives reordering.
7. **Type 3 fonts.** Two remain (TC `tcrm` bitmap fonts, from © on p. 1 and `\textmu` on p. 2). Add `\usepackage{lmodern}` or `\usepackage{textcomp}` with cm-super, or build on Overleaf. A 253 pt overfull hbox during output, from the template header, is cosmetic.
8. **Reference style.** Numeric order of appearance is now correct (unsrtnat), but entries use full first names and unabbreviated journal titles. The OUP/NAR Overleaf `.bst` produces NAR style ("Zhao,E., Stone,M.R. … (2021) … Nat. Biotechnol., 39, 1375–1384."). This is acceptable at first submission; switch at revision. Unify the author truncation: `chen2022mosta` lists six authors and others list three before "et al.". `holm1979` is in `refs.bib` but no longer cited, which is harmless.
9. **Internal checklist.** `paper/SUBMISSION_CHECKLIST.md` is still headed "*Bioinformatics Advances*", claims "Three datasets … 20 sections" and "Holm-corrected statistics", and lists finished items. It is not submitted, but update it so it does not mislead.
10. **Template option.** `contemporary,large` is still used. Use whichever option the OUP NAR Overleaf template ships ("Modern Large" per the secondary source). This does not matter for the first-submission PDF.

## New datasets: integration check

| Place | Breast cancer (Visium) | Stereo-seq (MOSTA) |
|---|---|---|
| Abstract | ✓ ("brain, breast cancer and mouse embryo"; "10x Visium, STARmap, MERFISH and Stereo-seq"; 24 sections) | ✓ |
| Introduction | ✓ (four technologies, three tissue types) | ✓ |
| Methods: Data and preprocessing | ✓ (3798 spots, 20 regions, SEDR annotation) | ✓ (three sections, bin50, spot counts; added after the first analysis) |
| Methods: seeds, runner, memory cap | ✓ | ✓ (CCST 2 seeds on E10.5 E1S1) |
| Statistics (7 groups) | ✓ | ✓ |
| Results and Discussion | ✓ | ✓ |
| Limitations (annotation provenance) | ✓ | ✓ |
| Fig. 1 (design) | **✗ (R2)** | **✗ (R2)** |
| Fig. 2, Fig. 4, Fig. 5 | ✓; Fig. 5 is missing the OOM marker (R5) | ✓ / R5 |
| Fig. 3 (maps, DLPFC only) | n/a | n/a |
| Graphical abstract | **✗ (R1)** | **✗ (R1)** |
| Data availability | ✓ named; URL generic (R7) | ✓ STDS0000058 (verified) |
| Supplement Note 1, Tables S1/S3/S5–S7 | ✓ | ✓ |
| Supp. Table S12 caption / S20 | **✗ (R4, R3)** | **✗ (R4, R3)** |
| Cover letter | ✓ (24 sections, four technologies, numbers match the macros) | ✓ |

**References, checked by web search:**
- **`chen2022mosta`: correct.** Chen A, Liao S, Cheng M, Ma K, Wu L, Lai Y, …; *Cell* 185(10):1777–1792.e21, 2022; doi:10.1016/j.cell.2022.04.003 ([UPF repository record](https://repositori.upf.edu/items/ae98265f-3314-4c5e-8332-63b3129ac637/full); [CNGB project](https://db.cngb.org/stomics/project/STT0000013)).
- **`tenx2020brca`: details correct.** "Human Breast Cancer (Block A Section 1)", Space Ranger 1.1.0, 3798 spots under tissue, CC BY 4.0 ([10x dataset page](https://10xgenomics.com/datasets/human-breast-cancer-block-a-section-1-1-standard-1-1-0)). The `howpublished` URL is only the generic dataset index; use the dataset-specific URL (R7). The Space Ranger 1.0.0 version of the same section has 3813 spots, so the 3798 in the text confirms that 1.1.0 was used.

## Status of round-1 points

| R1 # | Point | Status |
|---|---|---|
| 1 | Article type | **Resolved.** `\appnotes{Computational Biology}`, `\journaltitle{Nucleic Acids Research}`; the cover letter frames it as a Computational Biology article. |
| 2 | Abstract ≤200 words | **Resolved** (195; little headroom). |
| 3 | URL/TODO in abstract | **Resolved.** |
| 4 | Non-standard abbreviations | **Resolved.** DLPFC and λ=0.8 removed from the abstract. |
| 5 | Graphical abstract | **Created** at the correct size, but the **content is outdated** (new R1). |
| 6 | Title | Pass. |
| 7 | Authors and affiliations | Author-side. |
| 8 | Keywords | Pass. |
| 9 | End-matter order | **Resolved.** Data availability → Supplementary data → Acknowledgements → Author contributions → Funding → Conflict of interest → References. |
| 10 | Length | Pass (9 pp., 5 figures). |
| 11 | Figure resolution | Pass (600 dpi PNG/TIFF, vector PDF). |
| 12 | Figure width and fonts | **Resolved.** All main figures are 175 mm wide; the smallest text is about 6.5 pt (Fig. 1) and about 7 pt elsewhere. |
| 13 | Alt text | **Open** (R6). |
| 14 | Data availability | **Partly resolved.** Datasets are named and MOSTA has an accession; URLs and commits are still missing (R7); code DOI is author-side. |
| 15 | Software versions | **Mostly resolved.** HiSTaR commit recorded (0039a3b); lock file and R sessionInfo in `environment/`. Main-text versions are optional (suggestion 4). |
| 16 | Supplementary data | Pass. Supp. Note 5 no longer says "not yet contacted"; the new table bugs are R3 and R4. |
| 17 | References | **Resolved** (numeric order of appearance; 0 `VERIFY` flags). NAR house style is optional (suggestion 8). |
| 18 | AI disclosure | **Resolved** in the Acknowledgements and cover letter; wording to confirm is author-side; a Methods pointer is optional. |
| 19 | Funding | Author-side. |
| 20 | Conflict of interest | **Resolved.** Heading and AnisoST declaration present. |
| 21 | CRediT | Author-side. |
| 22 | TODOs | **Reduced** to author-side placeholders only. The HiSTaR and Spatial-MGCN TODOs were removed and the text hedges. |
| 23 | Cover letter | **Resolved.** Addressed to NAR with the current title and numbers (0.17/0.60, 0.51 vs 0.65, 0.15); placeholders are author-side. |
| 24 | Suggested reviewers | **Drafted** (6 candidates); e-mails and conflicts are author-side. |
| 25 | Preprint | Author decision (placeholder in the cover letter). |
| 26 | Template and fonts | **Open, minor.** Two Type 3 fonts remain (suggestion 7). |
| 27 | Ethics line | **Open, optional.** Now more relevant with human tumour tissue (suggestion 3). |
| 28 | Editable tables | Pass. |
