# 04 (round 5, final): Reproducibility and code/data availability re-audit (NAR)

Audit date: 2026-11-03. Scope: `HEAD` = `e117233` of `claude/great-cori-opzfx7` (working tree clean apart from this report; 395 commits).
Static audit plus `python -m pytest -q tests` (14 passed, 18 s) and `scripts/check_paper_numbers.py` (7/7 claims; 122/122 macros
used in the text are defined). Nothing was downloaded or recomputed. Secret values are never reproduced. Author-side
placeholders listed in round 4 (GitHub URL/Zenodo DOI, licence confirmation, ORCID, `.zenodo.json` "TODO before deposit") are
unchanged and not repeated.

## Verdict

**Minor revision (release hygiene), no blocking scientific-reproducibility defect left.** The result set is now complete
(`\mcsN` = 336 embeddings, `\mcsNBig` = 294; the stale lock directory is gone; the four E10.5_E1S1 embeddings that were
missing in round 4 are present in `results/mclust_seed_g6.csv`), the stale `cat >>` merge instruction in
`docs/BIGMEM_RERUN.md` is fixed, and the GraphST wrapper is now recorded in `configs/methods.yaml`. What still stands between a
stranger and a clean rerun is (a) the second-server rerun and the merge are not `make` targets and three docs are stale,
(b) lab/personal identifiers are still in tracked files, (c) the large intermediates needed for Figures 1 and 5 are not
deposited yet (author side). Items 1-4 below are quick text fixes.

## Status of round-4 items

| Round-4 item | Status now | Evidence |
|---|---|---|
| Result set incomplete (332/336), B1 | **Resolved** | `paper_macros.tex:231-232` `\mcsN`=336; `results/emb/csv` has 360 files (336 + extra); g6 covers all 14 methods; `results/mclust_seed_g6.csv.lock_*` absent; commits `fde733b`, `fa3d31a`, `e117233`. |
| Stale merge step `cat >> benchmark_runs.jsonl` | **Mostly resolved** | `docs/BIGMEM_RERUN.md:32` now `python scripts/merge_bigmem.py ... do not use cat >>`. **Still stale in `docs/DEEPMED2_RUNBOOK.md:129`** ("append `benchmark_runs_bigmem*.jsonl`") and, harmlessly, `docs/RUN_ON_MAC.md:38`. |
| GraphST mclust wrapper provenance | **Partly resolved** | Now in `configs/methods.yaml:24`, `main.tex` and supplement `SNcompute`, code `scripts/adapters.py:86-98`. Open: see N1 below. |
| Makefile has no rerun/merge target | **Not resolved** | `Makefile` unchanged except one added `stats` line; `make benchmark-new` still sets the 12 GB cap and reproduces the 17 OOM records, not the rerun. |
| `*.lock_*` not git-ignored | **Not resolved** | `.gitignore` has no `lock_` pattern (lock dir is gone now, risk remains after a crash). |
| N5 no completeness guard | **Not resolved** | `paper_v2.py` has no assertion that the number of embeddings equals the expected 336; `check_paper_numbers.py` checks 7 claims plus macro definition only. The incomplete state of round 4 would again pass silently. |
| N6 `\memCap` from the environment | **Not resolved** | `paper_v2.py:435` `os.environ.get("SPATIALBENCH_MAX_RSS_GB","12")`; the rerun script exports 30 in its shell. |
| N7 cap/kill reason not stored in records | **Not resolved** | Unchanged. |
| m2 README sizes, CPU clock, CPU-hours | **Not resolved** | `README.md:141` 138 MB / 1.1 GB / 45 MB vs actual 200 MB / 1.6 GB / 92 MB; `README.md:148` "Xeon (2.1 GHz)" vs `supplementary.tex:32` and `make_supplement.py:311` "2.8 GHz"; "about 150 CPU-hours" unchanged; `Makefile:7` "<= 13 GB". |
| m1 `.zenodo.json` keywords | **Not resolved** | `.zenodo.json:11` keywords end at MERFISH. |
| m4 `mclust_seed.R` lock race | **Not resolved** | `mclust_seed.R` unchanged. |
| m5 TOFU checksums / UA | **Not resolved** | Unchanged; all raw files listed (32 lines in `CHECKSUMS.sha256`). |
| m6 `run_qc.py` docstring names non-existent `docs/QC_REPORT.md` | **Not resolved** | `scripts/run_qc.py:1`. |
| m7 EVIDENCE_MAP | **Not resolved** | 0 hits for brca/stereo/bigmem/mclust_seed. |
| m10 / P2-5 confidential and stray tracked files | **Not resolved** | Tracked: `paper/cover_letter.md`, `paper/suggested_reviewers.md`, `paper/SUBMISSION_CHECKLIST.md`, `deliverables/*` (13-method era, incl. a zip and a PDF), `docs/nar_review/round2..round4` (all review reports, including this round's predecessors). |
| P2-3 personal identifiers / absolute paths | **Not resolved** | See "Identifiers" below (unchanged). |
| P2-4 authorship | **Not resolved** | All 396 commit authors are "Claude" (`git log --format=%an`). Squash or re-author for release. |
| Host tag is a hard-coded string | **Not resolved** | `merge_bigmem.py:17` writes `"deepmed2"`; no CPU/RAM/hostname stored (the script prints them to the log only). |
| P0-6 large intermediates not archived | **Open, author side** | `results/runs` 200 MB, `results/emb` 1.6 GB, `results/cache` 92 MB are git-ignored; Data availability does not say they are deposited. |

## Resolved, not to be repeated

Secrets: re-grepped (key/secret/password/token/credentialed URL patterns) over all tracked files outside the review
folder: only the runbook rule "Never write passwords, tokens", the `push_overleaf.sh` comment about a saved secret
(not stored) and the `<your-secret-topic>` placeholder. **No secrets committed.** Tests pass; `make check` logic OK; checksum
file covers all raw inputs.

## New findings, ranked

### N1 (medium). GraphST wrapper: documentation is narrower than the code, and the equivalence evidence is not in the repository
* `configs/methods.yaml:24` and the supplement say the call is wrapped "on the second server". The code
  (`scripts/adapters.py:86-98`) applies the wrapper unconditionally on every host, dataset and section, so `make benchmark`
  gives wrapped GraphST on DLPFC/STARmap/MERFISH, whereas the committed GraphST records for those sections were produced
  (earlier) with GraphST's original `mclust_R`. So "same code as the paper" is not literally true for GraphST on the first
  datasets, and a stranger cannot tell which records used which function.
* The claim "identical labels on two test embeddings" (`methods.yaml`, `SNcompute`, `adapters.py:88` "gives the same result") has no script and no result file in the
  repository. The wrapper also differs in form from the original (it returns `$classification` rather than indexing the
  returned object, and seeds `np.random` and `set.seed` itself).
* Fix: commit a 20-line script (for example `scripts/check_graphst_mclust_wrapper.py`) that runs original and wrapped function on one seed-0 embedding of two
  sections and writes `results/graphst_mclust_wrapper_check.csv` (ARI between the label vectors); reword `methods.yaml:24` to
  "wrapper active in `adapters.py` on all hosts; earlier DLPFC/STARmap/MERFISH records used the original function; labels identical on N test embeddings (file)". Or gate the wrapper on an environment variable and record it.

### N2 (medium). The second-server rerun and merge are still outside `make`; README does not list the scripts
Documented order that works: `make benchmark-new` -> `sh scripts/rerun_memory_failures.sh` (or `run_detached.sh`) -> `python scripts/merge_bigmem.py` ->
`bash scripts/finish_bigmem_analyses.sh` (or `make robustness`) -> `make numbers supplement figures paper check`. It exists only
in `docs/BIGMEM_RERUN.md` section 3; the README "Compute" names `rerun_memory_failures.sh` and `merge_bigmem.py` but not
`finish_bigmem_analyses.sh`, `setup_deepmed2.sh`, `deepmed2_pipeline.sh`, `run_detached.sh` or `environment.deepmed2.yml`
(README layout table `environment/` row). Fix: add `rerun-bigmem` and `merge-bigmem` targets (`merge_bigmem.py` is idempotent) to the
Makefile and a three-line sequence to README "Reproducing the paper" tier 3. Also `setup_deepmed2.sh` does not run
`prepare_new_datasets.py`, while `BIGMEM_RERUN.md:11` lists it; confirm `bench_run.py` prepares on demand or add it to the script.

### N3 (medium). Lab and personal identifiers remain in tracked files (unchanged since round 4)
Locations: `/mnt/disk/bikashkumar/SpatialBench` default `BASE` in `scripts/setup_deepmed2.sh`, `scripts/deepmed2_pipeline.sh:6`,
`scripts/run_detached.sh`; `docs/BIGMEM_RERUN.md:8,53,60`; `docs/DEEPMED2_RUNBOOK.md` (about 15 lines; line 3 names the owner); lab server
name "DeepMed2" in README:161, BIGMEM_RERUN, runbook, `merge_bigmem.py:1,3,17`, `paper_v2.py:420`, `environment.deepmed2.yml:1` and as the
data value `"host": "deepmed2"` (20 lines in `results/benchmark_runs.jsonl`); institutional e-mail `paper/cover_letter.md:27`;
private Overleaf project ID as default in `scripts/push_overleaf.sh:8`; git identity `deepmed2@localhost` in `deepmed2_pipeline.sh:65`;
container path `/home/user/Spatial` in error strings of `results/benchmark_runs.jsonl`, `feasibility.jsonl`, `new_methods.jsonl`.
Author name/affiliation in LICENSE, CITATION.cff, `.zenodo.json` is expected. Fix: move maintainer files (runbook,
pipeline, run_detached, `push_overleaf.sh`, `package_overleaf.sh`, cover letter, reviewers, checklist, `deliverables/`, `docs/nar_review/`) to an untracked or
`maintainer/` folder for the release; default `BASE` to `$PWD/..`; either keep the tag but describe it as "second server, 125 GB, i9-9820X" or
rename to `bigmem` in `merge_bigmem.py`, `paper_v2.py:420`, `make_supplement.py` and the JSONL. Optionally sanitise the container path in error strings.

### N4 (low-medium). Stale documentation numbers
README sizes (138 MB/1.1 GB/45 MB vs 200 MB/1.6 GB/92 MB), CPU clock 2.1 vs 2.8 GHz (README:148 vs supplement), "about 150 CPU-hours"
(README:149; records sum to about 226 h incl. the rerun), `Makefile:7` "<= 13 GB" beside the 12 GB cap, `.zenodo.json` keywords, `run_qc.py:1`
dangling `docs/QC_REPORT.md`, runbook section 9 (see above). All are one-line edits. Pick one clock value (check `/proc/cpuinfo` of the benchmark container; the two documents
disagree, so one is wrong).

### N5 (low-medium). No guard against a partial result set going into the paper
Round 4 showed that the numbers can be generated from 332 of 336 embeddings without any error. Add to `paper_v2.py` (or
`check_paper_numbers.py`) `assert n_embeddings == len(expected)` (expected = methods x sections from `configs`), and one
claim that `\mcsN` equals that count. Also: only 7 numbers in `main.tex` are verified against JSON; other hard-coded values in the text
(for example `main.tex:354` 0.65 and 0.718; 0.025 and 9 of 12 are checked, 0.363/0.497 checked) are not all covered. The macro mechanism
covers the rest (122 macros defined), so the answer to "are all numbers generated by scripts" is: yes for macros, partly for the few hard-coded decimals;
list them or turn them into macros.

### N6 (low). Reproducibility of the rerun host
`\memCap` is read from the shell (N6 above), the cap used for the rerun (30 GB) is not stored in the records, and the host tag has no hardware
fields. Cheap fix: store `cap_gb`, `cpu_model`, `ram_gb` in each record in `spatialbench/resources.py`/`bench_queue.py`, and let `merge_bigmem.py` take
`--host NAME` (default as now). No seeds problem found: seeds are in the run ids (`__s0..s2`), the GraphST seed is `41+seed`, R mclust seeds 1..10 are in `mclust_seed.R`, and OMP/MKL/OPENBLAS=1 is exported in the Makefile and the rerun script.

### N7 (low). Data and code licence statements
Code MIT with the HiSTaR notice (`LICENSE`); data licences are in `docs/DATA_AND_LICENCES.md` (several "to confirm", CCST port
permission open). The Data availability section in `main.tex:430-439` gives sources, checksums and says per-run results are available,
but states neither a licence/terms sentence nor that `results/runs`/`results/emb` (needed for Figures 1 and 5 and for the 17 rerun outputs) are
deposited. Add one sentence once the DOI exists. Author side.

## Can a stranger rerun from raw data with make?

* `make data` (includes `data-new` with checksums) and `make cache`: yes; `make -n` resolves, BASS commit pinned
  (`81dfe73`), checksum file covers all inputs.
* `make benchmark benchmark-legacy benchmark-new robustness numbers supplement figures paper check`: yes, with the caveats that
  `benchmark-new` caps at 12 GB (so 17 jobs error out by design), runs CCST seed 2 for every section (paper reports 2 seeds on E10.5_E1S1), and the
  GraphST wrapper differs from the original one for the first datasets (N1).
* Second-server rerun: reproducible by hand following `docs/BIGMEM_RERUN.md`; versions are pinned (`environment.deepmed2.yml`, lock file,
  DeepST `e37997f`, Spatial-MGCN `cf4412d`, BASS commit); not through `make` (N2).
* `merge_bigmem.py`: works, idempotent, correct order documented in BIGMEM_RERUN.md; timing exclusion via the host tag (`paper_v2.py:420`).
* Figures 1 and 5 and byte-exact reruns need the Zenodo deposit of `results/runs`, `results/emb`, `results/cache`.

## Short fix list (in order)

1. Commit the GraphST wrapper equivalence script/CSV and correct the "second server only" wording (N1).
2. Add `rerun-bigmem`/`merge-bigmem` targets or a README sequence; list the five undocumented scripts (N2).
3. Remove or neutralise DeepMed2/`bikashkumar`/e-mail/Overleaf ID, `deliverables/`, review reports, cover letter from the release tree; squash commits (N3).
4. Fix README sizes, CPU clock, CPU-hours, `Makefile:7`, `.zenodo.json` keywords, runbook section 9, `run_qc.py` docstring; add `*.lock_*` to `.gitignore` (N4).
5. Add a coverage assertion and make `\memCap` constant (N5, N6).
6. After the Zenodo deposit: DOI, licence sentence, statement about deposited intermediates (N7, author side).
