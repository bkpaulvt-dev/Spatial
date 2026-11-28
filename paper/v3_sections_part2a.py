# V3 part 2a: real-tissue boundary-distance and domain-prevalence analysis (results/v3_boundary_size.json; macros \vc...).
p = "paper/main.tex"; t = open(p).read()
a = r"""The edge-preserving variant AnisoST did not improve on linear diffusion overall"""
assert a in t
t = t.replace(a, r"""Where on the tissue does smoothing gain? Scoring each annotated spot or cell as correct when its cluster maps to its
domain under a one-to-one matching, and comparing linear diffusion with PCA on all 24 sections (three seeds; Supplementary Table~\STbound),
the gain of diffusion was small next to annotation boundaries (\vcBoundOne{} accuracy for spots one spacing from another domain, equal-weight
mean of the seven groups) and grew with the distance from the boundary (\vcBoundTwo{} at two spacings, \vcBoundMid{} at three to four,
\vcBoundFar{} at five to eight and \vcBoundDeep{} beyond eight). In the breast cancer section and the Stereo-seq sections the gain was close
to zero or negative at every distance (beyond eight spacings \vcBoundDeepBrca{} and \vcBoundDeepStereo{}). Domain prevalence showed no
consistent pattern (\vcPrevSmall{} for domains with less than 5\% of the spots, in the \vcPrevSmallN{} groups that have them, against
\vcPrevLarge{} for domains above 20\%). The six-nearest-neighbour graph spans about one spot spacing on Visium (median \vcKnnVisium{}~\textmu m)
and two to three cell spacings on STARmap and MERFISH, and ten smoothing steps reach further. Smoothing therefore helps mainly in domain
interiors, which large layered domains have in abundance, rather than at boundaries.

The edge-preserving variant AnisoST did not improve on linear diffusion overall""", 1)
b = r"""Why does simple smoothing do so well on brain tissue? On layered tissue such as cortex, domains are large, contiguous regions, and
averaging each spot with its neighbours removes most of the sampling noise that separates spots of the same layer;"""
assert b in t
t = t.replace(b, r"""Why does simple smoothing do so well on brain tissue? On layered tissue such as cortex, domains are large, contiguous regions, and
averaging each spot with its neighbours removes most of the sampling noise that separates spots of the same layer; consistent with this,
its gain over PCA was concentrated in domain interiors and small at boundaries;""", 1)
open(p, "w").write(t); print("part 2a applied")
