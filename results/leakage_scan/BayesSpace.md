# Candidate leakage lines: BayesSpace

Screening output; unreviewed. {'L1': 0, 'L2': 0, 'L3': 2, 'L4': 0, 'L5': 0}

## L3 (2)
- `R/utils.R:271` `if (is.null(name) || is.na(name)) {`
- `R/spatialCluster.R:273` `df_j <- map(df_j, function(nbrs) discard(nbrs, function(x) is.na(x)))`

