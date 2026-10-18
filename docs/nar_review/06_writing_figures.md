# NAR editorial review 06: writing and figures

Reviewer role: scientific editor, *Nucleic Acids Research*.
Material reviewed: `paper/main.tex` (with the macro values in `results/paper_macros.tex`), `paper/supplementary.tex`, the compiled `paper/main.pdf` (7 pp.) and `paper/supplementary.pdf` (15 pp.), and the figure files `docs/figures/nar_fig1_pipeline_v2`, `nar_fig2_accuracy`, `nar_fig3_robustness`, `nar_fig4_protocol` and `nar_fig5_maps` (PNG at 600 dpi and vector PDF).
Line numbers refer to `paper/main.tex` as it stands now.

---

## 0. Summary verdict

The prose is concise, uses British spelling throughout and is unusually honest about its limits: the exploratory reference, the post-hoc choice of baseline and the uncorrected *p* are all stated. The core findings are publishable and well suited to NAR. They are that a training-free diffusion baseline is in the top tier, that the clustering step on a fixed embedding causes large ARI variance, that R mclust is sensitive to spot order, and that released code can leak labels.

The manuscript is **not ready to submit** for six reasons, in priority order:

1. **Wrong journal shell, and placeholders that show in the PDF.** The class, `\journaltitle`, the header comment and "ORIGINAL PAPER" all say *Bioinformatics Advances*. There are 12 visible red TODOs. Eight references print the author as "VERIFY" in the reference list and in citations such as "[VERIFY, 2025a]". Supplementary Table S2 shows the HiSTaR commit as "TO RECORD", and Table S14 says "to be verified".
2. **Internal contradictions about which clustering counts as "standard" for the baselines and for HiSTaR and BANKSY** (details in §3). A reader cannot tell what Fig. 2a shows for AnisoST.
3. **Figure numbering and colour semantics.** In the PDF the robustness figure, file `nar_fig3`, prints as **Fig. 5**, the protocol figure (`nar_fig4`) as **Fig. 3** and the maps (`nar_fig5`) as **Fig. 4**. Blue, orange and green mean *method family* in Figs 1 and 2, *dataset* in the robustness figure, *higher or lower* in the protocol figure, and *Layer 1, 2 and 3* in the maps. Yet the Fig. 1 legend says "colours used throughout".
4. **Count mismatches between text and tables.** "Raised mean ARI for 6 of 12" contradicts Supplementary Table S11, which shows 7 positive changes. "Six patterns of label use" contradicts Table S16, which has five categories (L1–L5). The Table S12 caption says "CCST, DeepST and BayesSpace are still running", but the table contains their rows. The main text says "every fit is shown in Supplementary Fig. S1", but S1 shows only 3 of 14 methods. Section 3.2 calls both baselines "invariant", but Table S17 shows an ARI of 0.89–0.97 under spot permutation.
5. **Overclaims in three places.** These are the heading "Choosing fits by likelihood is not a remedy", "the R implementation used by most published methods", and "matched or outperformed every deep encoder".
6. **NAR format.** The abstract is about 222 words against NAR's limit of 200. The graphical abstract is missing. Panel letters are lowercase, and figure citations use "Fig." where NAR house style is "Figure 1A". Several figures are 18.2–18.9 cm wide and are shrunk on placement, so their smallest text is below 6 pt.

---

## 1. Title and abstract

### Title
The current title, "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods", is clear but does not state a finding. It also reuses the wording of several existing benchmarks. NAR allows declarative titles. Options:

- **A (recommended):** "The clustering step, not the encoder, limits the accuracy and reproducibility of spatial domain identification"
- B: "A training-free baseline and an unstable clustering step: benchmarking spatial domain identification across three technologies"
- C, if the authors want to stay neutral: "Accuracy, robustness and reproducibility of spatial domain identification methods across three spatial technologies"

Option A is supported by the robustness figure, Supplementary Tables S9 and S10, and Fig. 2b. If it is chosen, the Discussion must state the encoder-versus-clustering conclusion explicitly (§5).

The running title `[Benchmarking spatial domain identification methods]` is fine.

### Abstract
- **Length.** About 222 words without the code line, which exceeds NAR's limit of 200.
- **The finding is stated only implicitly.** The reader gets a list of numbers but no sentence saying what they mean.
- **"14 of 16 methods" is ambiguous** right after "13 published methods and three baselines". The 16 comparators are the 13 published methods, with BANKSY counted at two λ values, plus AnisoST and PCA.
- **Hard-coded and unverified numbers.** "0.51 … reported 0.65" rests on a value the authors have not yet verified (TODO at line 280). Do not put it in the abstract until it is verified.
- **"Improved 6 of 12 … worsened 5"** leaves the twelfth method unexplained and conflicts with Supplementary Table S11 (§3).
- **"All methods were run with default or published settings"** is a limitation. It reads oddly between results and recommendations.

**Replacement (about 198 words; recount after the macros expand).** Lines 33–46: replace the entire `\abstract{...}` body with:

> Spatial domain identification methods are usually compared by small differences in adjusted Rand index (ARI), mostly on one tissue and from a single run. We benchmarked \nMethodsPub{} published methods and three training-free baselines on \nSections{} annotated sections from 10x Visium, STARmap and MERFISH, and separated each learned embedding from its clustering step. A training-free graph-diffusion baseline had a higher mean ARI than \nStdBetter{} of \nStdTot{} comparators (95\% hierarchical-bootstrap intervals excluding zero) and could not be separated from BASS or BANKSY. The clustering step was a larger source of variation than most between-method differences: on fixed embeddings, refitting the same Gaussian mixture from different random starts changed ARI by \lotMean{} on average (up to \lotMax), and reordering the spots changed the ARI of R mclust by up to \mcPermMax. Keeping the most likely of 20 fits did not reliably help, because likelihood and ARI were unrelated on single-cell MERFISH data. With its official code, HiSTaR reached a median DLPFC ARI of 0.51, compared with 0.65 reported, and the released code of one method selects its reported epoch using the labels (ARI inflated by \mgcnLeak). We recommend reporting the clustering protocol and its variance, never selecting runs with labels, and including training-free baselines.

The "Code, per-run results and figures" sentence should go to the Data availability section. Add a macro for the HiSTaR median and the reported value instead of the hard-coded "0.51" and "0.65".

---

## 2. Journal format (NAR)

| Line | Original | Replacement / action |
|---|---|---|
| 1 | `% Manuscript for Bioinformatics Advances (OUP authoring template, texlive-publishers).` | `% Manuscript for Nucleic Acids Research.` and switch to the NAR template, or to the OUP template with the NAR options |
| 12 | `\journaltitle{Bioinformatics Advances}` | `\journaltitle{Nucleic Acids Research}` |
| 17 | `\appnotes{Original Paper}` | NAR uses the article type "Computational Biology" or "Methods"; set this to match the submission category |
| 95 | `\section{Materials and methods}` | `\section{Materials and Methods}` (NAR heading case) |
| 321 | `\section*{Competing interests}` / `No competing interest is declared.` | `\section*{Conflict of interest statement}` / `None declared.` |
| 324 | `\section*{Author contributions statement}` | NAR uses an Author contributions section in CRediT form; fill it in |
| 332–333 | `Supplementary Data are available at NAR Online.` | Keep this, and move it so the order matches NAR: Data availability → Supplementary data → Acknowledgements → Funding → Conflict of interest |
| 335–339 | Data availability without identifiers | Add accession numbers or DOIs: spatialLIBD (Bioconductor package version), the BASS-Analysis commit, the GitHub URL and the Zenodo DOI for code and per-run results |
| throughout | `Fig.~\ref{...}`; `Figure~\ref{fig:robust}a` (l. 231) | NAR style is "Figure 1", with uppercase panel letters "(Figure 2B)". Define `\newcommand{\figref}[1]{Figure~\ref{#1}}` and use it everywhere |
| — | Graphical abstract missing | Required by NAR; see §8 |

**References.** Eight bibliography entries carry `author = {{VERIFY}}` or a `VERIFY` note: `nar2025bench`, `explanatory2026`, `nichepca2025`, `yu2025histar`, `hu2024gbbench`, `yuan2024benchmark`, `wang2024pearlst`, `do2026graphbg`, plus the CCST, SpaceFlow, DeepST, Spatial-MGCN and SEDR entries. "VERIFY" appears **in the printed citations** on pages 1, 2 and 6. Every one must be resolved before submission.

---

## 3. Terminology consistency (must fix)

### 3.1 "Standard", "own" and "Robust" clustering
The same two protocols go by at least eight names:

| Concept | Names used |
|---|---|
| The method's usual clustering | "Standard" (l. 148, 178, Figs 2 and 4), "own clustering" (Supp. S3, S5, S7, S8, S11), "method's own" (Fig. 4 legend), "the method's own clustering" (Fig. 1 caption) |
| 20-start, best-likelihood tied GMM | "Robust" (l. 151), "20-start clustering" (l. 182), "20-start, best-likelihood fit" (l. 88), "matched protocol" (l. 268), "best-likelihood fit of 20 random starts" (l. 261), "Best of 20 starts" (Fig. 1d) |

"Robust" is a particularly bad name: it clashes with the paper's own *Robustness* axis and implies a property the paper shows it lacks.

**Edits:**
- l. 148: `\emph{Standard}: each method's usual clustering.` → `\emph{Default clustering}: the clustering step of each method's official pipeline.`
- l. 151: `\emph{Robust}: the method's embedding clustered with a tied-covariance Gaussian mixture (the mclust EEE model) with 20 random starts,` → `\emph{Best-of-20 (BL20)}: the method's embedding clustered with a tied-covariance Gaussian mixture (equivalent to the mclust EEE model) from 20 random starts,`
- Then use "default clustering" and "BL20" everywhere: main text, captions, the Fig. 4 legend, Supplementary captions S3, S5–S8 and S11, and the Supplementary Table S3 column headers ("DLPFC own" → "DLPFC default").
- l. 268: `Replacing each method's standard clustering by this matched protocol` → `Replacing each method's default clustering by BL20`.

### 3.2 What "standard" means for the baselines, HiSTaR and BANKSY (contradiction)
- l. 149 says the standard clustering for "HiSTaR, BANKSY and the baselines" is a **3-start scikit-learn GMM**.
- The Fig. 2 caption (l. 195) says that for the "training-free baselines: their 20-start clustering".
- The Supplementary Table S3 caption says "Training-free baselines are clustered only with the 20-start mixture". The same table nevertheless gives AnisoST a separate "own" value (0.526/0.564/0.377), and Fig. 2a prints exactly those "own" values for AnisoST but the 20-start values for linear diffusion and PCA.
- Supplementary Table S2 lists HiSTaR's own clustering as "R mclust EEE" and BANKSY's as "Leiden / mclust (package)". Both contradict l. 149.

**Action.** Decide on one definition, then make l. 149, the Fig. 2 caption, the Table S2 "Own clustering" column and the Table S3 caption agree with it. If linear diffusion is scored with BL20 while every comparator uses its default clustering, the headline comparison in Fig. 2b is asymmetric. State this explicitly in the Fig. 2 caption and in the Limitations. Alternatively, make Table S6, the like-for-like BL20 comparison, an equal co-headline.

### 3.3 Method families
- Fig. 1c uses "Deep encoders / Statistical / Bayesian / Training-free baselines".
- The Fig. 2 legend uses "Graph / deep encoders / Statistical, neighbourhood, Bayesian / Training-free baselines".
- The text uses "deep methods" (l. 67, 185), "neural methods" (l. 189) and "deep encoder" (l. 298).

Pick one set, for example **"Deep graph encoders", "Statistical and neighbourhood methods" and "Training-free baselines"**, and use it in all figures and the text.

**NichePCA** is a published method, but Supplementary Table S2 types it as "training-free (neighbour aggregation + PCA)", and Fig. 1c groups it with BASS and BayesSpace. Add one clause at l. 129: "NichePCA, a published training-free method,". This matters for the claim that training-free pipelines are competitive.

### 3.4 BANKSY λ
- Notation is consistent in the main text (`BANKSY $\lambda=0.8$`). Supplementary Table S2 prints "banksy" in lowercase; correct it to "BANKSY".
- The main text never says that λ = 0.2 is BANKSY's cell-typing setting and λ = 0.8 its domain setting; only Table S2 says so. Add this at l. 123–124: `$\lambda\in\{0.2,0.8\}$` → `$\lambda=0.8$ (recommended for domain segmentation) and $\lambda=0.2$ (recommended for cell typing, included for reference)`.
- Counting BANKSY λ = 0.2 as a separate loser among the "14 of 16" inflates the count. Say so in the Fig. 2 caption, or exclude it from the count.

### 3.5 "Cluster" used for two things
"The unit of analysis is the cluster: 5 clusters (three DLPFC donors, STARmap, MERFISH)" (l. 161; also Fig. 2 caption, Supplementary Note 4, Table S5). In a paper about clustering, this is confusing.

**Replace with "group" or "block":**
- l. 161: `so the unit of analysis is the cluster: \statClusters{} clusters` → `so the unit of analysis is the group: \statClusters{} groups`
- l. 163: `(\statBoot{} resamples of clusters, then of sections within a cluster; the estimate is the equal-weight mean of cluster means)` → `(\statBoot{} resamples of groups, then of sections within a group; the estimate is the equal-weight mean of group means)`
- l. 177, l. 184 and l. 197, and Supplementary Note 4 and Table S5: replace "clusters" with "groups" in the same way.

### 3.6 Other naming
- "Linear diffusion", "linear graph diffusion" (l. 175), "training-free diffusion baseline" (l. 38, 297) and "neighbourhood smoothing" (l. 310). Use "linear diffusion" after first definition.
- "AnisoST", "edge-preserving variant" (l. 228) and "Anisotropic" (Supp. Fig. S3 axis). Use "AnisoST" in the figure.
- "Lottery" (l. 153; Supplementary Table S18 and Fig. S1; Limitations l. 316) is jargon that is never defined for the reader. Replace it with "repeated single-start fits" or "initialisation experiment".
- `\lotWorstSection` expands to "dlpfc 151672" in lowercase (l. 233). Fix the generator so it outputs "DLPFC section 151672".
- l. 236: "GraphST's 20-dimensional PCA embeddings" is misleading because GraphST's embedding is learned. Write "GraphST's 20-PC projection of its learned embedding".
- Spelling is consistently British: initialisation, normalised, neighbour, colour, favoured, optimisation, summarised. No American forms were found in main.tex or supplementary.tex. Keep "ARI" and "mclust" lowercase as now. Note that "R mclust" and "mclust" alternate; use "R mclust" when the implementation matters.

---

## 4. Line-level edits by section

### Introduction
| Line | Original | Replacement / comment |
|---|---|---|
| 64–65 | "report median ARI improvements of a few hundredths over previous methods." | ARI is not defined in the main text. Write "report median adjusted Rand index (ARI) \citep{hubert1985ari} improvements of a few hundredths over previous methods \citep{...}". Cite 2–3 papers, or a table in the Supplementary, as evidence for "a few hundredths"; it is later used as the yardstick at l. 237–238. |
| 65–66 | "Many share the same last step: the learned embedding is clustered once with mclust's EEE Gaussian mixture" | Add the evidence: "Many (for example GraphST, STAGATE and SEDR) share the same last step: the learned embedding is clustered once with mclust's EEE (equal-covariance) Gaussian mixture" |
| 70–71 | "Simple training-free pipelines are also competitive" | "Simple training-free pipelines can also be competitive" |
| after 72 | — | Add a gap statement such as: "What these benchmarks do not measure is how much of the variation is caused by the clustering step itself, independent of the encoder." Without it, the novelty relative to \citet{hu2024gbbench} is unclear. |
| 77–78 | "Reproducibility: do published results reproduce with the official code (here HiSTaR's DLPFC results), and does released code select models using the labels?" | Fine. Add one closing sentence that previews the answer, which NAR introductions commonly do: "We find that a training-free baseline is among the most accurate methods, that the clustering step varies more than most differences between methods, and that released code can leak labels into model selection." |

### Materials and Methods
| Line | Original | Replacement / comment |
|---|---|---|
| 104 | "The STARmap and MERFISH annotations are those distributed with the BASS analyses" | BASS is a benchmarked method. Add: "(these annotations are independent of BASS's predictions; \todo{confirm})", or else state the potential bias in the Limitations. |
| 112–113 | "SpaGCN, GraphST and the methods added later (below) their own documented preprocessing" | "SpaGCN, GraphST and the methods listed under 'Other methods' used their own documented preprocessing of the same raw counts" (a verb is missing in the current sentence) |
| 127 | "\textbf{Methods added in the extended study}" | "\textbf{Other published methods}" (the current wording exposes the project history) |
| 133–134 | "NichePCA, SEDR, SpaceFlow and DeepST were run with three seeds per section; STAGATE, CCST, Spatial-MGCN and BASS with one seed" | Fine. Also add to the Limitations that SD comparisons (Table S8) exclude single-seed methods. |
| 144 | "All methods were run with default or published settings; none were tuned per dataset (equal tuning budgets are a topic for future work)." | This duplicates the abstract and l. 313. Delete it here and keep it in the Limitations. |
| 151 | see §3.1 | — |
| 153–154 | "\emph{Lottery}: one seed-0 embedding per section and method, clustered 20 times with a single random start each (\lotNMethods{} methods with embeddings)." | "\emph{Initialisation experiment}: one seed-0 embedding per section and method, clustered 20 times with a single random start each (\lotNMethods{} methods and baselines that output an embedding)." |
| 157 | "(\mcNMethods{} methods in the extended set, plus HiSTaR, GraphST and AnisoST)" | `\mcNMethods` = 14 already *includes* HiSTaR, GraphST and AnisoST (Table S10 has 14 rows). Replace with "(\mcNMethods{} methods and baselines with an embedding)". |
| 160 | "NMI gave the same conclusions" | "NMI gave the same ranking of methods" (be specific, or show the rank correlation) |
| 162–163 | "the reference, which was chosen after the means were seen, so this comparison is exploratory" | Good. Keep it here and in the Fig. 2 caption, and drop the third repetition at l. 184–185 ("and the reference was chosen after seeing the means, so the comparison is exploratory"). |

### Results 3.1: Accuracy (no take-home sentence at the start)
| Line | Original | Replacement |
|---|---|---|
| 172 | heading "Accuracy across methods and technologies" | "A training-free diffusion baseline is among the most accurate methods" |
| 173 | "Fig.~\ref{fig:accuracy} and Fig.~\ref{fig:matched} compare all methods under both protocols" | Fig. 2 shows only the default protocol. Write "Figure 2 compares all methods with their default clustering, and Figure 4 shows the effect of replacing it by BL20 (per-dataset values in Supplementary Table S3); Figure 5 shows example partitions." Renumber as in §7. |
| 176 | "(average over datasets \overallLin, against \overallBass{} for BASS …)" | Add "(unweighted mean of the three dataset means)". This number differs from the bootstrap estimate, which weights the 3 donors and 2 datasets equally; say so to pre-empt confusion. |
| 183 | "linear diffusion ranked first in \pBestLin{} of the resamples" | "…in 70\% of the resamples". Use a percentage macro. |
| 184–185 | "These intervals rest on \statClusters{} clusters and are wide, and the reference was chosen after seeing the means, so the comparison is exploratory." | "These intervals rest on five groups and are wide." (The exploratory caveat is already stated twice.) |
| 185–186 | "The ranking of the deep methods relative to the baselines changed with the clustering protocol (Fig.~\ref{fig:matched})." | Too vague; give an example: "The clustering protocol alone changed rankings: with BL20, NichePCA's DLPFC ARI rose from 0.32 to 0.51 and SEDR's STARmap ARI fell from 0.59 to 0.24 (Figure 4)." |
| 187 | "against 0.003--0.04 for the training-free baselines" | Fine. Move the hard-coded 0.047, 0.18 and 0.003–0.04 into macros. |
| 188–189 | "in a separate feasibility test, one DLPFC section took tens of minutes on one CPU thread for most of the neural methods and about 50 minutes for BayesSpace." | "The median time per job ranged from under 30 s for the training-free baselines and BANKSY to 40 min for CCST on one CPU thread (Supplementary Table S13)." The current sentence cites a pilot (`\timePilotBayesspace` = 52 min) that disagrees with Table S13 (31 min). |

### Results 3.2: Edge preservation
| Line | Original | Replacement |
|---|---|---|
| 223–224 | "improved accuracy on spots at layer boundaries by 0.025 (9/12 sections, $p=0.034$, uncorrected)" | "…(9 of 12 sections; Wilcoxon signed-rank $p=0.034$, uncorrected)". Name the test. Use macros, because these numbers are hard-coded. |
| 225 | "A pilot check that both baselines are invariant to transformations that should not change the answer is in Supplementary Table~\STinv." | Table S17 shows ARI 0.89–0.97 under spot permutation, so the baselines are **not** invariant. Write "A pilot check (Supplementary Table S17) showed that both baselines are invariant to rescaling, rotating and reflecting the coordinates and to rescaling expression, but not fully to spot order (ARI 0.89–0.97), because of the clustering step." Move this sentence to the R mclust subsection, where it supports the main point. |
| 227–228 | "We report this as a negative result for the edge-preserving variant; the simpler linear diffusion was the more robust baseline." | "…; the simpler linear diffusion was the more reliable baseline across technologies." ("Robust" is overloaded.) |
| — | placement | This subsection breaks the accuracy → robustness → reproducibility flow. Either shorten it to three sentences at the end of 3.1, or move it to the Supplementary. |

### Results 3.3: Initialisation
| Line | Original | Replacement |
|---|---|---|
| 230 | heading "Robustness to the clustering initialisation" | "Random initialisation of the clustering step changes ARI by up to 0.60 on a fixed embedding" |
| 233–234 | "the mean range was \lotLo{} for \lotLoName{} and \lotHi{} for \lotHiName{} (Fig.~\ref{fig:robust}a)" | The figure orders methods by the **median** and draws the median, while the text quotes **means**. Quote medians in the text (Table S9 has them), or add the mean to the figure. |
| 236–239 | "would inflate a reported result by about as much as the gap between most published methods" | "would inflate a reported result by \lotOracle{} ARI on average, more than the improvements of a few hundredths typically reported between successive methods (Introduction)". Also "explicitly or by trying a few seeds" → "explicitly or implicitly by trying several seeds" (best-of-20 is not "a few"). |
| 239 | "every fit is shown in Supplementary Fig.~\SFlottery" | Supp. Fig. S1 shows HiSTaR, GraphST and AnisoST only. Either extend S1 to all 14 methods, or write "every fit for three representative methods is shown in Supplementary Figure S1". |

### Results 3.4: R mclust
| Line | Original | Replacement |
|---|---|---|
| 254 | heading | "R mclust's answer depends on spot order and negligible noise" |
| 258 | "on DLPFC the mean was \mcPermMeanDlpfc{} and on MERFISH \mcPermMeanMerfish" | Add: "whereas on STARmap permutation had no effect (\mcPermMeanStarmap) but 1\% noise did (\mcJitMeanStarmap)". This is otherwise invisible: in the robustness figure, panel b, every STARmap point is stacked at 0. |
| 261–262 | "its log-likelihood was at least as high in only \mcLLfrac\% of cases" | Fine. "in only 34% of embeddings" is clearer. |

### Results 3.5: Likelihood selection (overclaim)
The heading "Choosing fits by likelihood is not a remedy" overstates the evidence. The like-for-like test in Supplementary Table S9 ("best-likelihood minus mean") shows that within the same model, the best-likelihood fit beat the average single start for 11 of 14 methods (`\lotBLUp` = 10 with a threshold, `\lotBLDown` = 3). The 6-of-12 comparison at l. 268 changes the algorithm *and* the number of starts at the same time; the Table S11 caption admits this.

| Line | Original | Replacement |
|---|---|---|
| 266 | "Choosing fits by likelihood is not a remedy" | "Selecting fits by likelihood helps on average but not reliably" |
| 267–268 | "A natural fix is to run many starts and keep the most likely fit. It helped some methods and hurt others." | "A natural fix is to run many starts and keep the most likely fit. On the same embedding and model, this beat the average single start for \lotBLUp{} of \lotNMethods{} methods and was worse for \lotBLDown{} (Supplementary Table S9)." |
| 268–269 | "raised mean ARI for \nGainPos{} of \nGainTot{} methods and lowered it for \nGainNeg." | Table S11 lists 7 positive changes (BANKSY λ = 0.8 is +0.003) and 5 negative. Either set `\nGainPos` = 7, or write "raised mean ARI by more than 0.005 for 6 of 12 methods, lowered it for 5 and left one unchanged". The abstract has the same problem. |
| 271 | "The reason is visible in Fig.~\ref{fig:robust}" | "The reason is visible in Figure 3C" (after renumbering) |
| 274 | "Better optimisation of the mixture model is therefore not the same as better domains." | Good take-home; keep it. |

### Results 3.6: HiSTaR
| Line | Original | Replacement |
|---|---|---|
| 276 | heading | "HiSTaR's published DLPFC accuracy was not reproduced with its official code" |
| 278 | "95\% bootstrap CI 0.454--0.525" | State the resampling unit (sections), which is not hierarchical like the rest of the paper; or use the donor-level bootstrap. |
| 280–281 | `\todo{verify the reported values…}` | Must be resolved. Until it is, remove "0.65" from the abstract. |
| 283–284 | "the robustness results above show that the clustering step alone produces differences of this size" | "the robustness results above show that the clustering step alone can produce per-section differences of this size". A per-section range of 0.18 is not a 0.14 shift in a 12-section median. |
| 284 | `\todo{Report the outcome of contacting the authors.}` | Must be resolved. NAR reviewers will expect the authors to have been contacted. |

### Results 3.7: Label use
| Line | Original | Replacement |
|---|---|---|
| 286 | heading "Reproducibility and label use in released code" | "Released code of one method selects the reported epoch using the labels" |
| 287 | `\todo{Contact the Spatial-MGCN authors…}` | Must be resolved before submission. Supplementary Note 5 also says "authors … have not yet been contacted". |
| 293 | "An automated screen of all released repositories" | Table S16 includes SPARK, SpatialPCA and conST, which are not benchmarked, and omits HiSTaR and NichePCA. Write "An automated screen of the released repositories of 14 methods" and explain the selection in Supplementary Note 5. |

### Discussion
| Line | Original | Replacement |
|---|---|---|
| 297–298 | "a training-free diffusion baseline matched or outperformed every deep encoder we tested" | "Matched" was not shown: no equivalence test passed. Write "a training-free diffusion baseline had a higher mean ARI than every deep encoder with its default clustering, and than 8 of 13 comparators with BL20 (the rest unresolved)". |
| 300 | "the R implementation used by most published methods changed its answer when the spots were merely reordered" | Only GraphST, STAGATE and SEDR (plus HiSTaR's official pipeline) use R mclust here. Write "the R mclust implementation used by several widely used methods". |
| 301–302 | "Reproducibility was limited by both the clustering step and by choices in released code" | "Reproducibility was limited both by the clustering step and by choices in released code" (fixes the doubled "by") |
| 303–304 | "add a direct, quantitative measurement of clustering variance on fixed embeddings across a broader set of methods" | "add a direct measurement of clustering variance on fixed embeddings for 14 methods across three technologies" ("broader" than what?) |
| after 304 | — | Add 3–4 sentences of **interpretation**: why smoothing on a 6-NN graph is enough on layered tissues; why MERFISH differs (cell types versus regions; see Figure 3C); what a practitioner should choose. The Discussion currently restates Results and goes straight to recommendations. |

**Recommendations (l. 306–311).** These are good and actionable. Suggested changes:
- Present them as a numbered box or table, and give each recommendation its evidence pointer: (1) → Figure 3A,B; (2) → Results 3.7 and Table S15; (3) → Tables S8–S10; (4) → Figure 4 and Table S11; (5) → Table S13.
- (3) "(or input permutations)" → "and, for R mclust, input permutations".
- Add (6): "Release per-run results and seeds so that variance can be recomputed."
- Add (7): "If fits are selected, use a label-free criterion and report how often it agrees with ARI."

**Limitations (l. 313–319).** These are honest; add:
- "The reference baseline was chosen after the means were seen, and the comparisons with it are exploratory."
- "The training-free baselines were scored with BL20 while other methods used their default clustering" (if this remains the case after §3.2 is resolved).
- "Methods were run with one or three seeds, so seed variance is unavailable for four methods."
- "All runs were on CPU; run times are not representative of GPU use."
- "ARI is the primary metric; other metrics are in Supplementary Table S12."
- "The STARmap and MERFISH annotations were distributed with the BASS analyses" (make this explicit instead of the generic l. 319).
- Small fix, l. 316: "The lottery and mclust experiments use one embedding per section and method" → "The initialisation and R mclust experiments use one seed-0 embedding per section and method, so they do not include training-seed variance."

### Other TODOs (all visible in the PDF)
l. 23–27 (authors and affiliations), 46 (URL/DOI), 280, 284, 287, 325 (CRediT), 328–330 (AI statement; keep the substance, it is appropriate), 342 (Funding). In the Supplementary: the Table S2 commit "TO RECORD", Table S14 "to be verified", the Table S12 "still running" caption, and Note 5 "not yet been contacted".

---

## 5. Supplementary-specific edits

| Item | Problem | Fix |
|---|---|---|
| Note 1 | The order is "normalised … log-transformed and reduced to 2000 HVGs", but main l. 108–109 selects HVGs first (Seurat v3 on counts) | Make the two descriptions identical |
| Note 5 | "six patterns of label use", but Table S16 has L1–L5 | "five patterns" |
| Table S2 | "banksy"; "TO RECORD"; `package_default` and `our_rule` run into the next column; "Own clustering" contradicts main l. 149 | Clean the generator: proper names, a commit for HiSTaR, human-readable "package default" / "fixed rule", widen the column |
| Table S9 | "20 sections per method" | Fine. Rename "Best minus mean" to "Best-by-ARI minus mean" |
| Table S10 | "Range: median over sections", while the main text quotes means | Add mean columns, or align the text |
| Table S11 | 7 positive changes against the text's "6" | see §4, Results 3.5 |
| Table S12 | Caption "CCST, DeepST and BayesSpace are still running and are not yet included" contradicts the rows present; DeepST has 20 runs and BayesSpace 12, against 60 for the others | Update the caption and note the unequal runs |
| Table S16 | Repos not in the benchmark (SPARK, SpatialPCA, conST); "Banksy_py" spelling | Explain, or drop |
| Table S17 | Internal labels (`pca_gmm`, `linear_diffusion`, `anisost`, "rotate coords 37deg") | Use "PCA", "Linear diffusion", "AnisoST", "rotate coordinates by 37°" |
| Table S18 | Lowercase header "method"; "lottery"; "invariance tests 0/20" for most methods reads like failure | "Method"; "initialisation experiment"; mark "not run" |
| Fig. S1 | Shows 3 methods, but the main text says "every fit"; axis tick labels about 5 pt | Extend to 14 methods across 2–3 pages, or change the text; enlarge the fonts |
| Fig. S2 | "the training-free baseline" is ambiguous; "Edge-scale quantile q" is an AnisoST parameter, the others are linear diffusion's; the caption does not say which sections | "Sensitivity of linear diffusion (T, k, number of PCs, α) and AnisoST (q) on the 12 DLPFC sections…"; state that the dashed line is HiSTaR's mean |
| Fig. S3 | Test not named; n not stated; "p = 1.000"; "Anisotropic" vs "AnisoST"; DejaVu font unlike the other figures | "Wilcoxon signed-rank test, n = 12 sections"; "p > 0.99"; rename to AnisoST; use the house font |

---

## 6. Figure-by-figure fixes

**General measurements.** At 17.5 cm (496 pt) wide, the source figure PDFs are 17.5 cm (Fig. 1), 18.2 cm (Fig. 2), 18.6 cm (robustness), 18.9 cm (protocol) and 16.6 cm (maps). When placed at `\linewidth` they are scaled by 1.00, 0.96, 0.94, 0.92 and 1.05.

Text bounding-box heights measured with `pdftotext -bbox` and scaled to print size (glyph size is about 0.85 × bbox):

| Figure | Smallest text (bbox, after scaling) | Comment |
|---|---|---|
| Fig. 1 | 5.5 pt (axis 0.20/0.45/0.70; "HiSTaR on DLPFC section 151669"; grey sub-captions 5.8–5.9 pt) | **below 6 pt** |
| Fig. 2 | 6.4–6.6 pt (P(best), legend) | borderline |
| Robustness | 6.3 pt (legend, dataset labels) | borderline |
| Protocol | 6.7 pt | OK |
| Maps | 7.7 pt | OK |

**Action for all figures.** Export every figure at exactly 17.5 cm width, or 8.4 cm for single column, so no scaling occurs. Set a 7 pt minimum and 8 pt for axis labels. Use uppercase panel letters A, B, C in 9–10 pt bold, as NAR requires. Keep vector PDF output.

**Colour.** The family palette (blue #2A78D6, vermilion #EB6834, green #1BAF7A) is reasonably safe for colour blindness: simulated deutan/protan ΔE is above 25 between all pairs. The problem is that the same three colours carry four different meanings across the paper; see the per-figure fixes.

### Fig. 1, study design (`nar_fig1_pipeline_v2`)
1. **Caption and panel labels disagree.** The caption numbers panels (1)–(5), but the figure is labelled **a–e**. Rewrite the caption with **A–E**.
2. **Text is too small and too faint.** The grey secondary text (about #9a9a9a; "Same embedding", "R mclust plus noise", "Versus own method", "ARI NMI and AMI", "Cells and RNA molecules") is 4.7–5 pt glyph and low-contrast. Raise it to at least 6.5 pt and darken it to #595959 or darker.
3. **Panel E lists lack commas.** "ARI NMI and AMI" → "ARI, NMI and AMI"; "macro F1 CHAOS and PAS" → "macro-F1, CHAOS and PAS".
4. **The neuron icon is in the wrong panel.** The neuron with "Layers L1 to L6 and white matter" sits in column B but describes the DLPFC annotation in A. Move it under the Visium inset in A, or delete it.
5. **Panel B implies every method uses one graph.** The text "Expression profiles / 6-nearest-neighbour graph" and the caption l. 86 ("linked to its six nearest neighbours") suggest all methods use this graph, but BANKSY uses 18 neighbours and SpaGCN a radius. Caption: "(B) … the baselines use the six-nearest-neighbour graph; other methods build their own as documented."
6. **"Colours used throughout" is false.** Panel E's bootstrap tree also colours its leaves blue, orange and green, and those leaves are donors and datasets, not families. Make the tree nodes grey.
7. **Family counts are unexplained.** "9 / 4 / 3" counts BANKSY once, but the analyses use BANKSY at two λ values; add "BANKSY (λ = 0.2, 0.8)". Rename the families to match Fig. 2 (§3.3). NichePCA's placement under "Statistical / Bayesian" should be justified or moved.
8. **Panel D's inset strip is unreadable.** The "ARI of 20 random starts" strip has 5.5 pt ticks and dots that overlap. Enlarge it, or drop the axis and annotate only the extremes, as now with "ARI 0.23 / ARI 0.67".
9. **The caption is long and procedural.** Cut it to about 90 words, and move the icon credits to the end as now.

### Fig. 2, accuracy (`nar_fig2_accuracy`)
1. **The caption's statement about baselines is wrong for AnisoST.** "(training-free baselines: their 20-start clustering)" does not hold: the panel A row for AnisoST shows its 3-start "own" values (0.53/0.56/0.38), not BL20 (0.55/0.62/0.36). Resolve this per §3.2.
2. **The row count does not match the text.** "14 of 16" includes BayesSpace, but BayesSpace is omitted from the figure. Readers who count the panel B rows find 13 filled out of 15. Add a BayesSpace row in B, marked "DLPFC only", or caption: "BayesSpace (DLPFC only; Δ = +0.121, interval above zero) is in Supplementary Table S5."
3. **Panel A has no colour key.** Add a colour bar (ARI 0–0.8) or state "cell shade proportional to ARI".
4. **Panel B wording.** The title "Difference to the reference, 95% CI" → "Linear diffusion minus method, 95% bootstrap interval". The paper says "interval" elsewhere, never "CI"; keep that consistent.
5. **Panel C shows P(best) for only three rows.** State "P(best) shown when ≥ 0.01".
6. **Line widths look uneven.** In the 200-dpi render of the PDF, some interval lines (BASS, BANKSY λ = 0.8, CCST) look thinner than others. If the width encodes something (seed count?), define it; otherwise make them uniform.
7. **Family legend names** must match Fig. 1 (§3.3).
8. **The caption lacks n.** Add "n = 20 sections (12 DLPFC, 3 STARmap, 5 MERFISH); values are means over seeds (1–3 per method; Supplementary Table S18)."

### Robustness figure (`nar_fig3_robustness`, currently printed as Fig. 5)
1. **Renumber** it as Figure 3 (§7).
2. **Colour clash.** Blue, orange and green here mean DLPFC, STARmap and MERFISH, but the same colours mean families in Figs 1 and 2. Use a distinct dataset palette, for example black, grey and light grey, or three shapes (circle, triangle, square). Alternatively, reserve the family colours for families throughout and use shape for dataset.
3. **Panel B hides STARmap.** Every STARmap point is stacked at x = 0 (permutation range 0.00). Add to the caption: "STARmap ranges are all zero and overlap at the axis."
4. **Panel C has no colour key, no row labels and no n.** Add a diverging colour bar (−1 to +1). Add "rows as in A". Give n per cell (12, 3 and 5 sections). Note that the STARmap medians rest on 3 correlations.
5. **The caption does not explain the ordering.** It says "Methods are ordered by the median range in **a**", but the text quotes means; align them (§4, Results 3.3).
6. **The caption's n is incomplete.** "(14 methods with embeddings; one dot per section; colour: dataset)" → "(14 methods and baselines that output an embedding; one dot per section, n = 20 per method; dots jittered vertically)".
7. **"Black bars: interquartile range; open circle: median"** is good. Keep it, and add it to the in-figure legend as now.
8. **Print size.** The figure is 18.6 cm wide; re-export at 17.5 cm and raise the legend text to 7 pt.

### Protocol figure (`nar_fig4_protocol`, currently printed as Fig. 3)
1. **The caption has no panel letters**, although the figure has a, b and c. Write: "(A) DLPFC, (B) STARmap, (C) MERFISH."
2. **Third meaning for blue and orange** (higher and lower). Use a single neutral colour for the BL20 point and a direction arrow, or green and grey for up and down, so that the family colours keep one meaning.
3. **The row order is not explained.** State it, for example "ordered by mean ARI with BL20".
4. **Missing methods are only partly explained.** The caption explains SpaGCN, BASS and BayesSpace, but not why **linear diffusion and PCA** are absent; they are present in Fig. 2. Add: "The linear-diffusion and PCA baselines have only BL20 clustering and are not shown."
5. **Add n:** "Means over 12, 3 and 5 sections; methods with one seed (STAGATE, CCST, Spatial-MGCN) are not averaged over seeds."
6. **Width.** The figure is 18.9 cm; re-export at 17.5 cm.

### Maps (`nar_fig5_maps`, currently printed as Fig. 4)
1. **The clustering protocol is not stated.** The caption says "(seed 0)" but not which protocol. Specify "default clustering", and whether GraphST is shown with or without refinement (its 0.60 here differs from its 0.51 DLPFC mean).
2. **Panel selection is not justified.** Add "nine methods chosen to span the accuracy range" or similar. Also state that section 151673 is from donor 3 (a test section, not used for development), which pre-empts concerns about cherry-picking.
3. **Two layer pairs are hard to tell apart for colour-blind readers.** Simulated deuteranopia ΔE is about 12 for Layer 1 blue against Layer 6 purple, and about 13 for Layer 3 green against Layer 5 pink. The pairs are not adjacent, but replace Layer 6 purple with a dark teal or brown, or add layer labels on the annotation panel.
4. **Legend labels.** "Layer1 … Layer6" → "L1 … L6" to match the Methods text ("L1, L2/3…").
5. **Same palette reused.** Layer 1–3 colours repeat the family blue, orange and green. This is acceptable for a categorical map, but it is another reason to state colour meanings in every caption.
6. **Optional:** add a 500 µm scale bar. If the figure is moved, it could also become Figure 2D, since the maps illustrate accuracy.

---

## 7. Figure order and placement

The current LaTeX float order (accuracy → protocol → maps → robustness) prints Figures 2–5 in an order that matches neither the file names nor the logic of the Results.

Recommended order:
- **Figure 1:** design.
- **Figure 2:** accuracy. Optionally add the maps as panel D, or keep them as a separate figure.
- **Figure 3:** robustness (`nar_fig3`): initialisation, R mclust and likelihood–ARI.
- **Figure 4:** protocol (`nar_fig4`), cited in Results 3.5.
- **Figure 5:** maps (`nar_fig5`), or move them to the Supplementary.

Move the `figure*` environments so each follows its first citation, and cite Figure 4 first in Results 3.5, not in 3.1. Each Results subsection then has one figure that carries its message:
- 3.1 → Figure 2
- 3.3–3.4 → Figure 3A, B
- 3.5 → Figures 3C and 4
- 3.6–3.7 → Supplementary Tables S14 and S15. Consider a small Figure 6 or panel showing the Spatial-MGCN final versus label-selected epoch per dataset: it is a headline claim with no figure.

---

## 8. Evidence pointers: claims without one

| Claim | Location | Missing pointer |
|---|---|---|
| "report median ARI improvements of a few hundredths" | l. 64–65 | citations or a supplementary table |
| "Many share the same last step … mclust EEE" | l. 65–66 | list or citation |
| "inflate … by about as much as the gap between most published methods" | l. 238 | the same evidence |
| "Possible causes include per-section tuning … described in the HiSTaR supplement" | l. 282 | cite the supplement section |
| "the R implementation used by most published methods" | l. 300 | none; overclaim |
| "matched or outperformed every deep encoder" | l. 297 | Figure 2B / Table S6; "matched" unsupported |
| Run times "tens of minutes" | l. 188–189 | Table S13 numbers |
| Edge-preservation numbers | l. 223–226 | hard-coded; move to macros + Supp. Fig. S3 |

---

## 9. Graphical abstract (NAR requirement)

**Purpose:** a single message readable in about 5 seconds: *the clustering step, not the encoder, drives variation; a training-free baseline is competitive; report your clustering.* It should be one panel, landscape, with large type and at most about 25 words. Check NAR's current pixel and format specification before export.

Proposed layout, three columns read left to right, with thin arrows between them:

1. **Input (left).** Small thumbnails of the three tissues (Visium DLPFC, STARmap, MERFISH), reused from Fig. 1A, with "20 sections · 3 technologies · 16 methods" underneath.
2. **Two findings (centre, stacked).**
   - **Top, "Accuracy":** a mini forest plot of five rows (linear diffusion as reference at the top, BASS, BANKSY and two deep encoders), with the caption "Training-free diffusion ≈ best".
   - **Bottom, "Clustering lottery":** one fixed embedding with an arrow to two domain maps from the same embedding, "ARI 0.23" and "ARI 0.67" (reuse the Fig. 1D example). Beneath them a dice icon labelled "random start: ±0.18 ARI" and a shuffle icon labelled "spot order (R mclust): up to 0.37".
3. **Take-home (right).** A checklist icon with three ticks: "Report clustering protocol & variance", "Never select with labels", "Include training-free baselines".

Colours: keep the family palette for the forest plot only. Use a neutral grey for icons, and white or very light grey for the background. No panel letters and no axis numbers beyond the two ARI values.

---

## 10. Checklist of blocking items before submission
- [ ] Use the NAR template and journal title; uppercase panel letters; "Figure" citations
- [ ] Abstract ≤ 200 words that states the finding
- [ ] Graphical abstract
- [ ] Remove all `\todo` and fill in authors, CRediT, funding, URL/DOI and the AI statement
- [ ] Resolve all `VERIFY` bibliography entries
- [ ] Contact the HiSTaR and Spatial-MGCN authors and report the outcome
- [ ] Settle the "standard/own" clustering definition for the baselines, HiSTaR and BANKSY across main text, Fig. 2 and Tables S2 and S3
- [ ] Unify the protocol names ("default" / "BL20") and the family names; rename statistical "clusters" to "groups"
- [ ] Fix `\nGainPos` against Table S11; "six" against five patterns; the Table S12 caption; the Fig. S1 "every fit" claim; the "invariant" claim
- [ ] Renumber the figures, restate colour meaning per caption, add n and keys, and re-export at 17.5 cm with ≥ 7 pt text
- [ ] Soften the three overclaims (likelihood heading, "most published methods", "matched or outperformed")
