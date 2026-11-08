# Completion plan (written 2026-11-08; planning only, nothing was changed in code, settings, paper or running jobs)

## 1. What delays completion
1. **Two heavy slots only (owner rule), on a machine shared with ~350 other users** (load 25-50, 25-35 GB RAM free). Everything below is serial inside a slot.
2. **Queue order, not compute, is the main loss.** R5 (the equal-tuning arm, the reviewers' most important missing experiment) is last of 19 stages; simulation tier 3 waits for *every* review stage, including optional ones (Amendment 2).
3. **False infrastructure kills** cost days (fixed 2026-11-06); ~26 Allen jobs and 25 simulation jobs were rerun.
4. **Method faults that cost whole blocks of runs**: SEDR and STAGATE mclust (STAGATE fixed), SpaGCN length-scale search on mm coordinates (open), 20 real memory-limit records.
5. **Author-only paper items** (names, funding, CRediT, Zenodo/GitHub, licences, HiSTaR published-number check, AI statement): nothing a job can do; they take the authors a day or two but are not started.

## 2. Essential vs optional (proposal; the owner's cut order D6/D7, M3, R5, M1 is respected except R5, see decision 1)
| Item | Needed for the paper's claim? | Status | Remaining cost (one slot) |
|---|---|---|---|
| Allen MERFISH real data (3 sections x 16 methods x 3 seeds) | Yes: first new whole-brain real data | 73/144 ok; 58 jobs planned (incl. retries) | ~58 h lower bound, ~2.5-4 days |
| Simulation tier 1-2 (domain size, full design) | Yes | done for tier 1; tier 2 follows Allen | not re-estimated |
| Simulation tier 3 (8 deep methods, reduced: 72 jobs) | Yes for "deep methods too" | paused by Amendment 2 | ~106 h from the queue cost model, ~4.5 days |
| R5 equal-tuning arm, cheap methods | **Yes: reviewers' key request** | not built; docs/PREREGISTERED_TUNING.md missing | ~2 days (REVIEW_QUESTIONS Q9), plus ~0.5-1 day build |
| R5 deep methods (GPU) | Desirable | not built | 4-5 days GPU, 8-9 days CPU |
| M2 CellCharter/MENDER | Yes (new methods) | running, 8-9 of 12 DLPFC sections | hours to ~1 day |
| M6 HiSTaR official fidelity | Yes (fixes "official code" wording) | built, queued | ~0.5 day |
| A9 Spatial-MGCN stopping rules | Yes (pre-registered, finding must be fair) | built, queued | hours to 1 day |
| D3/D4 osmFISH + BaristaSeq | Useful (separate group, labels undocumented) | built, queued | hours |
| M5 multi-sample BASS | Optional | built | up to 24 h cap |
| M1 SpatialPCA/PRECAST, M4 Novae, M3 GraphBG/DR-SC, M6 CCST original, R4 GPU timing, D6/D7 scalability | Optional: report as "not done" | M1/M4 held, others unbuilt | 0.5-1 day build each + run time |
| D1 HER2+, D2 prostate | Not possible (data/labels) | stubs | none |

## 3. Realistic timeline (two slots, load as now; wide error bars because other users set the speed)
- **Slot A (new data):** Allen finishes about **11-12 Nov**; tier 2 (not re-estimated) then tier 3 (~4.5 days) if released: **about 18-22 Nov**.
- **Slot B (review):** M2, M6 HiSTaR, D3/D4, A9 done about **10-12 Nov**; build R5 (pre-register first, 1 day) and run the cheap arm about **13-16 Nov**.
- **Essential data complete: ~20-22 Nov** (about 12-14 days). Add 4-9 days if the R5 deep arm is required, 1-4 days for each optional item run.
- Stage-by-stage numbers are lower bounds from the queue's own cost model; I have not measured them under today's load.

## 4. Parallel work that needs no compute slot
- Statistics: rerun `scripts/stats_cluster_aware.py` and `scripts/newdata_stats.py` as results arrive (minutes, CPU light); extend with the Allen group and the SDMBench group as clearly separate strata.
- Figures: regenerate from the macros pipeline (`make numbers supplement figures paper check`) once per data freeze, not per result.
- Manuscript: a results-addendum and limitations draft can be written now from existing results (domain-size simulation, review checks, incident note, wrapper deviations). **I have not touched `paper/`** (earlier owner rule); the draft would go to `docs/MANUSCRIPT_ADDENDUM_DRAFT.md`.
- Incomplete work is stated, not waited for: unfinished cells are reported as such and never imputed.

## 5. Decisions needed (each changes an earlier owner decision, so none was applied)
1. **R5 order.** Move the cheap-method R5 arm (build + ~2 days) to run right after M2/HiSTaR/A9, ahead of M1, M4, CCST, M3, D6/D7, M5. Deep arm only if time remains. Saves ~1 week on the critical path.
2. **Tier 3 release.** Let the 8 deep simulation methods start when the *essential* review stages (M2, M6 HiSTaR, D3/D4, A9, R5 cheap) are done, instead of after all 19. Needs a dated Amendment 3 (cost only).
3. **Optional stages** M1, M4, M3, M6 CCST, R4, D6/D7, M5: run only if the critical path is clear, otherwise listed as not done in the paper.
4. **Method faults:** SEDR mclust wrapper (same as GraphST/STAGATE, with ARI = 1 check) and SpaGCN on Allen (keep as error or investigate unit effect).
5. **Paper edits:** may I edit `paper/` (macros, new sections, limitations) as results land? Until you say yes I write only in `docs/`.
6. **Parallelism:** I keep the cap at 2 heavy jobs. A third heavy job would speed up little on a loaded shared machine; ask the admin for a reserved slot if you want faster.
