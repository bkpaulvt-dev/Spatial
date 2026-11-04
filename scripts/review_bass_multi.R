# Multi-sample BASS (joint fit of several sections), settings of the authors' analysis/DLPFC.Rmd (multi-sample) and analysis/MERFISH.Rmd, as in the single-section branch of run_r_method.R.
# Usage: Rscript scripts/review_bass_multi.R <dir> <n_samples> <R> <seed> <dataset>; <dir>/<i>/{counts.mtx,genes.txt,barcodes.txt,coords.csv}; writes <dir>/labels_<i>.csv
args <- commandArgs(trailingOnly = TRUE); dir <- args[1]; n <- as.integer(args[2]); R <- as.integer(args[3]); seed <- as.integer(args[4]); ds <- args[5]
suppressPackageStartupMessages({library(Matrix); library(BASS)})
cnts <- list(); xys <- list()
for (i in 0:(n - 1)) {
  d <- file.path(dir, i)
  m <- as(readMM(file.path(d, "counts.mtx")), "CsparseMatrix"); rownames(m) <- readLines(file.path(d, "genes.txt")); colnames(m) <- readLines(file.path(d, "barcodes.txt"))
  xy <- read.csv(file.path(d, "coords.csv")); xym <- as.matrix(xy[, c("x", "y")]); rownames(xym) <- colnames(m)
  xym[, 1] <- xym[, 1] - min(xym[, 1]); xym[, 2] <- xym[, 2] - min(xym[, 2])   # as in MERFISH.Rmd (BASS builds neighbours per sample: translation does not matter)
  cnts[[i + 1]] <- m; xys[[i + 1]] <- xym
}
g <- Reduce(intersect, lapply(cnts, rownames)); cnts <- lapply(cnts, function(m) m[g, , drop = FALSE])
set.seed(seed)
ns <- Sys.getenv("BASS_NSAMPLE", "")   # dry runs only
if (ds == "dlpfc") {
  obj <- createBASSObject(cnts, xys, C = 20, R = R, beta_method = "SW", init_method = "mclust", nsample = if (nzchar(ns)) as.integer(ns) else 10000)
  obj <- BASS.preprocess(obj, doLogNormalize = TRUE, geneSelect = "sparkx", nSE = 3000, doPCA = TRUE, scaleFeature = FALSE, nPC = 20)
} else {
  obj <- if (nzchar(ns)) createBASSObject(cnts, xys, C = 20, R = R, beta_method = "SW", nsample = as.integer(ns)) else createBASSObject(cnts, xys, C = 20, R = R, beta_method = "SW")
  obj <- BASS.preprocess(obj, doLogNormalize = TRUE, doPCA = TRUE, scaleFeature = TRUE, nPC = 20)
}
obj <- BASS.run(obj); obj <- BASS.postprocess(obj)
for (i in 0:(n - 1)) write.csv(data.frame(label = obj@results$z[[i + 1]]), file.path(dir, paste0("labels_", i, ".csv")), row.names = FALSE)
