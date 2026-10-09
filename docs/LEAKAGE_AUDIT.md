# Evaluation-leakage audit of released method code (Phase 1, in progress)

**Scope.** Official repositories of the benchmarked methods, at the commits below. **Method.** (1) static
screening with `scripts/audit_leakage.py` (candidate lines per category, `results/leakage_scan/`), then
(2) manual reading of every candidate. Only findings confirmed by reading the code are listed as
findings. **Status: authors not yet contacted; do not publish a claim about a specific method before
they have been given the chance to respond.**

## Taxonomy
| Code | Leakage type | Why it matters |
|---|---|---|
| L1 | Result/epoch/seed/run chosen by agreement with the annotation | reported score is the maximum over runs, optimistic by construction |
| L2 | Number of domains taken from the annotation | benign if every method is given K (our T1), but then K is not estimated |
| L3 | Unannotated spots removed before training | uses the annotation (tissue-region curation) to select training spots |
| L4 | Hyper-parameters keyed by benchmark section | tuning on the test sections |
| L5 | Loop over seeds/epochs/resolutions together with a label metric | screening aid for L1 |
| L6 | Hyper-parameters tuned on the sections later used for headline results | cannot be seen in code; taken from the papers (to be collected) |

## Confirmed findings
| Method (commit) | Type | Evidence | Effect (our measurement) |
|---|---|---|---|
| **Spatial-MGCN** (cf4412d) | **L1** | `DLPFC_test.py:113-128`, `HBC_test.py:112-126`: at every epoch the clustering is scored with `adjusted_rand_score(labels, idx)` against the annotation and the epoch with the highest ARI is kept (`idx_max`, `emb_max`) and reported (`print(dataset, ari_max)`, plot title) | label-selected epoch minus final epoch, mean over 20 sections (seed 0): **+0.147 ARI** (STARmap +0.38, DLPFC +0.13, MERFISH +0.04) |
| Spatial-MGCN | L2 | `DLPFC_test.py:78` `config.class_num = len(ground.unique())` | K from annotation |
| Spatial-MGCN | L3 | `DLPFC_generate_data.py:30-48` unannotated spots deleted from counts, positions and labels before graph construction and training | trains on annotated spots only |

The L1 effect compares the label-selected epoch with the *final* epoch under our label-free rule; the
authors never state a label-free alternative, so the size of the inflation depends on that choice.

## Reviewed and not leakage (false alarms of the scanner)
| Method (commit) | Candidate | Judgement |
|---|---|---|
| BANKSY (9278996) | `test_with_real_data.py:173` `assert ari > 0.0` | unit test, not selection |
| DeepST (e37997f) | `Benchmark/run_DLPFCs_SEDR.py:76` loop over Leiden resolutions; `:138` drops NA after clustering | resolution search targets the *given* K, annotation used only for evaluation afterwards |
| SEDR (ef48360), SpaGCN (dc7a1c2), DeepST benchmark scripts | `n_clusters = 5 if sample in [...] else 7` | K given per section (L2, convention of the DLPFC benchmark) |
| CCST (890de27) | `CCST_ST_utils.py:221` `n_clusters = max(cell_type_indeces)+1` | K from annotated types (L2) |
| SEDR | `Tutorial1_Clustering.ipynb` filters NA spots only to compute ARI | evaluation only |

## No candidate found by the scan (not a proof of absence)
GraphST (d62b0b7), STAGATE (ae1158c), SpaceFlow (58d1ab0), BASS (5c2690f), BayesSpace
(ba8b422): no label metric computed in the released code, so no selection by labels can occur there.

## Limits of this audit
1. Static scan + reading: leakage outside the repository (tuning done in the paper's development
   phase, e.g. hyper-parameters selected on DLPFC and then reported on DLPFC) is **L6** and must be
   collected from the papers; for example DeepST states that hyper-parameters were evaluated on DLPFC
   sections (to be confirmed from the article).
2. HiSTaR's official repository, conST's notebooks and NichePCA were not yet audited line by line.
3. Pending: authors' replies.
