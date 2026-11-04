# Runbook: new-datasets extension on DeepMed2 (what to run, what is left)

For the owner or a Claude Code session on DeepMed2. Same rules as `docs/NEWDATA_COMMAND.md` and `docs/DEEPMED2_RUNBOOK.md`: only the project
environment (`/mnt/disk/bikashkumar/SpatialBench/env`, R packages in `Rlib`), no sudo, never write tokens, at most 2 heavy jobs, stop processes
by PID or process group (never `pkill -f`), do not change method code, do not edit the paper or existing results, no pull requests.

## Start, watch, stop
```bash
cd /mnt/disk/bikashkumar/SpatialBench/Spatial
bash scripts/run_newdata_detached.sh            # start (refuses a second copy, or while another benchmark job of yours runs)
bash scripts/run_newdata_detached.sh status     # plain-language status: running?, last 15 status lines, jobs, counts, RAM, disk
tail -f /mnt/disk/bikashkumar/SpatialBench/newdata_status.txt     # one line per stage, tier and failed job; ends PIPELINE_DONE or STOP: <reason>
# stop: kill -- -$(ps -o pgid= <PID from newdata_pipeline.pid> | tr -d ' ')   (resumable: start again with the first command)
```
Phone alerts use the topic file `/mnt/disk/bikashkumar/SpatialBench/ntfy_topic` if it exists (never printed or committed).
Logs: `newdata_pipeline.log`, `newdata_queue.log`, `newdata_sim.log`, `newdata_stats.log` in `/mnt/disk/bikashkumar/SpatialBench/`.

## What the pipeline does (`scripts/newdata_pipeline.sh`)
1. Preflight (project python only; `tests/test_dataset_groups.py` must pass). 2. Generates the 45 simulated tissues (`scripts/simulate_domains.py`; design in
`docs/PREREGISTERED_SIM.md`). 3. Three tiers, each after >= 64 GB RAM is available: the cheapest 5 methods, then 9, then all 17 (`scripts/newdata_queue.py`,
24 h and 30 GB per job, out-of-memory and timeouts recorded and not retried, other errors retried up to 3 times with unchanged settings).
4. After each tier: `scripts/newdata_stats.py` (pre-registered primary analysis; writes `results/newdata_sim_*`, `docs/figures/newdata_sim_ari.png`), a local commit of the
small result files on branch `new-datasets`, and a push of that branch only (no force; skipped silently if credentials are missing).
Results: `results/newdata_runs_deepmed2.jsonl` (host-tagged), per-job `results/newdata_runs/*.json|npz` (git-ignored; copy them back, about 100 MB per 100 jobs).

## Left to do (no code passed a dry run yet)
- **G3 on the simulation** (a-e of `docs/PREREGISTERED_SIM.md`): a script working on the seed-0 embeddings in `results/newdata_runs/<id>.npz` (20 single-start fits and log-likelihoods; matched vs default from the records; K-1/K+1 fits; R mclust seeds on exported embeddings as in `scripts/mclust_seed.R`).
- **osmFISH**: `scripts/download_new_datasets.py` entry (linnarssonlab.org/osmFISH, SHA-256), confirm that the region labels are anatomical, add to `configs/datasets_newdata.yaml` as a targeted panel (the CSV fallback of `load_section` already handles targeted panels: `data/ext/csv/<ds>_<sec>_counts.csv` and `_info.csv`).
- **HER2+ (ST), prostate, Allen MERFISH**: confirm labels and sections first (rules in `docs/NEWDATA_REPORT.md`); whole-transcriptome ones need an additive membership edit like commit `5b01ab9` plus the same config-equivalence test.
- **Extended bootstrap** with the new real-data groups next to the original 7-group result (same hierarchical bootstrap, linear diffusion as reference, margin +-0.03).
- Final `docs/NEWDATA_HANDOFF.md`.

## What to report (short, plain language)
Hardware and free RAM; per tier: jobs ok / error (with reasons), cells not run; H1/H2 verdicts exactly as the script prints them (including "inconclusive" and the ceiling/floor flag); every deviation; where the result files are and whether the push worked.
