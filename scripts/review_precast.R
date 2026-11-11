# PRECAST (Liu et al., Nat Commun 2022; CRAN PRECAST) on ONE section with the settings of its tutorial: 2000 SPARK-X genes, Sigma_equal = FALSE, default maxIter, K domains.
# Platform: spot grids (Visium group) use platform "Visium" with the array row/col; every other platform "Other_SRT" (distance graph on the coordinates).
# Usage: Rscript scripts/review_precast.R <dir> <k> <seed> <dataset> <is_visium 0|1>; writes <dir>/labels.csv and <dir>/emb.csv (latent features hZ of the kept spots)
args <- commandArgs(trailingOnly = TRUE); dir <- args[1]; k <- as.integer(args[2]); seed <- as.integer(args[3]); ds <- args[4]; vis <- as.integer(args[5])
suppressPackageStartupMessages({library(Matrix); library(Seurat); library(PRECAST)})
cnt <- as(readMM(file.path(dir, "counts.mtx")), "CsparseMatrix")
rownames(cnt) <- readLines(file.path(dir, "genes.txt")); colnames(cnt) <- readLines(file.path(dir, "barcodes.txt"))
xy <- read.csv(file.path(dir, "coords.csv"), row.names = 1)
meta <- if (vis == 1) data.frame(row = xy$row, col = xy$col, row.names = colnames(cnt)) else data.frame(row = xy$y, col = xy$x, row.names = colnames(cnt))
seu <- CreateSeuratObject(counts = cnt, meta.data = meta, min.cells = 0, min.features = 0)
set.seed(seed)
whole <- nrow(cnt) > 2000
pre <- CreatePRECASTObject(seuList = list(seu), project = "sp", gene.number = if (whole) 2000 else nrow(cnt), selectGenesMethod = if (whole) "SPARK-X" else "HVGs",
                           premin.spots = 20, premin.features = 20, postmin.spots = 1, postmin.features = 10)
pre <- AddAdjList(pre, platform = if (vis == 1) "Visium" else "Other_SRT")
pre <- AddParSetting(pre, Sigma_equal = FALSE, verbose = FALSE, int.model = NULL, seed = seed)
cat("PRECAST", as.character(packageVersion("PRECAST")), "platform", if (vis == 1) "Visium" else "Other_SRT", "\n")
pre <- PRECAST(pre, K = k)
pre <- SelectModel(pre)                  # tutorial step: with one K it fills resList$cluster / resList$hZ with one entry per sample
kept <- colnames(pre@seulist[[1]]); lab <- pre@resList$cluster[[1]]
stopifnot(length(lab) == length(kept))
full <- rep(NA_integer_, ncol(cnt)); names(full) <- colnames(cnt); full[kept] <- as.integer(lab)
write.csv(data.frame(barcode = colnames(cnt), label = full), file.path(dir, "labels.csv"), row.names = FALSE)
Z <- pre@resList$hZ[[1]]; E <- matrix(NA_real_, ncol(cnt), ncol(Z)); rownames(E) <- colnames(cnt); E[kept, ] <- Z
write.csv(E, file.path(dir, "emb.csv"))
