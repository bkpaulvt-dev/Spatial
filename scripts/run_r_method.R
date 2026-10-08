# Run BASS or BayesSpace on one section with the authors' published settings.
# Usage: Rscript scripts/run_r_method.R <method> <dir> <k> <seed> <dataset>
# <dir> holds counts.mtx (genes x spots), genes.txt, barcodes.txt, coords.csv (x, y, row, col);
# writes <dir>/labels.csv.
args <- commandArgs(trailingOnly = TRUE)
method <- args[1]; dir <- args[2]; k <- as.integer(args[3]); seed <- as.integer(args[4]); ds <- args[5]
suppressPackageStartupMessages(library(Matrix))
cnt <- as(readMM(file.path(dir, "counts.mtx")), "CsparseMatrix")
rownames(cnt) <- readLines(file.path(dir, "genes.txt")); colnames(cnt) <- readLines(file.path(dir, "barcodes.txt"))
xy <- read.csv(file.path(dir, "coords.csv"), row.names = 1)
set.seed(seed)
if (method == "bass") {
  # BASS-Analysis/analysis/{DLPFC,STARmap,MERFISH}.Rmd (run per section here, not jointly)
  suppressPackageStartupMessages(library(BASS))
  xym <- as.matrix(xy[, c("x", "y")]); rownames(xym) <- colnames(cnt)
  if (ds == "dlpfc") {
    obj <- createBASSObject(list(cnt), list(xym), C = 20, R = k, beta_method = "SW", init_method = "mclust", nsample = 10000)
    obj <- BASS.preprocess(obj, doLogNormalize = TRUE, geneSelect = "sparkx", nSE = 3000, doPCA = TRUE, scaleFeature = FALSE, nPC = 20)
  } else {
    obj <- createBASSObject(list(cnt), list(xym), C = if (ds == "starmap") 15 else 20, R = k, beta_method = "SW")
    obj <- BASS.preprocess(obj, doLogNormalize = TRUE, doPCA = TRUE, scaleFeature = TRUE, nPC = 20)
  }
  obj <- BASS.run(obj)
  obj <- BASS.postprocess(obj)
  lab <- obj@results$z[[1]]
} else if (method == "bayesspace") {
  # Package defaults for Visium (v1.5.1): 2000 HVGs, 15 PCs, mclust init, t model, gamma 3, 50000 MCMC
  suppressPackageStartupMessages({library(BayesSpace); library(SingleCellExperiment)})
  sce <- SingleCellExperiment(assays = list(counts = cnt),
                              colData = DataFrame(row = xy$row, col = xy$col, imagerow = xy$y, imagecol = xy$x))
  sce <- spatialPreprocess(sce, platform = "Visium", n.PCs = 15, n.HVGs = 2000, log.normalize = TRUE)
  sce <- spatialCluster(sce, q = k, platform = "Visium", d = 15, init.method = "mclust", model = "t",
                        nrep = 50000, burn.in = 1000)
  lab <- sce$spatial.cluster
}
write.csv(data.frame(barcode = colnames(cnt), label = lab), file.path(dir, "labels.csv"), row.names = FALSE)
