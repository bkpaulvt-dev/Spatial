# Command for Claude Code: add new datasets to the benchmark and re-test the findings (run in the background)

You are Claude Code working in the repository **Spatial** (GitHub `bkpaulvt-dev/Spatial`, branch `claude/great-cori-opzfx7`), a benchmark of 16
spatial-domain methods whose paper is in `paper/`. The owner (Bikash Kumar Paul) wants new datasets added and the paper's findings re-tested
on them. **The owner will switch off the laptop about 30 minutes after starting you.** Read this whole file first, then follow it.

Work in plain language. Report in a few sentences after every phase. If something is unclear, ask in ONE list during the first 30 minutes and
give a default for each question.

## 0. Rules that never change
1. **Do not change any method code or setting**: `scripts/adapters.py`, `scripts/new_methods.py`, `scripts/bench_run.py`, `spatialbench/`,
   `configs/methods.yaml`. You may add new files (dataset registry entries, downloaders, a simulator, new analysis scripts).
2. **Do not edit, regenerate or delete existing results, tables, figures or the paper** (`paper/`, `results/*.json*` that exist). Write new
   results to NEW files named `results/newdata_*`. The original 7-group analysis stays as it is; the new groups are reported as an *extension*.
3. **No sudo. Nothing system-wide.** All environments, caches and data under `/mnt/disk/bikashkumar/SpatialBench` (conda env `env/`, R packages
   `Rlib/`), never in the shared base conda environment or in `~/R/library`. If `python`/`pip` is not the project environment's, abort.
4. **Never write passwords, tokens or credentials into any file, log or commit.** Do not look for credentials. The ntfy topic (if any) is
   stored only in `$BASE/ntfy_topic`, never in git.
5. The server is shared with other users: at most 2 heavy jobs at once, one thread each; never two setups, downloads or pipelines at the
   same time (they overwrite each other). Stop processes **by PID or process group**, never by name pattern (`pkill -f` is forbidden).
6. Do not open pull requests. Do not contact any dataset or method authors.
7. **Honest reporting.** If something fails or looks wrong, say exactly what happened. Never retry with different settings, never hide
   failures, never score labels that are not domain labels as if they were.

## 1. Goals
- **G1** More tissues and technologies for the accuracy comparison.
- **G2** Test the paper's explanation that *smoothing wins on large, layered domains*, with a simulation in which domain size is varied.
- **G3** Re-test the paper's clustering findings on every new dataset and say, for each, whether it **replicates, weakens or reverses**:
  (a) ARI range over 20 single-start fits of the same Gaussian mixture on a fixed embedding; (b) R mclust default fit depends on the R seed
  (10 seeds; and initialisation on all observations); (c) matched (20-start, best likelihood) versus each method's default clustering;
  (d) log-likelihood versus ARI (Spearman rho); (e) sensitivity to K (K-1, K, K+1).
- **G4** Complete consistency with the previous experiments, so the new groups can join the same hierarchical bootstrap.

## 2. Datasets (verify every detail yourself from the original paper or data page; the owner's wording may be imprecise)
1. HER2-positive breast cancer spatial transcriptomics, Andersson et al. 2021 (pathologist annotations).
2. Human prostate cancer, Visium, Erickson et al. 2022 (check which annotation exists and who made it).
3. osmFISH mouse cortex (Codeluppi et al. 2018) and BaristaSeq mouse cortex (check where the layer or region labels come from).
4. Simulated tissue with known domains (SRTsim and/or scDesign3; R packages into `Rlib/`). Vary domain size over a grid defined in advance
   (for example stripe or patch width from about 3 to 40 spot spacings; same number of spots and expression model; several replicates per size).
5. Visium HD (colorectal cancer) and Xenium (breast cancer), 10x public data. **First check whether DOMAIN-level ground truth exists.** If
   only cell types or no labels exist, STOP and put it in the question list; do not score cell-type labels as domains. Without domain labels
   run only label-free analyses (G3 a, b, d; run time; memory) and say so.
6. Allen whole-mouse-brain MERFISH (Zhang et al. 2023): sections with more than 20,000 cells, region labels from atlas registration (CCF),
   not from clustering. Heavy: lab server only. Choose the sections by a rule fixed before running (for example 3 sections with more than
   20,000 cells at different anterior-posterior positions).

For each dataset record in `configs/datasets.yaml`: source and accession, label provenance class (`expert` / `reference_atlas` / `algorithm` /
`unknown`), who made the labels and how, licence, sections used, label level used for K and why (decide **before** running), and the
development/test split (no tuning on any new section). Add downloaders with SHA-256 checksums to `scripts/download_new_datasets.py`
(resumable; the servers can be slow, about 0.3 MB/s per connection; one download at a time).

## 3. Consistency rules (the most important part)
- Same preprocessing as `paper/main.tex` "Preprocessing": whole-transcriptome data: genes in at least 50 spots and 10 counts, 2000 HVG
  (Seurat v3), library-size normalise, log1p, scale, 200 PCs; targeted panels: all genes, 50 PCs.
- The true number of domains K is given to every method; 3 seeds (0, 1, 2) per method per section; standardised runner
  `scripts/bench_queue.py` (one job at a time, `SPATIALBENCH_MAX_RSS_GB=12`); records in the format of `results/benchmark_runs.jsonl`
  (one record per run id; the newest wins); BayesSpace only on regular spot lattices (Visium/ST), "not run" elsewhere.
- Records produced on any machine other than the original benchmark machine carry `host="<machine>"` (see `scripts/merge_bigmem.py`). Their
  run times and energy are NOT compared; accuracy and peak memory are. Keep one result file per host and merge with a small idempotent
  script, as `merge_bigmem.py` does.
- A job that exceeds the memory cap or 24 h is recorded as such (status error, reason) and the queue goes on. Settings are never changed.
- Before any simulation result exists, write and commit `docs/PREREGISTERED_SIM.md`: hypothesis ("the advantage of smoothing over PCA
  shrinks as domains become smaller or more interleaved"), the domain-size grid, replicates, the metric (ARI of linear diffusion minus ARI of
  PCA per size, with a 95% bootstrap interval over replicates) and what would count as support or contradiction.
- New analysis scripts only (no edits to existing ones): `scripts/newdata_stats.py` writes `results/newdata_stats_extended*.json` using the
  same hierarchical bootstrap, the same reference (linear diffusion) and the same margin (+-0.03 ARI) with the new groups added; report it
  **next to** the original 7-group result.

## 4. Machines
- **A: this VS Code environment.** Report CPU, RAM and free disk first. Use it for code, registry, QC and tiny tests.
- **B: lab server DeepMed2** (125 GB RAM, 20 threads, CPU only because torch cu130 cannot use driver 570; project folder
  `/mnt/disk/bikashkumar/SpatialBench`; see `docs/DEEPMED2_RUNBOOK.md`, `scripts/setup_deepmed2.sh`, `scripts/deepmed2_pipeline.sh`,
  `scripts/run_detached.sh`). **All long jobs run here.**
- If VS Code is connected to B over Remote-SSH, still start the pipeline with the detached script (section 5): processes started from a
  normal VS Code terminal die when the connection drops. If you cannot reach B, do NOT start long jobs on a laptop; write the self-contained
  runbook `docs/NEWDATA_DEEPMED2.md` (rules, commands, what to report; same style as `docs/DEEPMED2_RUNBOOK.md`) and tell the owner the two or
  three commands to paste on B. Assume B cannot push to GitHub unless told otherwise.

## 5. Background execution (the laptop will be off)
1. **Interactive part: first 30 minutes only.** Do phase P0 and all code. Give the owner ONE list of questions with defaults. After the answers
   the owner gives ONE approval ("go all") for the whole queue. Ask for no further approval afterwards.
2. **One resumable pipeline** `scripts/newdata_pipeline.sh` (model: `scripts/deepmed2_pipeline.sh`) running P1-P6 in order, one heavy job at a
   time; every stage skips what is finished; writes one line per finished stage and job to `$BASE/newdata_status.txt`, ending with
   `PIPELINE_DONE` or `STOP: <reason>`; waits (up to 6 h) for free RAM; retries failed jobs at most 3 times with UNCHANGED settings, then
   continues; commits small result files locally after each stage; pushes only if credentials exist.
3. **Detached launcher** `scripts/run_newdata_detached.sh`: no argument = start with `setsid nohup ... < /dev/null &` and refuse to start a
   second copy; `status` = running or not, last 15 status lines, running jobs, RAM and disk, in plain language. Optional phone alerts through
   `https://ntfy.sh/<topic>` on stage end, job failure, STOP and PIPELINE_DONE (topic from the owner, never committed).
4. **Dry run before the owner leaves**: `bench_queue.py --dry-run`, a tiny simulated set, and one real small job; check that nothing needs sudo,
   a login, a password or an interactive confirmation. Fix such steps now.
5. After the dry run, tell the owner: (a) the exact commands you started, (b) how to check progress from a phone or any computer,
   (c) expected duration per phase, (d) what will NOT run while the owner is away.

## 6. Phases
- **P0 (interactive).** Read README, Makefile, `configs/datasets.yaml`, `scripts/download_new_datasets.py`, `docs/BIGMEM_RERUN.md`,
  `docs/DEEPMED2_RUNBOOK.md`, `paper/main.tex` (Methods, Limitations). `git pull origin claude/great-cori-opzfx7`; create branch
  `new-datasets`. Verify the six datasets (section 2) and report what is usable. Questions list. Dry run (section 5.4).
- **P1.** Simulation (cheap and most informative): pre-register, build `scripts/simulate_domains.py`, show example maps for small, medium and
  large domains, run all methods, run G3 on it.
- **P2.** osmFISH and BaristaSeq. **P3.** HER2+ and prostate. **P4.** Visium HD / Xenium (only if domain labels exist, otherwise label-free).
  **P5.** Allen MERFISH sections (machine B).
- **P6.** Analysis on the new files only: (i) mean ARI per method per dataset (default and matched); (ii) the extended bootstrap next to the
  original; (iii) a G3 replication table (replicates / weakens / reverses, per finding and dataset); (iv) a simulation figure: ARI of linear
  diffusion, PCA and the best three methods versus domain size.
- **Novelty check (optional, only if you can search the literature).** For each finding in G3 list the closest prior work you find (benchmarks
  that vary clustering initialisation or R mclust seed) and say whether the claim is still new. If you cannot search, skip and say so. Do not
  invent citations.

## 7. Handoff
Write and keep updating `docs/NEWDATA_REPORT.md` and, at the end, `docs/NEWDATA_HANDOFF.md`: files produced (with host tags and counts), the
tables and figures, the G3 verdicts, every failure with its reason, anything the owner must verify (annotation provenance, licences), and the
commit hash. Push the branch if possible. The owner will give this to the Claude session that maintains the paper; **do not edit the paper**.
