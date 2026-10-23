# Alternative text for the figures (paste into the NAR submission system)

**Graphical abstract.** Schematic of the benchmark: spatial transcriptomics sections from four technologies are embedded by 16 methods, every embedding is clustered with the same Gaussian mixture, and accuracy and the variance of the clustering step are compared; a neighbourhood-smoothing baseline is among the most accurate methods on brain tissue but not on breast cancer or mouse embryo.

**Figure 1.** Study design in five panels: example tissue sections from 10x Visium, STARmap and MERFISH coloured by expert annotation; the spot-by-gene input and spatial graph; the 16 methods grouped into three families; the two clustering protocols with a strip showing how the ARI of one fixed embedding varies over 20 random starts; and the metrics and hierarchical bootstrap used for evaluation.

**Figure 2.** Three-panel accuracy summary with matched clustering. A heat map of mean ARI for 17 methods across five datasets (DLPFC, STARmap, MERFISH, breast cancer, Stereo-seq); a forest plot of the ARI difference between linear diffusion and each method with 95% bootstrap intervals, eight of which lie above zero; and bootstrap rank intervals, where BASS and linear diffusion most often rank first.

**Figure 3.** Ten maps of DLPFC section 151673: the expert layer annotation and the domains found by nine methods, each titled with its ARI, showing that most methods recover the laminar layers with varying boundary accuracy.

**Figure 4.** Three panels on the variance of the clustering step for 14 methods. Dot plots of the ARI range over 20 single-start Gaussian-mixture fits per fixed embedding (mean about 0.17, up to 0.60); dot plots of the ARI range of R mclust over ten random seeds; and a heat map of the median correlation between log-likelihood and ARI per dataset, positive on DLPFC and STARmap and near zero or negative elsewhere.

**Figure 5.** Five dumbbell plots, one per dataset, comparing each method's mean ARI with its default clustering (open circle) and with matched clustering (filled circle); the protocol changes some methods by more than 0.1 ARI in either direction.
