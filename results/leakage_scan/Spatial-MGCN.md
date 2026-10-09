# Candidate leakage lines: Spatial-MGCN

Screening output; unreviewed. {'L1': 10, 'L2': 3, 'L3': 5, 'L4': 0, 'L5': 2}

## L1 (10)
- `Spatial-MGCN/HBC_test.py:112` `ari_max = 0`
- `Spatial-MGCN/HBC_test.py:123` `ari_res = metrics.adjusted_rand_score(labels, idx)`
- `Spatial-MGCN/HBC_test.py:124` `if ari_res > ari_max:`
- `Spatial-MGCN/HBC_test.py:125` `ari_max = ari_res`
- `Spatial-MGCN/DLPFC_test.py:113` `ari_max = 0`
- `Spatial-MGCN/DLPFC_test.py:125` `ari_res = metrics.adjusted_rand_score(labels, idx)`
- `Spatial-MGCN/DLPFC_test.py:126` `if ari_res > ari_max:`
- `Spatial-MGCN/DLPFC_test.py:127` `ari_max = ari_res`
- `Spatial-MGCN/DLPFC_test.py:133` `print(dataset, ' ', ari_max)`
- `Spatial-MGCN/DLPFC_test.py:135` `title = 'Spatial-MGCN: ARI={:.2f}'.format(ari_max)`

## L2 (3)
- `Spatial-MGCN/HBC_test.py:70` `config.class_num = len(ground.unique())`
- `Spatial-MGCN/DLPFC_test.py:78` `config.class_num = len(ground.unique())`
- `Spatial-MGCN/utils.py:327` `n_clusters = len(np.unique(labels))`

## L3 (5)
- `Spatial-MGCN/DLPFC_generate_data.py:30` `NA_labels = np.where(labels.isnull())`
- `Spatial-MGCN/DLPFC_generate_data.py:31` `labels = labels.drop(labels.index[NA_labels])`
- `Spatial-MGCN/DLPFC_generate_data.py:46` `data = np.delete(adata1.X.toarray(), NA_labels, axis=0)`
- `Spatial-MGCN/DLPFC_generate_data.py:47` `obs_names = np.delete(obs_names, NA_labels, axis=0)`
- `Spatial-MGCN/DLPFC_generate_data.py:48` `positions = np.delete(positions, NA_labels, axis=0)`

## L5 (2)
- `Spatial-MGCN/HBC_test.py:116` `for epoch in range(config.epochs):`
- `Spatial-MGCN/DLPFC_test.py:118` `for epoch in range(config.epochs):`

