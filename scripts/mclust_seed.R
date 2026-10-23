# R mclust: what drives the variation of its default fit? (replaces the spot-order design of mclust_lottery.R)
#
# For n > mclust.options("subset") (2000) Mclust initialises EM by hierarchical agglomeration on a RANDOM
# subset of 2000 rows drawn with R's RNG, so the default fit depends on the R random seed. We separate:
#   seed     : default initialisation, row order fixed, set.seed(r), r = 1..10
#   full     : initialization = list(subset = 1:n)  (all rows; deterministic)
#   full_jit : full initialisation after adding N(0, (0.01 * column SD)^2) noise, 5 repetitions
# Input : results/emb/csv/<dataset>__<section>__<method>__k<k>.csv (+ __labels.csv)
# Output: one csv (dataset, slice, method, n, kind, rep, ARI, loglik_per_obs, seconds)
#   Rscript scripts/mclust_seed.R <csv dir> <out.csv> <filename regex>
suppressPackageStartupMessages(library(mclust))
args <- commandArgs(trailingOnly = TRUE)
dir <- args[1]; out <- args[2]
files <- list.files(dir, pattern = "__k[0-9]+\\.csv$", full.names = TRUE)
if (length(args) > 2) files <- files[grepl(args[3], files)]
done <- if (file.exists(out)) unique(paste(read.csv(out)$dataset, read.csv(out)$slice, read.csv(out)$method)) else character(0)
fit <- function(Z, k, ...) tryCatch(Mclust(Z, G = k, modelNames = "EEE", verbose = FALSE, ...), error = function(e) NULL)
for (f in files) {
  parts <- strsplit(sub("\\.csv$", "", basename(f)), "__")[[1]]
  ds <- parts[1]; sec <- parts[2]; method <- parts[3]; k <- as.integer(sub("k", "", parts[4]))
  # several workers may share one output file: re-read what is done and claim the embedding with an atomic lock directory
  if (file.exists(out)) done <- unique(paste(read.csv(out)$dataset, read.csv(out)$slice, read.csv(out)$method))
  if (paste(ds, sec, method) %in% done) next
  lock <- paste0(out, ".lock_", ds, "_", sec, "_", method)
  if (!dir.create(lock, showWarnings = FALSE)) next
  Z <- as.matrix(read.csv(f, header = FALSE)); n <- nrow(Z)
  y <- readLines(file.path(dir, paste0(ds, "__", sec, "__labels.csv"))); keep <- y != "NA"
  rows <- list()
  rec <- function(kind, rep, m, secs) data.frame(dataset = ds, slice = sec, method = method, n = n, kind = kind, rep = rep,
    ARI = if (is.null(m)) NA else adjustedRandIndex(m$classification[keep], y[keep]),
    loglik_per_obs = if (is.null(m)) NA else m$loglik / n, seconds = secs)
  for (r in 1:10) { set.seed(r); t0 <- Sys.time(); m <- fit(Z, k)
    rows[[length(rows) + 1]] <- rec("seed", r, m, as.numeric(Sys.time() - t0, units = "secs")) }
  t0 <- Sys.time(); m <- fit(Z, k, initialization = list(subset = 1:n))
  rows[[length(rows) + 1]] <- rec("full", 0, m, as.numeric(Sys.time() - t0, units = "secs"))
  sds <- apply(Z, 2, sd)
  for (r in 1:5) { set.seed(100 + r); Zj <- Z + matrix(rnorm(length(Z)), n) %*% diag(0.01 * sds, ncol(Z))
    m <- fit(Zj, k, initialization = list(subset = 1:n)); rows[[length(rows) + 1]] <- rec("full_jit", r, m, NA) }
  write.table(do.call(rbind, rows), out, sep = ",", row.names = FALSE, col.names = !file.exists(out), append = file.exists(out))
  unlink(lock, recursive = TRUE)
  cat(ds, sec, method, "done\n")
}
