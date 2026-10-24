# 04 (round 3): Reproducibility and code/data availability re-audit (NAR)

Audit date: 2026-10-24. Scope: `HEAD` = `dcc39ca` of `claude/great-cori-opzfx7`. The working tree was clean and no
benchmark or R workers were running. This was a static audit plus `make -n` and the read-only
`scripts/check_paper_numbers.py` (7/7 claims, 115/115 macros defined). Nothing was downloaded and no file other than this
report was changed. The GitHub URL and Zenodo DOI are author-side placeholders and are not counted as defects.

## Verdict

The two serious round-2 problems are fixed.

* **B1:** the paper numbers now come from a **complete** R mclust experiment. All 332 of 332 exported embeddings are
  covered, and the macros were regenerated after the last fit (`c42cfb5` → `dcc39ca`).
* **B2:** the false "12 GB cap for every job" statement has been corrected.

The Makefile now covers the new datasets. Every requested target resolves under `make -n`: `data`, `cache`,
`benchmark-new`, `robustness`, `stats`, `numbers`, `supplement`, `figures` and `paper`.

What remains is mostly the gap between the documented `make` recipe and what was actually run:

* The final results were produced by one-off scripts (`finish_queue.sh`, `rerun_graphst_stereo.sh`,
  `run_deepst_seeds.sh`, `run_pending.sh`). They used `MCLUST_NO_JIT=1`, kept CCST to 2 seeds and filtered results in place.
* `brca_coarse.py` and `make_graphical_abstract.py` are not in any make target.
* Dataset licences are still unverified.

None of these is blocking if it is documented, but `make robustness` and `make benchmark-new` would **not** reproduce
the committed files exactly.

## Round-2 blocking items

| # | Status | Evidence |
|---|---|---|
| B1 Numbers from an unfinished experiment | **Resolved** | `results/mclust_seed_g*.csv` covers 332 (dataset, section, method) triples, exactly the set of `results/emb/csv/*__k*.csv`. Nothing is missing or extra. `mclust_seed_summary.csv` has 332 rows (stereo 38, of which E10.5_E1S1 has 10). `\mcsN`=332 and `\mcsNBig`=290. g6 was committed in `a72c7a8`, the macros in `c42cfb5`, the supplement, figures and PDFs in `dcc39ca`. No lock directories are left. Remaining weakness: `paper_v2.py:345-347` still drops unfinished embeddings **silently** (`ok_` filter). There is no coverage assertion, so a future partial file would again pass unnoticed (see N5). |
| B2 False 12 GB cap claim | **Resolved (text); partly (Makefile)** | `main.tex:161-163` now says the cap applied to breast cancer and Stereo-seq only, and that the earlier runs had no cap (BayesSpace 12.5 GB). The supplement matches. However, `Makefile:23` sets `export SPATIALBENCH_MAX_RSS_GB ?= 12` **globally**, so `make benchmark` (DLPFC/STARmap/MERFISH) would now kill `dlpfc__151509/151510__bayesspace__s0` (12.54 and 12.19 GB). The header still says "<= 13 GB RAM per job". Run records still do not store the cap (`bench_queue.py:39-41` records `threads` only), and they do not say whether a kill came from the cap or from the "< 0.8 GB free" rule (`resources.py:81`). Fix: write `SPATIALBENCH_MAX_RSS_GB=0` in the `benchmark` recipe, and add `max_rss_cap_gb` and the kill reason to `rec["resources"]`. |
| B3 `make data`/`cache` skip new datasets | **Resolved (Makefile); partly (README)** | `data: data-dlpfc data-extra data-new cache`, `data-new` → `download_new_datasets.py`, and `cache` → `prepare_new_datasets.py` all resolve. The README "Data" section still has bullets only for DLPFC and STARmap/MERFISH. The new datasets are mentioned only in the Overview, with no URLs or sizes (≈2.3 GB MOSTA). |
| B4 New analyses not regenerable | **Mostly resolved** | (a) The `k-sensitivity` target is in `robustness`. (b) `scripts/export_runner_emb.py` exports every seed-0 `emb` for brca/stereo, and `export-emb` calls it. Lottery and K-sensitivity both cover 52/52 new-section embeddings. (c) `mclust-seed-g5`/`g6` were added. Still open: g1–g4 have no dataset filter, so they overlap g5/g6. Five embeddings are present in two files, giving 80 duplicate rows: brca `banksy_l0.2`, `banksy_l0.8`, `ccst`, `graphst`, and stereo E10.5_E1S1 `banksy_l0.2`. The values are identical and `paper_v2.py:343` and `make_figures_nar.py:190` deduplicate them, so the results are correct, but the layout is not one-to-one. `clustering_lottery.py:49-50` still returns `None` silently for a missing embedding. |
| B5 R mclust memory hazard | **Partly resolved** | The Makefile header (lines 10-11) and README "Compute" now document "~5 GB per fit, at most two workers on 16 GB", the shared-file lock mode and stale-lock cleanup. There is still no `.NOTPARALLEL`/serial guard for g6. Because locks are per output file, `make -j2 mclust-seed` can run g1/g2 and g6 **on the same 18k-bin embedding at the same time** (duplicate hours of work and about 10 GB). R remains outside the cap. |
| B6 Licences of new datasets | **Partly resolved** | `docs/DATA_AND_LICENCES.md:22-24` has rows for the 10x breast cancer data, the SEDR annotation and MOSTA, with exact URLs. Both are still "**to confirm**" (10x CC BY 4.0, CNGB redistribution terms). `configs/datasets.yaml:89,108` still has `license: {status: to_check}`. The Data availability section (`main.tex:409-418`) now gives sources for all five datasets but no licence or terms clause. |
| B7 Code URL/DOI | **Not resolved (author-side placeholder, accepted)** | `main.tex:15` `\DOI{DOI HERE}`, `main.tex:418` `\todo{GitHub URL and Zenodo DOI}`, and the DOI is commented out in `CITATION.cff`. There is still no tag or `main` branch. `repository-code` now points to a GitHub URL. |

## Round-2 minor items

| # | Status | Evidence |
|---|---|---|
| m1 CITATION/.zenodo stale | **Partly** | `CITATION.cff` abstract: 24 sections, five sources ✔. `.zenodo.json` description ✔, but `keywords` still end at "10x Visium, STARmap, MERFISH" (no Stereo-seq or breast cancer). |
| m2 Compute statement | **Partly** | README "Compute" adds the cap, the 5 out-of-memory methods, DeepST seeds 1-2 and CCST ≈5.5 h ✔. It still says "about 150 CPU-hours" (the sum of `cpu_s` over all records in `benchmark_runs.jsonl` is ≈226 h, of which ≈76 h is on brca/stereo). "Large intermediates" still gives 138 MB / 1.1 GB / 45 MB; the actual sizes are 190 MB / 1.5 GB / 92 MB. The Makefile header "<= 13 GB" contradicts the 12 GB default (B2). |
| m3 `benchmark-new` vs actual recipe | **Not resolved** | `benchmark-new` runs `--seeds 0 1 2` on every section, so it would add CCST seed 2 on E10.5_E1S1 (the paper reports 2 seeds) and spend about 5.5 h on it. The exact recipe is still only in `run_pending.sh` plus `run_deepst_seeds.sh` and `rerun_graphst_stereo.sh`. The GraphST Stereo setting is automatic in `adapters.py:88-89` ✔, so the results themselves would match. |
| m4 `mclust_seed.R` locks/header race | **Not resolved** | `mclust_seed.R:24-41` has no PID in the lock and no cleanup at start-up. `col.names = !file.exists(out)` and unserialised appends are unchanged. Stale locks are documented only as "delete after a crash". |
| m5 TOFU checksums, UA spoof | **Not resolved** | `download_new_datasets.py:84-88` still appends unknown files to `CHECKSUMS.sha256` (there is no `--record` flag), and `:51` still sends `User-Agent: curl/8.5.0`. All 6 new files do have entries ✔. |
| m6 `run_qc.py` | **Partly** | A `make qc` target exists, but it is not in `data`/`all`. The docstring still promises `docs/QC_REPORT.md`, which does not exist. |
| m7 EVIDENCE_MAP | **Not resolved** | Last changed 2026-10-15. It has no entry for brca, stereo, K sensitivity, mclust_seed or out of memory (0 matches). |
| m8 Number check | **Partly** | `check_paper_numbers.py` now checks that every macro used in the text is defined (115/115) ✔. It still has no freshness check (`make check-fresh` / `git diff --exit-code`) and no coverage assertions. |
| m9 MOSTA label provenance | **Partly** | `DATA_AND_LICENCES.md:24` and the paper's Limitations now describe the annotation as derived from clustering. |
| m10 Confidential files / Overleaf ID | **Not resolved** | `paper/cover_letter.md`, `paper/suggested_reviewers.md` and `paper/SUBMISSION_CHECKLIST.md` are still tracked. `scripts/push_overleaf.sh:8` still defaults to the private project ID (value not reproduced here). `make_submission.sh` copies `cover_letter.md` into the git-ignored `paper/submission/` (fine). |

## Round-1 carry-overs (brief)

| Item | Status | Note |
|---|---|---|
| P0-6 Large intermediates archived | **Not resolved** | `results/runs`, `results/emb` and `results/cache` are git-ignored and not yet deposited. Figures 1 and 5, the graphical abstract (`results/emb/dlpfc_151669_histar.npy`, cache) and `brca_coarse.py` need them. |
| P1-5 Per-run env/git SHA | **Not resolved** | Records have no package versions, git SHA or cap. |
| P1-7/P1-8 Licences (data, CCST port) | **Not resolved** | All `to_check`. The CCST port still needs permission or a rewrite (`DATA_AND_LICENCES.md:44`). |
| P2-1 Secrets | **Pass** | `git grep` over tracked files and `git log -p --since=2026-10-22` found no tokens, keys or credentialed URLs. |
| P2-3 Absolute paths | **Not resolved** | `/home/user/Spatial` in traceback strings: `benchmark_runs.jsonl` (6 lines), `feasibility.jsonl` (4), `new_methods.jsonl` (3). There are none in scripts, Makefile, README or configs. |
| P2-4 Authorship | **Not resolved** | All 357 commits are authored by "Claude". Squash and re-author for the public release. |
| P2-5 Stray files | **Not resolved** | `deliverables/*` (13-method-era PDF and zip), `paper/main.pdf` and `paper/supplementary.pdf` are tracked. |
| P3-1 NaN in JSONL | **Not resolved** | All 1139 lines of `benchmark_runs.jsonl` contain bare `NaN`. It also has 17 ids with more than one record (reruns). Every reader takes the newest one (`paper_v2.py:45,410`, `stats_cluster_aware.py:39`, `make_supplement.py:45,183`, `coverage_matrix.py:29`, `make_figures_nar.py:65`) ✔. |

## New gaps

| # | Gap | Where | Fix |
|---|---|---|---|
| N1 | **One-off maintainer scripts produced committed results but are not documented as the recipe.** `finish_queue.sh` (clears locks, runs g6 with `MCLUST_NO_JIT=1` and 2 workers, then DeepST seeds, the GraphST rerun and g5 Spatial-MGCN), `rerun_graphst_stereo.sh` (`bench_queue.py --force`, `export_runner_emb.py --force graphst`, **rewrites** `clustering_lottery.jsonl`, `k_sensitivity.jsonl` and `mclust_seed_g*.csv` in place to drop old GraphST rows, then recomputes them), `run_deepst_seeds.sh` and `run_pending.sh`. None of them is mentioned in the README. They poll `ps` for running jobs. | `scripts/*.sh`, README "Compute" | Add a README paragraph "How the committed new-dataset results were produced" that lists these four scripts in order and states that `make benchmark-new robustness` reproduces the same records except for CCST seed 2 and the noise repetitions. Alternatively, mark them as maintainer-only next to `push_overleaf.sh`. |
| N2 | **`make mclust-seed-g6` differs from what was run.** The committed g6 has the noise repetitions (`full_jit`) only for anisost, banksy_l0.2 and banksy_l0.8. The other 7 embeddings were run with `MCLUST_NO_JIT=1`. The Makefile has no `MCLUST_NO_JIT`, so a rerun would add 5 × ~30 min fits per embedding and change `\mcsJitMean`/`\mcsJitMax`. Related: `main.tex:306` says the noise test was "not run on the 18,408-bin Stereo-seq section", but `mclust_seed_summary.csv` has `jrng` for 3 embeddings of that section, and they enter `\mcsJitMean`. | `Makefile:150-151`, `paper/main.tex:306` | Write `MCLUST_NO_JIT=1` in the g6 rule, and either drop `full_jit` for E10.5_E1S1 in `paper_v2.py` or change the text to "run on only 3 of the 10 embeddings of …". |
| N3 | **`brca_coarse.py` (Supplementary Table `\STbrca`, `\brcaCoarse*` macros) is in no make target.** `paper_v2.py:394` and `make_supplement.py:224` skip it silently when `results/brca_coarse.json` is missing. | `Makefile` `robustness` | Add `brca-coarse: export-emb ; $(PYTHON) scripts/brca_coarse.py` to `robustness`. It also needs `data/BRCA/.../metadata.tsv` and `results/cache`. |
| N4 | **`make_graphical_abstract.py` is not in `figures`.** The committed `nar_graphical_abstract.{pdf,png,tif}` were regenerated in `dcc39ca` by hand. `make_submission.sh` is also not a target (the README mentions it ✔). | `Makefile` `figures` | Add `$(PYTHON) scripts/make_graphical_abstract.py` to `figures`, and optionally a `submission` target. |
| N5 | There is no guard that the committed result sets are complete. B1 was fixed by waiting for the run to finish, not by an assertion. | `paper_v2.py:345-347`, `clustering_lottery.py:49-50` | Have `paper_v2.py` exit non-zero, or print a warning macro, when the mclust, lottery or K-sensitivity coverage is smaller than the set of exported embeddings. |
| N6 | `\memCap` is read from the environment when the numbers are built (`paper_v2.py`: `os.environ.get("SPATIALBENCH_MAX_RSS_GB","12")`), not from the run records. With a different value in the shell, `make numbers` would print a cap that was never used. | `scripts/paper_v2.py` (memCap) | Record the cap in each run record and derive the macro from the records, or hard-code 12 there. |
| N7 | DeepST on Stereo E10.5_E2S1 peaked at 10.8 GB (seed 0, ok) but was killed at 12.0 GB for seeds 1 and 2. Because the guard also kills when less than 0.8 GB is free on the machine, whether a run succeeds can depend on other load. Concurrent runs are not recorded. | `spatialbench/resources.py:81` | Store the kill reason (`cap` or `low_free`) in the record, and add one sentence to the Methods text. |

## Make dry run (`make -n data cache benchmark-new robustness stats numbers supplement figures paper`)

All targets resolve. The order is: data (DLPFC, BASS clone/checkout/checksums, `download_new_datasets.py`), cache (3 preparers),
`bench_queue.py --datasets brca stereo --seeds 0 1 2`, `baselines_3start.py`, export-emb, lottery, k_sensitivity,
mclust_seed g1–g6, stats (×2), paper_numbers, paper_v2, coverage_matrix, make_supplement, the three figure scripts, and
pdflatex/bibtex for main and supplementary. Missing from the chain: `brca_coarse.py` (N3), `make_graphical_abstract.py`
(N4), `run_qc.py` (in `qc` only, m6), `MCLUST_NO_JIT` (N2) and the per-section CCST seed exception (m3).
