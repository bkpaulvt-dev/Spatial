# Revision V3 (reviewed draft "SP-Ben-Main_v0" = paper/versions/V2): work plan and frozen analysis specifications

Source: `SP-Ben_V1_Revision_Plan.md` (four AI reviews, major revision, mean 6.75/10). Output: paper/versions/V3, exported also as
`SP-Ben-Main_v1.pdf`. Written 2026-11-28 before the new analyses below were run. Each item: action, evidence file, status.

## Item 1: main claim and ranking analysis (re-analysis of existing records, no new runs)
- 1a Abstract/Discussion lead with the fixed-embedding restart experiment (mean of within-embedding ranges 0.16 over 336 embeddings; max 0.60).
- 1b Linear diffusion result labelled exploratory; 8/16 unadjusted, 3 Bonferroni, none equivalent within +-0.03.
- 1c `scripts/v3_paired_effects.py`: per-group paired effects, group-weighted, dataset-weighted (5 datasets equal), full DLPFC omission;
  joint resampling per pair; eligible sections/groups per contrast; BayesSpace own denominator (single group without DLPFC: no interval).
- 1d Figure 5F and AnisoST boundary: group-level effects (7 groups; 3 donors for the boundary result); descriptive where < 3 groups.
- 1e Added methods: five complete comparisons; Novae separate, paired on its completed sections. Table 1: untuned and tuned on the same
  18 test sections, same seeds; note that test sections share studies with development sections.

## Item 2: crossed-seed experiment
Frozen in `docs/PREREGISTERED_CROSSED_SEED.md` (commit 964eb10, before any run). Known-K: Figure 1/Methods state that K is supplied;
BIC sweep described as a sensitivity centred on the annotated K (329/336 at the upper endpoint; diffusion third); claims scoped to known K.

## Item 3: biological interpretation
- 3a Annotation provenance table (source, derivation, granularity, dependence on benchmarked methods) for every label set.
- 3b **Cavity sensitivity (frozen here):** the 16 original methods (BayesSpace does not run on bin50) are rerun with seed 0 on the three
  Stereo-seq sections with unchanged settings (stage `cavity_rescore`, 48 jobs); each saved prediction is scored (i) on all annotated bins and
  (ii) with Cavity bins excluded from scoring only (prediction and graph unchanged). Reported: ARI both ways per method and section, the
  change, and linear diffusion's rank both ways; coverage table. A rerun that excludes Cavity bins from the graph is NOT done (not claimed).
- 3c **Boundary and domain-size analysis (frozen here):** on all 24 sections, linear diffusion and PCA (benchmark settings, matched
  clustering = 20-start GMM, seeds 0-2; both deterministic given the seed, recomputed in `scripts/v3_boundary_size.py` and checked against the
  benchmark ARI). Per annotated spot: correct = its predicted cluster maps to its annotated domain under the Hungarian matching of clusters to
  domains that maximises total overlap (one-to-one; unmatched clusters count as wrong). Distance to the nearest spot of another annotated
  domain, in units of the median nearest-neighbour spacing; bins 1, 2, 3-4, 5-8, > 8. Domain prevalence = share of annotated spots; bins
  < 5%, 5-10%, 10-20%, > 20%. Effect = accuracy(diffusion) - accuracy(PCA) per bin, mean over seeds, then per group (3 donors + 4 datasets),
  reported per group and as the equal-weight group mean (descriptive; no test). Effective neighbourhood: median 6-NN distance in spacings and,
  where the unit is physical (Visium 100 um spacing; STARmap/MERFISH micrometres), in micrometres.
- 3d Figure 3: an Allen MERFISH example (section ABCA1-085, the middle section by the fixed selection rule; seed 0) from existing predictions.
- 3e Tissue claims bounded; Allen 0.420, rank 5 of 14 with all three sections; completion by method and seed (S25 extended).
- 3f Figure 6: within-band effect = narrowing under this simulator; band-vs-block contrast also changes geometry and fragmentation; tier-3
  entries descriptive. No new simulation (claims narrowed instead).

## Item 4: reproducibility
- 4a Release: environment lock files (pip freeze, R sessionInfo), dataset IDs and checksums (data/CHECKSUMS.sha256), pinned commits
  (configs/methods.yaml), per-run configs and seeds (records), regeneration commands (Makefile targets and the V3 scripts), the commits and
  timestamps of every pre-registration, a failure table (host, threads, memory limit, reason, retry). Clean-environment check: a fresh
  virtual environment from the lock file runs linear diffusion and PCA on one DLPFC section and reproduces the recorded ARI.
- 4b HiSTaR: published median 0.65 vs official-code median 0.519 (means and medians labelled); paired section x seed table official vs port.
- 4c Spatial-MGCN: audited script versions and line references, per-epoch results, the section/seed lists behind the 20- and 23-section
  numbers; rules re-evaluated with shared clustering seeds where embeddings exist.
- 4d Reconcile Methods, captions and supplement (native / port / wrapper / benchmark-assigned clustering; S24 references; BayesSpace ST).
