#!/usr/bin/env bash
# Install R packages when CRAN/Bioconductor are unreachable: try apt (r-cran-* / r-bioc-*),
# otherwise build from the official read-only CRAN mirror on GitHub (github.com/cran/<pkg>).
# Missing dependencies are resolved recursively. Usage: install_r_pkg.sh pkg [pkg ...]
SRC=${RSRC:-/home/user/Spatial/data/ext/rsrc}
mkdir -p "$SRC"
have() { Rscript -e "quit(status = !requireNamespace('$1', quietly = TRUE))" >/dev/null 2>&1; }
inst() {
  local p=$1 lc; lc=$(echo "$p" | tr 'A-Z.' 'a-z.')
  have "$p" && return 0
  for a in "r-cran-$lc" "r-bioc-$lc"; do
    if apt-cache show "$a" >/dev/null 2>&1; then apt-get install -y -q "$a" >/dev/null 2>&1 && have "$p" && { echo "apt   $p"; return 0; }; fi
  done
  [ -d "$SRC/$p" ] || timeout 300 git clone -q --depth 1 "https://github.com/cran/$p" "$SRC/$p" 2>/dev/null || { echo "FAIL  $p (no apt package, no CRAN mirror)"; return 1; }
  local deps; deps=$(awk '/^(Depends|Imports|LinkingTo):/{f=1} /^[A-Za-z@]+:/{if($1!~/^(Depends|Imports|LinkingTo):/)f=0} f' "$SRC/$p/DESCRIPTION" \
         | sed 's/^[A-Za-z]*://' | tr ',' '\n' | sed 's/(.*//; s/[[:space:]]//g' | grep -v '^$' | grep -vx 'R')
  for d in $deps; do have "$d" || inst "$d"; done
  R CMD INSTALL "$SRC/$p" >"$SRC/$p.install.log" 2>&1 && have "$p" && { echo "built $p"; return 0; }
  echo "FAIL  $p (build error, see $SRC/$p.install.log)"; return 1
}
for p in "$@"; do inst "$p"; done
