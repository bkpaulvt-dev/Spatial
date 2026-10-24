Dear Editor,

Please consider our manuscript "Benchmarking the accuracy, robustness and reproducibility of spatial domain identification methods" for publication in Nucleic Acids Research as a Computational Biology article.

Identifying spatial domains is one of the first analyses of spatial transcriptomics data, and new methods are usually judged by improvements of a few hundredths in adjusted Rand index (ARI), mostly on one tissue and from a single run. We benchmarked 13 published methods and three training-free baselines on 24 annotated sections of human brain, human breast cancer and mouse embryo from four technologies (10x Visium, STARmap, MERFISH and Stereo-seq). Unlike previous benchmarks, we separated each learned embedding from its clustering step and measured the variance of that step directly.

Our main findings are:

1. When every embedding is clustered in the same way, a standard neighbourhood-smoothing baseline that needs no training has a higher mean ARI than half of the comparators and cannot be separated from the rest; it and BASS are the methods most likely to rank first. Its lead comes from brain tissue; on breast cancer and embryo sections most methods are slightly ahead of it and close to each other, so method rankings are tissue-dependent.
2. The clustering step is a larger source of variation than most differences between methods. On a fixed embedding, refitting the same Gaussian mixture from different random starts changes ARI by 0.16 on average and by up to 0.60. The default fit of R mclust, used by several widely used methods, depends on a fixed but arbitrary random seed through its subsampled initialisation.
3. Choosing the most likely of many fits helps on cortex but not on MERFISH, breast cancer or embryo data, where likelihood and ARI are unrelated.
4. HiSTaR's published DLPFC accuracy (median ARI 0.65) was not reproduced with its official code (0.51), and the released code of one method selects its reported epoch using the labels, which inflates its ARI by 0.15.

From these results we derive seven concrete reporting recommendations for method developers and benchmark authors.

All analyses are reproducible from scripts that generate every number, table and figure in the manuscript. Code, per-run results and download scripts with checksums are available at [GitHub URL] and archived at Zenodo [DOI]. The comparisons use a hierarchical bootstrap over donors and datasets. We state openly that the reference baseline was chosen after the means were seen, and that we developed one of the baselines (AnisoST).

Use of AI tools: code, experiments and a first draft of the manuscript were produced with the assistance of an AI coding assistant (Claude, Anthropic). All results were checked by the authors, who take full responsibility for the content. This is also stated in the Acknowledgements.

The manuscript has not been published and is not under consideration elsewhere. [A preprint is / is not posted at bioRxiv.] All authors approved the submission.

Suggested reviewers are listed in the submission form.

Sincerely,
Bikash Kumar Paul
Virginia Tech
bikashkumar@vt.edu
