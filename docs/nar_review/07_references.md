# 07 — References: verification report

Date: 2026-10-18. Scope: `paper/refs.bib` (rewritten) and how `paper/main.tex` cites it.
Sources: Crossref REST API (`api.crossref.org/works/<doi>`), Europe PMC full text (PMC XML), bioRxiv API (`api.biorxiv.org/details/biorxiv/<doi>`).
BibTeX test: `bibtex` on a copy of `main.aux` with the new `refs.bib`, using `abbrvnat`. It ran with 0 warnings and produced 26 entries.

## 1. Entries that were incomplete or marked VERIFY. All are now resolved.

| Key | Verified metadata | DOI |
|---|---|---|
| yu2025histar | Yu J, Yuan J, Yi Q, Ye Z, Xu P, Liu W. *J Transl Med* 23:1416 (published 23 Dec 2025) | 10.1186/s12967-025-07404-3 |
| yuan2024benchmark | Yuan Z, Zhao F, Lin S, Zhao Y, Yao J, Cui Y, Zhang X-Y, Zhao Y. *Nat Methods* 21(4):712–722 (2024) | 10.1038/s41592-024-02215-8 |
| hu2024gbbench | Hu Y, Xie M, Li Y, Rao M, Shen W, Luo C, Qin H, Baek J, Zhou XM. *Genome Biol* 25:212 (2024) | 10.1186/s13059-024-03361-0 |
| nar2025bench | Kang L, Zhang Q, Qian F, Liang J, Wu X. *Nucleic Acids Res* 53(7):gkaf303 (2025). **The paper exists**: the title, volume, issue and article number in the old entry were correct. | 10.1093/nar/gkaf303 |
| explanatory2026 | Descoeudres A, Prusina T, Schmidt N, Do VH, Mages S, Klughammer J, Matijević D, Canzar S. bioRxiv preprint, posted 16 Mar 2026 | 10.64898/2026.03.12.710462 |
| nichepca2025 | Schaub DP, Yousefi B, Kaiser N, Khatri R, Puelles VG, Krebs CF, Panzer U, Bonn S. *Bioinformatics* 41(1):btaf005 (2025) | 10.1093/bioinformatics/btaf005 |
| wang2024pearlst | Wang H, Zhao J, Nie Q, Zheng C, Sun X. *Research* 7:0390 (2024) | 10.34133/research.0390 |
| do2026graphbg | Do VH, **Tran TPL**, Canzar S. This paper has **3 authors**. The old entry wrongly split "Tran, Thi Phuong Lan" into two authors. bioRxiv preprint, posted 31 Mar 2026 | 10.64898/2026.03.28.715026 |
| li2022bass | Li Z, Zhou X. *Genome Biol* 23:168 (2022). The journal and volume in the old entry were correct. | 10.1186/s13059-022-02734-7 |
| xu2024sedr | Xu H, Fu H, Long Y, … Chen J (14 authors). *Genome Med* 16:12 (2024) | 10.1186/s13073-024-01283-x |
| ren2022spaceflow | Ren H, Walker BL, Cang Z, Nie Q. *Nat Commun* 13:4076 (2022) | 10.1038/s41467-022-31739-w |
| li2022ccst | Li J, Chen S, Pan X, Yuan Y, Shen H-B. *Nat Comput Sci* 2(6):399–408 (2022) | 10.1038/s43588-022-00266-5 |
| wang2023spatialmgcn | Wang B, Luo J, Liu Y, Shi W, Xiong Z, Shen C, Long Y. *Brief Bioinform* 24(5):bbad262 (2023) | 10.1093/bib/bbad262 |
| xu2022deepst | Xu C, Jin X, Wei S, … Jiang Q (18 authors). *Nucleic Acids Res* 50(22):e131 (2022) | 10.1093/nar/gkac901 |

Changes to the other entries:
- I checked every other entry against Crossref: Maynard, BANKSY, SpaGCN, STAGATE, BayesSpace, GraphST, mclust, Perona–Malik, Hubert–Arabie, STARmap and MERFISH.
- I added DOIs and issue numbers, and completed the SpaGCN author list (9 authors).
- Entries with more than 10 authors list the first three authors followed by "and others".
- `holm1979` has no DOI (the paper is on JSTOR) and stays as it was.
- `pedregosa2011sklearn` has no DOI (JMLR); I added the second and third authors.

No entry turned out to be fabricated, so none needed a `CHECK:` note.

## 2. Does each reference support what main.tex says?

**Mismatch, which needs an edit in main.tex (lines 67–69).** Two citations are swapped:
> "...that deep methods vary with the random seed \citep{nar2025bench}, that replacing each method's clustering algorithm changes results \citep{hu2024gbbench}..."

- **Kang et al. (nar2025bench)** is the paper that replaces the clustering algorithm. Quote: "Instead of using the default clustering algorithm in each GNN method, we applied four different clustering algorithms, including mclust, K-means, Louvain, and Leiden", plus a refinement step. Its full text contains no random-seed analysis. Its "stability" means consistency across DLPFC sections and datasets, not across seeds.
- **Hu et al. (hu2024gbbench)** is the paper with the seed analysis. It has a "Random seed analysis" section and states that for CCST, ADEPT and STAGATE "clustering performance, measured by ARI, was randomly associated with both the loss value and the selected seed". It does not swap clustering algorithms: joint embeddings are clustered with mclust.
- **Proposed fix:** "deep methods vary with the random seed \citep{hu2024gbbench}, that replacing each method's clustering algorithm changes results \citep{nar2025bench}".

Line 67 cites `nar2025bench` for "rankings depend on the dataset". Keep that citation: the abstract says "no single method works best… optimal method depends on the data".

Other citations are supported:
- `yuan2024benchmark`: the abstract says the methods are complementary and performance depends on the scenario. This is acceptable support for "rankings depend on the dataset".
- `explanatory2026`: the abstract says "the choice of preprocessing and clustering often has a larger impact on performance than architectural novelty alone". This supports the main.tex sentence almost word for word.
- `nichepca2025`: a simple PCA-based method rivals ten state-of-the-art methods. This supports the citation.
- `do2026graphbg` ("simple training-free pipelines"): **this is a soft fit.** GraphBG combines approximate spectral graph convolutions with a variational Bayesian GMM, so it is not a trained neural network. However, it describes itself as a "unified framework" with "representation learning", not as a simple baseline. Consider rewording to "simple or training-free pipelines", or keep NichePCA alone.
- `wang2024pearlst` ("similar idea used inside a deep model"): **confirmed.** PearlST integrates a PDE diffusion model and states "we adopt a diffusion function proposed by Perona and Malik".
- `perona1990`, `hubert1985ari`, `scrucca2016mclust` and `pedregosa2011sklearn` are standard method citations and are appropriate.
- Data citations (`maynard2021dlpfc`, `wang2018starmap`, `moffitt2018merfish`, `li2022bass` for the processed annotations) are appropriate.
- `holm1979` is in refs.bib but is **not cited** in main.tex or supplementary.tex, and the manuscript never mentions Holm correction. Either cite it where multiple-testing correction is described, or ignore it (BibTeX drops uncited entries).

## 3. HiSTaR DLPFC numbers (yu2025histar)

Source: the full text in Europe PMC, PMC12729201 (DOI 10.1186/s12967-025-07404-3), Results section on Fig. 2.
- 12 sections: "HiSTaR achieving a **median ARI of 0.65** and a peak ARI of 0.76 across 12 DLPFC dataset slices, with median NMI and FMS of 0.73 and 0.76 respectively". The per-section values are in Supplementary Fig. S1 and Tables S1–S3.
- Section 151673: HiSTaR "records the highest ARI score of **0.7182**" (Fig. 2B). Table 1 also gives 0.7182 for the full two-block model (NMI 0.7535, FMS 0.7736).
- **Both of the manuscript's values (median 0.65; 0.718 on 151673) are correct.** The `\todo` at main.tex line 280 can be resolved. Suggested wording: "median ARI 0.65 over the 12 sections and 0.718 on section 151673 (ref)".
- Caveat: the paper says "median", not "mean", and also reports a peak of 0.76. HiSTaR is compared there with Leiden, Louvain, ST-SCSR, SEDR, STAGATE, STMGraph and DeepST.

## 4. Formatting for NAR

- Capitals in titles are protected with braces: {HiSTaR}, {SpaGCN}, {BANKSY}, {BayesSpace}, {GraphST}, {PCA}, {GraphBG}, {B}ayesian, {G}aussian, {P}ython, {Spatial-MGCN}, {DeepST}, {BASS}, {SpaceFlow}. Accents are escaped: Matijevi{\'c}, Ga{\"e}l.
- Journal names are written in full. Article numbers (gkaf303, btaf005, bbad262, e131, eaat5691) go in `pages`.
- Preprints carry `journal = {bioRxiv}`, `note = {Preprint}` and a DOI.
- **Style issue (main.tex, not mine to edit):** main.tex uses `\bibliographystyle{abbrvnat}`, which sorts references alphabetically and abbreviates first names. NAR numbers references in order of citation, so switch to `unsrtnat` (with `\usepackage[numbers,sort&compress]{natbib}`). The bib file works with either style.

## 5. What remains uncertain

- The two 2026 bioRxiv preprints (`explanatory2026`, `do2026graphbg`) may have been published in a journal since then. Re-check before submission and update the entries if so.
- The bioRxiv DOI prefix 10.64898 is the new openRxiv prefix. I confirmed it resolves in Crossref.
- Holm 1979: the volume, issue and pages (6(2):65–70) are from standard knowledge and were not checked against Crossref, because the paper has no DOI.
