# Export the STARmap and MERFISH sections packaged in BASS-Analysis/data to CSV.
# Usage: Rscript scripts/export_bass_data.R <BASS-Analysis/data> <out_dir>
args <- commandArgs(trailingOnly = TRUE)
src <- args[1]; out <- args[2]; dir.create(out, showWarnings = FALSE, recursive = TRUE)
e <- new.env()
load(file.path(src, "starmap_mpfc.RData"), envir = e)
for (n in names(e$starmap_cnts)) {
  write.csv(t(e$starmap_cnts[[n]]), file.path(out, paste0("starmap_", n, "_counts.csv")))
  write.csv(e$starmap_info[[n]], file.path(out, paste0("starmap_", n, "_info.csv")))
}
load(file.path(src, "MERFISH_Animal1.RData"), envir = e)
for (n in c("-0.04", "-0.09", "-0.14", "-0.19", "-0.24")) {
  write.csv(t(e$cnts_mult[[n]]), file.path(out, paste0("merfish_", n, "_counts.csv")))
  write.csv(e$info_mult[[n]], file.path(out, paste0("merfish_", n, "_info.csv")))
}
