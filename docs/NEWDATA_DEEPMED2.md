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

## Phase 2 (real data): `bash scripts/run_newdata_detached.sh phase2`
Waits for tier 1 to finish and push, then (the hold file keeps tiers 2-3 waiting): Allen MERFISH dry run (job list + one real small job), all methods x 3 seeds (24 h and 30 GB per job),
G3 (a-e) on the seed-0 embeddings (`scripts/newdata_g3.py`: python fits, R mclust seeds via `scripts/mclust_seed.R` unchanged), commit/push, **removes `$BASE/newdata_hold`** so the
simulation continues with tiers 2 and 3; then waits for `PIPELINE_DONE`, runs the final analysis, G3 on the simulation (full-design methods) and `scripts/newdata_handoff.py`
(writes `docs/NEWDATA_HANDOFF.md`). To let tiers 2-3 start earlier, delete the hold file by hand (but never run two queues at once: at most 2 heavy jobs).
Estimated: Allen benchmark about 4-8 days (about 30,000 cells per section, 16 methods x 3 seeds, deep methods may hit the 30 GB or 24 h limit and are then recorded as such), G3 about 1 day; simulation tier 2 about 1 day, tier 3 about 2-5 days, G3 on the simulation about 1-2 days.

## Left to do
- **osmFISH**: needs confirmation from the paper's Methods that `Region` is anatomical (then `data/ext/csv/osmfish_<sec>_{counts,info}.csv` from the loom file, targeted panel through the CSV fallback).
- **HER2+ (ST)**: needs the unpacked files from the owner (see `docs/NEWDATA_REPORT.md`). **Prostate**: needs confirmation that the deposit has the spot labels.
- **Extended bootstrap** (G4) and the novelty check: not implemented (reason in `docs/NEWDATA_REPORT.md`).

## What to report (short, plain language)
Hardware and free RAM; per tier and dataset: jobs ok / error (with reasons), cells not run; H1/H2 verdicts exactly as the script prints them (including "inconclusive" and the ceiling/floor flag); the G3 table; every deviation; where the result files are and whether the push worked.
