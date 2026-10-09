# Candidate leakage lines: CCST

Screening output; unreviewed. {'L1': 0, 'L2': 5, 'L3': 0, 'L4': 0, 'L5': 1}

## L2 (5)
- `CCST_merfish_utils.py:60` `n_clusters = max(cell_cluster_type_list) + 1 # start from 0`
- `CCST.py:116` `n_clusters = len(clusters)`
- `CCST.py:162` `n_clusters = len(clusters)`
- `CCST_ST_utils.py:131` `n_clusters = max(cell_cluster_type_list) + 1 # start from 0`
- `CCST_ST_utils.py:221` `n_clusters = max(cell_type_indeces)+1 #num_cell_types, start from 0`

## L5 (1)
- `CCST.py:86` `for epoch in range(args.num_epoch):`

