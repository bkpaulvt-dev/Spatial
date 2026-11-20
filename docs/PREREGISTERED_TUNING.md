# Pre-registration: R5 equal-tuning arm (Arm B), cheap methods

Written and committed on 2026-11-20, **before any R5 result exists** (no R5 job has run; the dry run below only reproduces Arm A settings and
goes to scratch files that are never counted). Owner approval: "go" on 2026-11-20 (APPROVE_R5, budget of docs/REVIEW_QUESTIONS.md Q9:
cheap methods, up to 10 settings, six development sections, 1 seed, then the tuned arm on the 24 sections x 3 seeds).
Code: `scripts/r5_tuning.py` (grids, adapters), `scripts/r5_select.py` (selection), `scripts/r5_analysis.py` (analysis), committed with this file.

## Why
Reviewers' main objection: linear diffusion (our baseline) may look good only because the published methods were run at their default
settings. Arm B gives every method, including our baselines, the same tuning budget on development sections only, then freezes the choice.

## Methods (5)
linear diffusion, AnisoST, PCA + GMM (non-spatial), BANKSY, NichePCA: every training-free / non-deep method of the benchmark.
The deep and Bayesian methods (HiSTaR, GraphST, STAGATE, SEDR, SpaceFlow, CCST, Spatial-MGCN, DeepST, SpaGCN, BASS, BayesSpace) are **not** in
this arm (cost: 4-9 days; listed as not done). The paper must say the tuned comparison covers the cheap methods only.

## Budget (equal for every method)
10 configurations per method, fixed in `scripts/r5_tuning.py` (`GRIDS`) before any run. Configuration 0 is the method's Arm A setting.
This deviates from docs/PROTOCOL.md section 5 (20 configurations sampled from the authors' ranges): the owner-approved budget is 10, and the
grids are hand-set around the Arm A value (each varies one or two settings), not random draws. BANKSY's grid includes both of the authors'
recommended lambdas (0.2, 0.8) and 0.5, so Arm B BANKSY is one method; its Arm A comparator is BANKSY lambda 0.8 (domain setting).

| Method | Settings varied |
|---|---|
| linear diffusion | k-NN 4/6/10/15, alpha 0.3/0.5/0.7, steps 5/10/20, PCs 15/30 |
| AnisoST | k-NN 4/6/10, alpha 0.3/0.5/0.7, steps 5/10/20, q 0.25/0.5/0.75 |
| PCA + GMM | PCs 5-50 |
| BANKSY | lambda 0.2/0.5/0.8, neighbours 10/18/30, PCs 20/30 |
| NichePCA | k-NN 4/6/10/15/20, components 15/30/50 |

## Tuning phase
Six development sections (configs/datasets.yaml split `dev`, frozen before the benchmark): DLPFC 151507-151510 (donor Br5292), STARmap
20180417_BZ5_control, MERFISH -0.04. Seed 0 only. 5 x 10 x 6 = 300 jobs (method names `r5__<method>__c<j>`).

## Selection rule S (applied by `scripts/r5_select.py`, no human choice)
Score = mean over the 3 development datasets of the per-dataset mean ARI (method's own clustering, `metrics.ARI`), so DLPFC's 4 sections
do not outweigh STARmap and MERFISH. Highest score wins; ties (< 1e-9) go to the lower index (Arm A first). A configuration missing or
failed on any development section is ineligible. Output: `results/r5_selected.json`, frozen and committed before the tuned run starts.

## Tuned run
The selected configuration of each method (`r5__<method>__tuned`) on the 24 original sections x seeds 0, 1, 2 = 360 jobs.
Same runner, caps and failure rules as every review stage (failures are recorded, never rerun with other settings).

## Analyses (`scripts/r5_analysis.py`)
Per section: mean ARI over the 3 seeds. Clusters and hierarchical bootstrap as in `scripts/stats_cluster_aware.py` (DLPFC donors; STARmap,
MERFISH, breast cancer, Stereo-seq one cluster each; 5000 draws).
- **P1 (primary):** on the 18 **test** sections (6 clusters), delta_B = ARI(tuned linear diffusion) - ARI(tuned method), 95% interval.
  "Linear diffusion better" if the interval is above 0, "method better" if below, otherwise unresolved.
- **P2:** tuning gain per method on the test sections, ARI(tuned) - ARI(Arm A), 95% interval.
- **P3:** ranking of the 5 tuned methods next to their Arm A ranking (test sections).
- **S1 (secondary):** P1 on all 24 sections; dev sections are in-sample for the tuned arm and are reported as such.

## What would change the paper's claim
If any method is "method better" in P1, or if linear diffusion loses its rank among these 5 methods in P3, the paper reports that the
baseline's standing depends on tuning. If P1 agrees with Arm A, the paper reports that equal tuning of the cheap methods does not change
the conclusion, and that the deep methods were not tuned (limitation).

## Dry run (not a result)
Before the tuning phase: configuration 0 of each method on DLPFC 151507 seed 0, to scratch files. Pass = finite ARI and, because
configuration 0 is Arm A, the ARI should equal the Arm A record of the same job (`results/benchmark_runs.jsonl`); a difference above 0.001 is
reported in review_status.txt before anything else runs.
