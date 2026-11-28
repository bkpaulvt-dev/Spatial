# Applies the V3 revision (SP-Ben_V1_Revision_Plan.md) to paper/main.tex, part 1: everything that does not depend on the crossed-seed,
# Cavity and boundary/size results (those are added by paper/v3_sections_part2.py). Numbers are macros (paper_macros_v3.tex, v3b).
import sys
p = "paper/main.tex"; t = open(p).read()


def rep(a, b):
    global t
    assert a in t, "NOT FOUND: " + a[:90]
    t = t.replace(a, b, 1)


rep(r"\input{../results/paper_macros_review.tex}", r"\input{../results/paper_macros_review.tex}" + "\n" + r"\input{../results/paper_macros_v3.tex}" + "\n" + r"\input{../results/paper_macros_v3b.tex}" + "\n" + r"\input{../results/paper_macros_v3c.tex}")

# ---------- Abstract (plan item 1a/1b; crossed-seed sentence is the macro \vcAbstract from part 2)
a0 = t.index(r"\abstract{"); a1 = t.index(r"\keywords{")
t = t[:a0] + r"""\abstract{Spatial domain identification methods are usually compared by small differences in adjusted Rand index (ARI), mostly on one
tissue and one run. We benchmarked \nMethodsPub{} published methods and three training-free baselines on \nSections{} sections of brain,
breast cancer and mouse embryo from four technologies, separating each learned embedding from its clustering step. Across \lotN{} fixed
embeddings, the mean ARI range over 20 single-start Gaussian mixture fits was \lotMean, and the largest range was \lotMax. \vcAbstract{} R mclust's
default fit depended on its random seed. Linear diffusion, a training-free smoothing baseline, performed well on several brain datasets. In the
exploratory overall comparison, \nRobBetter{} of \nRobTot{} unadjusted intervals and \nRobBetterBonf{} after Bonferroni adjustment favoured
diffusion, none met a $\pm$\statMargin{} ARI equivalence criterion, and without the DLPFC sections \vtNBetterN{} favoured it and \vtNWorseN{}
favoured the comparator. On three held-out whole-brain MERFISH sections from one mouse it ranked \rvAllenRankLin{} of \rvAllenNRanked{} methods,
and in a simulation its advantage over PCA fell as layered bands narrowed. Equal tuning of five training-free methods left their order unchanged.
The official HiSTaR code did not reproduce its published median (\vsHistarOffMed{} against 0.65), and one method's released test scripts select
the epoch with the labels. We recommend reporting the clustering protocol and its variance, never selecting runs with labels, and testing
baselines on several tissues.}

""" + t[a1:]

# ---------- Introduction: position the restart analysis
rep(r"""What these studies do not measure directly is how much of the variation
comes from the clustering step itself when the embedding is held fixed.""",
    r"""These studies vary the clustering algorithm or report overall sensitivity to the seed; what they do not measure directly is how much of
the variation comes from the random start of the clustering step itself when the embedding is held fixed, and how this compares with the
variation between training seeds.""")

# ---------- Figure 1 caption: known K
rep(r"""The true number of domains is given to every method.""",
    r"""The annotated number of domains $K$ is given to every method; the annotation itself is used only for scoring and in the specified
development and oracle analyses.""")

# ---------- Methods: native / port / wrapper / benchmark-assigned clustering
rep(r"""\emph{Default clustering}: the clustering step of each method's pipeline.""",
    r"""We distinguish four kinds of implementation: native code (the released package or repository), ports (HiSTaR, our PyTorch port of the
official code, also compared with the official code below; CCST, our re-implementation), wrappers (the R mclust call of GraphST and STAGATE on
the second server, equivalence-checked) and benchmark-assigned clustering (the 3-start Gaussian mixture we use as default for HiSTaR and
BANKSY, whose pipelines use R mclust and Leiden). \emph{Default clustering}: the clustering step of each method's pipeline.""")

# ---------- Results 1: exploratory framing, paired group effects, DLPFC omission, conditional ranks
rep(r"""Ranked on all \rankSections{} sections, BASS was first in""",
    r"""Because the reference was chosen after the means were inspected, these comparisons are exploratory; the Bonferroni adjustment addresses
multiplicity within the comparison family but not the post hoc choice of reference. The same records give a consistent picture when the groups
are weighted differently (Supplementary Table~\STpaired, which lists the effect in each donor and study and the eligible sections of each
contrast; seeds averaged within sections, sections paired, groups and sections resampled jointly for each pair): weighting the five datasets
equally, \vtNBetterD{} of \vtNComp{} comparisons favoured diffusion and \vtNUnresD{} were unresolved; omitting all twelve DLPFC sections (four
groups), \vtNBetterN{} favoured diffusion, \vtNWorseN{} (BASS, \vtBassN, 95\% interval \vtBassNLo{} to \vtBassNHi) favoured the comparator and
\vtNUnresN{} were unresolved. BayesSpace was compared on its 13 Visium sections only, and without DLPFC on a single section, for which no
interval is given. The overall result therefore depends on the DLPFC donors. Ranked on all \rankSections{} sections (rank frequencies are
conditional on the datasets and methods included), BASS was first in""")

# ---------- breast: both endpoints together
rep(r"""The breast cancer annotation has 20 numbered regions of four classes; scored against the four
classes with $K=4$,""", r"""The breast cancer annotation has 20 numbered regions of four histological classes (each region belongs to one class: ductal or
lobular carcinoma \emph{in situ}, invasive carcinoma, tumour edge or healthy tissue); we report both endpoints together: against the 20
regions linear diffusion reached \meanLinBrca, and scored against the four classes with $K=4$,""")

# ---------- AnisoST boundary: donor-level effects
rep(r"""(by 0.025, 9 of 12 sections, Wilcoxon signed-rank $p=0.034$, uncorrected;
Supplementary Figure~\SFboundary)""", r"""(by \vsBoundMean{} on average; \vsBoundBrA, \vsBoundBrB{} and \vsBoundBrC{} in the three donors, descriptive with three
groups; Supplementary Figure~\SFboundary)""")

# ---------- K: sensitivity centred on annotated K, scope
rep(r"""BIC did not provide a usable label-free choice: within $K\pm2$ it selected the largest value in
\kBicEdge{} of \kN{} embeddings.""", r"""As a sensitivity analysis centred on the annotated $K$, BIC within $K\pm2$ selected the upper endpoint for \kBicEdge{} of \kN{}
embeddings, so it did not provide a usable label-free choice in this range.""")
rep(r"""so the lead of the baseline
depends on giving every method the true $K$.""", r"""so the lead of the baseline depends on giving every method the annotated $K$; our conclusions apply to this known-$K$ setting.""")

# ---------- likelihood selection / Figure 5F: group-level effects
rep(r"""Replacing each method's default clustering by matched clustering changed mean ARI by more than 0.005 upwards for \nGainPos{} of
\nGainTot{} methods and downwards for \nGainNeg{} (\figref{fig:matched}; Supplementary Table~\STgain); for example HiSTaR gained
\gainHistar{} (\gainPHistar) and NichePCA \gainNichepca{} (\gainPNichepca), whereas SEDR changed by \gainSedr{} (\gainPSedr) and CCST
by \gainCcst{} (\gainPCcst), all uncorrected.""", r"""Replacing each method's default clustering by matched clustering changed the group-level mean ARI (equal weight per donor or
study) by amounts whose 95\% intervals excluded zero for only \vtNMatchedUp{} of \vtNMatched{} methods (GraphST, upwards); the others were
unresolved, from upward shifts for HiSTaR, STAGATE and NichePCA to downward shifts for SEDR and CCST (\figref{fig:matched}F; Supplementary
Table~\STgain).""")
rep(r"""(\textbf{F}) the change in mean ARI over all 24 sections when the default clustering is replaced by matched clustering (purple: matched higher; brown: matched lower; filled: Wilcoxon signed-rank $p<0.05$, uncorrected for 14 methods; the second column gives the number of sections on which matched clustering was higher).""",
    r"""(\textbf{F}) the change in mean ARI when the default clustering is replaced by matched clustering, as the equal-weight mean of the seven
donor or study effects with its 95\% hierarchical-bootstrap interval (purple: matched higher; brown: matched lower; filled: interval excludes
zero; the second column gives the number of the seven groups in which matched clustering was higher). HiSTaR and BANKSY use a
benchmark-assigned 3-start Gaussian mixture as default; SpaGCN, BASS and BayesSpace keep their internal clustering and are not shown.""")
rep(r"""The change in F is the mean over sections as quoted in the text (Supplementary Table~\STgain).""", r"""Section-level values are in Supplementary Table~\STgain.""")
rep(r"""\includegraphics[width=\linewidth]{nar_fig4_protocol.pdf}""", r"""\includegraphics[width=\linewidth]{nar_fig4_protocol_v3.pdf}""")

# ---------- Figure 3: Allen example
rep(r"""\includegraphics[width=\linewidth]{nar_fig5_maps.pdf}""", r"""\includegraphics[width=\linewidth]{nar_fig5_maps.pdf}
\includegraphics[width=\linewidth]{nar_fig3_allen_v3.pdf}""")
rep(r"""Maps for breast
cancer and Stereo-seq are in Supplementary Figure~\SFmapsnew.}""", r"""(\textbf{C}, \textbf{D}) The same for the held-out Allen MERFISH
section ABCA1-085 (the middle of the three sections chosen by the fixed anterior--posterior rule; seed 0; the nine original methods that
finished all three sections; CCF divisions as annotation). Maps for breast cancer and Stereo-seq are in Supplementary Figure~\SFmapsnew.}""")

# ---------- added methods: five complete comparisons, Novae separately
rep(r"""Zero-shot Novae, without
fine-tuning, reached \rvNovaeDlpfc{} on DLPFC and failed on the MERFISH sections.""", r"""These are five complete comparisons. Zero-shot Novae,
without fine-tuning, completed \vsNovaeN{} sections in \vsNovaeG{} groups (it failed on the MERFISH sections); paired on those sections, linear
diffusion was ahead by \vsNovaeD{} (\vsNovaeLo{} to \vsNovaeHi; Supplementary Table~\STextra).""")
rep(r"""On the 24 original sections, linear diffusion was ahead of each of the added methods that ran on every dataset:""",
    r"""On the 24 original sections, linear diffusion was ahead of each of the five added methods that ran on every dataset:""")
rep(r"""\subsection{Six further methods did not change the picture on the original sections}""", r"""\subsection{Five further methods that ran on every dataset did not change the picture on the original sections}""")

# ---------- Allen: rank among 14 with all three sections; completion; hypothesis
rep(r"""ranked \rvAllenRankLin{} of the \rvAllenNRanked{}
methods with results on all three sections,""", r"""ranked \rvAllenRankLin{} among the \rvAllenNRanked{} methods with results on all three sections
(completion by method and seed in Supplementary Table~\STallencomp),""")
rep(r"""which agrees with the single-cell results above: on single-cell data, regions are defined by cell composition,
and plain smoothing of expression is not enough.""", r"""We hypothesise, without having tested it, that on single-cell data regions are defined partly by cell composition,
which plain smoothing of expression does not capture.""")
rep(r"""\subsection{On held-out whole-brain MERFISH sections the baseline ranked fifth}""", r"""\subsection{On three held-out whole-brain MERFISH sections from one mouse the baseline ranked fifth}""")

# ---------- simulation: narrowed claims
rep(r"""The simulation supports the
explanation proposed in the first analysis: smoothing wins when domains are large and contiguous, as cortical layers are, and loses when
they are small and fragmented.""", r"""Within the band geometry the simulation isolates narrowing: under this simulator, the advantage of smoothing fell as layered
domains narrowed. The contrast between narrow bands and small random blocks also changes the geometry and fragmentation of the domains, so it
does not isolate domain size, and the tier-3 entries are single tissues with seed 0 and are descriptive. The simulation uses one expression
profile (DLPFC section 151507); tissues are paired by replicate index and resampled with replacement for each contrast.""")
rep(r"""\subsection{The advantage of smoothing depends on domain size}""", r"""\subsection{In simulation, the advantage of smoothing fell as layered domains narrowed}""")

# ---------- Table 1: both arms on the same 18 sections
rep(r"""Method & Development score, default $\to$ tuned & Test ARI, tuned & $\Delta$ (95\% interval) \\
\midrule
Linear diffusion & \rvRfiveDevALin{} $\to$ \rvRfiveDevLin & \rvRfiveTunedLin & reference \\
AnisoST & \rvRfiveDevAAnisost{} $\to$ \rvRfiveDevAnisost & \rvRfiveTunedAnisost & \rvRfiveAnisostD{} (\rvRfiveAnisostLo, \rvRfiveAnisostHi) \\
BANKSY & \rvRfiveDevABanksy{} $\to$ \rvRfiveDevBanksy & \rvRfiveTunedBanksy & \rvRfiveBanksyD{} (\rvRfiveBanksyLo, \rvRfiveBanksyHi) \\
NichePCA & \rvRfiveDevANichepca{} $\to$ \rvRfiveDevNichepca & \rvRfiveTunedNichepca & \rvRfiveNichepcaD{} (\rvRfiveNichepcaLo, \rvRfiveNichepcaHi) \\
PCA & \rvRfiveDevAPca{} $\to$ \rvRfiveDevPca & \rvRfiveTunedPca & \rvRfivePcaD{} (\rvRfivePcaLo, \rvRfivePcaHi) \\""",
r"""Method & Dev. score, untuned $\to$ tuned & Test ARI, untuned & Test ARI, tuned & Gain (95\% interval) & LD $-$ method, tuned (95\% interval) \\
\midrule
Linear diffusion & \rvRfiveDevALin{} $\to$ \rvRfiveDevLin & \vsUntunedLin & \vsTunedLin & \vsGainLin{} (\vsGainLinLo, \vsGainLinHi) & reference \\
AnisoST & \rvRfiveDevAAnisost{} $\to$ \rvRfiveDevAnisost & \vsUntunedAnisost & \vsTunedAnisost & \vsGainAnisost{} (\vsGainAnisostLo, \vsGainAnisostHi) & \rvRfiveAnisostD{} (\rvRfiveAnisostLo, \rvRfiveAnisostHi) \\
BANKSY & \rvRfiveDevABanksy{} $\to$ \rvRfiveDevBanksy & \vsUntunedBanksy & \vsTunedBanksy & unchanged setting & \rvRfiveBanksyD{} (\rvRfiveBanksyLo, \rvRfiveBanksyHi) \\
NichePCA & \rvRfiveDevANichepca{} $\to$ \rvRfiveDevNichepca & \vsUntunedNichepca & \vsTunedNichepca & \vsGainNichepca{} (\vsGainNichepcaLo, \vsGainNichepcaHi) & \rvRfiveNichepcaD{} (\rvRfiveNichepcaLo, \rvRfiveNichepcaHi) \\
PCA & \rvRfiveDevAPca{} $\to$ \rvRfiveDevPca & \vsUntunedPca & \vsTunedPca & \vsGainPca{} (\vsGainPcaLo, \vsGainPcaHi) & \rvRfivePcaD{} (\rvRfivePcaLo, \rvRfivePcaHi) \\""")
rep(r"""\begin{tabular}{lccc}""", r"""\begin{tabular}{lccccc}""")
rep(r"""Right: tuned linear diffusion minus the tuned method on the 18 test sections (three seeds), with 95\%
intervals from the hierarchical bootstrap.}""", r"""Test columns: the same \vsTabSections{} test sections and seeds 0--2 for both arms, equal weight per donor or study;
gain = tuned minus untuned; last column: tuned linear diffusion minus the tuned method; 95\% intervals from the hierarchical bootstrap. Some test
sections come from studies that also contributed development sections (DLPFC donors Br5595 and Br8100 are separate donors, but STARmap and
MERFISH test sections share their study with a development section).}""")
rep(r"""therefore not a result of tuning the baseline alone; whether tuning the deep methods would change their position was not tested.""",
    r"""therefore not a result of tuning the baseline alone; the conclusion is limited to the five training-free methods assessed, and whether
tuning the deep methods would change their position was not tested.""")

# ---------- HiSTaR: medians and paired table
rep(r"""mean ARI \rvMsixOffDef{} (median \rvMsixOffMed) with its own clustering, against \rvMsixOursDef{} for our port, and \rvMsixOffMat{} against
\rvMsixOursMat{} with matched clustering (Supplementary Table~\STextra). Our port therefore reproduces the official code, and neither
reproduces the published median of 0.65.""", r"""a median over the twelve sections of \vsHistarOffMed{} (mean \vsHistarOffMean) with its own clustering, against a median of
\vsHistarPortMed{} (mean \vsHistarPortMean) for our port in the same runner; paired by section and seed (\vsHistarPairs{} pairs; Supplementary
Table~\SThistarpairs), the official code was ahead by \vsHistarDiffMean{} on average (SD \vsHistarDiffSD). With matched clustering the means
were \rvMsixOffMat{} and \rvMsixOursMat. For these settings, neither the official code nor the port reproduced the published median of 0.65.""")

# ---------- Spatial-MGCN: code references, section lists, shared clustering seeds
rep(r"""Spatial-MGCN's released test scripts (\texttt{DLPFC\_test.py}, \texttt{HBC\_test.py}) compute ARI against the annotation at every
training epoch and keep the best epoch for reporting.""", r"""Spatial-MGCN's released test scripts (repository commit cf4412d: \texttt{DLPFC\_test.py}, line 125, and
\texttt{HBC\_test.py}, line 123) compute ARI against the annotation at every training epoch and keep the best epoch for reporting.""")
rep(r"""With three label-free stopping rules applied to the same runs (\rvAnineNsec{} sections),""", r"""The \mgcnLeakN{} sections of that
comparison are the seed-0 runs on DLPFC, STARmap and MERFISH. With three label-free stopping rules applied to the same runs (\rvAnineNsec{}
sections: all 24 except Stereo-seq E10.5 E1S1, where every seed exceeded the memory cap; three seeds; the embeddings of all three rules clustered
with the same $k$-means seed and ten starts, so that clustering randomness is shared between rules),""")
rep(r"""We do not know whether the published numbers were obtained with these scripts; we report what the released code does.""",
    r"""We did not verify whether the published numbers were obtained with these scripts; we report what the released scripts do, not the
reporting workflow of the original paper.""")

# ---------- Discussion: lead with the fixed-embedding experiment
rep(r"""We benchmarked \nMethodsPub{} published methods and three training-free baselines on \nSections{} sections from four
technologies and three tissue types and separated the learned embedding from the clustering step.""", r"""The most robust result of
this study concerns the clustering step: on \lotN{} fixed embeddings, single-start refits of the same Gaussian mixture spanned \lotMean{} ARI on
average and up to \lotMax. We benchmarked \nMethodsPub{} published methods and three training-free baselines on \nSections{} sections from four
technologies and three tissue types and separated the learned embedding from the clustering step.""")
rep(r"""The ranking of methods is therefore tissue-dependent, and a benchmark on one tissue, especially DLPFC alone, does not identify a generally best
method.""", r"""The ranking of methods therefore depends on the dataset: five of the seven primary groups are brain tissue, the breast cancer data are one
section, the embryo data come from one study and the held-out MERFISH sections from one mouse, so we make dataset-specific statements; a
general brain-versus-non-brain claim would need an independently annotated non-brain cohort with several donors. A benchmark on DLPFC alone
does not identify a generally best method.""")

# ---------- Limitations additions
rep(r"""The reference baseline was chosen after
the means were seen, and the comparisons with it are exploratory.""", r"""The reference baseline was chosen after the means were seen, and the comparisons with it are
exploratory; without DLPFC the comparisons change (Supplementary Table~\STpaired). All conclusions apply to the setting in which the annotated
number of domains is given. The provenance of every label set is in Supplementary Table~\STprov.""")

# ---------- Code availability
rep(r"""Code, download scripts with checksums, per-run results and the scripts that generate
every number, table and figure: \todo{GitHub URL and Zenodo DOI}.""", r"""Code, download scripts with checksums, environment lock files,
per-run records (host, threads, memory limit, failure reason and retries; Supplementary Table~\STfail), the commits and times of every analysis
specified before its results, and the commands that regenerate every number, table and figure are described in \texttt{docs/RELEASE.md}; a
fresh environment built from the lock file reproduced the recorded ARI and regenerated the extension numbers and Figure 6
(\texttt{results/clean\_env\_check.txt}): \todo{GitHub release URL and Zenodo DOI}.""")
open(p, "w").write(t); print("V3 part 1 applied")
