# Runbook for Claude Code on DeepMed2: rerun of the memory-capped Stereo-seq jobs

You are Claude Code running on the lab server **DeepMed2** for the owner (Bikash Kumar Paul). Follow this runbook from top to
bottom. It is self-contained. Report to the owner after every phase in a few plain sentences.

## 0. The task in one paragraph
A benchmark paper compares 16 spatial-domain methods on 24 sections. On the original 15 GB machine five methods ran out of
memory on the Stereo-seq section **E10.5_E1S1 (18,408 bins)**: BASS, GraphST, NichePCA, Spatial-MGCN, DeepST; and DeepST seeds
1-2 failed on **E10.5_E2S1**. Your job is to rerun exactly these 17 jobs on DeepMed2 (CPU; GraphST and DeepST optionally on GPU
index 1), with the same code and settings as the paper, and to hand back the result records. The jobs are 15 (5 methods x 3
seeds on E10.5_E1S1) + 2 (DeepST seeds 1, 2 on E10.5_E2S1).

## 1. Rules (read first, they matter)
1. Work **only** inside `/mnt/disk/bikashkumar/SpatialBench` (the repository is its subfolder `Spatial`, branch
   `claude/great-cori-opzfx7`, GitHub `https://github.com/bkpaulvt-dev/Spatial`).
2. **No sudo.** Install nothing system-wide. **Never modify the shared base conda environment** or `~/R/library`; everything goes
   into `/mnt/disk/bikashkumar/SpatialBench/env` (conda) and `/mnt/disk/bikashkumar/SpatialBench/Rlib` (R packages).
3. The server is **shared** with other lab users (125 GB RAM total, usually 60-90 GB available; 2x TITAN RTX 24 GB, partly used by
   others; 20 CPU threads). Run at most 2 heavy jobs at once, single-threaded each; never run anything else heavy meanwhile.
4. **Never run two setups, two pipelines or two downloads at the same time** (they overwrite each other's files). Before starting
   anything, list what is already running (phase 2). Stop a process **by PID or process group**, never by name pattern.
5. Do **not** change the scientific code or settings (they must match the paper). If something seems to require that, stop and ask.
6. Never write passwords, tokens or the owner's credentials into any file, log or commit. Do not look for credentials.
7. Do not open pull requests. Commit only the result files listed in phase 7.
8. If a command is blocked waiting for approval, tell the owner what you need approved.

## 2. Phase 1: look around (read-only)
```bash
cd /mnt/disk/bikashkumar/SpatialBench/Spatial && git pull --ff-only origin claude/great-cori-opzfx7 && git log --oneline -1
free -g; nproc; nvidia-smi --query-gpu=index,name,memory.used,memory.total,driver_version --format=csv
df -h /mnt/disk | tail -1
ps -u $USER -o pid,ppid,etime,args | grep -E "download_new|setup_deepmed2|deepmed2_pipeline|bench_run|bench_queue|mclust_seed" | grep -v grep | cut -c1-140
cat /mnt/disk/bikashkumar/SpatialBench/status.txt 2>/dev/null | tail -15
```
- If `git pull` fails because of an untracked file (for example `environment/environment.deepmed2.yml`), delete that one untracked file
  and pull again.
- If **more than one** `deepmed2_pipeline.sh` or `setup_deepmed2.sh` is running, or a setup runs without a pipeline parent, stop
  the extra ones: `kill -- -$(ps -o pgid= <PID> | tr -d ' ')`, keep a single pipeline (or none), and delete any
  `data/Stereo/*.part` files if two downloads wrote to them. Tell the owner.
- If a pipeline is already running and `status.txt` shows it progressing, **do not start another**; go to phase 5.

## 3. Phase 2: check the shared base environment (read-only; an earlier run may have touched it)
An earlier setup attempt reported that `pip` once ran against the shared base miniforge (a build log showed `cpython-312`).
Find out, without changing anything:
```bash
BASEPREFIX=$(conda info --base); echo $BASEPREFIX
conda list --revisions -n base | tail -40                      # history of changes to base, with dates
ls -lt $BASEPREFIX/lib/python3*/site-packages | head -40        # recently modified packages in base
ls -lt ~/.local/lib/python3*/site-packages 2>/dev/null | head   # user-site installs
ls -lt ~/R/library 2>/dev/null | head                          # R packages in the home library
```
Anything modified on or after **2026-10-28 16:40 (EDT)** and related to torch, scanpy, igraph, louvain, numpy, nvidia-*, GraphST, SEDR,
STAGATE, SpaGCN, rpy2 or R packages (reticulate, BASS dependencies) may be ours. **Report the list to the owner and do not uninstall
or delete anything without their explicit approval** (other lab users may rely on that environment). The setup script now aborts
if `python`/`pip` are not the project environment's, so this cannot happen again.

## 4. Phase 3: start the run (once)
The whole job is one resumable, detached script. Start it exactly once:
```bash
cd /mnt/disk/bikashkumar/SpatialBench/Spatial
NTFY_TOPIC=<owner's ntfy topic, if they gave one> bash scripts/run_detached.sh cuda    # or without NTFY_TOPIC
```
What it does (`scripts/deepmed2_pipeline.sh`, uses `setsid nohup`, so it survives closing terminals and sessions):
1. **Setup** (`scripts/setup_deepmed2.sh`, up to 3 attempts): conda env in `/mnt/disk/bikashkumar/SpatialBench/env` (Python + R 4.3 +
   R/Bioconductor pins from `environment/environment.deepmed2.yml`), Python packages in stages (torch first; the lock file with
   `--no-deps`; `torch_scatter`/`torch_sparse` compiled with `--no-build-isolation`; `louvain` optional), R package BASS into
   `.../Rlib`, clones of DeepST and Spatial-MGCN at pinned commits, download of the two Stereo-seq sections
   `E10.5_E1S1` (1.4 GB) and `E10.5_E2S1` (0.4 GB) (slow server: about 0.3 MB/s per connection, so ~1.5 h), checksum check, preflight.
2. **Wait** until >= 64 GB RAM is available (up to 6 h).
3. **Rerun** the jobs with `scripts/rerun_memory_failures.sh` (GraphST and DeepST on GPU 1 if torch can use CUDA, otherwise CPU;
   BASS, NichePCA, Spatial-MGCN always CPU; 2 jobs at a time; 30 GB cap per job; failed runs restarted up to 5 times, finished
   jobs skipped). Results: `results/benchmark_runs_bigmem*.jsonl` and `results/runs/<id>.json|npz`.
4. **Collect**: summary lines in `status.txt`, commit of the jsonl records, push attempt; last line `PIPELINE_DONE`.

Expected duration: setup 1-3 h (mostly the slow download), jobs 12-24 h.

## 5. Phase 4: monitor
```bash
bash scripts/run_detached.sh status                  # RUNNING / NOT running, last lines, jobs, RAM, GPU
tail -5 /mnt/disk/bikashkumar/SpatialBench/status.txt
tail -30 /mnt/disk/bikashkumar/SpatialBench/setup_deepmed2.log     # setup details
tail -30 /mnt/disk/bikashkumar/SpatialBench/rerun.log              # one line per finished run: id, ok/error, ARI, time, memory
ls -lh /mnt/disk/bikashkumar/SpatialBench/Spatial/data/Stereo/     # download progress (.part files grow)
```
Report progress to the owner after each stage (setup done, RAM found, first results, finished). A `STOP:` line in `status.txt`
means the pipeline gave up: read the logs, fix the cause (phase 6), and start it again with `bash scripts/run_detached.sh cuda`.
If the pipeline is "NOT running" and the last line is not `PIPELINE_DONE` (server reboot, killed), start it again the same way:
every stage is resumable.

## 6. Phase 5: known problems and their fixes (all already handled in the scripts; listed so you recognise them)
| Symptom | Cause | Fix |
|---|---|---|
| `PackagesNotFoundError ... bioconductor-scran=1.30.2` | exact Bioconductor patch versions are not on conda | series pins in `environment.deepmed2.yml` (already) |
| `ResolutionImpossible ... louvain 0.8.2 ... igraph` | the lock file is a freeze whose declared metadata conflicts | install with `--no-deps` (already) |
| `No module named 'torch'` building `torch_scatter` | build isolation | torch first, then `--no-build-isolation` (already) |
| `Build failed for the C core of igraph` (louvain) | louvain needs CMake; only SpaGCN/SpaceFlow use it | optional extra (already) |
| `installing to /home/.../R/library` | R used the home library | `R_LIBS_USER=.../Rlib` (already) |
| two `.part` files plus an unexpected third | two downloads at once | one pipeline only; delete `*.part`, restart |
| `git pull` refuses (untracked file would be overwritten) | an old script generated `environment.deepmed2.yml` | delete that untracked file, pull |
| `CUDA not available to torch` | driver older than the +cu130 torch build supports | the pipeline falls back to the CPU variant by itself; mention it to the owner |
| a job killed at the 30 GB cap | memory use above the cap | report it (method, seed, peak GB); raise `CAP_GB` only if the machine has the RAM and the owner agrees |
If a new error appears: read the end of the relevant log, fix the cause minimally (install a missing compiler into the **project**
environment, relax one pin, and so on), run the failing stage again, and tell the owner what you changed. Do not edit the
benchmark code (`scripts/adapters.py`, `scripts/new_methods.py`, `scripts/bench_run.py`, `spatialbench/`).

## 7. Phase 6: finish
When `status.txt` ends with `PIPELINE_DONE`:
```bash
cd /mnt/disk/bikashkumar/SpatialBench/Spatial
tail -25 /mnt/disk/bikashkumar/SpatialBench/status.txt       # the result table: id, status, ARI, peak memory, device
git status --short
git add results/benchmark_runs_bigmem.jsonl results/benchmark_runs_bigmem_gpu.jsonl 2>/dev/null
git commit -m "Rerun of the memory-capped Stereo-seq jobs on DeepMed2"     # if the pipeline did not already commit
git push origin HEAD                                                   # may fail without GitHub credentials: then leave the files and report
ls results/runs/stereo__E10.5_E1S1__* results/runs/stereo__E10.5_E2S1__deepst__* | wc -l
```
`results/runs/*.json|npz` are git-ignored on purpose (large); do **not** force-add them. List them for the owner so they can be
copied back (about 17 jobs x 2 files).

## 8. Final report to the owner (short, plain language)
- Hardware found (CPU, RAM available, GPUs, driver); whether GraphST/DeepST ran on GPU or CPU.
- Per job (method, section, seed): ok or error, ARI, peak memory in GB, device, run time.
- Anything that failed again and why; anything changed in the scripts; anything found in phase 2 about the shared base environment.
- Where the result files are, and whether the push to GitHub worked.
- Note for the owner: run times from DeepMed2 are on a different CPU and are **not** comparable with the paper's timing table; accuracy
  (ARI) and memory are reportable.

## 9. What happens afterwards (not your job, for information)
The cloud session merges the records (append `benchmark_runs_bigmem*.jsonl` to `results/benchmark_runs.jsonl`; analyses keep the newest
record per run id), exports the new embeddings, redoes the initialisation, K-sensitivity and R mclust analyses for the newly working
methods, regenerates every number, figure and table, rebuilds the paper and pushes it to GitHub and Overleaf (see
`docs/BIGMEM_RERUN.md`, section 3).
