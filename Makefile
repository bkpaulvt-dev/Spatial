# Reproduce "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods".
#
#   make check        numbers + tests against the committed results (~2 min, no data needed)
#   make numbers supplement figures paper    rebuild every table, number, figure and the PDFs
#   make data         download DLPFC, STARmap, MERFISH, Visium breast cancer and Stereo-seq (MOSTA) and verify
#                     data/CHECKSUMS.sha256 (Stereo-seq files are ~1-2 GB each)
#   make benchmark    LONG: the full benchmark (16 methods, 17 configurations) (~150 CPU-hours, single thread, <= 13 GB RAM per job)
#   make benchmark-new LONG: breast cancer and Stereo-seq in the standardised runner, one job at a time with a 12 GB cap
#                     (the cap is set only for this target; the first three datasets were run without it)
#   make robustness   LONG: clustering-initialisation (lottery), K sensitivity and R mclust experiments (~1-2 days)
# Memory: one R mclust fit on the 18,408-bin Stereo-seq section uses ~5 GB; run at most two mclust jobs at a time on a
# 16 GB machine. The runner's cap is set with SPATIALBENCH_MAX_RSS_GB (benchmark-new only).
#   make all          = numbers supplement figures paper check (does NOT rerun the benchmark)
#
# Everything runs on CPU with one thread per job (OMP_NUM_THREADS=1), as for the paper.
# Figures 1 and 5 need results/cache, results/runs and results/emb (see README "Large intermediates").

PYTHON  ?= python
RSCRIPT ?= Rscript
WORKERS ?= 1
export OMP_NUM_THREADS := 1
export MKL_NUM_THREADS := 1
export OPENBLAS_NUM_THREADS := 1

BASS_ANALYSIS_COMMIT := 81dfe7353093823eed68f403d9c4033031b73de4
BASS_ANALYSIS := data/ext/BASS-Analysis
EMBCSV := results/emb/csv

.PHONY: all env data data-dlpfc data-extra data-new cache benchmark benchmark-new benchmark-legacy robustness lottery \
        k-sensitivity mclust mclust-seed export-emb qc stats numbers supplement figures paper check test help

all: numbers supplement figures paper check

help:
	@sed -n '1,12p' Makefile

# ---------------------------------------------------------------- environment
env:
	$(PYTHON) -m pip install -r environment/requirements-lock.txt
	@echo "R packages: see README 'Installation' (R 4.3.3; mclust 6.0.1, BASS, BayesSpace 1.5.1, SPARK)."
	@echo "Method clones: git clone each repository in configs/methods.yaml into data/ext/methods/ at its commit."

# ---------------------------------------------------------------- data
data: data-dlpfc data-extra data-new cache

data-dlpfc:
	$(PYTHON) scripts/download_dlpfc.py

data-extra:
	@if [ ! -d $(BASS_ANALYSIS)/.git ]; then git clone https://github.com/zhengli09/BASS-Analysis $(BASS_ANALYSIS); fi
	git -C $(BASS_ANALYSIS) checkout -q $(BASS_ANALYSIS_COMMIT)
	sha256sum -c --ignore-missing data/CHECKSUMS.sha256
	$(RSCRIPT) scripts/export_bass_data.R $(BASS_ANALYSIS)/data data/ext/csv

# Visium breast cancer (10x) and Stereo-seq MOSTA E9.5_E1S1, E10.5_E2S1, E10.5_E1S1 (CNGB), with checksums
data-new:
	$(PYTHON) scripts/download_new_datasets.py

# preprocessed sections: results/cache/<section>.npz (whole transcriptome: HVG + 200 PCs; STARmap/MERFISH: 50 PCs)
cache:
	$(PYTHON) scripts/download_dlpfc.py --verify-only --build-cache
	$(PYTHON) scripts/prepare_extra.py
	$(PYTHON) scripts/prepare_new_datasets.py

# per-section quality control -> results/qc/section_qc.csv
qc:
	$(PYTHON) scripts/run_qc.py

# ---------------------------------------------------------------- benchmark (LONG)
# Unified runner: every (method, dataset, section, seed) -> results/runs/<id>.json|npz and results/benchmark_runs.jsonl.
# Memory-safe order of scripts/run_fill_v2.sh: DeepST, BayesSpace and NichePCA alone (up to 12.5 GB).
benchmark:
	$(PYTHON) scripts/bench_queue.py --methods linear_diffusion anisost pca_gmm banksy_l0.2 banksy_l0.8 histar spagcn \
	    graphst stagate sedr spaceflow spatial_mgcn ccst bass --seeds 0 1 2 --workers $(WORKERS)
	$(PYTHON) scripts/bench_queue.py --methods nichepca --seeds 0 1 2 --workers 1
	$(PYTHON) scripts/bench_queue.py --methods deepst bayesspace --seeds 0 --workers 1
	$(PYTHON) scripts/bench_queue.py --methods linear_diffusion anisost pca_gmm banksy_l0.2 banksy_l0.8 histar spagcn \
	    graphst stagate sedr spaceflow spatial_mgcn ccst bass nichepca --seeds 0 1 2 --workers 1 --retry-errors
	$(PYTHON) scripts/bench_queue.py --methods deepst bayesspace --seeds 0 --workers 1 --retry-errors
	$(PYTHON) scripts/baselines_3start.py

# breast cancer and Stereo-seq (added later; runner only), every method, one job at a time under the memory cap
benchmark-new:
	SPATIALBENCH_MAX_RSS_GB=12 $(PYTHON) scripts/bench_queue.py --datasets brca stereo --seeds 0 1 2 --workers 1
	$(PYTHON) scripts/baselines_3start.py

# Earlier per-family pipelines whose result files the paper also reads (HiSTaR/HiCAST, AnisoST, BANKSY/SpaGCN,
# STARmap/MERFISH, GraphST, the 9 "new" methods) and the boundary analysis.
benchmark-legacy:
	$(PYTHON) scripts/benchmark_dlpfc.py --data data/DLPFC --out results/dlpfc_main.jsonl --cache results/cache \
	    --seeds 0 1 2 --methods histar histar_deterministic hicast --workers $(WORKERS)
	$(PYTHON) scripts/benchmark_anisost.py --cache results/cache --out results/anisost_main.jsonl
	$(PYTHON) scripts/benchmark_baselines.py --data data/DLPFC --out results/baselines.jsonl
	$(PYTHON) scripts/benchmark_extra.py --out results/extra.jsonl
	$(PYTHON) scripts/benchmark_graphst.py --out results/graphst.jsonl
	$(PYTHON) scripts/benchmark_new_methods.py --methods all --workers $(WORKERS)
	$(PYTHON) scripts/benchmark_new_methods.py --methods deepst --workers 1
	$(PYTHON) scripts/boundary_analysis.py

# ---------------------------------------------------------------- robustness (LONG)
robustness: lottery k-sensitivity mclust mclust-seed

# seed-0 embeddings of the runner methods -> results/emb/<dataset>_<section>_<method>.npy
export-emb:
	$(PYTHON) scripts/export_runner_emb.py
	$(PYTHON) -c "import glob,os,numpy as np; [np.save('results/emb/%s_%s_%s.npy' % tuple(os.path.basename(f).split('__')[:3]), np.load(f)['emb']) for f in sorted(glob.glob('results/runs/*__s0.npz')) if os.path.basename(f).split('__')[2] in ('linear_diffusion','pca_gmm','banksy_l0.2','banksy_l0.8') and not os.path.exists('results/emb/%s_%s_%s.npy' % tuple(os.path.basename(f).split('__')[:3]))]"

# 20 single-start GMM fits per fixed seed-0 embedding (also writes results/emb/csv for R)
lottery: export-emb
	METHODS="histar anisost graphst stagate sedr spaceflow nichepca ccst spatial_mgcn deepst linear_diffusion pca_gmm banksy_l0.2 banksy_l0.8" \
	    WORKERS=$(WORKERS) $(PYTHON) scripts/clustering_lottery.py

# K - 2 ... K + 2 and BIC choice of K on every seed-0 embedding (matched clustering)
k-sensitivity: lottery
	$(PYTHON) scripts/k_sensitivity.py

# R mclust perturbation experiment (row permutation, 1% noise). File names follow the committed files;
# an existing file is not recomputed (delete it, or use make -B, to rerun it).
MCLUST_METHODS := linear_diffusion pca_gmm banksy_l0.2 banksy_l0.8 stagate sedr spaceflow nichepca ccst spatial_mgcn deepst
MCLUST_OUT := $(foreach m,$(MCLUST_METHODS),results/mclust_lottery_$(m).csv) results/mclust_lottery_dlpfc.csv \
	results/mclust_lottery_extra.csv results/mclust_lottery_graphst_dlpfc1.csv results/mclust_lottery_graphst_dlpfc2.csv \
	results/mclust_lottery_graphst_dlpfc3.csv results/mclust_lottery_graphst_extra.csv
mclust: $(MCLUST_OUT)
results/mclust_lottery_dlpfc.csv:         ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ '^.*/dlpfc__.*__(histar|anisost)__k'
results/mclust_lottery_extra.csv:         ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ '/(starmap|merfish)__.*__(histar|anisost)__k'
results/mclust_lottery_graphst_dlpfc1.csv: ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ 'dlpfc__(151507|151508|151671|151672|151673|151674)__graphst__k'
results/mclust_lottery_graphst_dlpfc2.csv: ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ 'dlpfc__(151509|151510|151669)__graphst__k'
results/mclust_lottery_graphst_dlpfc3.csv: ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ 'dlpfc__(151670|151675|151676)__graphst__k'
results/mclust_lottery_graphst_extra.csv: ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ '/(starmap|merfish)__.*__graphst__k'
results/mclust_lottery_%.csv:             ; $(RSCRIPT) scripts/mclust_lottery.R $(EMBCSV) $@ '__$*__k'

# R mclust random-subset initialisation (set.seed 1..10, full-data and jittered initialisation). Resumable;
# run as groups (make -j2 mclust-seed: see the memory note at the top); paper_v2.py reads results/mclust_seed_g*.csv.
# Groups 1-4 match their method regex on every section, so they include the breast cancer and smaller Stereo-seq sections
# when those embeddings exist; group 6 is the 18,408-bin Stereo-seq section. Several workers may share one output file
# (an embedding is claimed with a lock directory <out>.lock_*; after a crash delete stale lock directories).
MCLUST_SEED_G1 := __(histar|anisost|linear_diffusion|pca_gmm)__k
MCLUST_SEED_G2 := __(banksy_l0.2|banksy_l0.8|graphst|stagate)__k
MCLUST_SEED_G3 := __(sedr|spaceflow|nichepca)__k
MCLUST_SEED_G4 := __(ccst|spatial_mgcn|deepst)__k
MCLUST_SEED_G5 := (brca__block_a_1|stereo__E9.5_E1S1|stereo__E10.5_E2S1)__
MCLUST_SEED_G6 := stereo__E10.5_E1S1__
mclust-seed: mclust-seed-g1 mclust-seed-g2 mclust-seed-g3 mclust-seed-g4 mclust-seed-g5 mclust-seed-g6
mclust-seed-g6:   # 18,408 bins: ~30 min per full-data fit, so without the noise repetitions except where already run
	MCLUST_NO_JIT=1 $(RSCRIPT) scripts/mclust_seed.R $(EMBCSV) results/mclust_seed_g6.csv '$(MCLUST_SEED_G6)'
mclust-seed-g%:
	$(RSCRIPT) scripts/mclust_seed.R $(EMBCSV) results/mclust_seed_g$*.csv '$(MCLUST_SEED_G$*)'

# ---------------------------------------------------------------- analysis (fast, from committed results)
stats:
	$(PYTHON) scripts/stats_cluster_aware.py
	STATS_SOURCE=runner $(PYTHON) scripts/stats_cluster_aware.py
	STATS_EXCLUDE=starmap,stereo $(PYTHON) scripts/stats_cluster_aware.py

numbers: stats
	$(PYTHON) scripts/brca_coarse.py
	$(PYTHON) scripts/paper_numbers.py
	$(PYTHON) scripts/paper_v2.py
	$(PYTHON) scripts/coverage_matrix.py

supplement: numbers
	$(PYTHON) scripts/make_supplement.py

figures: numbers
	$(PYTHON) scripts/make_figures_nar.py
	$(PYTHON) scripts/make_fig1_pipeline_v2.py
	$(PYTHON) scripts/make_graphical_abstract.py
	$(PYTHON) scripts/make_figures.py

paper:
	cd paper && pdflatex -interaction=nonstopmode main >/dev/null; bibtex main >/dev/null; \
	    pdflatex -interaction=nonstopmode main >/dev/null; pdflatex -interaction=nonstopmode main
	cd paper && pdflatex -interaction=nonstopmode supplementary >/dev/null; bibtex supplementary >/dev/null; \
	    pdflatex -interaction=nonstopmode supplementary >/dev/null; pdflatex -interaction=nonstopmode supplementary

test:
	$(PYTHON) -m pytest -q tests

check: test
	$(PYTHON) scripts/check_paper_numbers.py
	@if [ -d data/DLPFC ]; then sha256sum -c --quiet --ignore-missing data/CHECKSUMS.sha256 && echo 'raw data checksums OK'; \
	    else echo 'data/ not downloaded: checksum verification skipped'; fi
