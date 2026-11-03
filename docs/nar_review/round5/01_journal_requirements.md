# NAR journal-requirements audit, round 5

**Role:** journal-requirements editor. **Checked:** `paper/main.pdf` (10 pp., 3 Nov 22:11), `paper/supplementary.pdf` (20 pp.), `main.tex`, `main.log`, `cover_letter.md`, `SUBMISSION_CHECKLIST.md`, `paper/submission/`, graphical abstract files. Only `pdftotext`, `pdffonts` and `pdfinfo` were run.

## Verdict: MINOR revision (technical clean-up only)
All round-4 "required" items except one are fixed. One layout defect remains (the Data availability URLs). It is small but visible in the PDF. The rest is optional or author-side.

## Round-4 "required before acceptance" items

| Item | Status | Evidence |
|---|---|---|
| M1 `paper/submission/` stale | **Resolved** | Every file in `submission/` is dated 3 Nov 22:11. `Figure1`-`Figure5.pdf` and `nar_graphical_abstract.*` are byte-identical in size to `docs/figures`. The `manuscript.pdf` size (2,946,545) equals `main.pdf`, and `supplementary_data.pdf` (1,523,010) equals `supplementary.pdf`. Figure numbering matches the manuscript order (Fig. 3 = maps, 4 = robustness, 5 = protocol; checked against `make_submission.sh` and the `\includegraphics` order). |
| M2 Data availability URLs overrun the column | **NOT resolved** | `main.log` still reports Overfull `\hbox` 140.9 pt (10x Genomics URL), 38.1 pt (BASS-Analysis), 13.2 pt, and 4.8 pt in the paragraph at lines 431-440. In the PDF (p. 8, right column, bottom) the 10x URL is cut off at "...block-a-sectio" and runs into the gutter. The 7.9 pt box at l. 361-371 (`DLPFC_test.py`, `HBC_test.py`) is also still there. See finding 1. |
| M3 Table S9 caption/redundant block | **Resolved** | The old S9 content was removed and the tables were renumbered. The only "not ranked" wording left is the new S10 caption: "BayesSpace, run on Visium only, is not ranked". No "stopped at the cap" wording is presented as a failure. The text in Supplementary Note 6 ("stopped and recorded as out of memory") describes the cap protocol and is correct. |
| M4 Table S12 caption vs text | **Resolved** | The caption (now Table S13) says "Noise repetitions were run for 3 of the 14 embeddings ... of the 18,408-bin Stereo-seq section". This matches main.tex l. 322-323. |
| M5 Thread count | **Resolved** | Limitations says "one CPU thread, except the reruns on the 125 GB server"; Note 6 says the same. |
| M6 GraphST 12 GB peak | Not rechecked in detail (minor, not a requirement) | |
| M7 S23 23/24 counts | Author-side experiment; table now has no pending flag that I could see | |
| Round-3 leftovers | Partly | Checklist still stale (finding 2). Type 3 fonts: 2 remain (finding 4). |

## Requirements that pass
- **Abstract:** 198 words by `pdftotext | wc -w` (limit 200; headroom is only 2 words, so any edit must be a net deletion). Unstructured, no citations, no URLs, no figure references. Cover letter wording agrees with it (0.16, up to 0.60, 24 sections, 13 methods).
- **Key words:** 5 are given.
- **Article type:** cover letter names "Computational Biology".
- **Page size:** OUP template, 594.7 x 781.9 pt, class `oup-authoring-template` (`contemporary,large`, `webpdf`).
- **End matter:** Data availability, Supplementary data ("available at NAR Online"), Acknowledgements (AI use disclosed), Author contributions, Funding (including open-access charge), Conflict of interest. Order and headings are as NAR requires.
- **References:** 32 entries, no `??` in either PDF, no undefined citations.
- **Supplement:** Tables S1-S24 and Figures S1-S4 are all present, Notes 1-6 are present, and every Supplementary item cited in the main text exists (S24 is cited three times).
- **Figure files:** Figs 1-5 are vector PDFs at 175 mm width with 0 Type 3 fonts. The graphical abstract is 6000 x 2400 px at 600 dpi in TIFF and PDF (10 x 4 in).
- **Compile state:** no `LaTeX Error`, no missing references. Warnings are limited to hyperref bookmark levels and boxes.
- **Data/code:** specific accession (STDS0000058), per-dataset URLs, and checksums and `configs/datasets.yaml` named.

## New findings, ranked

1. **Data availability URLs still overflow the column (Required, small).** main.tex l. 431-440, p. 8 right column. The 10x link is 141 pt too wide, so it prints into the gutter and is truncated in the PDF, which makes the link unusable for readers. Fix: break URLs. Use `\usepackage[hyphens]{url}` and `\urlstyle{same}` with `\Urlmuskip=0mu plus 2mu`, or a `\sloppy` group around the paragraph, or shorten the 10x link to the datasets page plus the dataset name in `configs/datasets.yaml`. Rebuild, copy to `submission/` with `make_submission.sh`, and check p. 8 visually. The same fix helps the 38 pt BASS-Analysis box.
2. **`paper/SUBMISSION_CHECKLIST.md` is stale and addressed to the wrong journal (Recommended).** Its title and text still say *Bioinformatics Advances*, 13 methods, 20 sections, three datasets, and "Clustering lottery". It is not part of the upload, but it is in the deliverable folder and contradicts the manuscript (24 sections, four technologies). Fix: rewrite for NAR with the actual open items (list in the placeholder section below) or delete it.
3. **Supplementary Table S9 (brain-only sensitivity) may not be cited in the main text** (no `\ST...` macro for it in `main.tex`; S21 and S23 are cited through macros, so my first grep was wrong about those). Optional: cite S9 where the brain-only result is stated, or confirm it is cited in the supplement.
4. **Type 3 fonts (2) remain in `main.pdf`** (F156, F158). They are not in the figure files. Some NAR production checks flag Type 3. Fix: find the source (probably a template symbol or math font) and substitute, or accept; production re-typesets the accepted file in any case. Optional.
5. **Abstract headroom is 2 words.** Not an issue now. Note it if anything is added after review.
6. **Overfull box at l. 361-371 (7.9 pt).** Break the `\texttt` file names (for example `DLPFC\_\allowbreak test.py`). Cosmetic.
7. **Cover letter:** states "13 published methods and three training-free baselines" while the abstract says "8 of 16 comparators". These count different sets (the 16 comparators include the BANKSY variants and BayesSpace). Consider adding "(16 configurations)" to avoid a reader's arithmetic question. Optional.

## Author-side placeholders (listed once, not counted as defects)
- Author names, `\authormark`, affiliations, email; the cover letter is signed with a name and a vt.edu address while the manuscript author block is still TODO (make them agree); ORCIDs.
- Acknowledgements wording; CRediT statement; Funding including the open-access charge.
- GitHub URL and Zenodo DOI (Data availability l. 439 and the cover letter), and the licence statement for the repository.
- Preprint sentence in the cover letter; suggested reviewers (`suggested_reviewers.md`); OUP template fields (DOI, received/accepted dates).
