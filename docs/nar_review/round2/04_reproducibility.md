# 04 (round 2): Reproducibility and code/data availability audit (NAR)

Audit date: 2026-10-23. Scope: `HEAD` = `c8aedc1` of branch `claude/great-cori-opzfx7` (working tree clean).
This was a **static audit**. Running the generators again in a clean `git archive` export, as in round 1, was
refused because two R `mclust_seed.R` workers (PIDs 7797 and 8558) are still running and use most of the RAM.
No data were downloaded and nothing except this file was changed.

## Verdict

The new datasets are **half integrated**. On the good side, both have a download script with fixed URLs, they
have SHA-256 entries in `data/CHECKSUMS.sha256`, there is a cache builder, they are in the registry, the runner
handles them, and every result file the numbers depend on is committed. The documented entry points, however,
still describe the 20-section, three-dataset study. `make data`, `make cache`, `make robustness`, README, CITATION and
.zenodo.json, `DATA_AND_LICENCES.md` and `EVIDENCE_MAP.md` do not cover breast cancer or Stereo-seq.
`k_sensitivity.py` is not wired in, the 12 GB cap is not set by `make`, and the step that exports embeddings for
the new sections is not scripted.

Two points are worse than documentation gaps:

* The committed paper numbers come from an **unfinished R experiment**. The commit message says "Final", but only
  1 of 10 embeddings of the largest Stereo-seq section is done.
* The manuscript's statement **"Every job had a memory cap of 12 GB" is false** for the DLPFC BayesSpace runs.

## Blocking gaps (fix before submission)

| # | Gap | Where | Concrete fix |
|---|---|---|---|
| B1 | **Paper numbers built from a running, incomplete experiment.** `results/mclust_seed_g6.csv` (committed in `c8aedc1`, "Final benchmark data …") holds only `banksy_l0.2` for `stereo/E10.5_E1S1`. `results/mclust_seed_summary.csv` has 1 row for that section against 10 embeddings in `results/emb/csv`, and 2 workers are still appending. `\mcsN`=322, `\mcsNBig`=280, `\mcsSeedMeanBig`, `\mcsSeedMax`, `\mcsJitMean` and the other macros, Figure 3B and Supplementary Table `\STmclust` will all change when the workers finish. Nothing in `main.tex` says that this section is only partly covered. | `results/mclust_seed_g6.csv`, `scripts/paper_v2.py:332-357`, `paper/main.tex:283-293` | Either wait for g6 to finish and then run `make numbers supplement figures paper check` and commit, or exclude `E10.5_E1S1` explicitly in `paper_v2.py` and state this in the text. In both cases add a coverage assertion to `paper_v2.py`: the set of (dataset, section, method) in `mclust_seed_g*.csv` must equal the set of `*__k*.csv` embeddings, otherwise exit non-zero or print a macro that the text cites. |
| B2 | **The "memory cap of 12 GB for every job" claim is false and cannot be reproduced.** The cap exists only when `SPATIALBENCH_MAX_RSS_GB` is set; `spatialbench/resources.py:81` defaults to 0 (off). It is set only in `scripts/run_pending.sh:10` (new datasets). In `results/benchmark_runs.jsonl`, `dlpfc__151509__bayesspace__s0` (12.54 GB) and `dlpfc__151510__bayesspace__s0` (12.19 GB) succeeded above 12 GB. With a 12 GB cap a rerun would kill them, and without one the 5 out-of-memory failures on E10.5_E1S1 would not happen on a larger machine. | `paper/main.tex:157`, `:219-220`, `:377`; `Makefile` `benchmark`; `README.md` "Compute" | State the truth in Methods: "a 12 GB cap was applied to the runs on the breast cancer and Stereo-seq sections; the earlier runs had no cap (maximum observed 12.5 GB, BayesSpace)". Alternatively, rerun the two BayesSpace jobs under the cap. In the `Makefile`, set `export SPATIALBENCH_MAX_RSS_GB ?= 12` only for the new-dataset part of `benchmark`, or split the target so that each part uses the cap that produced the published results. Record `threads` and `max_rss_cap_gb` in `rec["resources"]` (`bench_queue.py:40-43`). |
| B3 | **`make data` / `make cache` skip the new datasets.** The `data` target has only `data-dlpfc` and `data-extra`, and `cache` builds DLPFC and STARmap/MERFISH only. The Makefile header and README ("make data — download DLPFC, STARmap, MERFISH") were not updated. Without `results/cache/brca_*.npz` and `stereo_*.npz`, `baselines_3start.py` (called by `make benchmark`), `clustering_lottery.py` and `k_sensitivity.py` cannot run on the new sections. | `Makefile` lines 3-5, 39-52; `README.md` "Data" | Add a `data-new` target (`$(PYTHON) scripts/download_new_datasets.py`) to `data`, and `$(PYTHON) scripts/prepare_new_datasets.py` to `cache`. Add a "Breast cancer and Stereo-seq" bullet to the README Data section with sizes (MOSTA ≈ 2.3 GB: 0.46 + 0.40 + 1.41 GB) and the 10x / CNGB URLs. |
| B4 | **The new analyses cannot be regenerated from documented commands.** (a) `scripts/k_sensitivity.py` (Supplementary Table `\STk`, `\kOneMax` and related macros) is in no Makefile target and not in the README. (b) It and `clustering_lottery.py` read `results/emb/<ds>_<sec>_<method>.npy`. For the new sections, all 13 methods' embeddings were exported from `results/runs/*__s0.npz` by an **unscripted** step: every `stereo_E9.5_E1S1_*.npy` file has the same mtime, 10-21 04:56. The only scripted exporter, `make export-emb`, exports 4 methods. `clustering_lottery.py:48-49` returns `None` for a missing embedding, so `make lottery` on a fresh rerun would silently produce fewer than the 51 committed brca/stereo records. (c) `Makefile` `mclust-seed` uses groups g1–g4, while the committed new-section results are in g5/g6, which come from `run_pending.sh`. Because the g1–g4 regexes have no dataset filter, they would also pick up the new sections. | `Makefile` `export-emb`, `lottery`, `mclust-seed`; `scripts/k_sensitivity.py`; `scripts/clustering_lottery.py:46-49` | Change `export-emb` to export every method that has `emb` in its seed-0 npz, which is what was done. Add a `k-sensitivity` target (`WORKERS=$(WORKERS) $(PYTHON) scripts/k_sensitivity.py`) to `robustness`. Add `mclust-seed-g5`/`g6` with the patterns from `run_pending.sh:14,28`, and restrict g1–g4 to the first three datasets (`^.*/(dlpfc|starmap|merfish)__…`), so that `make` writes exactly the committed file layout. Make `clustering_lottery.py` and `k_sensitivity.py` print, and exit non-zero, when an expected embedding is missing. |
| B5 | **The R mclust memory hazard is undocumented, and the Makefile invites the crash.** The `Makefile` comment recommends `make -j4 mclust-seed`. With the g1–g4 regexes matching the 18,408-bin section, that runs up to 4 R processes on it at about 5 GB each (`run_pending.sh:6`). On the 15 GB machine this is the scenario that, per commit `c360933`, "restarted the machine". R runs are outside `measure_command` and so are not covered by the cap. The README does not mention any of this. | `Makefile` (`mclust-seed`), `README.md` "Compute" | In the README, document "R mclust on stereo E10.5_E1S1: ≈5 GB per process, uncapped; run it alone or with at most 2 workers on 16 GB". In the Makefile, run `mclust-seed-g6` last and alone (`.NOTPARALLEL: mclust-seed-g6`, or a separate target), and set `WORKERS6 ?= 1`. Optionally wrap the R calls in `ulimit -v` or `systemd-run --scope -p MemoryMax=6G`. |
| B6 | **Licences and terms for the new datasets are not recorded.** `docs/DATA_AND_LICENCES.md` §1 lists only DLPFC, STARmap and MERFISH. `configs/datasets.yaml` has `license: {status: to_check}` for brca ("CC BY 4.0 (to confirm)") and stereo ("CNGB STOmics DB terms of use"). The Data availability section (`main.tex:388-394`) states no licences. | `docs/DATA_AND_LICENCES.md`, `configs/datasets.yaml:91,109`, `paper/main.tex:388-394` | Add two rows to `DATA_AND_LICENCES.md`. (1) 10x Genomics V1_Breast_Cancer_Block_A_Section_1 (Space Ranger 1.1.0): exact URLs, the 10x dataset licence (verify on the dataset page; usually CC BY 4.0, which requires attribution), and SEDR_analyses `data/BRCA1/metadata.tsv` at `00084465…` with "no licence file". (2) MOSTA: CNGB STOmics STDS0000058 and CNGdb terms of use (quote the clause), citing Chen et al., Cell 2022. Set `license.status` to the verified value, and add one licence clause per dataset to the Data availability section. |
| B7 (carried over) | Code DOI and URL still missing: `main.tex:394` `\todo{GitHub URL and Zenodo DOI}` and `main.tex:15` `\DOI{DOI HERE}`. There is no `main` branch, tag or Zenodo record (round-1 P0-1). | `paper/main.tex`, `CITATION.cff`, `.zenodo.json` | As in round 1: create a `main` branch, a `v1.0.0` tag, the GitHub–Zenodo release, and a data record for `results/runs` (190 MB) and the seed-0 `results/emb` (1.5 GB). Then fill in the URL and DOI. |

## Minor gaps

| # | Gap | Where | Concrete fix |
|---|---|---|---|
| m1 | `CITATION.cff` (abstract) and `.zenodo.json` (description, keywords) still say "20 tissue sections from 10x Visium (DLPFC), STARmap and MERFISH". | `CITATION.cff:24-27`, `.zenodo.json` | Change to 24 sections and five datasets, and add "Stereo-seq" and "breast cancer" to the keywords. |
| m2 | README "Compute" still gives "~150 CPU-hours" and "peak … up to 12.5 GB for BayesSpace, 9.2 GB for DeepST, 7.2 GB for NichePCA". The new runs (CCST > 5 h per run on E10.5_E1S1; 5 methods out of memory at 12 GB) are not included, and the cap is not mentioned. The Makefile header says "<= 13 GB RAM per job". | `README.md`, `Makefile:5` | Recompute the CPU-hours from `benchmark_runs.jsonl` (`resources.cpu_s`). Add the cap, the 5 out-of-memory methods and the 6 h `--timeout` default (`bench_queue.py`); CCST on the largest section is close to that limit. |
| m3 | `make benchmark` reruns CCST with 3 seeds on E10.5_E1S1, but the paper has 2 (`run_pending.sh:21-22`). It also does not separate the per-dataset queue order that `run_pending.sh` used. | `Makefile` `benchmark`, `scripts/run_pending.sh` | Either document `run_pending.sh` as the exact recipe for the new datasets (call it from a `benchmark-new` target, without the backgrounded R line), or exclude CCST seed 2 on that section in the Makefile and say so. |
| m4 | `mclust_seed.R` lock mode. (a) A lock directory left by a crash or container restart is never cleared, so that embedding is skipped silently forever, and the run still ends normally (two lock directories exist now, for the live workers: `results/mclust_seed_g6.csv.lock_stereo_E10.5_E1S1_{anisost,banksy_l0.8}`). (b) The header race: two workers starting on a missing output file can both write a header (`col.names = !file.exists(out)`), and appends are not serialised. | `scripts/mclust_seed.R:19-41` | Write the PID and host into the lock (`writeLines(Sys.getpid(), file.path(lock,"pid"))`) and remove locks whose PID is dead at start-up. Write each embedding's rows to `out.d/<ds>_<sec>_<method>.csv` with an atomic `file.rename`, and merge them at the end, or append while holding a second global lock. At exit, list any matching embeddings that are not in `out`. Document the multi-worker mode in the script header and in the README (`Rscript scripts/mclust_seed.R <dir> <same out.csv> <regex>` started N times). |
| m5 | `download_new_datasets.py:89-96` uses trust-on-first-use: a file without a checksum entry is **added** to `CHECKSUMS.sha256` rather than rejected. The entries exist now, so third parties do verify, but a future file or a renamed path would pass silently. It also spoofs `User-Agent: curl/8.5.0` for cf.10xgenomics.com, which is fragile. | `scripts/download_new_datasets.py` | Add a `--record` flag that is off by default, and fail on unlisted files. Document a manual `curl -O` fallback with the same URLs. |
| m6 | `run_qc.py` (needed for Supplementary Table `\STqc`, through `results/qc/section_qc.csv`) is in no Makefile target, and its docstring still promises a `docs/QC_REPORT.md` that does not exist. | `scripts/run_qc.py:1`, `Makefile` | Add `$(PYTHON) scripts/run_qc.py` after `cache`, and fix the docstring. |
| m7 | `docs/EVIDENCE_MAP.md` was last changed on 2026-10-15 and has no entry for the breast cancer and Stereo-seq results, K sensitivity, the out-of-memory statement or the mclust seed experiment. | `docs/EVIDENCE_MAP.md` | Add rows: claim → `results/k_sensitivity.jsonl` / `k_sensitivity_summary.csv` → `\STk`; out-of-memory → `benchmark_runs.jsonl` `error` contains "out of memory" → `\nOom`/`\listOom`; tissue dependence → `stats_cluster_aware.json`. |
| m8 | `check_paper_numbers.py` still checks only the 8 DLPFC/STARmap/MERFISH literals. It has no check for the new datasets and does not check that `paper_macros.tex` is up to date. B1 would have been caught by such a test. | `scripts/check_paper_numbers.py` | Add `make check-fresh`: rerun `numbers supplement`, then `git diff --exit-code results/ paper/supp*.tex`. Also add the coverage assertions from B1 and B4. |
| m9 | Superseded statement in `datasets.yaml:103`: the MOSTA label provenance is "algorithm, verified: false … confirm before ranking". Not a reproducibility issue, but it decides whether the Stereo-seq ranking can be shown. | `configs/datasets.yaml` | Verify the provenance against Chen et al. 2022 Methods, and set `verified: true`. |
| m10 | `paper/suggested_reviewers.md` and `paper/cover_letter.md` are tracked; they are confidential submission material. `scripts/push_overleaf.sh:8` still has the private Overleaf project ID as a default, and lines 1-12 include the author's e-mail. | as listed | Remove these files from the public release (`git rm --cached`, and keep them elsewhere). Make `push_overleaf.sh` read `$OVERLEAF_PROJECT` with no default. |

## Status of the round-1 points (`docs/nar_review/04_reproducibility.md`)

| # | Round-1 item | Status now | Evidence / remaining fix |
|---|---|---|---|
| P0-1 | Public repo and DOI | **OPEN** | `main.tex:15,394` TODOs; CITATION/.zenodo DOI commented out; no tag. See B7. |
| P0-2 | LICENSE | **FIXED** | MIT `LICENSE` with the HiSTaR third-party notice. The authors still have to confirm the choice (README). |
| P0-3 | Download scripts + checksums | **FIXED for the original 3 datasets, PARTIAL overall** | `download_dlpfc.py`, `make data-extra`, `data/CHECKSUMS.sha256` (DLPFC 24, BASS 2, BRCA 3, Stereo 3 entries). The new datasets are not reachable through `make data` (B3). |
| P0-4 | Software versions | **MOSTLY FIXED** | HiSTaR commit recorded (`0039a3b`, inferred). The `methods.yaml:1` warning that publication fields are "NOT verified" remains, and CCST says "volume and pages to verify". Verify them and delete the warning. |
| P0-5 | Environment | **FIXED** | `environment/environment.yml`, `requirements-lock.txt` (135 lines), `R-packages.txt`, `R-sessionInfo.txt`. Still no `install_methods.sh` for clone-based methods (README has one example) and no Docker image (recommended). |
| P0-6 | Large intermediates (Fig 1, 5) | **OPEN** | Still not archived. Sizes have grown: `runs/` 190 MB, `emb/` 1.5 GB, `cache/` 92 MB. Fig 5 still needs `results/cache/151673.npz` and `results/runs/dlpfc__151673__*__s0.npz`. |
| P1-1 | README | **FIXED, but stale for the new data** | Rewritten with tiers and layout (good). See B3, B5, m2. |
| P1-2 | Makefile | **FIXED, but stale for the new data** | Targets exist. Missing: new datasets, `k_sensitivity`, export of all embeddings, g5/g6, cap, `run_qc` (B2–B5, m3, m6). `run_fill_v2.sh` still has git/Overleaf side effects (the README flags this). |
| P1-3 | Item → script map | **PARTIAL** | `EVIDENCE_MAP.md` is linked from the README but stale (m7). |
| P1-4 | Number checking | **PARTIAL** | Unchanged scope (m8). No CI (`.github/` absent). |
| P1-5 | Versions per run record | **OPEN** | `bench_run.py` still writes no `env` (package versions, git SHA, host, cap). |
| P1-6 | Seeds | **PASS** | Unchanged. The new R seeds (1..10, 101..105 for jitter) are explicit in `mclust_seed.R`. |
| P1-7 | Dataset licences | **OPEN** | All five datasets still have `license.status: to_check`. DATA_AND_LICENCES now has a table for 3 datasets, but no rows for BRCA/Stereo (B6). |
| P1-8 | Method code licences | **PARTIAL** | Table in `DATA_AND_LICENCES.md` §2 (good). The CCST port (`scripts/new_methods.py`) still needs permission or a statement that it was rewritten independently. |
| P1-9 | Interactive browsing | **OPEN** | No site or app. |
| P2-1 | Secrets | **PASS** | Tracked files and history since 2026-10-17 scanned for Overleaf/GitHub/AWS/Anthropic tokens, private keys and `user:pass@` URLs: none found. Same for `.git/config`. |
| P2-2 | Private identifiers | **OPEN** (acknowledged in README) | `scripts/push_overleaf.sh:8` project-ID default; e-mail in `push_overleaf.sh`, `paper/cover_letter.md`; also `paper/suggested_reviewers.md` (m10). |
| P2-3 | Absolute paths | **PARTIAL** | `install_r_pkg.sh:5` fixed (relative `RSRC`). `/home/user/Spatial` is still embedded in tracebacks: `results/benchmark_runs.jsonl` (6 lines), `results/feasibility.jsonl` (4), `results/new_methods.jsonl` (3). Strip the prefix. Defaults to `/tmp` in `run_pending.sh:11` are harmless. |
| P2-4 | Commit authorship | **OPEN** | All 335 commits are authored by "Claude". `.git` keeps growing with results snapshots. Squash for the public release. |
| P2-5 | Stray generated files | **OPEN** | `deliverables/*` (13-method-era PDF and zip), `paper/main.pdf`, `paper/supplementary.pdf`, `paper/SUBMISSION_CHECKLIST.md` are still tracked. |
| P2-6 | CITATION.cff | **FIXED, but stale** | Exists. Says 20 sections and 3 technologies (m1); DOI and ORCID are TODO. |
| P2-7 | Stale docs | **PARTIAL** | "Bioinformatics Advances" still appears in `paper/SUBMISSION_CHECKLIST.md`, `scripts/push_overleaf.sh`, `docs/AnisoST.md`. `QC_REPORT.md` is still missing (m6). |
| P2-8 | Unit tests | **Not re-run** (static audit) | `tests/` present. No tests for the `brca`/`stereo` loaders. Add a tiny synthetic fixture. |
| P3-1 | NaN in JSONL | **OPEN** | `benchmark_runs.jsonl` still has bare `NaN` (1124 lines affected). |
| P3-2 | PDF determinism | **OPEN** | No `CreationDate`/`SOURCE_DATE_EPOCH` handling in `make_figures_nar.py`. |
| P3-3 | Compute statement | **PARTIAL** | In the README, but stale (m2). |
| P3-4 | Smoke test | **OPEN** | No `make smoke`. |

## Answers to the specific questions

* **Can a third party download the new data?** Yes, through `python scripts/download_new_datasets.py`. The URLs
  are fixed: 10x `cf.10xgenomics.com/.../1.1.0/V1_Breast_Cancer_Block_A_Section_1/` and CNGB
  `ftp.cngb.org/.../STDS0000058/...MOSTA.h5ad`. The annotation is pinned to SEDR_analyses commit `00084465`. Downloads
  resume after interruption, and all 6 new files have SHA-256 entries. `make data` does not call the script (B3), and
  the licences and terms are not recorded (B6).
* **Can the caches be regenerated?** Yes, with `python scripts/prepare_new_datasets.py`, but this command is not in
  `make cache` (B3).
* **Can the runner be rerun?** Yes: `bench_queue.py --datasets brca stereo …`, and the loaders are in
  `spatialbench/data.py`. The exact recipe, including the cap, the seed exceptions and the order, is only in the
  maintainer script `scripts/run_pending.sh` (B2, m3).
* **Can every number, table and figure be regenerated?** From the committed results, the number, table and
  supplement scripts read only tracked files (checked: the only untracked inputs are `results/cache` and
  `results/runs`, for Fig 5). Rebuilding the robustness inputs for the new sections is not scripted (B4). The
  committed numbers come from an unfinished experiment (B1).
* **Are the memory requirements documented?** No. The 12 GB cap appears only in `run_pending.sh` and the manuscript,
  and the manuscript claim is inaccurate (B2). The R mclust memory on the 18k-bin section is documented only in the
  `run_pending.sh` header (B5).
* **Are the result files committed?** Yes: `benchmark_runs.jsonl`, `baselines_3start.jsonl`,
  `clustering_lottery.jsonl`, `k_sensitivity.jsonl`, `mclust_seed_g1..g6.csv`, `qc/section_qc.csv` and the
  summaries are tracked. g6 is incomplete (B1).
* **Are there absolute paths or secrets?** No secrets. Absolute paths appear only inside the traceback strings of 3
  result files (P2-3). There are private identifiers in `push_overleaf.sh` and tracked confidential submission files
  (m10).
