# NAR submission requirements audit, round 4 (final compliance check)

**Checked:** `paper/main.tex` (460 lines, 2 Nov 23:21), `paper/main.pdf` (10 pp., 2 Nov 23:25), `paper/supplementary.pdf` (20 pp.), `results/paper_macros.tex`, `paper/supp_labels.tex`, `paper/refs.bib` / `main.bbl` (32 references), `paper/cover_letter.md`, `paper/figure_alt_text.md`, `scripts/make_submission.sh`, `paper/submission/`, `docs/figures/nar_fig*.{png,pdf}` and `nar_graphical_abstract.*`.
Only this report was written; nothing memory-heavy was run.

## Verdict
**Almost ready. Four small required fixes remain, plus the author-side placeholders.**
The rerun rewrite is consistent in the main text. All numbers I cross-checked against the macros agree. No sentence treats a method as failed, "not ranked" or "stopped at the cap".

**Tally:**
- Round-3 points (9 N-items, 10 optional suggestions): 8 resolved, 2 partly, 2 not resolved. The not-resolved items are cosmetic or optional.
- Optional round-3 suggestions: 0 of 10 done (1 partly).

## Abstract word count
`pdftotext main.pdf`, text between "Abstract" and "Key words", `wc -w`: **197 words (limit 200), so it passes.** There are 3 words of headroom. It has no URL, citation or figure reference. Numbers match the macros: 13 methods, 24 sections, 8 of 16, 0.16, up to 0.60.

## Round-3 points

| # | Round-3 point | Status | Evidence |
|---|---|---|---|
| N1 | Cover letter 0.17 vs 0.16 | **Resolved** | `cover_letter.md` says "0.16 on average and by up to 0.60", matching `\lotMean` and `\lotMax`. Also 13 methods, 24 sections, 0.65, 0.51, 0.15 (= `\mgcnLeak` 0.147). |
| N2 | Alt text stale for Fig. 1 and Fig. 4 | **Resolved** | Fig. 1 now names breast cancer on Visium and the Stereo-seq embryo. Fig. 4 reads "mean about 0.16, up to 0.60" and "14 methods" (`\lotNMethods` = 14). Fig. 2 "eight above zero" matches (8 filled symbols in the PNG). |
| N3 | Coverage table: "20/24" for R mclust perturbation | **Partly resolved** | It is now Table S23. The column reads "R mclust noise/order (first 3 datasets) 20/20", and the seed column reads 24/24 (23/24 for GraphST, NichePCA, Spatial-MGCN and DeepST, the four pending embeddings, expected). **Still inconsistent:** the S12 caption says "Noise repetitions were not run on the 18,408-bin Stereo-seq section". Main text l. 322–323 says they were run "only for three embeddings", which the data confirm (AnisoST and BANKSY λ=0.2/0.8 in `mclust_seed_summary.csv`). Reword the caption to "run only for AnisoST and BANKSY". The string is in `scripts/make_supplement.py` l. 188. |
| N4 | Generic 10x URL | **Resolved in source, new layout defect** | main.tex l. 434 and `refs.bib` l. 277 now use the dataset-specific URL. The text does not break, though (see M2 below). |
| N5 | "Lottery" in the S22 header | **Resolved** | The header reads "Initialisation (20 starts)". No "Lottery" remains in either PDF. |
| N6 | Graphical abstract repeats Fig. 1D | **Not resolved** | The file is unchanged (24 Oct). Optional. |
| N7 | Embryo thumbnail clipped in Fig. 1 | **Not resolved** | The file is unchanged (24 Oct). Cosmetic. |
| N8 | Overfull boxes | **Not resolved** | The 7.9 pt box in l. 360–370 remains. A worse one has appeared in the Data availability paragraph (M2). |
| N9 | Cover letter signed while the author block is TODO | **Author-side** | Unchanged. |
| Opt. 1 | Abstract headroom | Partly | 3 words now. |
| Opt. 2–10 | AI pointer in Methods; ethics line; software versions; "Bayesian models" third family (l. 131); Type 3 fonts; unsrtnat; `SUBMISSION_CHECKLIST.md`; template option | Not done | `main.pdf` has 2 Type 3 fonts. `SUBMISSION_CHECKLIST.md` is still dated 12 Oct and says *Bioinformatics Advances*. l. 130–131 still list "Bayesian models" as a family while the figures use deep / statistical and neighbourhood. |

## New problems since round 3

| # | Problem | Location | Fix | Severity |
|---|---|---|---|---|
| M1 | **`paper/submission/` is stale.** Figure2/4/5.pdf, `manuscript.pdf` and `supplementary_data.pdf` date from 24 Oct, before the rerun. Figure2.pdf is 74,986 bytes against 74,758 in `docs/figures`, and the manuscript is 2,943,223 against 2,943,318 bytes. The alt text and cover letter copies are current. | `paper/submission/` | Rerun `scripts/make_submission.sh` after the final build, once the R mclust job is finished and figures and PDFs are regenerated. | **Required** |
| M2 | **The Data availability URLs overrun the column.** The 10x URL is 140 pt overfull and the BASS-Analysis and SEDR URLs also overflow (`main.log` l. 1201–1231). On p. 8 the 10x URL overprints the "Conflict of interest statement" text in the neighbouring column. | main.tex l. 430–438 | Allow URL breaks. Options: `\usepackage{url}` with `\urlstyle{same}` and `\Urlmuskip=0mu plus 2mu`, `\sloppy` in this paragraph, or `\emph{} ... 10xgenomics.com/datasets` with the page name in `configs/datasets.yaml`. Rebuild and check p. 8. | **Required** |
| M3 | **The S9 caption is stale and its last block is now redundant.** It says "sections completed by every method" and that the last rows "exclude the methods stopped at the memory cap". All 16 methods now cover all 24 sections, so the "Methods with every section" block repeats the first table. This is the only remaining "stopped at the memory cap" wording as a failure. | `scripts/make_supplement.py`, Table S9 | Delete the block and the sentence, and keep "BayesSpace, run on Visium only, is not ranked". | **Required** |
| M4 | The S12 caption is inconsistent with the text (see N3). | Table S12 | See N3. | **Required** (small) |
| M5 | **Thread count.** Methods l. 131–132 say "one CPU thread". Supplementary Note 6 says the reruns used a server with "125 GB RAM and 20 threads". | main.tex l. 163–165 | Add "(one thread per job)" if that is true, or say that thread count differed. | Recommended |
| M6 | GraphST peak memory is shown as 12 GB (`\peakBigGraphst`), the same as the cap, while the text says all five "exceeded" it. S15 gives 11.8 GB as a median over jobs. | l. 239–240; Table S15 | Print one decimal (for example 12.4) or write "about 12". | Minor |
| M7 | S23 shows 23/24 in the R mclust seeds column for GraphST, NichePCA, Spatial-MGCN and DeepST. Main text l. 322–323 and the Fig. 3 caption describe 24 sections. | Table S23 | **Known and in progress (R experiment).** Check that the counts, Table S12 (`mcsNBig`, now 290) and Fig. 3B update together. | Expected |

## Checks with no problems found
- **Failure wording:** the only remaining "not ranked" (Fig. 2 caption l. 277, Fig. 2C panel text, S9) refers to BayesSpace, which is Visium-only by design. The cap is described as a memory-cap rerun, not a failure (Methods l. 161–166, Limitations l. 412–414, S15 caption).
- **Rerun count:** "17 jobs" is consistent in main.tex and Supplementary Note 6: 5 methods × 3 seeds on E10.5 E1S1, plus DeepST seeds 1 and 2 on E10.5 E2S1.
- **Run-time and memory claims:** reruns "count for peak memory but not for run time" (S15) agrees with l. 164.
- **References:** 32 entries in `main.bbl`, no undefined citations, no `??` in either PDF, no BibTeX warnings. The `tenx2020brca` and `chen2022mosta` entries are correct.
- **End matter:** Data availability → Supplementary data → Acknowledgements (AI use) → Author contributions → Funding → Conflict of interest → References. The order is correct and the AI use is disclosed.
- **Figure specifications:** Figs 1–5 are 175 mm wide at 600 dpi (PNG, 4133 px) and vector PDF with no Type 3 fonts. The graphical abstract is 254 × 101.6 mm (5:2) at 600 dpi in PNG, TIFF and PDF. The new Figs 2–4 (2 Nov 23:17) show no "*" markers and no memory-cap labels. Fig. 2B has 8 filled and 8 open symbols, matching `\nRobBetter` = `\nRobUnres` = 8.
- **Data availability:** specific URLs and accession STDS0000058; `configs/datasets.yaml` and `data/CHECKSUMS.sha256` exist.

## Author-side placeholders (listed once)
- **Author block:** names, `\authormark`, department, university, country and email (main.tex l. 25–29); ORCIDs in the submission system.
- **Acknowledgements:** confirm the AI wording and add thanks.
- **CRediT** statement.
- **Funding**, including the open-access charge.
- **GitHub URL and Zenodo DOI** in Data availability and the cover letter ("[GitHub URL]", "[DOI]"); cite the Zenodo record.
- **Preprint** statement in the cover letter.
- **Suggested reviewers** (`paper/suggested_reviewers.md`): confirm emails and conflicts.
- **OUP template fields** (`\DOI`, received/revised/accepted and Advance Access dates).
