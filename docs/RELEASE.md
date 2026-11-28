# Release for reviewers (manuscript V3 = "SP-Ben-Main_v1")

Everything needed to check or regenerate the results of the manuscript. Repository: github.com/bkpaulvt-dev/Spatial, branch `new-datasets`;
the release tag and Zenodo DOI are created by the authors at submission (placeholders in the manuscript until then).

## Data
- Dataset identifiers, URLs, repository commits of the annotation sources and label provenance: `configs/datasets.yaml` (24 original
  sections) and `configs/datasets_newdata.yaml` (Allen MERFISH, osmFISH, BaristaSeq, simulation). SHA-256 of every downloaded file:
  `data/CHECKSUMS.sha256`. Derived CSVs of third-party data are not redistributed; `scripts/newdata_allen.py --export` rebuilds them.
- Annotation provenance per label set: Supplementary Table S27 (`results/supp/v3_provenance.tex`).

## Code and environments
- Method commits and settings, and every deviation from the tutorials: `configs/methods.yaml` (original methods) and the header of each
  adapter or worker in `scripts/review_methods.py`, `scripts/review_workers/` and `scripts/review_*.R` (added methods).
- Python: `environment/requirements-lock.txt` (first machine) and `environment/requirements-lock-deepmed2.txt` (second server); method
  environments: `envs/*.freeze.txt` on the server (HiSTaR official, CellCharter/scVI, MENDER, Novae). R: `environment/R-packages.txt`,
  `environment/R-sessionInfo.txt`.
- Clean-environment check: `scripts/clean_env_check.sh` builds a fresh virtual environment from the lock file, runs linear diffusion and
  PCA on DLPFC 151673 and compares with the recorded ARI, and regenerates the V2 numbers and Figure 6 from the archived outputs; result:
  `results/clean_env_check.txt`.

## Runs
- One JSON record per job with method, dataset, section, seed, host, threads, peak memory, run time, outcome and method version:
  `results/benchmark_runs*.jsonl` (first machine and big-memory reruns), `results/newdata_runs_deepmed2.jsonl`,
  `results/review_runs_deepmed2.jsonl`, `results/review_runs_d3d4_deepmed2.jsonl`, `results/cs_runs_deepmed2.jsonl`,
  `results/cavity_runs_deepmed2.jsonl`. Per-job predictions: `results/*_runs/<id>.npz`.
- Failures (host, threads, memory cap, peak memory, reason, attempts): `results/v3_failures.csv` (`scripts/v3_failure_table.py`).
  Retry rule: a job killed below 80% of the 30 GB cap is an infrastructure kill and is retried with unchanged settings; a job at the cap
  or the 24 h limit is final.

## Analyses specified before their results (commit and time of the specification; first job of the analysis)
| Specification | Commit, time (EST) | First job |
|---|---|---|
| Simulation, `docs/PREREGISTERED_SIM.md` | c9222cf, 2026-11-04 11:35 | pipeline start 2026-11-04 11:43 |
| Amendment 1 (reduced tier-3 design) | 89fa31c, 2026-11-04 12:00 | before any tier-3 job |
| Amendment 2 (slot use) | d2a2177, 2026-11-04 16:13 | cost only |
| Spatial-MGCN stopping rules, `docs/PREREGISTERED_A9.md` | e9b6f1e, 2026-11-04 19:07 | stage start 2026-11-09 22:28 |
| Equal-tuning arm, `docs/PREREGISTERED_TUNING.md` | 4d288f4, 2026-11-20 00:38 | stage start 2026-11-22 12:11 |
| Crossed seeds, `docs/PREREGISTERED_CROSSED_SEED.md` | 964eb10, 2026-11-28 11:23:09 | stage start 2026-11-28 11:23:19 |
| Cavity and boundary/size analyses, `docs/V3_REVISION_WORKPLAN.md` | 3715c70, 2026-11-28 11:24 | after the commit |

## Regenerating the manuscript numbers, tables and figures
```
make numbers supplement figures            # original analyses (paper_macros.tex, Figures 1-5, Tables S1-S23)
python scripts/paper_review_numbers.py     # V2 extensions: paper_macros_review.tex, Tables S24-S26
python scripts/make_fig_simulation_v2.py   # Figure 6
python scripts/v3_paired_effects.py        # V3: group-level paired effects, dataset weighting, DLPFC omission (Table S28)
python scripts/v3_small_tables.py          # V3: Table 1 both arms, Novae, Allen completion, HiSTaR pairs, boundary per donor
python scripts/cs_analysis.py              # V3: crossed seeds (after review_stage_cs.sh)
python scripts/v3_cavity.py                # V3: Cavity sensitivity (after review_stage_cavity.sh)
python scripts/v3_boundary_size.py         # V3: boundary distance and domain prevalence on real tissue
python scripts/v3_failure_table.py         # failure table
cd paper && tectonic main.tex && tectonic supplementary.tex
```
