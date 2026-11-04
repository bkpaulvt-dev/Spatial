# New-datasets extension: running report

Branch `new-datasets` (from `origin/claude/great-cori-opzfx7`). Rules: `docs/NEWDATA_COMMAND.md`. This file is updated as work proceeds;
the final summary goes to `docs/NEWDATA_HANDOFF.md`. The paper and all existing results are untouched.

## Status by dataset (2026-11-04)
| Dataset | Status | Why |
|---|---|---|
| Simulated tissue (domain-size experiment) | **running** (pipeline `scripts/newdata_pipeline.sh`) | design pre-registered in `docs/PREREGISTERED_SIM.md` before any result |
| osmFISH mouse cortex (Codeluppi 2018) | not run | no loader/downloader yet; region labels must first be shown to be anatomical, not cluster-derived (otherwise label class `algorithm`, excluded from accuracy) |
| HER2-positive breast (Andersson 2021, ST platform) | not run | which sections carry pathologist labels is not yet confirmed from the data deposit; ST lattice needs a decision on BayesSpace gating |
| Prostate Visium (Erickson 2022) | not run | not confirmed that the deposit contains pathologist region labels (dropped if not) |
| BaristaSeq mouse cortex (SDMBench) | **skipped** | the SDMBench pages I could reach list BaristaSeq only as a technology: no tissue and no label provenance are documented there (processed data are on Figshare project 163942 / sdmbench.drai.cn; the Nature Methods article could not be opened from this server). SDMBench is Nature Methods 2024, not Genome Biology as in the task text |
| Visium HD (colorectal) and Xenium (breast) | **skipped, not downloaded** | see below |
| Allen whole-mouse-brain MERFISH (Zhang 2023) | not run | needs section choice by the pre-set rule (3 sections of > 20,000 cells at the 25th/50th/75th percentile of A-P position, major CCF divisions with >= 1% of cells as labels) and a downloader; heavy |

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

## Not yet written (so not run)
`scripts/newdata_g3.py` (G3 re-tests a-e on the simulation), the extended hierarchical bootstrap `scripts/newdata_stats.py --extended` for real datasets, and the novelty check. See `docs/NEWDATA_DEEPMED2.md`.
