# Referee report, round 5 (final): Reviewer 2 (spatial domain method developer)

Material read: paper/main.pdf and main.tex, paper/supplementary.pdf, configs/methods.yaml, configs/datasets.yaml, results/paper_macros.tex, scripts/run_r_method.R, scripts/new_methods.py, docs/LEAKAGE_AUDIT.md, DATA_AND_LICENCES.md, and the BayesSpace clone under data/ext/methods. Nothing was re-run. Line numbers refer to paper/main.tex.

## Verdict
Minor revision. The method-specific claims are now largely accurate and neutrally worded, and none of my remaining points changes a conclusion. Most round-4 items were fixed properly. The remaining defects fall into four groups:
- one factual error about a named method (BayesSpace);
- HiSTaR wording that credits "released code" for what a port produced;
- the "expert annotation" label, which is not supported by the dataset registry;
- unfinished housekeeping (breast-cancer coarse range, Spatial-MGCN pooling, LEAKAGE_AUDIT and methods.yaml flags).

## A. Status of the round-4 required items
1. GraphST "more than the cap" and the thread caveat. Mostly resolved.
   - Results l.239-241 now says "reaching or exceeding the 12 GB cap ... on the first attempt" and "measured on the larger server with 20 threads".
   - Left over: Limitations l.413 still says five methods "needed more than the 12 GB". The GraphST peak macro is 12 (11.8 GB), so this is wrong for GraphST (see C9).
2. Runner-reversal caveat and stale captions. Resolved for the Discussion (l.376 "in the primary analysis; the order reversed in the runner sensitivity analysis and the intervals overlap"). The redundant ranks block and the S9 and S14 captions are fixed. The Table S7 caption still says "sections completed by every method" (trivial now; see C12).
3. BayesSpace reason. Not resolved (B1). The NichePCA sparse backend is now stated (l.241, S2). The Spatial-MGCN NaN patch is now listed in S2.
4. Clustering-derived annotation and Cavity next to the blurring hypothesis, plus CellCharter and MENDER. Mostly resolved.
   - l.386-388 now names the annotation explanation, cites CellCharter and MENDER, and labels both explanations "neither tested".
   - Limitations l.416 gives Cavity's share (15-24%) and UMI ratio (0.5-0.9).
   - Still missing: an ARI without the Cavity class (B3).
5. Table S20 breast row and in-scope inflation. Not resolved (B5; this is now Table S21).
   - The LEAKAGE_AUDIT.md line 6 ("authors not yet contacted; do not publish a claim about a specific method before they have been given the chance to respond") is still there.
   - methods.yaml still opens with "WARNING ... written from memory and are NOT verified".
   - datasets.yaml still has `verified: false` and `license: to_check`.

Other round-4 points now fixed:
- Table S19/S20 label HiSTaR as a "PyTorch port".
- The Table S24 coverage is consistent.
- The mclust seed statements (2020 for STAGATE and GraphST, 2023 for SEDR; seeds in the clones) are correct. I checked SEDR's `random_seed=2023`. The seed dependence is correctly restricted to n > 2000.
- The BASS-versus-linear-diffusion ranking is stated neutrally in Abstract, Results and Discussion.

## B. New findings, ranked

### B1. BayesSpace "Visium only" rationale is not accurate (medium; named-method claim)
Location: Methods l.147-148 ("requires a regular spot lattice (it models neighbours on the Visium array), so it was run on the Visium sections only"); Table S2 and methods.yaml ("needs a regular spot lattice with a fixed neighbour structure"); the adapter error in scripts/new_methods.py l.301.

Problem:
- BayesSpace has a `platform = "ST"` mode with a square-lattice, four-neighbour model. In the clone's source, lines 9, 175 and 222-234 of R/spatialCluster.R, 'ST' is described as square-lattice geometry. This mode exists in 1.5.1 too.
- MOSTA bin50 is a regular square grid, so the stated reason does not exclude it. The docstring at new_methods.py l.298-299 says the mode is "designed for 100 um ST spots; untested here". That is the honest reason, and the paper does not give it.
- The adapter error message ("not applicable to ... Stereo-seq data") repeats the overstatement.
- Single-cell STARmap and MERFISH are legitimately excluded, because they have no lattice.

Fix:
- Either run `platform="ST"` on the three bin50 sections (the 18,408-bin section will be costly; "not run for cost" is acceptable).
- Or reword to: "BayesSpace was run on Visium only. Its square-lattice (ST) mode was not used on the Stereo-seq bin50 grid, which it was not designed for (100 um spots), and STARmap and MERFISH have no lattice." Apply this in main text l.147-148, in S2 and in the adapter message.
- Consequence: BayesSpace is absent from the Stereo-seq comparison. State this in the Fig. 2 and Table S3 captions as "not run" rather than "inapplicable".

### B2. HiSTaR: wording credits "released code" for results of a port, and "default clustering" is misdescribed (medium)
(a) l.358 reads "document what the released code and defaults reproduce". The study used a PyTorch port, not the released code. The port's equivalence to the official implementation is not shown:
- methods.yaml says the commit is "inferred, no vendored copy kept".
- The port takes the shared 200 PCs as input.
- The per-section tuning is not applied.
- The Abstract's "HiSTaR's published accuracy was not reproduced" omits the port.

Fix:
- Say "our PyTorch port of the released code" at l.358 and in the Abstract ("... was not reproduced by our port of its code").
- Add one sentence naming the missing fidelity check (no run of the official code, and no author contact).
- Keep the neutral closing sentence.

(b) Methods l.174-176 define default clustering as "the clustering step of each method's official pipeline" and then list a 3-start scikit-learn GMM for HiSTaR and BANKSY. HiSTaR's official pipeline uses R mclust (the paper itself says so at l.353, and methods.yaml says "official: R mclust EEE"). BANKSY's tutorial uses Leiden/mclust. The 3-start GMM is the benchmark's default for these two, not theirs.

Fix: "Default clustering: the clustering step of each method's pipeline, except HiSTaR and BANKSY (a 3-start tied GMM chosen by us; HiSTaR's official R mclust result is given in the reproduction section)." Table S2's "Default clustering" column needs the same correction.

(c) The 0.718 value for 151673 is cited at l.354 but there is no matching row in Table S20; add the 151673 value of the port.

### B3. "Expert annotation" label and ground-truth adequacy (medium)
- Results l.242 and Table S8 define the sensitivity subset as "datasets with an expert annotation" (DLPFC, MERFISH, breast cancer). datasets.yaml does not support this:
  - MERFISH is class `reference_atlas`, "believed to come from the original MERFISH study's registration ...; confirm", `verified: false`.
  - Breast cancer is `expert`, but "confirm who drew it and whether expression clusters were used", and DATA_AND_LICENCES.md says "Who drew the annotation is not stated in the repository".
  - STARmap and MERFISH labels come from the same BASS-Analysis repository, yet one is "unknown" and the other "expert".
  - Data availability says the labels are "from the original studies", while Results says STARmap's provenance is unknown. These conflict.
- Fix:
  - Rename the subset "datasets whose annotation is not known to be clustering-derived", or verify and cite the provenance of each annotation (Moffitt 2018; the SEDR breast annotation).
  - Make Data l.109-111 and l.242 agree.
  - Remove "expert" from the overview figure label (make_overview_figure.py: "expert domain labels") unless it is verified.
- Breast cancer: the ground truth is 20 numbered sub-regions (IDC_1..7, DCIS/LCIS_1..5, Tumor_edge_1..6). Against the 4 coarse classes, every method reaches ARI 0.04-0.31 (Table S19). This shows the annotation is histological, not expression-defined, and mostly not recoverable. The Discussion should say that breast-cancer ARI differences of about 0.05 are close to noise on a single section.
  - Round-4 M4.4 is still open at l.237-239. Add "ten of 14 methods lie within 0.18-0.21", which Table S19 confirms (0.181 to 0.210). Currently only the lowest and highest values are quoted, and the 0.31 NichePCA outlier drives the "order changed" statement.
- Stereo-seq/Cavity:
  - The Limitations sentence (l.416) is a good start. "Partly reflects low count depth" is too strong for a ratio of up to 0.9 (one section is almost the same depth as other bins). Give the per-section ratio.
  - Report ARI without Cavity bins (with K reduced by one), per section, for linear diffusion, PCA and three other methods. This is cheap on cached embeddings and is the one empirical check that would turn "may favour similar methods" into evidence. The `algorithm` provenance class in datasets.yaml is still `verified: false` ("as far as we know"), so cite the MOSTA Methods for the claim. If it cannot be verified, say "we believe".
  - bin50 annotation is cell-resolution-agnostic: add that Stereo-seq annotations are defined on the original bin resolution and carried to bin50 (confirm this is true).

### B4. Generalising from one breast section and one embryo study; biological explanation partly asserted (medium-low)
- The Abstract ("on breast cancer and embryo most methods ... were slightly ahead") and Discussion ("In tumour and embryo sections") generalise from one breast-cancer section and three embryo sections of one study. Write "on the one breast-cancer section and three embryo sections".
- l.386 ("domains are smaller, interleaved and defined partly by cell composition") is stated as fact, then followed by two explanations labelled untested. The first sentence is also an untested hypothesis. No domain-size or interleaving statistic is reported (one could be computed cheaply from the annotation, e.g. the boundary-spot fraction or number of connected components per domain, for DLPFC against the other datasets). Either report it or write "may be".
- l.388: "There the methods performed similarly" follows the CellCharter/MENDER sentence and reads as if it referred to them. Move the CellCharter/MENDER sentence after "gave no gain over PCA alone".
- Add the Stereo-seq range (0.24-0.39) to "the methods were close to each other" (l.234; round-4 M4.5).
- A third untested explanation is worth one clause: on a square bin grid the six-nearest-neighbour graph has ties among equidistant bins, and bin50 spacing is a different physical scale. This is in the Limitations but not in the Discussion's list of explanations.

### B5. Spatial-MGCN label-selected epoch: pooling and scope (medium-low; wording)
- l.362-365 and Table S21 pool DLPFC, STARmap and MERFISH (20 sections) into "+0.147 on average" and quote 0.38 on STARmap. The released scripts only target DLPFC and breast (DLPFC_test.py, HBC_test.py), so STARmap and MERFISH are a reuse of the rule on datasets the code does not cover. Report "in scope: DLPFC +0.133, breast +0.03 (3 seeds)" as the headline, and mark the pooled figure and STARmap as "rule applied by us".
- Table S21 lacks the breast row, although the text quotes it. Add it.
- The comparison "0.551 against 0.558" is fair. Also give the breast point (Spatial-MGCN default 0.575 against linear diffusion 0.545), so the sentence "inflation was smaller" is not read as "no concern". It is a different, tuned configuration with its own risk of label influence.
- docs/LEAKAGE_AUDIT.md l.6 still says "do not publish a claim about a specific method before they have been given the chance to respond". The manuscript publishes exactly this claim. Contact the Spatial-MGCN authors (and HiSTaR's) and record the response, or remove the sentence before release. The paper's wording ("we report what the released code does") is appropriate.

### B6. BASS inputs and settings differ from the shared protocol and are not fully disclosed (low-medium)
- scripts/run_r_method.R l.15-19: on DLPFC, breast cancer and Stereo-seq BASS runs on 3000 SPARK-X spatially variable genes (`geneSelect="sparkx", nSE=3000`), with C=20, not on the shared 2000 HVG. On STARmap C=15 (and 20 on MERFISH). These are the authors' per-dataset tutorial settings, so Methods l.132-133 ("none was tuned per dataset") should read "none was tuned by us".
- Table S2 and methods.yaml list the DLPFC, STARmap and MERFISH settings, but not that the DLPFC settings (C=20, SPARK-X) were reused on breast cancer and Stereo-seq (C=20 with K=12/13/18). Add this clause.
- In the Preprocessing section, state that BASS selects its own genes. A spatially informed feature selection is a plausible part of BASS's advantage, and the paper should say it is not isolated.
- Together with the BASS-derived STARmap/MERFISH annotation (already conceded in Limitations), this is the only place where the benchmark leans in a named method's favour. It does not change the conclusion, but it belongs next to the ranking sentence in the Discussion.

### B7. Selection of methods (low)
Methods l.130-131 give the criterion "maintained public code that runs on CPU". SpatialPCA and PRECAST are cited in the Introduction as spatially aware methods, and they run on CPU. SpatialPCA, SPARK and conST were even screened in the audit (Table S22) but not benchmarked. CellCharter and MENDER, the published versions of the neighbourhood-smoothing idea behind the baseline, are cited but not run.

Fix: one sentence stating why each was left out (for example the n x n kernel of SpatialPCA, or runtime). If the reason is cost, say so. The Discussion already says they are "related", which is fair.

### B8. Reproducibility metadata that does not match the clone (low)
methods.yaml/S2/DATA_AND_LICENCES list BayesSpace as "tag v1.5.1, commit ba8b422". The clone at data/ext/methods/BayesSpace is development version 1.21.2 at ba8b422, whereas the installed R package reports 1.5.1. The commit therefore does not identify the version that was run. Record the commit of the v1.5.1 tag.

## C. Wording and consistency points
9. Limitations l.413: "Five methods needed more than the 12 GB". GraphST's peak is 11.8 GB (the macro rounds to 12), and it was stopped by the cap or the system-memory rule. Use the Results phrasing: "reached or exceeded the cap in the first attempt".
10. Methods l.168-170 say every published method "was run with its authors' defaults". Spatial-MGCN uses the final epoch, SEDR the Visium graph on Stereo-seq, and GraphST the Stereo mode. Say "default or tutorial settings, with the deviations in Table S2".
11. Methods l.117: "without changing any setting" is still not literally true (the Stereo mode for GraphST). Reword to "without changing any shared setting".
12. Table S7 caption: "sections completed by every method" is now trivial. Delete the clause.
13. methods.yaml first lines ("written from memory and are NOT verified") and the CCST entry "(volume and pages to verify)": all citation fields I checked (SpaGCN, STAGATE, GraphST, BANKSY, DeepST, BayesSpace, BASS, SpaceFlow, SEDR) match my knowledge, so verify the rest (HiSTaR, NichePCA, CCST, Spatial-MGCN) and delete the warning, or leave it out of the released file.

## D. Items checked and found correct
- Spatial-MGCN: the label-selected epoch is reported factually, with the "we do not know whether the published numbers were obtained with these scripts" caveat. The NaN patch applies to the diagnostic only, and S2 says so.
- GraphST, STAGATE and SEDR mclust seed dependence: mechanism (2000-point hierarchical-agglomeration subset), seed values, n > 2000 restriction and the full-data fit's noise sensitivity are described fairly. The Abstract's "depended on its random seed" is neutral.
- BASS versus linear diffusion: stated neutrally everywhere, including the reversal in the runner analysis.
- NichePCA, DeepST and GraphST memory: attributed to the implementations on this section, with 20 threads, with the dense-graph versus workflow distinction (l.241) and the sparse option for NichePCA.
- Smoothing on layered cortex but not tumour or embryo: stated as an observation (counts 0/1/1 against 13/16 and 11/15; PCA ahead). The explanations are marked untested, except the first sentence (B4).
- MERFISH cell-type remark: marked "may".
- Conflict-of-interest and neutrality paragraphs are adequate (AnisoST disclosed; linear diffusion and PCA identified as its ablations).

## E. Required before acceptance
1. B1: correct the BayesSpace rationale (main text, S2, adapter message), or run its ST mode on the bin50 sections.
2. B2: HiSTaR "port" wording at l.358 and in the Abstract, and the default-clustering definition in Methods l.174-176 and Table S2.
3. B3: replace or verify the "expert annotation" label (l.242, Table S8, overview figure). Add the "ten of 14 within 0.18-0.21" clause. Report ARI without Cavity (or concede it was not done).
4. B5: Table S21 breast row and in-scope headline. Resolve the LEAKAGE_AUDIT contact statement.
5. B4: restrict generalisation to the sections actually tested, and mark l.386 as untested.
6. Remaining low items B6-B8 and C9-C13.
