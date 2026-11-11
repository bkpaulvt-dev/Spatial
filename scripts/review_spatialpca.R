# SpatialPCA (Shang & Zhou, Nat Commun 2022; github.com/shangll123/SpatialPCA) with the settings of its DLPFC tutorial: SPARK-X spatially variable genes (3000; all genes for targeted panels),
# Gaussian kernel with Sheather-Jones bandwidth, 20 spatial PCs, walktrap clustering on the PCs (knearest 70) with K domains.
# Deviation for large sections (O(n^2) kernel): n > 5000 -> fast = TRUE with 20 eigenvectors (the authors' option for large data); n > 20000 -> sparse kernel too. Recorded in `mode` of the output.
# Usage: Rscript scripts/review_spatialpca.R <dir> <k> <seed> <dataset>; writes <dir>/labels.csv and <dir>/emb.csv (spatial PCs, spots x 20)
args <- commandArgs(trailingOnly = TRUE); dir <- args[1]; k <- as.integer(args[2]); seed <- as.integer(args[3]); ds <- args[4]
suppressPackageStartupMessages({library(Matrix); library(SpatialPCA)})
cnt <- as(readMM(file.path(dir, "counts.mtx")), "CsparseMatrix")
rownames(cnt) <- readLines(file.path(dir, "genes.txt")); colnames(cnt) <- readLines(file.path(dir, "barcodes.txt"))
xy <- read.csv(file.path(dir, "coords.csv"), row.names = 1); loc <- as.matrix(xy[, c("x", "y")]); rownames(loc) <- colnames(cnt)
set.seed(seed); n <- ncol(cnt); whole <- nrow(cnt) > 3000
obj <- if (whole) {
  CreateSpatialPCAObject(counts = cnt, location = loc, project = "sp", gene.type = "spatial", sparkversion = "sparkx", numCores_spark = 1, gene.number = 3000, min.loctions = 20, min.features = 20)
} else {
  CreateSpatialPCAObject(counts = cnt, location = loc, project = "sp", gene.type = "custom", customGenelist = rownames(cnt), min.loctions = 20, min.features = 20)
}
big <- n > 5000; sparse <- n > 20000
cat("SpatialPCA", as.character(packageVersion("SpatialPCA")), "n", n, "fast", big, "sparse kernel", sparse, "\n")
obj <- SpatialPCA_buildKernel(obj, kerneltype = "gaussian", bandwidthtype = "SJ", sparseKernel = sparse)
obj <- if (big) {
  SpatialPCA_EstimateLoading(obj, fast = TRUE, SpatialPCnum = 20, eigenvecnum = 20)
} else {
  SpatialPCA_EstimateLoading(obj, fast = FALSE, SpatialPCnum = 20)
}
obj <- if (big) {
  SpatialPCA_SpatialPCs(obj, fast = TRUE, eigenvecnum = 20)
} else {
  SpatialPCA_SpatialPCs(obj, fast = FALSE)
}
Z <- obj@SpatialPCs                      # PCs x kept spots
lab <- walktrap_clustering(clusternum = k, latent_dat = Z, knearest = 70)
kept <- colnames(Z)
full <- rep(NA_integer_, ncol(cnt)); names(full) <- colnames(cnt); full[kept] <- as.integer(factor(lab))
write.csv(data.frame(barcode = colnames(cnt), label = full), file.path(dir, "labels.csv"), row.names = FALSE)
E_ <- matrix(NA_real_, ncol(cnt), nrow(Z)); rownames(E_) <- colnames(cnt); E_[kept, ] <- t(Z)
write.csv(E_, file.path(dir, "emb.csv"))
