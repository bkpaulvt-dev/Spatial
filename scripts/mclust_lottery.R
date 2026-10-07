# Clustering lottery with R mclust (the implementation used by HiSTaR, STAGATE, SEDR, ...).
#
# mclust initialises EM with model-based hierarchical agglomeration, so one call on a fixed
# embedding is deterministic. We therefore ask how sensitive that call is to perturbations
# far smaller than the differences between training runs:
#   base : Mclust(Z, G = k, modelNames = "EEE") with defaults
#   jit  : Z + N(0, (0.01 * column SD)^2), 10 repetitions
#   perm : rows randomly permuted (result mapped back), 10 repetitions
# Input : results/emb/csv/<dataset>__<section>__<method>__k<k>.csv (+ __labels.csv)
# Output: results/mclust_lottery.csv
suppressPackageStartupMessages(library(mclust))
args <- commandArgs(trailingOnly = TRUE)
dir <- if (length(args) > 0) args[1] else "results/emb/csv"
out <- if (length(args) > 1) args[2] else "results/mclust_lottery.csv"
files <- list.files(dir, pattern = "__k[0-9]+\\.csv$", full.names = TRUE)
if (length(args) > 2) files <- files[grepl(args[3], files)]
rows <- list()
fit <- function(Z, k) Mclust(Z, G = k, modelNames = "EEE", verbose = FALSE)
for (f in files) {
  parts <- strsplit(sub("\\.csv$", "", basename(f)), "__")[[1]]
  ds <- parts[1]; sec <- parts[2]; method <- parts[3]; k <- as.integer(sub("k", "", parts[4]))
  Z <- as.matrix(read.csv(f, header = FALSE))
  y <- readLines(file.path(dir, paste0(ds, "__", sec, "__labels.csv")))
  keep <- y != "NA"
  ari <- function(cl) adjustedRandIndex(cl[keep], y[keep])
  rec <- function(kind, rep, m, secs) data.frame(dataset = ds, slice = sec, method = method, kind = kind,
                                                 rep = rep, ARI = if (is.null(m)) NA else ari(m$classification),
                                                 loglik_per_obs = if (is.null(m)) NA else m$loglik / nrow(Z),
                                                 seconds = secs)
  t0 <- Sys.time(); m <- fit(Z, k); rows[[length(rows) + 1]] <- rec("base", 0, m, as.numeric(Sys.time() - t0, units = "secs"))
  sds <- apply(Z, 2, sd)
  for (r in 1:10) {
    set.seed(r)
    Zj <- Z + matrix(rnorm(length(Z)), nrow(Z)) %*% diag(0.01 * sds)
    m <- tryCatch(fit(Zj, k), error = function(e) NULL)
    rows[[length(rows) + 1]] <- rec("jitter1pct", r, m, NA)
    o <- sample(nrow(Z))
    m <- tryCatch(fit(Z[o, , drop = FALSE], k), error = function(e) NULL)
    if (!is.null(m)) { cl <- integer(nrow(Z)); cl[o] <- m$classification; m$classification <- cl }
    rows[[length(rows) + 1]] <- rec("permute", r, m, NA)
  }
  cat(ds, sec, method, "done\n")
  write.csv(do.call(rbind, rows), out, row.names = FALSE)
}
