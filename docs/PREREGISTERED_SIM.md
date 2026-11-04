# Pre-registration: simulation of domain size (new-datasets extension)

Written and committed **before any simulated tissue or simulation result exists** (2026-11-04). It fixes the design, the primary
analysis and the decision rules. Anything done differently later is reported as a deviation, never silently.

## Question and hypothesis
The paper explains that smoothing wins on large, layered domains. **H0/H1:** the advantage of a smoothing method (linear diffusion)
over a non-spatial one (PCA + the same mixture model, `pca_gmm`) **shrinks as domains become smaller or more interleaved**.
- **H1 (layered bands, geometry A):** the advantage falls as the bands get narrower (m = 1 -> 7).
- **H2 (random blocks, geometry B):** the advantage is smallest for random blocks (no layering at all).

## Tissue (identical in every setting except geometry)
- Square lattice 120 x 120 = 14,400 spots, spacing 1 (x = column, y = row). K = 6 domains. 5 replicates per setting.
- **Expression profiles:** DLPFC section 151507 (donor Br5292, a *dev* section), layers L1-L6 (white matter excluded to get six
  domains). Genes: the 5,000 with the highest mean count over L1-L6 spots. For domain d, gene g:
  `mu[g,d] = sum_{i in d} c[g,i] / sum_{i in d} l[i] * L0` (l[i] = library size over the 5,000 genes, L0 = median l[i] over L1-L6 spots),
  so every domain has the observed composition and the same library scale. The effect size is therefore fixed by the real data
  and identical in all settings; nothing is tuned.
- **Counts:** `y[g,i] ~ NB(mean = s[i] * mu[g,d(i)], variance = mean + phi * mean^2)`, phi = 0.5 for all genes, size factors
  `s[i] ~ LogNormal(-sigma^2/2, sigma)` with sigma = 0.3 (mean 1). Generated with numpy (gamma-Poisson). SRTsim / scDesign3 are
  used only if they install into `Rlib` before the first tissue is written; the choice is recorded in `results/newdata_sim_manifest.json`.
- **Geometry A "layered bands"** (`sim_bands`): domains 1..6 repeat m times as parallel horizontal bands in the same order,
  m in {1, 2, 4, 7}; domain(row) = floor(row * 6m / 120) mod 6 (band width about 20, 10, 5, 2.9 rows; for m = 7 widths are 2 or 3 rows,
  so domain areas differ by at most 5%). Section names `m<m>_r<replicate>`.
- **Geometry B "random blocks"** (`sim_blocks`): the lattice is cut into w x w blocks, w in {3, 5, 8, 12, 20} (all divide 120); every
  block draws one of the 6 domains uniformly at random; draws are repeated (rejection) until all 6 domains occur so that K = 6.
  Section names `w<w>_r<replicate>`.
- Generator seed: `numpy.random.default_rng([2026, geometry (A=1, B=2), m or w, replicate])`. 9 settings x 5 replicates = 45 sections.

## Methods, runs, measurements
- The 16 comparators + reference of the benchmark (`scripts/adapters.py`), unchanged code and settings; BayesSpace is **not run**
  (square lattice, not a Visium lattice). K = 6 given to every method; seeds 0, 1, 2; standardised runner (`bench_queue.run`), same
  preprocessing as the paper (whole-transcriptome path: genes in >= 50 spots and >= 10 counts, 2000 HVG, 200 PCs).
- Per-job memory cap 30 GB (deviation from the 12 GB of the 15 GB benchmark machine, which cannot hold 14,400-spot jobs for several
  methods; this host has 125 GB). Records carry `host = "deepmed2"`; run times are not compared. A job above the cap or 24 h is
  recorded as an error and not retried with other settings.
- **Execution order (priority, not design):** methods are queued cheapest first by their median measured wall time in the original
  benchmark (`results/benchmark_runs.jsonl`), all 45 sections per method before the next method. If time runs out, the
  missing cells are reported as "not run (time)"; nothing is imputed. Linear diffusion and PCA come first, so the primary
  analysis is available first.

## Primary analysis
Per section and seed, ARI of each method's own default clustering (`metrics.ARI`; secondary: matched clustering `metrics_matched`).
For each setting and replicate: `Delta = mean over seeds of [ARI(linear_diffusion) - ARI(pca_gmm)]`. For each setting: mean of Delta
over the 5 replicates with a 95% percentile bootstrap interval over replicates (10,000 resamples, numpy seed 20261104).
Equivalence margin: **0.03 ARI** (as in the paper). Differences are called effects only if |difference| > 0.03 **and** the 95% interval excludes 0.
- **H1 supported:** Delta_A(m=1) - Delta_A(m=7) > 0.03 with a 95% interval (bootstrap over replicates, paired by replicate index)
  excluding 0, and the point estimates Delta_A(m) are non-increasing in m. **Contradicted:** the difference is < -0.03 with the interval
  excluding 0. Otherwise **not supported / inconclusive**.
- **H2 supported:** Delta_B(w=3) is the smallest of the nine point estimates and Delta_B(w=3) - Delta_A(m=7) < -0.03 with the interval
  excluding 0, and Delta_B(w) is non-decreasing in w. **Contradicted:** Delta_B(w=3) - Delta_A(m=7) > 0.03 with the interval excluding 0.
  Otherwise inconclusive.
- **Ceiling/floor rule:** if all methods have mean ARI > 0.95 or < 0.10 in every setting, the design cannot discriminate; this is reported as
  "uninformative" and the design is **not** changed retroactively (a changed design would be a new, clearly labelled exploratory run).
- Descriptive: mean ARI per method and setting; the best three methods per setting (mean over replicates and seeds).

## G3 re-tests on the simulation (per setting, one statistic per finding, computed per replicate, bootstrap over the 5 replicates)
Original reference S0 = the same statistic pooled over the original datasets from the existing result files (`results/clustering_lottery*`,
`results/mclust_*`, `results/k_sensitivity*`, `results/benchmark_runs.jsonl`), which this extension never modifies. The null value n0 and the
rule are fixed here: with direction d0 = sign(S0 - n0), a finding **replicates** if d0 * (S - n0) > 0 and the 95% interval excludes n0;
it **reverses** if d0 * (S - n0) < 0 with the interval excluding n0; otherwise it **weakens** (interval includes n0).
(a) ARI range over 20 single-start fits of the same Gaussian mixture on a fixed embedding, mean over methods with an embedding: n0 = 0.03.
(b) R mclust default fit vs the R seed (10 seeds; embeddings with > 2000 observations, so all simulated tissues): mean ARI range: n0 = 0.03;
initialisation on all observations (deterministic) reported alongside.
(c) matched (20-start, best likelihood) minus default clustering, mean ARI gain over methods: n0 = 0.
(d) Spearman rho between log-likelihood and ARI of the 20 fits, median over methods: n0 = 0.
(e) K sensitivity: mean over methods of ARI(K) minus the mean of ARI(K-1) and ARI(K+1) (each method's own clustering re-run with K -/+ 1 on its
fixed embedding): n0 = 0.
With only 5 replicates the intervals are wide; this is stated wherever the verdicts are reported.

## Not part of the confirmatory analysis
Any other metric (NMI, boundary metrics), any other contrast, and any analysis suggested by looking at the results are exploratory and labelled as such.
