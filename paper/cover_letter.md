[Date]

Editor-in-Chief
*Bioinformatics Advances*

Dear Editor,

We submit our manuscript **"The clustering lottery: initialisation and input-order sensitivity of
mixture-model clustering confounds benchmarks of spatial domain identification"** for
consideration as an Original Paper in *Bioinformatics Advances*.

New methods for spatial domain identification are typically ranked by differences of a few
hundredths in adjusted Rand index, mostly on the same twelve DLPFC Visium sections. Nearly all of
them produce domains by fitting a Gaussian mixture model (usually R mclust) once to a learned
embedding. Our study measures directly how much this final step contributes to reported results.
We use 20 annotated sections from three technologies (10x Visium, STARmap and MERFISH), and five
methods plus training-free baselines.

Our main findings are:

1. With its official code, a recently published hierarchical graph VAE (HiSTaR) reached a median
   ARI of 0.51 on DLPFC rather than the reported 0.65.
2. On a fixed embedding, refitting the same mixture model from different random starts changed ARI
   by 0.21 on average and by up to 0.54. R mclust is deterministic, but merely permuting the order
   of the spots changed its result by up to 0.29.
3. Selecting fits by likelihood is not a remedy: likelihood and ARI were even negatively correlated
   on MERFISH.
4. Under matched clustering, neither graph deep-learning method outperformed a training-free graph
   diffusion baseline on any dataset.

These results complement recent large benchmarks, which concluded that clustering choices can
outweigh architectural novelty. Our contribution is a direct, quantitative and fully reproducible
measurement of clustering variance on fixed embeddings, together with concrete reporting
recommendations for method developers and reviewers. We believe this fits the journal's emphasis on
technically sound, reproducible computational work of broad use to the community.

All code, per-run results and figures are openly available [URL / DOI]. The manuscript is not under
consideration elsewhere, and all authors have approved the submission. [Disclose AI assistance as
required by the journal.]

Suggested reviewers: [names, affiliations, e-mails; no conflicts of interest]

Sincerely,
[Corresponding author, affiliation, e-mail]
