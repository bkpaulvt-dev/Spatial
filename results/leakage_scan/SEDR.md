# Candidate leakage lines: SEDR

Screening output; unreviewed. {'L1': 0, 'L2': 0, 'L3': 2, 'L4': 1, 'L5': 0}

## L3 (2)
- `docs/Tutorial3_Batch_integration.ipynb:cell5:11` `adata_tmp= adata_tmp[~pd.isnull(adata_tmp.obs['layer_guess'])]`
- `docs/Tutorial1_Clustering.ipynb:cell19:1` `sub_adata = adata[~pd.isnull(adata.obs['layer_guess'])]`

## L4 (1)
- `docs/Tutorial1_Clustering.ipynb:cell6:9` `n_clusters = 5 if sample_name in ['151669', '151670', '151671', '151672'] else 7`

