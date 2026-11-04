# Review scale-up (docs/DEEPMED2_NEXT.md): questions with defaults, time per item, launch command

Written 2026-11-04. **Defaults apply unless you change them** (edit `/mnt/disk/bikashkumar/SpatialBench/review_config.env`, re-read before every stage).
Time = estimated compute on DeepMed2 after the gate opens (2 CPU jobs at a time, linear cost model from the original benchmark; deep methods and large sections may take longer).
"Build" = engineering still to do by a Claude session before the stage can run; the runner picks a stage up as soon as its script file exists.

## What exists now
Runner `scripts/review_runner.sh` + launcher `scripts/run_review_detached.sh` (tested with fake stages), explicit-job queue `scripts/review_queue.py`,
stage list `scripts/review_stages.txt`, built stages: **prep_data** (runs now) and **a10_cross_host**. Everything else is listed as "blocked: script not built yet" in the status.

## Facts found today that bear on the questions
- GPUs 0 and 1 are idle (TITAN RTX 24 GB, driver 570); torch cu128/cu126 wheel indexes, PyPI (novae, cellcharter), CRAN (PRECAST, DR.SC), GitHub (SpatialPCA, CellCharter, MENDER, CCST, SDMBench, her2st) and Hugging Face are reachable. MENDER is not on PyPI (install from GitHub).
- SDMBench Figshare (CC BY 4.0): osmFISH = 1 section, 4,839 cells, 33 genes, `Region` with 11 anatomical names (Layer 2-3 medial/lateral, 3-4, 4, 5, 6, White matter, Hippocampus, Ventricle, Pia Layer 1, Internal Capsule Caudoputamen);
  BaristaSeq = 3 slices (1,525 / 2,042 / 1,690 cells, 79 genes), `layer` = VISp_I ... VISp_wm plus depth and distance-to-pia columns. **Names are anatomical; how the labels were derived is not documented** in the descriptions.
- HER2+ (Zenodo 3957257, CC-BY-4.0): count matrices, spot selections and the 8 pathologist-label files are password-encrypted zips (passwords are in the authors' README). Prostate (Mendeley, CC BY-NC 3.0): per-spot annotation files not confirmed in the deposit.

## ONE list of questions (default in bold)
1. **Order.** Heavy stages start after the current plan has finished (`PHASE2_DONE`: Allen run, simulation tiers 2-3, G3 on the simulation; about 2-3 weeks from now); light prep (downloads, installs, source checks, dry runs on tiny inputs) may run now, one at a time, in their own folders. Alternative: pause simulation tier 3 (63 jobs, 2-5 days) to bring the review forward. **Default: as written.**
2. **HER2+ (D1).** **You place the unpacked files in `data/HER2ST/` and set `HER2_UNPACKED=1`; until then D1 is skipped.** Alternative: allow decryption with the authors' published password passed through an environment variable and never written to a file or log (needs your explicit yes).
3. **osmFISH and BaristaSeq from SDMBench (D3, D4).** The runbook uses a dataset only if its labels are documented as anatomical, not clustering-derived. **Default: skipped (`INCLUDE_SDMBENCH=0`).** Set it to 1 to run both (class `unknown`: anatomical names, derivation undocumented), reported as a separate, labelled group.
4. **Prostate (D2).** **Dropped unless you supply the per-spot labels** (`data/PROSTATE/`, `PROSTATE_LABELS_CONFIRMED=1`).
5. **New methods (M1-M4).** **Each in its own conda env under `/mnt/disk/bikashkumar/SpatialBench/envs/` and R packages in `Rlib_extra`; at most about 3 h of attempts per method, then recorded as failed and skipped.**
6. **Novae weights from Hugging Face.** **Yes, if the licence permits research use (recorded).**
7. **GPU.** **GPU index 1 only, one GPU job at a time, counted inside the 2-job cap.**
8. **A9 Spatial-MGCN stopping rules (pre-registered before any result).** **(i) the repository's default epoch count; (ii) loss plateau: stop when the smoothed training loss improves by less than 0.1% over 50 consecutive epochs; (iii) the final epoch; all three from ONE run per section and seed (embeddings saved at each stop point).**
9. **R5 equal-tuning arm.** **NOT approved (`APPROVE_R5=0`).** Proposed budgets if you approve: cheap methods only (up to 10 settings, six development sections, 1 seed, then tuned arm on the 24 sections x 3 seeds), about 2 days; full including deep methods on GPU, about 4-5 days (about 8-9 days on CPU).
10. **Visium HD / Xenium scalability** (one section above 100,000 cells each, scalable methods only, no accuracy): **yes, last.**
11. **Pushing.** **Small files only, branch `new-datasets` only, no force.**
12. **Time budget.** **No limit; run in the runbook order until the end or until you stop it.** If you need a cut, drop in this order: R5, M3, M1, D6/D7, M2.

## Estimated time per item (after the gate; engineering excluded)
| Item | Estimate | Status |
|---|---|---|
| prep_data (DLPFC 12, STARmap, MERFISH, breast, Stereo E9.5) | about 1 h (slow Stereo server) | built, runs now |
| A10 cross-host (DeepST seed 0 and linear diffusion seed 0 on E10.5_E2S1) | under 1 h | built |
| D3/D4 osmFISH + BaristaSeq (only if question 3 = yes) | about 0.5 day each incl. G3 | build |
| D1 HER2+ (8 sections, about 600 spots; only with files) | about 0.4 day | build |
| D2 prostate (only with labels) | about 0.5-1 day | build |
| M5 multi-sample BASS (DLPFC donors, MERFISH) | about 1 day | build |
| M6 official HiSTaR vs port (12 DLPFC sections x 3 seeds); original CCST on one dataset | 1-2 days incl. env builds (CCST needs PyTorch 1.7: high risk) | build |
| BayesSpace ST on Stereo-seq (largest section capped at 24 h) | about 0.5 day | build |
| M2 CellCharter + MENDER | 1.5-2 days | build |
| M1 SpatialPCA + PRECAST (SpatialPCA is O(n^2) memory: expect memory-limit records on large sections) | 1.5-2.5 days | build |
| M3 GraphBG + DR-SC | about 2 days | build |
| M4 Novae (if weights download) | 0.5-1 day | build |
| A9 Spatial-MGCN stopping rules (24 sections x 3 seeds) | about 1.5 days | build |
| R4 GPU env + CPU/GPU timing on two reference sections | env 2-4 h + about 1 day | build |
| R5 tuning arm | off by default (2-9 days if approved) | build |
| D6/D7 scalability (one section above 100,000 cells each) | 1-2 days incl. downloads | build |
Total after the gate: about 3-4 weeks without R5; the gate opens in about 2-3 weeks, so about 5-8 weeks overall. Each "build" item also needs about 0.5-1 day of engineering by a Claude session.

## Exact detached launch command
```bash
cd /mnt/disk/bikashkumar/SpatialBench/Spatial && bash scripts/run_review_detached.sh          # start (refuses a second copy)
bash scripts/run_review_detached.sh status                                                    # runner, gate, stage table, last lines, decisions
# progress file: /mnt/disk/bikashkumar/SpatialBench/review_status.txt (ends PIPELINE_DONE or STOP: <reason>); logs: .../review_logs/<stage>.log
# stop (by process group): kill -- -$(ps -o pgid= $(cat /mnt/disk/bikashkumar/SpatialBench/review_pipeline.pid) | tr -d ' ')
```
Phone alerts: the existing topic file (never printed or committed).
