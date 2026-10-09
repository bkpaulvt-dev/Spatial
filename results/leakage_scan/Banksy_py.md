# Candidate leakage lines: Banksy_py

Screening output; unreviewed. {'L1': 2, 'L2': 0, 'L3': 4, 'L4': 0, 'L5': 3}

## L1 (2)
- `test_with_real_data.py:173` `assert ari > 0.0, f"ARI should be positive, got {ari}"`
- `test_with_real_data.py:176` `print("[PASS] Step 5: labels and ARI verified\n")`

## L3 (4)
- `starmap_analysis.ipynb:cell5:2` `adata = adata[adata.obs["cluster_name"].notnull()]`
- `test_with_real_data.py:46` `adata = adata[adata.obs["cluster_name"].notnull()]`
- `starmap_analysis.py:82` `adata = adata[adata.obs["cluster_name"].notnull()]`
- `src/banksy_utils/plot_utils.py:571` `if isinstance(c, pd.Series) and c.isnull().any():`

## L5 (3)
- `src/banksy_utils/refine_clusters.py:91` `while ((total_entropy * 100 > 5) and (num_iter < 20)):`
- `src/banksy/cluster_methods.py:288` `for resolution in resolutions:`
- `src/banksy/cluster_methods.py:425` `while (num_labels != max_labels) and (iter < max_iter):`

