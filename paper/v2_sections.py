# Applies the V2 revision to paper/main.tex (run once from the repository root): new macros input, abstract, introduction
# sentence, Methods subsection "Extensions", five Results subsections, updated reproduction paragraphs, Discussion and Limitations.
# Every number is a macro from results/paper_macros_review.tex (scripts/paper_review_numbers.py) or results/paper_macros.tex.
import re, sys
p = "paper/main.tex"; t = open(p).read()


def rep(a, b, count=1):
    global t
    assert t.count(a) >= 1, a[:80]
    t = t.replace(a, b, count)


rep(r"\input{../results/paper_macros.tex}", r"\input{../results/paper_macros.tex}" + "\n" + r"\input{../results/paper_macros_review.tex}")

# ---------------- abstract
a0 = t.index(r"\abstract{"); a1 = t.index(r"\keywords{")
t = t[:a0] + r"""\abstract{Spatial domain identification methods are usually compared by small differences in adjusted Rand index (ARI),
mostly on one tissue and one run. We benchmarked \nMethodsPub{} published methods and three training-free baselines
on \nSections{} sections of brain, breast cancer and mouse embryo from 10x Visium, STARmap, MERFISH and Stereo-seq,
separating each learned embedding from its clustering step, and extended the benchmark with six further methods, three held-out
whole-brain MERFISH sections, a pre-registered simulation of domain size and a pre-registered equal-tuning arm. With the same clustering
for every embedding, a training-free neighbourhood-smoothing baseline (linear diffusion) had a higher mean ARI than \nRobBetter{} of
\nRobTot{} comparators and could not be separated from the other \nRobUnres{} (exploratory); it was also ahead of the six added methods.
Its lead depended on tissue and domain size: it came from brain tissue, it ranked \rvAllenRankLin{} of \rvAllenNRanked{} methods on the
held-out MERFISH sections, and in simulation its advantage over PCA fell as domains became narrower and reversed for small random
blocks, where several deep and Bayesian methods stayed accurate. Giving every training-free method the same tuning budget did not change
their order. On fixed embeddings, random restarts of the same Gaussian mixture changed ARI by \lotMean{} on average (up to \lotMax),
and R mclust's default fit depended on its random seed. Neither the official HiSTaR code nor our port reproduced its published
accuracy, and one method's released scripts select its epoch using the labels. We recommend reporting clustering protocol and variance,
never selecting runs with labels, and testing training-free baselines on several tissues and domain sizes.}

""" + t[a1:]

# ---------------- introduction: extensions sentence
rep(r"""most differences between methods, and that released code can use the labels for model selection.""",
    r"""most differences between methods, and that released code can use the labels for model selection. Because the
reference baseline was chosen after the first results were seen, we then tested the main finding in four ways that were fixed before
their results existed: six further methods, held-out whole-brain MERFISH sections, a simulation that varies domain size, and an
equal tuning budget for every training-free method.""")

# ---------------- Methods: extensions subsection (before Results)
ext = r"""
\subsection{Extensions tested after the first analysis}
These analyses were added after the first analysis was complete; each was specified in a file committed to the repository before any of
its results existed (\texttt{docs/PREREGISTERED\_SIM.md}, \texttt{docs/PREREGISTERED\_TUNING.md}, \texttt{docs/PREREGISTERED\_A9.md}). They
ran on the second server (125 GB RAM, CPU only) with a cap of 30 GB per job; jobs above the cap are reported as memory-limit failures, and
failed jobs were repeated with unchanged settings only when the failure was an infrastructure kill (peak memory below 80\% of the cap).
No setting of any earlier method was changed.

\textbf{Added methods.} CellCharter \citep{varrone2024cellcharter} (scVI latent space, neighbour aggregation over three layers, Gaussian
mixture), MENDER \citep{yuan2024mender} (tutorial workflow), SpatialPCA \citep{shang2022spatialpca} (DLPFC tutorial settings; its fast
approximation above 5000 spots), PRECAST \citep{liu2023precast} and DR-SC \citep{liu2022drsc} (package tutorials), Novae
\citep{blampey2025novae} (zero-shot use of the pretrained human or mouse model, no fine-tuning) and a multi-sample BASS fit of all sections
of a DLPFC donor or of the MERFISH animal (the authors' setting; the single-section BASS of the main benchmark is unchanged). All were run
on the 24 sections with three seeds where they apply, with their own clustering. GraphBG could not be installed (it requires a Python
version not available on the server) and is not reported.

\textbf{Held-out data.} Three coronal sections of one adult mouse brain profiled by MERFISH (Allen Brain Cell Atlas, Zhuang-ABCA-1, 1122
genes) \citep{zhang2023abca}, chosen by a fixed rule (the 25th, 50th and 75th percentile along the anterior--posterior axis among sections with
more than 20,000 cells; 26,940, 32,047 and 29,220 cells), labelled by the registration of each cell to the Allen Common Coordinate Framework
(CCF divisions; 11, 11 and 7 domains). This is a reference-atlas annotation, not derived from expression clustering. All \nMethodsPub{}
methods and the baselines ran with unchanged settings (targeted-panel path) and three seeds. Two further datasets from the SDMBench release
\citep{yuan2024benchmark}, osmFISH somatosensory cortex \citep{codeluppi2018osmfish} (one section, 33 genes) and BaristaSeq visual cortex
\citep{sun2021baristaseq} (three slices, 79 genes), are reported separately and descriptively, because the derivation of their labels is not
documented.

\textbf{Simulation of domain size.} 120~$\times$~120 lattices with six domains whose expression profiles are those of the six cortical layers
of DLPFC section 151507 (a development section), with negative binomial counts (dispersion 0.5). Geometry A repeats the six layers as bands
$m\in\{1,2,4,7\}$ times (narrower bands with larger $m$); geometry B cuts the lattice into square blocks of side $w\in\{3,5,8,12,20\}$
spot spacings with random domain labels. Five tissues per setting and three seeds per method. The primary contrast is
$\Delta=$ ARI(linear diffusion) $-$ ARI(PCA), with 95\% intervals from a bootstrap over the five tissues. Hypotheses: H1, $\Delta$ falls from
$m=1$ to $m=7$ by more than 0.03; H2, $\Delta$ is smallest for random blocks of side 3 and lower than for $m=7$ by more than 0.03. Eight
methods ran the full design; the seven most expensive (BASS, STAGATE, GraphST, DeepST, CCST, Spatial-MGCN, SpaceFlow) ran one tissue per
setting with seed 0 and are reported descriptively. SEDR failed on every simulated tissue (an error inside its R mclust call) and BayesSpace
does not apply to this lattice.

\textbf{Equal-tuning arm.} Every training-free method (linear diffusion, AnisoST, PCA, BANKSY and NichePCA) received the same budget: ten
settings fixed in advance (setting 0 is the benchmark setting; for BANKSY the grid contains both recommended $\lambda$), each run once on the
six development sections. A rule fixed in advance chose for each method the setting with the highest mean, over the three development
datasets, of the per-dataset mean ARI; the choice was committed before the tuned run, which used all 24 sections and three seeds. The primary
comparison is tuned linear diffusion minus each tuned method on the 18 test sections (six groups), with the hierarchical bootstrap above. The
deep and Bayesian methods were not tuned.

\textbf{Further checks.} (i) Spatial-MGCN with three label-free stopping rules applied to one run per section and seed: its default epoch,
a loss-plateau rule and the final epoch. (ii) The official HiSTaR code (its own environment, pinned commit) on the 12 DLPFC sections with
three seeds, against our port. (iii) Linear diffusion and DeepST rerun with seed 0 on one Stereo-seq section on the second server, to measure
the effect of the host. (iv) BayesSpace with its square-lattice platform setting on the Stereo-seq sections.
"""
rep(r"""
\section{Results}
""", ext + r"""
\section{Results}
""")

# ---------------- Results: new subsections after the K / seed / cost subsection (before Figure 2 environment)
res = r"""
\subsection{Six further methods did not change the picture on the original sections}
On the 24 original sections, linear diffusion was ahead of each of the added methods that ran on every dataset: CellCharter by
\rvCellCharterD{} ARI (95\% interval \rvCellCharterLo{} to \rvCellCharterHi), MENDER by \rvMENDERD{} (\rvMENDERLo{} to \rvMENDERHi),
DR-SC by \rvDRSCD{} (\rvDRSCLo{} to \rvDRSCHi), PRECAST by \rvPRECASTD{} (\rvPRECASTLo{} to \rvPRECASTHi) and SpatialPCA by
\rvSpatialPCAD{} (\rvSpatialPCALo{} to \rvSpatialPCAHi; Supplementary Table~\STextra). SpatialPCA was the closest on DLPFC
(\rvSpatialPCADlpfc{} against \rvLinDlpfc{} for linear diffusion in the same runner) but low on the targeted-panel data (STARmap
\rvSpatialPCAStarmap, MERFISH \rvSpatialPCAMerfish); CellCharter and MENDER were the closest on the single-cell brain data (STARmap
\rvCellCharterStarmap{} and \rvMENDERStarmap, MERFISH \rvCellCharterMerfish{} and \rvMENDERMerfish). Zero-shot Novae, without
fine-tuning, reached \rvNovaeDlpfc{} on DLPFC and failed on the MERFISH sections. The multi-sample BASS fit was more accurate than
single-section BASS on DLPFC (\rvMfiveDlpfcMulti{} against \rvMfiveDlpfcSingle) and MERFISH (\rvMfiveMerfishMulti{} against
\rvMfiveMerfishSingle; DLPFC, two jobs exceeded the memory cap) and could not be separated from linear diffusion (\rvBassMultiD,
\rvBassMultiLo{} to \rvBassMultiHi, four groups); on MERFISH it was the most accurate result of the study, which is in line with the authors'
design of BASS for multi-sample data.

\subsection{On held-out whole-brain MERFISH sections the baseline ranked fifth}
On the three Allen MERFISH sections (CCF divisions as labels), \rvAllenOk{} of \rvAllenJobs{} jobs of the original methods finished
(Supplementary Table~\STallen). Linear diffusion reached a mean ARI of \rvAllenLin{} and ranked \rvAllenRankLin{} of the \rvAllenNRanked{}
methods with results on all three sections, behind SpaceFlow (\rvAllenSpaceflow), NichePCA (\rvAllenNichepca), MENDER (\rvAllenMender)
and CellCharter (\rvAllenCellcharter), and ahead of BASS (\rvAllenBass), BANKSY $\lambda=0.8$ (\rvAllenBanksyHi), STAGATE
(\rvAllenStagate), HiSTaR (\rvAllenHistar), AnisoST (\rvAllenAnisost) and PCA (\rvAllenPca). With three sections from one animal these
are descriptive means without intervals. Several methods did not complete: GraphST (8 of 9 jobs) and Spatial-MGCN (9 of 9) exceeded the
30 GB cap, as did 3 of 9 DeepST jobs; SEDR (an error in its R mclust call) and SpaGCN (its length-scale search did not converge on these
coordinates) failed on every job; and 7 jobs (DeepST 3, CCST 3, BASS 1) were stopped by the server and failed again on every repeat. The
methods that ranked ahead of the baseline aggregate neighbourhood composition (NichePCA, MENDER, CellCharter) or learn with spatial
regularisation (SpaceFlow), which agrees with the single-cell results above: on single-cell data, regions are defined by cell composition,
and plain smoothing of expression is not enough. On the osmFISH and BaristaSeq sections, whose labels are of undocumented origin, results
are given in Supplementary Table~\STsdm{} without interpretation.

\subsection{The advantage of smoothing depends on domain size}
In the simulation (\figref{fig:sim}; \rvSimN{} finished jobs), linear diffusion recovered wide layered bands almost perfectly (ARI
\rvSimFullLinAone{} at $m=1$, against \rvSimFullPcaAone{} for PCA), and its advantage over PCA fell steadily as the bands narrowed, to
\rvSimDAseven{} at $m=7$: $\Delta(m=1)-\Delta(m=7)=\rvSimHone$ (95\% interval \rvSimHoneLo{} to \rvSimHoneHi; H1 supported). On random blocks
of side 3, smoothing was harmful: linear diffusion reached \rvSimFullLinBthree{} against \rvSimFullPcaBthree{} for PCA ($\Delta$
\rvSimDBthree), and the contrast with $m=7$ was \rvSimHtwo{} (\rvSimHtwoLo{} to \rvSimHtwoHi; H2 supported); the advantage returned as the
blocks grew (\rvSimDBtwenty{} at $w=20$). The edge-preserving variant AnisoST did not collapse on small blocks (\rvSimFullAnisostBthree{} at
$w=3$), and several deep and Bayesian methods also stayed accurate there in the reduced design (one tissue, seed 0, no interval): DeepST
\rvSimRedDeepstBthree, STAGATE \rvSimRedStagateBthree, GraphST \rvSimRedGraphstBthree{} and BASS \rvSimRedBassBthree, whereas CCST
(\rvSimRedCcstBthree), Spatial-MGCN (\rvSimRedMgcnBthree) and SpaceFlow (\rvSimRedSpaceflowBthree) did not. The simulation supports the
explanation proposed in the first analysis: smoothing wins when domains are large and contiguous, as cortical layers are, and loses when
they are small and fragmented. In this simulation domains differ only by expression and not by cell composition, so it does not address the
single-cell results above.

\begin{figure*}[t]
\centering
\includegraphics[width=\linewidth]{nar_fig6_simulation.pdf}
\caption{Pre-registered simulation of domain size (120~$\times$~120 spots, six domains with the expression profiles of the six layers of DLPFC
section 151507). (\textbf{A}, \textbf{B}) Mean ARI of the eight methods of the full design (five tissues $\times$ three seeds per setting)
against the number of band repeats $m$ (A; larger $m$ = narrower bands) and the side $w$ of random square blocks (B). (\textbf{C}) Linear
diffusion minus PCA per setting with 95\% intervals from a bootstrap over the five tissues (blue: above zero). (\textbf{D}) The seven most
expensive methods in the reduced design (one tissue per setting, seed 0): single values, no interval. SEDR failed on every tissue and is
not shown.}
\label{fig:sim}
\end{figure*}

\subsection{Equal tuning of the training-free methods did not change their order}
When each training-free method chose one of ten settings on the development sections (Table~\ref{tab:tuning}), linear diffusion chose 15
instead of 30 principal components, AnisoST a larger neighbourhood and more steps, NichePCA four instead of six neighbours, PCA 50
components, and BANKSY kept its benchmark setting. On the 18 test sections the tuned settings changed accuracy little (tuning gain of
linear diffusion \rvRfiveGainLin, 95\% interval \rvRfiveGainLinLo{} to \rvRfiveGainLinHi; AnisoST \rvRfiveGainAnisost; NichePCA
\rvRfiveGainNichepca): the gains seen on the development sections did not carry over. Tuned linear diffusion ranked first
(\rvRfiveTunedLin), followed by AnisoST (\rvRfiveTunedAnisost), BANKSY (\rvRfiveTunedBanksy), NichePCA (\rvRfiveTunedNichepca) and PCA
(\rvRfiveTunedPca); it was ahead of tuned PCA (\rvRfivePcaD, \rvRfivePcaLo{} to \rvRfivePcaHi) and could not be separated from tuned
AnisoST (\rvRfiveAnisostD, \rvRfiveAnisostLo{} to \rvRfiveAnisostHi), BANKSY (\rvRfiveBanksyD, \rvRfiveBanksyLo{} to \rvRfiveBanksyHi)
or NichePCA (\rvRfiveNichepcaD, \rvRfiveNichepcaLo{} to \rvRfiveNichepcaHi). The advantage of the baseline among training-free methods is
therefore not a result of tuning the baseline alone; whether tuning the deep methods would change their position was not tested.

\begin{table}[t]
\caption{Equal-tuning arm: ten settings per method on the six development sections (seed 0); score = mean over the three development
datasets of the per-dataset mean ARI. Right: tuned linear diffusion minus the tuned method on the 18 test sections (three seeds), with 95\%
intervals from the hierarchical bootstrap.}
\label{tab:tuning}
\centering\small
\begin{tabular}{lccc}
\toprule
Method & Development score, default $\to$ tuned & Test ARI, tuned & $\Delta$ (95\% interval) \\
\midrule
Linear diffusion & \rvRfiveDevALin{} $\to$ \rvRfiveDevLin & \rvRfiveTunedLin & reference \\
AnisoST & \rvRfiveDevAAnisost{} $\to$ \rvRfiveDevAnisost & \rvRfiveTunedAnisost & \rvRfiveAnisostD{} (\rvRfiveAnisostLo, \rvRfiveAnisostHi) \\
BANKSY & \rvRfiveDevABanksy{} $\to$ \rvRfiveDevBanksy & \rvRfiveTunedBanksy & \rvRfiveBanksyD{} (\rvRfiveBanksyLo, \rvRfiveBanksyHi) \\
NichePCA & \rvRfiveDevANichepca{} $\to$ \rvRfiveDevNichepca & \rvRfiveTunedNichepca & \rvRfiveNichepcaD{} (\rvRfiveNichepcaLo, \rvRfiveNichepcaHi) \\
PCA & \rvRfiveDevAPca{} $\to$ \rvRfiveDevPca & \rvRfiveTunedPca & \rvRfivePcaD{} (\rvRfivePcaLo, \rvRfivePcaHi) \\
\bottomrule
\end{tabular}
\end{table}
"""
rep(r"""
\begin{figure*}[t]
\centering
\includegraphics[width=\linewidth]{nar_fig2_accuracy.pdf}""", res + r"""
\begin{figure*}[t]
\centering
\includegraphics[width=\linewidth]{nar_fig2_accuracy.pdf}""")

# ---------------- HiSTaR: official code
rep(r"""We report these numbers to document what our port of the released code and its defaults reproduce (we did not run the official code), not to question the method itself.""",
    r"""The official code, run in its own environment with the published defaults (\rvMsixN{} sections, three seeds), gave the same picture:
mean ARI \rvMsixOffDef{} (median \rvMsixOffMed) with its own clustering, against \rvMsixOursDef{} for our port, and \rvMsixOffMat{} against
\rvMsixOursMat{} with matched clustering (Supplementary Table~\SThistar). Our port therefore reproduces the official code, and neither
reproduces the published median of 0.65. We report these numbers to document what the released code and its defaults give, not to question
the method itself.""")

# ---------------- Spatial-MGCN: stopping rules
rep(r"""An automated screen of the released""",
    r"""With three label-free stopping rules applied to the same runs (\rvAnineNsec{} sections), Spatial-MGCN reached \rvAnineF{} with its default
epoch, \rvAnineP{} with a loss-plateau rule and \rvAnineL{} at the final epoch, against \rvAnineLab{} with the label-selected epoch: no
label-free rule recovers the reported accuracy (plateau minus default \rvAninePF, 95\% interval \rvAninePFLo{} to \rvAninePFHi). An automated screen of the released""")

# ---------------- cross-host sentence in compute paragraph
rep(r"""so host and seed are confounded for that section.""",
    r"""so host and seed are confounded for that section. Rerunning seed 0 on the second server gave the same ARI for linear diffusion
(difference \rvAtenLin) and a difference of \rvAtenDeepst{} for DeepST, so the host effect is of the size of seed variation for that method.""")

# ---------------- Discussion: new paragraph after first paragraph
rep(r"""
Why does simple smoothing do so well on brain tissue?""", r"""
The extensions, each fixed before its results existed, refine this picture without reversing it. Six further methods were behind the
baseline on the original sections, and equal tuning of the training-free methods left linear diffusion first among them. But on held-out
whole-brain MERFISH sections with atlas labels, four methods that model neighbourhood composition or regularise a learned embedding were
ahead of it, and in simulation its advantage over PCA disappeared as domains narrowed and reversed for small random blocks, where an
edge-preserving variant and several deep and Bayesian methods remained accurate. The baseline is therefore a strong reference for tissues
with large, contiguous domains, not a generally best method.

Why does simple smoothing do so well on brain tissue?""")
rep(r"""Neighbourhood-composition methods such as CellCharter
\citep{varrone2024cellcharter} and MENDER \citep{yuan2024mender} take a related smoothing-like view.""",
    r"""Neighbourhood-composition methods such as CellCharter \citep{varrone2024cellcharter} and MENDER \citep{yuan2024mender} take a related
view; they were behind the baseline on the original sections but ahead of it on the whole-brain MERFISH sections.""")
rep(r"""(4) Compare encoders under the same clustering, include training-free baselines such as neighbourhood smoothing, and evaluate on
more than one tissue""", r"""(4) Compare encoders under the same clustering, include training-free baselines such as neighbourhood smoothing, and evaluate on
more than one tissue and on domains of different size""")

# ---------------- Limitations
rep(r"""All methods were run with default or published settings, without a tuning budget, so the results do not show what each method can
reach with its authors' own tuning (we could not reproduce HiSTaR's per-section tuning).""",
    r"""The published deep and Bayesian methods were run with default or published settings, without a tuning budget; the equal-tuning arm
covered only the training-free methods, so the results do not show what each deep method can reach with tuning (we could not reproduce
HiSTaR's per-section tuning).""")
rep(r"""Slide-seq, Xenium and Visium HD data and sections with more than about 20,000 spots are not covered, and no simulated data were used.""",
    r"""Slide-seq, Xenium and Visium HD data are not covered; the held-out MERFISH sections (up to 32,047 cells) come from one animal, several
methods did not finish on them, and their means are descriptive. The simulation varies domain size and shape but not cell composition, and its
deep methods ran a reduced design without intervals. SEDR failed on the held-out and simulated data with an error in its R mclust call, which we
did not modify.""")
rep(r"""SpatialPCA and PRECAST, cited in the Introduction, were not benchmarked in this study.""",
    r"""SpatialPCA, PRECAST, DR-SC, CellCharter, MENDER and Novae were added after the first analysis and ran in the standardised runner only,
with their own clustering; GraphBG could not be installed.""")

# ---------------- Data availability
rep(r"""Exact file URLs, repository commits""", r"""Allen MERFISH (Zhuang-ABCA-1) and CCF registration: Allen Brain Cell Atlas
(\url{https://portal.brain-map.org/atlases-and-data/bkp/abc-atlas}) \citep{zhang2023abca}. osmFISH and BaristaSeq: SDMBench release
(Figshare articles 22565194 and 22550074) \citep{yuan2024benchmark}. Exact file URLs, repository commits""")
open(p, "w").write(t)
print("V2 edits applied")
