#!/bin/sh
# Push the current paper to the Overleaf project over Git, so Overleaf always shows the latest version.
# Credentials come from the environment's saved Basic-auth secret for git.overleaf.com (nothing is stored here).
#   scripts/push_overleaf.sh [PROJECT_ID] ["commit message"]
# Default project: the VT Overleaf project "Bioinformatics Advances".
set -e
cd "$(dirname "$0")/.."
PROJECT="${1:-6ac6b9475fb66a4d707766b3}"
MSG="${2:-Update from analysis repository}"
scripts/package_overleaf.sh >/dev/null                      # builds dist/overleaf_pkg with Overleaf-ready paths
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
GIT_TERMINAL_PROMPT=0 git clone -q "https://git.overleaf.com/$PROJECT" "$W/p"
# copy only the files the paper needs; Overleaf keeps its own history, so nothing else is touched
cp dist/overleaf_pkg/main.tex dist/overleaf_pkg/refs.bib dist/overleaf_pkg/paper_macros.tex \
   dist/overleaf_pkg/table_*.tex dist/overleaf_pkg/oup-authoring-template.cls "$W/p/"
mkdir -p "$W/p/figures"; cp dist/overleaf_pkg/figures/* "$W/p/figures/"
cd "$W/p"
git add -A
if git diff --cached --quiet; then echo "Overleaf already up to date."; exit 0; fi
git -c user.name="${GIT_AUTHOR_NAME:-Claude Code}" -c user.email="${GIT_AUTHOR_EMAIL:-noreply@anthropic.com}" commit -q -m "$MSG"
git push -q origin HEAD:master 2>&1 || git push -q origin HEAD 2>&1
echo "Pushed to Overleaf project $PROJECT."
