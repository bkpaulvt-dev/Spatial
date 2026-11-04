# New-datasets extension: running report

Branch `new-datasets` (from `origin/claude/great-cori-opzfx7`). Rules: `docs/NEWDATA_COMMAND.md`. This file is updated as work proceeds;
the final summary goes to `docs/NEWDATA_HANDOFF.md`. The paper and all existing results are untouched.

## Status by dataset (updated 2026-11-04)
| Dataset | Status | Why (what I found, from the primary sources) |
|---|---|---|
| Simulated tissue (domain-size experiment) | **running** (`scripts/newdata_pipeline.sh`) | design pre-registered in `docs/PREREGISTERED_SIM.md` (+ Amendment 1) before any result |
| Allen whole-mouse-brain MERFISH (Zhuang-ABCA-1, Zhang 2023) | **prepared, queued** (phase 2, after tier 1) | rule applied: 72 coronal sections with > 20,000 cells; 25/50/75th percentile of CCF x (Spearman with section number 1.0) = sections 066, 085, 103 (26,940 / 32,047 / 29,220 cells, 1,122 genes); labels = CCF divisions with >= 1% of cells (K = 11, 11, 7) from registration to the atlas, not clustering. CCF placeholders named "unassigned" are not anatomical divisions: set to NA (decided before any method ran). Licence not found: to be checked |
| osmFISH mouse cortex (Codeluppi 2018) | **skipped** | the data page (linnarssonlab.org/osmFISH/availability) describes the `Region` attribute only as "the location of the cell in one of the inferred regions"; the paper's Methods could not be read from this server (bioRxiv returned a block page, Nature needs a login), so the labels are **not documented as anatomical**; by the agreed default they are treated as algorithm-derived and left out of the accuracy comparison |
| HER2-positive breast cancer ST (Andersson 2021) | **skipped** | Zenodo 3957257 is open and CC-BY-4.0, but its data files (count matrices, spot selections and the 8 pathologist-label files `*_labeled_coordinates.tsv`) are **password-encrypted zips**; the passwords are in the authors' README. Using them would mean writing a password into a script, log or command line, which the run rules forbid. If the owner places the unpacked files in `data/HER2ST/`, a loader can be added |
| Prostate (Erickson 2022) | **skipped** | the paper says two uropathologists annotated all 23,282 Visium spots spot by spot, but I could not confirm that the per-spot annotation files are in the Mendeley deposit (10.17632/svw96g68dv; its description lists count matrices, histology images and additional material; licence CC BY-NC 3.0). Rule: only if the deposit contains the labels |
| BaristaSeq mouse cortex (SDMBench) | **skipped** | the SDMBench pages I could reach list BaristaSeq only as a technology: no tissue and no label provenance (processed data: Figshare project 163942, sdmbench.drai.cn; the Nature Methods article could not be opened). SDMBench is Nature Methods 2024, not Genome Biology as in the task text |
| Visium HD (colorectal) and Xenium (breast) | **skipped, not downloaded** | see below |

**Visium HD and Xenium.** The public 10x Visium HD colorectal-cancer sample ships with unsupervised clusters only, and I found no domain-level
ground truth for the Xenium breast sample; scoring cell types or clusters as if they were domains would be circular and is forbidden by the
rules. In addition, Visium HD has far more bins than any method in the benchmark handled within the memory cap (the 18,408-bin Stereo-seq
section already exceeded 12 GB for five methods). They were therefore not downloaded and not run; no label-free analysis was done either.

## Deviations and decisions (all recorded here, none silent)
1. New datasets are registered in `configs/datasets_newdata.yaml`, **not** in `configs/datasets.yaml`: `scripts/stats_cluster_aware.py` enumerates the latter as bootstrap groups, so adding them would change the original 7-group analysis.
2. Additive edits in `spatialbench/data.py` and `scripts/run_r_method.R` (commit `5b01ab9`, approved): names `sim_bands`, `sim_blocks` join the whole-transcriptome group (not the Visium group). `tests/test_dataset_groups.py` shows the five existing datasets resolve exactly as before.
3. Per-job memory cap 30 GB (original benchmark: 12 GB on a 15 GB machine); records carry `host`, run times are not compared.
4. The simulator is self-written (numpy gamma-Poisson); SRTsim/scDesign3 were not installed because they estimate their own models and give no control of geometry at a fixed effect size (the pre-registered design needs that control).
5. Methods run cheapest first by measured cost. Tiers 1-2 (9 cheapest methods) keep the full design (45 tissues x 3 seeds); the 8 tier-3 (deep) methods run a REDUCED design (seed 0, replicate 0, 9 tissues each), by Amendment 1 of `docs/PREREGISTERED_SIM.md` (2026-11-04, cost only, written before any tier-3 result). Headline contrast and verdicts use the full design only; tier 3 is reported separately. A job over 24 h is recorded as "time limit", never subsampled or retried with other settings.
6. The GraphST mclust wrapper is already in the base branch (`adapters.py`, merged in f5854f3); nothing was cherry-picked.

## Not done
The extended hierarchical bootstrap (new real-data group next to the original 7-group result, G4) and the novelty check are not implemented: the original bootstrap lives inside `scripts/stats_cluster_aware.py`, which runs and writes its outputs at import, so it cannot be reused without touching existing results. G3 (a-e) is implemented in `scripts/newdata_g3.py`.
