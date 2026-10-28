# Rerun of the memory-capped jobs on a large-memory machine

Five methods (BASS, GraphST, NichePCA, Spatial-MGCN, DeepST) exceeded the 12 GB per-job cap on Stereo-seq E10.5_E1S1
(18,408 bins) on the 15 GB benchmark machine, and DeepST seeds 1-2 on E10.5_E2S1. This reruns them on a machine with
at least 64 GB of free RAM (CPU only; GPUs are not needed and would change the numbers).

## 1. Setup (once): `bash scripts/setup_deepmed2.sh 2>&1 | tee setup_deepmed2.log`
The script puts everything under `/mnt/disk/bikashkumar/SpatialBench` (code, conda environment, data, results); the manual steps it performs are:
```bash
git clone <repository URL> spatial && cd spatial && git checkout claude/great-cori-opzfx7
conda env create -f environment/environment.yml -n spatialbench && conda activate spatialbench   # see README "Installation"
pip install -r environment/requirements-lock.txt     # exact versions
# R packages (BASS, mclust, ...): see environment/R-packages.txt
python scripts/download_new_datasets.py              # Stereo-seq E10.5_E1S1 and E10.5_E2S1 (several GB) + checksums
python scripts/prepare_new_datasets.py
free -g                                              # the "available" column should be >= 64
```
## 2. Run (about 12-24 h; resumable)
```bash
nohup sh scripts/rerun_memory_failures.sh > bigmem.log 2>&1 &
tail -f bigmem.log                                   # ends with BIGMEM_DONE
```
Other users share the machine: the script runs 2 jobs at a time (`WORKERS=1` to be gentler) and kills any job above
30 GB (`CAP_GB`).

## 3. Send the results back
Copy `results/benchmark_runs_bigmem.jsonl` and the new `results/runs/stereo__E10.5_E1S1__*` and
`results/runs/stereo__E10.5_E2S1__deepst__*` files (`json` and `npz`) into the repository (or `git add` and push them from
that machine). The analysis scripts use the newest record per run id, so the new records replace the earlier out-of-memory
records once appended to `results/benchmark_runs.jsonl`:
```bash
cat results/benchmark_runs_bigmem.jsonl >> results/benchmark_runs.jsonl
python scripts/export_runner_emb.py && python scripts/clustering_lottery.py && python scripts/k_sensitivity.py
python scripts/stats_cluster_aware.py && python scripts/paper_v2.py   # etc.: make numbers supplement figures paper
```
The text that lists the methods stopped at the cap (`\listOom`, the README Compute section, Limitations) then changes
automatically or needs a one-line edit; the run times of these jobs come from a different CPU and are kept out of the
timing comparison.

## Optional: use a GPU for GraphST and DeepST
```bash
nvidia-smi                      # driver version must support CUDA 13 (the locked torch build is +cu130; Turing GPUs are supported)
DEVICE=cuda GPU=1 nohup sh scripts/rerun_memory_failures.sh > bigmem_gpu.log 2>&1 &    # GPU=1 -> the second GPU
```
Only GraphST and DeepST use the GPU; BASS, NichePCA and Spatial-MGCN still run on CPU. The memory failures happened in
CPU-side graph construction before training, so the GPU does not remove the need for large host RAM; it only shortens
training. GPU results go to `results/benchmark_runs_bigmem_gpu.jsonl` with `"device": "cuda"` in each record, are not
bit-identical to CPU runs, and must be marked as GPU runs in the paper and left out of the run-time comparison. I recommend
the CPU variant for consistency and at most the GPU for DeepST/GraphST if the CPU runs prove too slow.

## Safe way to run it (survives closing the laptop)
```bash
cd /mnt/disk/bikashkumar/SpatialBench/Spatial && git pull
bash scripts/run_detached.sh cuda      # or: cpu    (starts scripts/deepmed2_pipeline.sh detached with setsid + nohup)
bash scripts/run_detached.sh status    # progress, running jobs, RAM and GPU memory; also fine from a new SSH session
```
The pipeline does setup, waits until 64 GB of RAM is available, runs the jobs (restarting them up to 5 times; finished jobs are
skipped), and commits and pushes the result records. It does not depend on the SSH connection, on your laptop or on a Claude
session. After a server reboot, run the same `run_detached.sh` command again; nothing is lost. Progress is in
`/mnt/disk/bikashkumar/SpatialBench/status.txt`, details in `pipeline.log`, `setup_deepmed2.log` and `rerun.log`.
