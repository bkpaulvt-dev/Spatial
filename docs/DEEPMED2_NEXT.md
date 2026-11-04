# Runbook for Claude Code on DeepMed2: scale-up and controls requested by the review (run in the background)

You are Claude Code on the lab server **DeepMed2** for the owner (Bikash Kumar Paul). The repository is `/mnt/disk/bikashkumar/SpatialBench/Spatial`
(GitHub `bkpaulvt-dev/Spatial`). This file is **self-contained**. Read it completely before doing anything, then report in plain language.

## 0. Where we are (do not redo this)
- The paper benchmarks 16 spatial-domain methods on 24 sections. All its results and the final paper are done and live on GitHub branch
  `claude/great-cori-opzfx7`. **Do not edit or regenerate any existing result, table, figure or the paper.**
- You (or an earlier session of you) already started `docs/NEWDATA_COMMAND.md`: a detached pipeline `scripts/newdata_pipeline.sh` running the
  simulation (tiers 1 to 3) on branch `new-datasets`. Check it first with `bash scripts/run_newdata_detached.sh status` (read-only).
- A reviewer's report asks for more data, more methods and a few decisive controls. This file lists **only the parts that need DeepMed2**
  (heavy runs). The text, figures and the analyses that use the embeddings kept on the cloud machine are done elsewhere.

## 1. Rules (never break)

> **Disk rule (always):** the root disk `/` of DeepMed2 can be 100% full. Never write temporary files, caches, installs or results to `/` (including `/tmp` and the home folder). Source `scripts/deepmed2_env.sh` at the top of every script and call `disk_guard` before every stage; see `CLAUDE.md`.
1. **Never change any method code or setting of the existing 16 methods**: `scripts/adapters.py`, `scripts/new_methods.py`, `scripts/bench_run.py`,
   `spatialbench/` (except purely additive dataset registration as already done), `configs/methods.yaml`. New methods go into **new files**
   (`scripts/extra_methods.py`, `configs/methods_extra.yaml`), with the source, commit and every deviation recorded.
2. No sudo. Nothing system-wide. Everything under `/mnt/disk/bikashkumar/SpatialBench` (conda envs, `Rlib/`, caches, data). Never touch the shared
   base conda environment or `~/R/library`. If `python`/`pip` is not the right project environment, abort.
3. **One pipeline at a time.** Never start a second pipeline, setup or download while another runs (they overwrite each other's files). Extend the
   existing queue: add stages to `scripts/newdata_pipeline.sh` (or write `scripts/review_pipeline.sh` that starts only after the first one prints
   `PIPELINE_DONE` or its tier 2 is finished, and say which). Stop processes **by PID or process group only**; `pkill -f` and `pgrep -f` are forbidden.
4. The server is shared: at most 2 heavy jobs at a time, one CPU thread each (GPU jobs: one at a time, GPU index 1, `CUDA_VISIBLE_DEVICES=1`; other users
   also use the GPUs). Check free RAM and disk before each stage; wait (up to 6 h) instead of starving other users.
5. Never write passwords, tokens or credentials into any file, log or commit. Do not contact any dataset or method authors. Do not open pull requests.
6. **Honest reporting.** Failures are recorded (status, reason), never hidden, never retried with different settings (at most 3 retries with
   unchanged settings). A job over the memory cap or 24 h is recorded as such and the queue goes on. Never score labels that are not domain labels as
   if they were.
7. Records from this machine carry `host="deepmed2"` and `device` (`cpu` or `cuda`). Run times and energy from this host are **not** compared with the
   original benchmark machine; accuracy and peak memory are.

## 2. Consistency rules for every new run (same as the paper)
- Preprocessing as `paper/main.tex` "Preprocessing": whole-transcriptome: genes in at least 50 spots and 10 counts, 2000 HVG (Seurat v3),
  library-size normalise, log1p, scale, 200 PCs; targeted panels: all genes, 50 PCs.
- The true number of domains K is given to every method; 3 seeds (0, 1, 2); standardised runner `scripts/bench_queue.py`; records in the format of
  `results/benchmark_runs.jsonl` written to NEW files `results/review_*.jsonl` (one record per run id, newest wins).
- Primary clustering = matched clustering (20-start tied Gaussian mixture, best likelihood), as in the paper, plus each method's default clustering.
- For every new dataset also run the paper's clustering-step experiments on fixed seed-0 embeddings, and state per finding whether it
  **replicates, weakens or reverses**: (a) ARI range over 20 single-start fits; (b) R mclust default fit versus the R seed (10 seeds, and
  initialisation on all observations; "not informative" on sections under 2000 observations); (c) matched versus default clustering;
  (d) log-likelihood versus ARI (Spearman rho); (e) K-1, K, K+1.
- Pre-register anything with a design choice (docs/PREREGISTERED_*.md) and commit it **before** the first result exists. Save the bootstrap draws and
  rank distributions of every new statistic (`.npz`) so figures can be redrawn.

## 3. Priority list (do in this order; each item: dry run first, then the real run; skip to the next on failure and write why)

### R1. New data (the review's main demand: 7 groups to about 15 to 20, about half non-brain)
Verify every source, label provenance, licence and section count yourself before use; record them in `configs/datasets_newdata.yaml`
(provenance class `expert` / `reference_atlas` / `algorithm` / `unknown`, who made the labels and how). Download with resumable downloaders and SHA-256
checksums, one download at a time (the servers can be slow).
- **D1 HER2-positive breast cancer**, Andersson et al. 2021 (Spatial Transcriptomics, 8 patients, pathologist-annotated sections): each patient is one
  group. Use only sections with pathologist labels that ship with the data; K from each section's labels.
- **D2 Human prostate cancer** (Erickson et al. 2022): only if the deposit contains pathologist region labels, otherwise drop it and say why.
- **D3 osmFISH mouse somatosensory cortex** (Codeluppi et al. 2018) and **D4 BaristaSeq mouse visual cortex**: try the SDMBench collection (Yuan et al.
  2024, Nature Methods; processed annotated data on Zenodo) as a shortcut; use a dataset only if its labels are documented as anatomical or
  histological, not clustering-derived.
- **D5 Simulation**: already running (see `docs/PREREGISTERED_SIM.md`). Do not change its design. Apply the cost-based tier-3 amendment.
- **D8 Allen whole-mouse-brain MERFISH** (Zhang et al. 2023; Yao et al. 2023): 3 coronal sections with more than 20,000 cells at the 25th, 50th and 75th
  percentile of anterior-posterior position; major CCF divisions with at least 1% of cells as labels (registration, not clustering).
- **D6/D7 Visium HD colorectal cancer and Xenium breast cancer**: **no domain labels expected**. Do not score them. Only after R1 to R4 are done, run ONE
  section above 100,000 cells (cropping not allowed) for the scalable methods only (PCA, linear diffusion, BANKSY, NichePCA and whichever else finishes
  within the caps), label-free and for time and memory, and write the result as "scalability, no accuracy".
- **Do not use spatialDLPFC (Huuki-Myers et al.) as a main test**: its domains came from BayesSpace clustering.
- Each new group joins the same hierarchical bootstrap as an **extension next to** the original 7-group result (new script `scripts/newdata_stats.py`:
  same reference linear diffusion, same margin +-0.03; report the group-level exact sign-flip P with Holm adjustment; save draws).

### R2. Missing methods (new files; published defaults; run on the 24 original sections and the new real-data sections, 3 seeds)
Record for each: source URL, commit or version, settings source (tutorial/paper/package default), every deviation, and what happens on large sections.
- M1 SpatialPCA, PRECAST (R; CPU). M2 CellCharter, MENDER (the closest published rivals of the smoothing baseline). M3 GraphBG, DR-SC.
- M4 one spatial foundation model: Novae (Nature Methods 2025); needs pretrained weights (check network access; if blocked, say so and skip).
- M5 **multi-sample BASS** on DLPFC (all four sections of a donor together) and on MERFISH (its five sections together), the way the BASS authors ran it;
  as an extra entry "BASS (multi-sample)", never replacing the single-section BASS records.
- M6 **Fidelity checks**: (i) the official HiSTaR code (clone, pinned commit, its own preprocessing and settings, in its own conda env under
  `/mnt/disk/bikashkumar/SpatialBench/envs/`) on the 12 DLPFC sections, 3 seeds, GPU if needed; compare ARI per section with our PyTorch port and report
  the difference; (ii) the original CCST code on ONE dataset (it needs PyTorch 1.7 pins: separate old env, CPU) against our re-implementation.
  If an environment cannot be built after a reasonable attempt, write what failed and move on.
- BayesSpace **on the three Stereo-seq sections** with `platform="ST"` (square lattice); the largest section may be too slow: cap 24 h, then record
  "time limit" and run the two smaller ones. State the setting as a deviation (BayesSpace was Visium-only before).

### R3. Controls that need new runs
- **A9 Spatial-MGCN with a label-free stopping rule** on all 24 sections, 3 seeds: pre-register one rule (default: the fixed epoch count of its paper, and
  separately a loss-plateau rule), keep the final epoch as a check; report the three values next to the existing label-selected-epoch value.
  Do not contact the authors.
- **A10 cross-host checks**: DeepST seed 0 on E10.5_E2S1 here (host confound with seeds 1 and 2 on this host); one same-seed rerun of one cheap method on
  this host for a section the original machine ran (so the host difference in ARI is measured, say which method, seed, section).

### R4. GPU (the review: "run deep methods on GPU where built for it, and report GPU and CPU cost side by side")
- The default environment here has torch 2.14.1+cu130, which cannot use the driver (570, CUDA up to 12.8), so all earlier runs were CPU-only.
  Build a **separate** env `/mnt/disk/bikashkumar/SpatialBench/env_gpu` with a torch build for CUDA 12.8 or 12.6 (wheel index `cu128`/`cu126`), check
  `torch.cuda.is_available()` and one forward pass on GPU index 1, and never use it for the primary comparison.
- With it, time and measure memory of GraphST, STAGATE, SEDR, SpaceFlow, DeepST, Spatial-MGCN, HiSTaR (port) on two reference sections (DLPFC 151673 and
  Stereo-seq E10.5_E1S1) on CPU (one thread) and on GPU, 1 seed each; records `device="cuda"`. GPU and CPU ARI may differ slightly; report both.

### R5. Equal tuning budget (last; the journal asks for tuned settings)
Pre-register first (`docs/PREREGISTERED_TUNING.md`): per method up to 10 settings from its documented hyper-parameters (learning rate, hidden size,
epochs, neighbourhood size or radius, lambda), search on the six development sections only (DLPFC donor 1 sections, first STARmap, first MERFISH), 1 seed,
chosen by ONE label-free score fixed in advance (default: mean silhouette of the matched clustering on the embedding), then frozen and run on all test
sections with 3 seeds as a separate "tuned arm" next to the default arm. Do the cheap methods first, deep methods on GPU, within a total budget you state
and I approve in the first 30 minutes. If it cannot finish, report what finished; never fill in missing cells.

## 4. Order and time
Order: finish the running simulation tiers, then R1 (D3, D4, D1, D2, D8), R2 (M5, M6, BayesSpace on Stereo-seq, M2, M1, M3, M4), R3, R4, R5, then D6/D7
scalability. Give me, in the first 30 minutes, one list of questions with defaults, a time estimate per item, and the exact detached launch command.
The owner will switch the laptop off; everything after the launch must run without any prompt, sudo or login. Start detached with
`setsid nohup ... < /dev/null &`; status line file `/mnt/disk/bikashkumar/SpatialBench/review_status.txt`, ending in `PIPELINE_DONE` or `STOP: <reason>`;
phone alerts through the existing ntfy topic file (never print or commit the topic).

## 5. Deliverables (small files only; no raw data, no large .npz in git)
`results/review_*.jsonl`, `results/review_stats_*.json` (+ draws `.npz`), tables and figures under `results/review_report/`, the registry
`configs/datasets_newdata.yaml`, `configs/methods_extra.yaml`, and **`docs/REVIEW_HANDOFF.md`**: what was run, host/device counts, failures with reasons,
the replicates / weakens / reverses verdict per finding and dataset, the fidelity-check differences (official HiSTaR vs port; CCST), the GPU versus CPU
table, anything the owner must verify (provenance, licences), and the commit hash. Commit on branch `new-datasets`; push only that branch (no force).
The paper is updated elsewhere from your handoff file.
