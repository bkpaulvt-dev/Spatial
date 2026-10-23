#!/bin/sh
# Copy the figures under the numbers printed in the manuscript (NAR upload) -> paper/submission/
cd "$(dirname "$0")/.."
mkdir -p paper/submission
F=docs/figures
cp $F/nar_fig1_pipeline_v2.pdf paper/submission/Figure1.pdf
cp $F/nar_fig2_accuracy.pdf    paper/submission/Figure2.pdf
cp $F/nar_fig5_maps.pdf        paper/submission/Figure3.pdf
cp $F/nar_fig3_robustness.pdf  paper/submission/Figure4.pdf
cp $F/nar_fig4_protocol.pdf    paper/submission/Figure5.pdf
for f in nar_graphical_abstract.pdf nar_graphical_abstract.tif; do [ -f $F/$f ] && cp $F/$f paper/submission/; done
cp paper/main.pdf paper/submission/manuscript.pdf; cp paper/supplementary.pdf paper/submission/supplementary_data.pdf
cp paper/figure_alt_text.md paper/cover_letter.md paper/submission/
ls paper/submission
