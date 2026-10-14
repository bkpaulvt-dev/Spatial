#!/bin/sh
# Push the current paper to the Overleaf project over Git (credentials: the environment's saved Basic-auth secret
# for git.overleaf.com; nothing is stored here). Keeps the project's own template class (.cls/.bst), sets the NAR
# journal header and author block, and overwrites main.tex, refs.bib, paper_macros.tex, table_*.tex and figures/.
#   scripts/push_overleaf.sh [PROJECT_ID] ["commit message"]
set -e
cd "$(dirname "$0")/.."
PROJECT="${1:-6ac6b9475fb66a4d707766b3}"
MSG="${2:-Update from analysis repository}"
scripts/package_overleaf.sh >/dev/null
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
GIT_TERMINAL_PROMPT=0 git clone -q "https://git.overleaf.com/$PROJECT" "$W/p"
python3 - "$W/p/main.tex" <<'PY'
import sys
s = open("dist/overleaf_pkg/main.tex").read()
s = s.replace("\\graphicspath{{figures/}}", "\\graphicspath{{figures/}}\n\\newcommand{\\societylogo}{}\n\\providecommand{\\authormark}[1]{}", 1)
s = s.replace("\\journaltitle{Bioinformatics Advances}", "\\journaltitle{Nucleic Acids Research}")
s = s.replace("\\appnotes{Original Paper}", "\\appnotes{Methods Online}")
s = s.replace("\\author[1,$\\ast$]{\\todo{First Author}}\n\\author[1]{\\todo{Second Author}}\n\\authormark{\\todo{Author} et al.}", "\\author[1,$\\ast$]{Bikash Kumar Paul}\n\\authormark{Paul}")
s = s.replace("\\address[1]{\\orgdiv{\\todo{Department}}, \\orgname{\\todo{University}}, \\orgaddress{\\country{\\todo{Country}}}}", "\\address[1]{\\orgdiv{\\todo{Department}}, \\orgname{Virginia Tech}, \\orgaddress{\\state{VA}, \\country{USA}}}")
s = s.replace("\\corresp[$\\ast$]{Corresponding author. \\href{mailto:email@example.org}{\\todo{email}}}", "\\corresp[$\\ast$]{Corresponding author. \\href{mailto:bikashkumar@vt.edu}{bikashkumar@vt.edu}}")
open(sys.argv[1], "w").write(s)
PY
cp dist/overleaf_pkg/refs.bib dist/overleaf_pkg/paper_macros.tex dist/overleaf_pkg/table_*.tex "$W/p/"
mkdir -p "$W/p/figures"; cp dist/overleaf_pkg/figures/* "$W/p/figures/"
cd "$W/p"
git add -A
if git diff --cached --quiet; then echo "Overleaf already up to date."; exit 0; fi
git -c user.name="${GIT_AUTHOR_NAME:-Claude Code}" -c user.email="${GIT_AUTHOR_EMAIL:-noreply@anthropic.com}" commit -q -m "$MSG"
git push -q origin HEAD
echo "Pushed to Overleaf project $PROJECT."
