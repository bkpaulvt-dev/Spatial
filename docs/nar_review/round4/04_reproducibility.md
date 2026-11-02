# 04 (round 4, final): Reproducibility and code/data availability re-audit (NAR)

Audit date: 2026-11-02. Scope: `HEAD` = `e755ad5` of `claude/great-cori-opzfx7` (working tree clean). Static audit plus `make -n`
and the read-only `scripts/check_paper_numbers.py` (7/7 claims, 119/119 macros defined). Nothing was downloaded; no file other
than this report was changed. Secret values are never reproduced; only locations are given.

**Author-side placeholders (listed once, not defects):** GitHub URL and Zenodo DOI (`main.tex:15` `\DOI{DOI HERE}`, Data
availability `\todo{GitHub URL and Zenodo DOI}`, DOI commented out in `CITATION.cff`, `"notes": "TODO before deposit"` in
`.zenodo.json`, ORCID TODO, no tag), licence confirmation (MIT choice; `configs/datasets.yaml` lines 23, 48, 64, 89, 108
`status: to_check`; 10x CC BY 4.0 and CNGB terms "to confirm"; CCST port permission), and the repository URL in
`CITATION.cff`/`.zenodo.json`/`setup_deepmed2.sh` (`bkpaulvt-dev/Spatial`, may be private until release).

## Verdict

The new rerun/merge chain is mostly documented and the earlier Makefile gaps (N2, N3, N4) are fixed. A third party can
reproduce the 17-job rerun and the merge, **but only by following `docs/BIGMEM_RERUN.md` section 3 with a different command than
the one it prints, and not through `make`**. Four items need action before release:

1. **Result set is not final.** The R mclust worker for `stereo__E10.5_E1S1__graphst` is still running (live process and lock
   directory `results/mclust_seed_g6.csv.lock_stereo_E10.5_E1S1_graphst`; the commit message of `e755ad5` says so). Coverage is
   332 of 336 exported embeddings: missing are E10.5_E1S1 `deepst`, `graphst`, `nichepca`, `spatial_mgcn`. The macros
   (`\mcsN`=332, `\mcsNBig`=290) and the committed PDFs/supplement therefore reflect a partial set. B1 of round 2 is open again for these
   four embeddings until the run finishes and `make numbers supplement figures paper` is rerun (N5: still no coverage assertion).
2. **Stale merge instruction.** `docs/BIGMEM_RERUN.md:35` (and DEEPMED2_RUNBOOK section 9) says
   `cat results/benchmark_runs_bigmem.jsonl >> results/benchmark_runs.jsonl`. That omits the `host` tag, so the DeepMed2 run times
   would enter the timing tables. The correct step is `python scripts/merge_bigmem.py` (in README only).
3. **Personal and lab identifiers in tracked files** (section below): lab server name, owner's full name and server home path in
   scripts/docs, institutional e-mail in the cover letter, Overleaf project ID.
4. Maintainer/review material and stray artefacts are still tracked (P2-5, m10).

## The 17-job rerun and the merge: can a third party reproduce them?

| Check | Result | Evidence |
|---|---|---|
| Job list matches the paper | Yes | `rerun_memory_failures.sh`: E10.5_E1S1 x {bass, graphst, nichepca, spatial_mgcn, deepst} x seeds 0-2 = 15, plus E10.5_E2S1 DeepST seeds 1-2 = 2. `benchmark_runs_bigmem.jsonl` has 20 lines for 17 unique ids (3 duplicate GraphST reruns), all `device: cpu`, 17 ok/error mix. Text (`main.tex:161-166`, supplement `SNcompute`, README) says 17. |
| Setup reproducible | Mostly | `setup_deepmed2.sh` + `environment.deepmed2.yml` pin Python 3.13, R 4.3, mclust 6.0.1, torch 2.14.1, lock file with `--no-deps`, BASS commit, DeepST `e37997f`, Spatial-MGCN `cf4412d`; checksums verified (`--verify-only`). Needs conda, git, about 30 GB disk, >= 64 GB RAM. Lab-specific: default `BASE=/mnt/disk/bikashkumar/SpatialBench`, `REPO`, `BRANCH` are overridable by env vars, but the defaults are personal. `setup_deepmed2.sh` does not run `prepare_new_datasets.py`, whereas `BIGMEM_RERUN.md` lists it; `bench_run.py` appears to prepare on demand, not verified here (no execution). |
| Merge | Works, idempotent | `merge_bigmem.py` adds `host="deepmed2"` and de-duplicates on the full record. In `benchmark_runs.jsonl` there are 20 host-tagged lines for 17 ids and, for all 17, the newest record is the host-tagged one. `paper_v2.py:417-419` and `make_supplement.py:201-202` blank run time and energy for records with a host tag; memory is kept. |
| Host tag is derived, not measured | Weak | The tag is hard-coded to the string `deepmed2` (also tags any other machine's file), and the records store no CPU, RAM or hostname. A third party who reruns elsewhere gets the tag `deepmed2` too. Suggest `HOST=<name>` argument and storing `cpu_model`/`ram` in the record. |
| Makefile covers it | **No** | `make -n benchmark-new` runs the capped job (`SPATIALBENCH_MAX_RSS_GB=12`), which reproduces the 17 out-of-memory records; there is no `benchmark-bigmem`/`merge-bigmem` target, and `finish_bigmem_analyses.sh` (export, lottery, K-sensitivity, g6 on the four merged methods) is only in the docs/scripts. Order that works: `benchmark-new` -> `sh scripts/rerun_memory_failures.sh` -> `python scripts/merge_bigmem.py` -> `bash scripts/finish_bigmem_analyses.sh` or `make robustness`. |
| `--retry-errors` / `--out` logic | OK | `bench_queue.py:57-64`: the done-set is read from `--out`, so the rerun file is independent of the main file. `--shard i/n` exists but is not used by any script or doc. |
| Scripts documented | Partly | README "Compute" names `rerun_memory_failures.sh`, `merge_bigmem.py`, `export_runner_emb.py`, `brca_coarse.py`, `docs/BIGMEM_RERUN.md`. It does not mention `setup_deepmed2.sh`, `deepmed2_pipeline.sh`, `run_detached.sh`, `finish_bigmem_analyses.sh`, nor the README layout table (`environment.deepmed2.yml` is not in the "environment/" row). The runbook (`DEEPMED2_RUNBOOK.md`) is an operational prompt for a Claude agent on the lab server, not a reproduction document. |
| GPU variant | Unmerged | `rerun_memory_failures.sh` can write `benchmark_runs_bigmem_gpu.jsonl`, which `merge_bigmem.py` does not read by default. No GPU records were committed, which agrees with the supplement. Fine, but say so. |
| `deepmed2_pipeline.sh` commits | Hygiene | Commits as `DeepMed2 run <deepmed2@localhost>` and pushes to `origin`; for a public release this is a maintainer-only script. |

## GraphST mclust wrapper

* **Code:** `scripts/adapters.py:86-98` defines `mclust_R` as an R function wrapper (fixes the mclust 6.x `dimnames` error when
  called directly via rpy2), monkey-patched into `GraphST.utils`. `datatype="Stereo"` is automatic for `ds == "stereo"` (`:103-105`).
* **Documented:** `main.tex:165-166` and the supplement `SNcompute` state the wrapper and that it gave identical labels on "test
  embeddings"/"two sections". `configs/methods.yaml:24` records the `datatype='Stereo'` deviation but **not** the wrapper (the
  wrapper is a code change to all GraphST runs, also DLPFC), and the equivalence test itself is not in the repository (no script, no
  result file) and the wrapper's comment says the "same result" without evidence.
* **Status: partly resolved.** Add the wrapper to `methods.yaml` deviations and commit the equivalence check as a script or CSV.

## Secrets, tokens, passwords, personal hostnames, absolute paths

* **Secrets: pass.** `git grep` for key/token/password/credentialed-URL patterns over all tracked files (including results and
  paper) finds only the word "token" in HiSTaR/HiCAST model code ("mask token") and docs, and "Never write passwords, tokens ..."
  in the runbook rule 6. No credentialed URLs. `scripts/push_overleaf.sh:2` mentions a "saved Basic-auth secret" (the secret itself
  is not stored). `run_detached.sh` writes an optional ntfy topic to `$BASE/ntfy_topic` outside the repository; only the placeholder
  `<your-secret-topic>` is tracked.
* **Personal/lab identifiers (location only):**
  * lab server name "DeepMed2": `README.md:161`, `docs/BIGMEM_RERUN.md` (title lines, 54, 60), the whole of
    `docs/DEEPMED2_RUNBOOK.md` (file name, title, 3, 9, 12 ...), `scripts/deepmed2_pipeline.sh`, `scripts/setup_deepmed2.sh`,
    `scripts/run_detached.sh`, `scripts/merge_bigmem.py:1,3,17`, `scripts/paper_v2.py:417`, `environment/environment.deepmed2.yml:1`, and
    as the data value `"host": "deepmed2"` in `results/benchmark_runs.jsonl` (20 lines);
  * the owner's full name and server home directory `/mnt/disk/bikashkumar/SpatialBench`: `scripts/setup_deepmed2.sh:3,11`,
    `scripts/deepmed2_pipeline.sh:6`, `scripts/run_detached.sh:7`, `docs/BIGMEM_RERUN.md:8,53,60`, `docs/DEEPMED2_RUNBOOK.md` (about
    15 lines), `DEEPMED2_RUNBOOK.md:3` ("the owner (Bikash Kumar Paul)"); the user name `bikashkumar` also reveals the account;
  * institutional e-mail address: `paper/cover_letter.md:27`; author name is expected in LICENSE, `CITATION.cff`, `.zenodo.json`;
  * Overleaf project ID (private): default value in `scripts/push_overleaf.sh:8`, nowhere else (git grep);
  * GitHub account `bkpaulvt-dev`: `CITATION.cff:8`, `.zenodo.json:13`, `setup_deepmed2.sh:12`, `DEEPMED2_RUNBOOK.md:15` (expected once the repository is public, but the runbook also says "a private repository asks for your GitHub login");
  * absolute container path `/home/user/Spatial` in error strings of `results/benchmark_runs.jsonl` (6 lines), `results/feasibility.jsonl`
    (4), `results/new_methods.jsonl` (3). None in scripts, Makefile, README, configs;
  * `/tmp/ksens_bigmem.log` in `finish_bigmem_analyses.sh` (harmless); the git author of all 379 commits is "Claude <noreply@anthropic.com>".
* **Verdict on the lab server / owner account:** the DeepMed2 name, the `/mnt/disk/bikashkumar` path and the owner's name belong in a
  maintainer log, not in a public release. Recommended: keep `merge_bigmem.py` and `rerun_memory_failures.sh` (generic), rename
  the host tag to a neutral value (for example `"host": "bigmem"`) or leave it and describe it as "a second server with 125 GB RAM", and
  move `DEEPMED2_RUNBOOK.md`, `deepmed2_pipeline.sh`, `run_detached.sh`, `setup_deepmed2.sh` (replace the `BASE` default by `$PWD/..`), and
  `push_overleaf.sh`/`package_overleaf.sh` out of the release tree (or into `maintainer/`). The README already lists
  `push_overleaf.sh` as maintainer-only; the DeepMed2 files are not on that list.

## Large intermediates (`results/runs`, `results/emb`, `results/cache`)

Handled consistently in policy, not yet in fact:
* `.gitignore`: `results/runs/`, `results/emb/`, `results/cache/`, `*.npz`, `data/*`. No `results/runs` files tracked (0). The
  DeepMed2 runbook and `BIGMEM_RERUN.md` section 3 say to copy `results/runs` files back by hand and "do not force-add".
* README "Large intermediates" says 138 MB / 1.1 GB / 45 MB; actual (this audit) 200 MB / 1.6 GB / 92 MB (earlier: 190 MB / 1.5 GB /
  92 MB). **Stale again.** README says they "will be archived on Zenodo (DOI to be added)"; `Makefile` header says "see README". The
  17 rerun runs are not in git and are not re-creatable without the 125 GB server. Tier 2 of the README ("Figures and PDFs") needs
  them for Figures 1 and 5, so without the Zenodo deposit a third party cannot rebuild those figures from the repository alone.
* Untracked but present: `results/mclust_seed_g6.csv.lock_*` (live lock directory; not ignored, would be picked up by `git add -A`
  once the run ends and not removed on crash). Add `*.lock_*` to `.gitignore`.

## Round-3 report, point by point

### Round-2 blocking items

| # | Round-3 status | Round-4 status | Evidence |
|---|---|---|---|
| B1 numbers from complete experiment | Resolved | **Partly (regressed)** | 332 of 336 embeddings; four E10.5_E1S1 embeddings (deepst, graphst, nichepca, spatial_mgcn) still pending, graphst fit is running. Macros/PDFs of `e755ad5` are from the partial set; `paper_v2.py:347` (`ok_` filter) still drops incomplete embeddings silently. Finish and regenerate. |
| B2 12 GB cap claim | Resolved (text); partly (Makefile) | **Mostly resolved** | Text as before; header lines 8-9 now say the cap is set "only for this target" and `Makefile:84` sets it inside `benchmark-new` only (the global `export ... ?= 12` is gone). Still: Makefile header line 7 says "<= 13 GB RAM per job" next to a 12 GB cap; records still do not store the cap or kill reason (`bench_queue.py`, `resources.py:81`). |
| B3 `make data`/`cache` skip new datasets | Resolved (Makefile); partly (README) | **Partly** | Makefile unchanged and fine (`data-new`, `cache`). README "Data" section still lists only DLPFC and STARmap/MERFISH; breast cancer and MOSTA have no bullet, URL or size. |
| B4 new analyses regenerable | Mostly | **Mostly** | `export-emb`, lottery, `k-sensitivity`, `mclust-seed-g5/g6` in `robustness`. Overlap of g1-g4 with g5/g6 and the silent `None` in `clustering_lottery.py` are unchanged. Now also `finish_bigmem_analyses.sh` duplicates the g6 call for four methods. |
| B5 R mclust memory hazard | Partly | **Partly** | Documentation of ~5 GB per fit and two-worker limit present; no `.NOTPARALLEL`; `make -j2 mclust-seed` may run g1/g2 and g6 on the same big embedding. |
| B6 licences of new datasets | Partly | **Partly (author side)** | Still "to confirm"; Data availability gives sources only. |
| B7 code URL/DOI | Placeholder | **Placeholder** | See above. |

### Round-2 minor items

| # | Round-3 | Round-4 | Evidence |
|---|---|---|---|
| m1 CITATION/.zenodo | Partly | **Partly** | `CITATION.cff` abstract is current. `.zenodo.json` keywords still end at "STARmap", "MERFISH" (no Stereo-seq, breast cancer). |
| m2 compute statement | Partly | **Partly** | README now covers the rerun, peak memory per method, hosts. Still "about 150 CPU-hours" (records sum to about 226 h incl. rerun), sizes stale (see above), and **CPU of the main machine is inconsistent**: README "Intel Xeon (2.1 GHz)" vs `supplementary.tex:32` and `make_supplement.py:298` "Intel Xeon (2.8 GHz)". Makefile "<= 13 GB". |
| m3 `benchmark-new` vs recipe | Not resolved | **Partly** | `benchmark-new` still `--seeds 0 1 2` for every method on every section (CCST seed 2 on E10.5_E1S1 about 5.5 h; paper reports 2 seeds). README now lists the four queue scripts "as a record of exactly what ran" (N1 resolved) and says the Makefile targets "reproduce the same results from scratch" (not exact for CCST seed 2 and the noise repetitions). |
| m4 `mclust_seed.R` lock/header race | Not resolved | **Not resolved** | `mclust_seed.R:21-41` unchanged: no PID in lock, no start-up cleanup; the live stale-lock directory in the tree shows the practical impact. |
| m5 TOFU checksums, UA spoof | Not resolved | **Not resolved** | `download_new_datasets.py:13-14,52,77-88` unchanged; but all 6 new files are listed in `CHECKSUMS.sha256` (30 lines) and `--verify-only` exists. |
| m6 `run_qc.py` | Partly | **Partly** | `make qc` exists; docstring still names `docs/QC_REPORT.md`, which does not exist. |
| m7 EVIDENCE_MAP | Not resolved | **Not resolved** | 0 matches for brca, stereo, mclust_seed, K sensitivity, out of memory, bigmem; last change 2026-10-15. |
| m8 number check | Partly | **Partly** | 119/119 macros defined; no freshness or coverage check (it would have caught B1 above). |
| m9 MOSTA label provenance | Partly | **Partly** | As before. |
| m10 confidential files / Overleaf ID | Not resolved | **Not resolved** | `paper/cover_letter.md`, `paper/suggested_reviewers.md`, `paper/SUBMISSION_CHECKLIST.md` tracked; project ID default in `push_overleaf.sh:8`; `docs/nar_review/round2..round3` review reports are tracked too (they discuss reviewers' weaknesses; remove from the release). |

### Round-1 carry-overs

| Item | Round-4 status | Evidence |
|---|---|---|
| P0-6 large intermediates archived | **Not resolved** | Not deposited; consistent git-ignore policy (above). |
| P1-5 per-run env / git SHA | **Not resolved** | Records have no package versions, SHA or cap; the new host tag is a name only. |
| P1-7/P1-8 licences | **Not resolved (author side)** | CCST port permission still open (`DATA_AND_LICENCES.md`). |
| P2-1 secrets | **Pass** | See above. |
| P2-3 absolute paths | **Not resolved** | 13 lines in three result files; plus new `/mnt/disk/bikashkumar` paths in scripts and docs. |
| P2-4 authorship | **Not resolved** | 379 commits by "Claude"; squash for release. |
| P2-5 stray files | **Not resolved** | `deliverables/*` (13-method era), `paper/main.pdf`, `paper/supplementary.pdf` tracked. |
| P3-1 NaN in JSONL | **Not resolved** | Bare `NaN` in `benchmark_runs.jsonl`; readers take the newest record per id, which is exactly what the merge relies on. |

### New gaps of round 3

| # | Round-4 status | Evidence |
|---|---|---|
| N1 one-off scripts undocumented | **Resolved** | README "Compute" last paragraph lists `run_pending.sh`, `run_deepst_seeds.sh`, `rerun_graphst_stereo.sh`, `finish_queue.sh` and what each does. They still poll `ps`; `finish_bigmem_analyses.sh` is not listed. |
| N2 g6 recipe vs run | **Resolved** | `Makefile:145` sets `MCLUST_NO_JIT=1`; header text above the rule says "without the noise repetitions except where already run". `main.tex:306` text vs `jrng` for E10.5_E1S1 not rechecked in detail (macro-level only: `check_paper_numbers.py` passes). |
| N3 `brca_coarse.py` not in a target | **Resolved** | In `numbers` (`Makefile:156`). It still skips silently when `results/brca_coarse.json` is missing in `paper_v2.py`/`make_supplement.py`; `results/brca_coarse.json` is committed. |
| N4 graphical abstract not in `figures` | **Resolved** | `make_graphical_abstract.py` at `Makefile:167` (`make_submission.sh` is still not a target; README mentions it). |
| N5 no completeness guard | **Not resolved** | `paper_v2.py:345-348` filters; `clustering_lottery.py:49-50` returns `None`. Directly relevant now (4 missing embeddings in the committed set). |
| N6 `\memCap` from the environment | **Not resolved** | `paper_v2.py:432` `os.environ.get("SPATIALBENCH_MAX_RSS_GB","12")`. The rerun script now sets `SPATIALBENCH_MAX_RSS_GB=30` (CAP_GB) in its own shell only; `make numbers` in the same shell would print 30. Hard-code 12 or read it from the records. |
| N7 kill reason not stored | **Not resolved** | `resources.py:80-81` unchanged. The 30 GB cap of the rerun is likewise not recorded. |

## `make -n data cache benchmark-new robustness stats numbers supplement figures paper`

All targets resolve; no error. Order: `data` (DLPFC, BASS clone and commit checkout, checksum check, `download_new_datasets.py`,
`prepare_*`), `benchmark-new` (cap 12 GB, seeds 0-2), `baselines_3start.py`, `export_runner_emb.py` (+ inline export of four baselines),
lottery, `k_sensitivity.py`, `mclust_seed` g1-g4, g5 and g6 (`MCLUST_NO_JIT=1`), `stats` (3 variants), `brca_coarse.py`, `paper_numbers.py`,
`paper_v2.py`, `coverage_matrix.py`, `make_supplement.py`, three figure scripts plus `make_graphical_abstract.py`, then pdflatex/bibtex for main and
supplement. `cache` printed "Nothing to be done" because it is a file target under `data`. Not in the chain: the 17-job rerun,
`merge_bigmem.py`, `finish_bigmem_analyses.sh` (the new steps), `mclust` (the `mclust_lottery_*.csv` files, since `make -n` finds them present), `run_qc.py` (only `qc`).

## Data availability section (`main.tex`, "Data availability")

Sources for all five datasets with URLs, accession STDS0000058, citations, pointer to `configs/datasets.yaml` and
`data/CHECKSUMS.sha256` are given. Open: the code/DOI placeholder, and no licence/terms sentence and no statement that
`results/runs` and the 17 rerun outputs are deposited on Zenodo (needed for Figures 1 and 5 and for byte-exact reruns).

## Required actions before release (short list)

1. Let the pending R mclust fit(s) finish (four E10.5_E1S1 embeddings), rerun `make numbers supplement figures paper check`, commit; add a coverage assertion (N5).
2. Fix `docs/BIGMEM_RERUN.md:35` and runbook section 9 to `python scripts/merge_bigmem.py`; add Makefile targets `rerun-bigmem` and `merge-bigmem` (and `finish_bigmem_analyses.sh`), or document the order in README.
3. Remove or neutralise the DeepMed2/`bikashkumar` identifiers in the release (runbook, pipeline, setup, run_detached, BIGMEM doc, host tag), the Overleaf project ID, the e-mail in `cover_letter.md`, the review reports, `deliverables/`, and tracked PDFs; add `*.lock_*` to `.gitignore`.
4. Document the GraphST mclust wrapper in `configs/methods.yaml` and commit its equivalence check; fix README sizes (200 MB/1.6 GB/92 MB), CPU clock (2.1 vs 2.8 GHz), CPU-hours (~226), `.zenodo.json` keywords, README Data bullets for breast cancer and MOSTA, Makefile "<= 13 GB".
5. Deposit `results/runs`, `results/emb` and `results/cache` on Zenodo and say so in the Data availability section.
