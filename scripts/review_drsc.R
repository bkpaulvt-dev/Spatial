# DR-SC (Liu et al., Nucleic Acids Res 2022; CRAN DR.SC) on ONE section with the settings of its tutorial: log-normalise, 2000 variable genes (all genes for targeted panels), DR.SC(seu, K, platform) with the package defaults
# (q = 50 PCA dimension of the wrapper, 15 latent factors), coreNum = 1. Spot grids (Visium group): platform "Visium" with the array row/col; every other platform "Other_SRT" (coordinates x, y).
# Usage: Rscript scripts/review_drsc.R <dir> <k> <seed> <dataset> <is_visium 0|1>; writes <dir>/labels.csv and <dir>/emb.csv (latent factors)
args <- commandArgs(trailingOnly = TRUE); dir <- args[1]; k <- as.integer(args[2]); seed <- as.integer(args[3]); ds <- args[4]; vis <- as.integer(args[5])
suppressPackageStartupMessages({library(Matrix); library(Seurat); library(DR.SC)})
cnt <- as(readMM(file.path(dir, "counts.mtx")), "CsparseMatrix")
rownames(cnt) <- readLines(file.path(dir, "genes.txt")); colnames(cnt) <- readLines(file.path(dir, "barcodes.txt"))
xy <- read.csv(file.path(dir, "coords.csv"), row.names = 1)
meta <- if (vis == 1) data.frame(row = xy$row, col = xy$col, row.names = colnames(cnt)) else data.frame(row = xy$y, col = xy$x, row.names = colnames(cnt))
seu <- CreateSeuratObject(counts = cnt, meta.data = meta, min.cells = 0, min.features = 0)
set.seed(seed)
seu <- NormalizeData(seu, verbose = FALSE)
seu <- FindVariableFeatures(seu, nfeatures = min(2000, nrow(cnt)), verbose = FALSE)
cat("DR.SC", as.character(packageVersion("DR.SC")), "platform", if (vis == 1) "Visium" else "Other_SRT", "\n")
seu <- DR.SC(seu, K = k, platform = if (vis == 1) "Visium" else "Other_SRT", coreNum = 1, verbose = FALSE)
lab <- seu@meta.data[["spatial.drsc.cluster"]]
write.csv(data.frame(barcode = colnames(seu), label = as.integer(lab)), file.path(dir, "labels.csv"), row.names = FALSE)
red <- grep("dr", names(seu@reductions), value = TRUE, ignore.case = TRUE)
if (length(red) > 0) write.csv(Embeddings(seu, red[1]), file.path(dir, "emb.csv"))
