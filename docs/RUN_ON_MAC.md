# Running a share of the benchmark on a Mac (Apple silicon)

**Not tested by the authors of this repository on macOS** (it was developed on Linux, CPU only). Treat the
steps below as a starting point and report what breaks.

## 1. What a Mac GPU can and cannot do
* Apple GPUs are used by PyTorch through the **MPS** backend, not CUDA. Many of the benchmarked methods
  (PyTorch Geometric layers, `torch_sparse`/`torch_scatter`, custom sparse ops) have no or partial MPS
  support and silently fall back to the CPU. All adapters in `scripts/adapters.py` run on the **CPU on
  purpose**, so that results and timings are comparable. Expect no speed-up from the GPU unless a method
  is re-written for MPS; do not enable MPS ad hoc for single methods (it breaks the comparison).
* The Mac is still very useful as an **extra CPU machine**: the jobs are independent and can be split.

## 2. What may be split across machines, and what may not
| Quantity | Split across machines? |
|---|---|
| Accuracy and all label-based / spatial metrics, predictions | **Yes**: up to floating-point noise they do not depend on the machine (record library versions) |
| Runtime, peak memory, energy, scaling curves, cost | **No**: each is only valid for one hardware profile. Run the timing jobs for *all* methods on **one** designated machine and report that machine; other machines' timings are reported separately, never mixed |
| Energy | macOS gives no unprivileged power counter; the tool falls back to a per-core estimate that is **not comparable** with a Linux/RAPL measurement |

## 3. Setup (macOS, untested)
1. Xcode command-line tools (`xcode-select --install`), Homebrew, `gfortran`, R (>= 4.3) with `mclust`.
2. A fresh Python environment (3.11 or 3.12 is safer than 3.13 for older packages); `pip install -r requirements.txt`
   plus the packages listed in the zip's README (`torch`, `torch_geometric`, `pybanksy`, `SpaGCN`, `GraphST`, `rpy2`
   matching your R version, `POT`, `leidenalg`, `igraph`, `python-louvain`, `gudhi`, `cmcrameri`, ...).
   `torch_sparse` and `torch_scatter` must be compiled from source on macOS (or avoided: STAGATE can use the
   stub in `scripts/_shims/`).
3. Clone the method repositories into `data/ext/methods/` at the commits recorded in `configs/methods.yaml`;
   install the R packages BASS (from the clone) and BayesSpace v1.5.1 (needs a C++ toolchain; skip them on the
   Mac if the build fails: they are Visium/R jobs that can stay on Linux).
4. Data: `data/DLPFC/<id>/`, and `python scripts/prepare_extra.py` for STARmap and MERFISH (see script header).

## 4. Running a shard
```bash
# machine A (Linux)             machine B (Mac)
python scripts/bench_queue.py --shard 0/2 --out results/benchmark_runs_A.jsonl   # first half of the sorted jobs
python scripts/bench_queue.py --shard 1/2 --out results/benchmark_runs_B.jsonl   # second half
cat results/benchmark_runs_A.jsonl results/benchmark_runs_B.jsonl > results/benchmark_runs_merged.jsonl
```
Use `--methods`, `--datasets`, `--sections`, `--seeds` to choose what to run, `--dry-run` to list the jobs, and
keep the memory-hungry DeepST on a machine with >= 16 GB free (it needs about 7 GB). The queue skips jobs already
recorded in its own output file, so an interrupted run resumes with the same command.

## 5. What to send back
The `.jsonl` result file(s) plus `pip freeze`, `R --version`, `sw_vers` and `sysctl -n machdep.cpu.brand_string`.
