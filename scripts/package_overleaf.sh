#!/bin/sh
# Build dist/overleaf_manuscript.zip (main.tex at the top level) from paper/ + results/ + docs/figures/.
set -e
cd "$(dirname "$0")/.."
D=dist/overleaf_pkg; rm -rf "$D"; mkdir -p "$D/figures"
sed -e 's#\\graphicspath{{../docs/figures/}}#\\graphicspath{{figures/}}#' \
    -e 's#\\input{../results/#\\input{#' paper/main.tex > "$D/main.tex"
cp paper/refs.bib results/table_main.tex results/table_resources.tex results/paper_macros.tex "$D/"
for f in $(grep -o '{[A-Za-z0-9_]*\.\(png\|pdf\)}' paper/main.tex | tr -d '{}' | sort -u); do cp "docs/figures/$f" "$D/figures/"; done
CLS=$(kpsewhich oup-authoring-template.cls); cp "$CLS" "$D/"
rm -f dist/overleaf_manuscript.zip; (cd "$D" && zip -qr ../overleaf_manuscript.zip .)
# compile test of the package itself
(cd "$D" && pdflatex -interaction=nonstopmode main >/dev/null 2>&1 && bibtex main >/dev/null 2>&1 && pdflatex -interaction=nonstopmode main >/dev/null 2>&1 && pdflatex -interaction=nonstopmode main >/dev/null 2>&1)
grep -c "Undefined" "$D/main.log" || true
unzip -l dist/overleaf_manuscript.zip | tail -n 1
