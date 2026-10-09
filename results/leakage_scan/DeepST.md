# Candidate leakage lines: DeepST

Screening output; unreviewed. {'L1': 0, 'L2': 1, 'L3': 3, 'L4': 3, 'L5': 1}

## L2 (1)
- `run_deepst.ipynb:cell1:78` `n_domains=len(SAMPLE_IDS) )                 # Number of batches`

## L3 (3)
- `deepstkit/utils_func.py:232` `count.dropna(inplace=True)`
- `Benchmark/run_DLPFCs_SEDR.py:138` `df_meta = df_meta[~pd.isnull(df_meta['layer_guess'])]`
- `Benchmark/run_DLPFCs_SpaGCN.py:140` `df_meta = df_meta[~pd.isnull(df_meta['layer_guess'])]`

## L4 (3)
- `Benchmark/run_DLPFC_bayesspace.R:20` `if(sample.name %in% c('151669', '151670', '151671', '151672')) {`
- `Benchmark/run_DLPFCs_SEDR.py:119` `if data_name in ['151669', '151670', '151671', '151672']:`
- `Benchmark/run_DLPFCs_SpaGCN.py:27` `if sample_name in ['151669', '151670', '151671', '151672']:`

## L5 (1)
- `Benchmark/run_DLPFCs_SEDR.py:76` `for res in sorted(list(np.arange(0.2, 2.5, increment)), reverse=True):`

