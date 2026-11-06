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

## Incident 2026-11-05/06: records wrongly labelled "memory limit" (infrastructure kills), found and fixed
**What was wrong.** The memory guard in `spatialbench/resources.py` kills a job when the cap (30 GB per job) is exceeded **or when less than 0.8 GB of the whole shared machine is left**, and in both cases sets
`oom_killed = true` (record field `resources.oom_killed`, queue field `outcome = "memory limit"`, error text "killed (out of memory)"). On 2026-11-05 other users filled the RAM (available RAM 10-57 GB for hours),
so our jobs were killed while their own memory was small. Signature: `oom_killed` with `resources.peak_rss_gb` far below the cap (0 to 18 GB; a real memory limit has a peak of about 30 GB). The queue treated every
`oom_killed` record as final and never retried it. These records say nothing about the methods.
**Counts (corrected).** In the newest records per id: Allen MERFISH 102 "memory limit" records, of which **85 are infrastructure kills (peak at most 3.9 GB)** and **17 are real memory limits** (graphst, peak 30.0-30.4 GB, i.e. the cap);
simulation tier 1: 25 `pca_gmm` jobs on `sim_blocks` (peak at most 1.6 GB; 20 still open when this was written, 5 already recovered by the retry); BayesSpace on Stereo-seq (review stage): all 9 jobs (peak at most 18.1 GB).
(An earlier message of mine said "127 Allen records": that number was 102 Allen + 25 simulation records, and not all Allen ones were false.)
**Fix** (commit `ed7832d`, queue code only, no method code or settings): in `scripts/newdata_queue.py` and `scripts/review_queue.py` a kill counts as a real memory limit only if the peak reached 80% of the per-job cap (24 GB); any other
`oom_killed` record is an "error" with `infra_kill = true` and is retried with unchanged settings (up to 3 attempts in total, counting the first); each job also waits until at least 25 GB of RAM is available before it starts.
The runner and pipeline no longer STOP after 6 h of low RAM; they wait (40 GB needed to start a stage or tier). The old records stay in the files (newest record per id wins), so the history is visible.
**Proof that no other records carry the same error.** I scanned every `oom_killed` record in all four result files (`benchmark_runs.jsonl`, `benchmark_runs_bigmem.jsonl`, `newdata_runs_deepmed2.jsonl`, `review_runs_deepmed2.jsonl`) and split them at 24 GB peak:
below 24 GB: Allen 85, simulation 25, review BayesSpace-ST 9 (all listed above and all being retried), plus 19 records of the ORIGINAL benchmark (18 on Stereo-seq with the original 12 GB cap, peaks up to 12.3 GB, i.e. real cap hits, and 1 DLPFC record, nichepca seed 2, peak 6.7 GB);
the original-benchmark ones are already superseded: all 15 Stereo-seq ids have a later `ok` record in `benchmark_runs_bigmem.jsonl`, and the DLPFC id has a later `ok` record (peak 7.2 GB). At or above 24 GB: 17 Allen graphst records (real). No other dataset has such records.
**Simulation `pca_gmm` retry.** 25 `pca_gmm` jobs on `sim_blocks` (tier 1, full design) were affected. Their old records are NOT excluded from the history, but they are superseded by the retry (newest record per id wins); the headline analysis
(`scripts/newdata_stats.py`) uses only `status == ok` records and is rerun after the retry, so the Delta contrast is computed with the complete tier-1 design, not with the 25 missing cells.
**CCST job stopped on purpose.** PID 3770287 was `bench_run.py --method ccst --dataset allenmerfish --section ABCA1-066 --seed 1` (about 2 h 45 min into its run), started by the old phase-2 queue. I stopped it, together with that queue and the phase-2 script, because that queue still ran the
old code (it would have gone on to G3 with the 85 wrong records). It had no record yet; the restarted phase 2 (new PID 384834, fixed queue) runs it again from the start (same job, unchanged settings).
**Other finding on Allen (not infrastructure, needs a decision).** 6 `stagate` records on ABCA1-085 and ABCA1-103 (seeds 0-2) failed with the rpy2/mclust 6.1.3 error `dimnames ... not equal to array extent`, the same bug that was fixed for GraphST by calling `Mclust` inside an R function.
STAGATE's own `mclust_R` is used unchanged; I did not touch it.
**Restart allowance.** The simulation pipeline was relaunched at 09:33 (fresh counter: 3 attempts per tier); phase 2 was relaunched at 10:07 (3 attempts for the Allen queue; none used). The review runner retries a failed stage 3 times.
**No `ok` record was affected** by the false memory kills: a job killed by the guard has `status = error`, never `ok`, so every `ok` record in all four result files is a completed run. The guard rule of the paper's Supplementary Note 6 (stop a job when the machine has under 0.8 GB left)
produced, on the original machine, only records that are superseded by later `ok` records (the 19 original-benchmark `oom_killed` records listed above; verified for all of them).
