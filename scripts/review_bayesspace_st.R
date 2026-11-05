# BayesSpace with platform "ST" (square lattice, 4 neighbours) on a bin grid (Stereo-seq). Everything else as the Visium run of scripts/run_r_method.R:
# 2000 HVGs, 15 PCs, mclust init, t model, burn-in 1000, 50000 MCMC iterations (package defaults of the installed version; gamma = platform default (2 for ST)).
# Usage: Rscript scripts/review_bayesspace_st.R <dir> <k> <seed> <dataset>   (BSPACE_NREP overrides the iterations: dry runs only)
args <- commandArgs(trailingOnly = TRUE)
dir <- args[1]; k <- as.integer(args[2]); seed <- as.integer(args[3])
nrep <- as.integer(Sys.getenv("BSPACE_NREP", "50000"))
suppressPackageStartupMessages({library(Matrix); library(BayesSpace); library(SingleCellExperiment)})
cnt <- as(readMM(file.path(dir, "counts.mtx")), "CsparseMatrix")
rownames(cnt) <- readLines(file.path(dir, "genes.txt")); colnames(cnt) <- readLines(file.path(dir, "barcodes.txt"))
xy <- read.csv(file.path(dir, "coords.csv"), row.names = 1)
set.seed(seed)
cat("BayesSpace", as.character(packageVersion("BayesSpace")), "platform ST, nrep", nrep, "\n")
sce <- SingleCellExperiment(assays = list(counts = cnt), colData = DataFrame(row = xy$row, col = xy$col, imagerow = xy$y, imagecol = xy$x))
sce <- spatialPreprocess(sce, platform = "ST", n.PCs = 15, n.HVGs = 2000, log.normalize = TRUE)
sce <- spatialCluster(sce, q = k, platform = "ST", d = 15, init.method = "mclust", model = "t", nrep = nrep, burn.in = 1000)   # gamma = NULL: the package default of the platform (2 for ST; the Visium value is 3) = the paper's rule 'package defaults'
write.csv(data.frame(barcode = colnames(cnt), label = sce$spatial.cluster), file.path(dir, "labels.csv"), row.names = FALSE)
