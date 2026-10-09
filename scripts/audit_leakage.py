"""Static scan of method repositories for patterns that can indicate evaluation leakage.

This is a *screening* tool: it lists candidate lines (file:line) per category so that a human can
review them; every finding in the paper must be confirmed by reading the code (see
docs/LEAKAGE_AUDIT.md for the reviewed, classified results).

Categories
  L1  label-based selection   a metric against the ground truth is computed together with a
                              max / best / argmax / threshold (epoch, seed, resolution or run chosen by labels)
  L2  K from labels           number of clusters taken from the annotation
  L3  drop unannotated spots  spots without annotation removed before training
  L4  per-section settings    hyper-parameters keyed by (or branching on) benchmark section ids
  L5  tuning loops            a loop over seeds/epochs/resolutions in the same file as a label metric

python scripts/audit_leakage.py [repo_dir ...]     (default: every repository under data/ext/methods)
-> results/leakage_scan/<repo>.md and results/leakage_scan/summary.csv
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
METHODS = os.path.join(ROOT, "data", "ext", "methods")
OUT = os.path.join(ROOT, "results", "leakage_scan")
EXT = (".py", ".R", ".Rmd", ".ipynb", ".r")
SKIP_DIRS = {".git", "__pycache__", "node_modules", "Figure", "figures", "imgs", "data", "Results", "dataset", "generated_data"}

METRIC = re.compile(r"adjusted_rand_score|adjustedRandIndex|\bARI\b|\bari\b|ari_res|ari_max|best_ari|normalized_mutual_info|\bNMI\b|\bnmi\b|metrics\.\w*(score|index)", re.I)
SELECT = re.compile(r"\bmax\b|\bbest\b|argmax|ari_max|best_|>\s*(ari|nmi|best|max)|(ari|nmi)\w*\s*>", re.I)
LOOP = re.compile(r"for\s+\w*(seed|epoch|res|resolution|iter|run)\w*\s+in|while\s", re.I)
KFROM = re.compile(r"(n_clusters|class_num|num_cluster|n_domains|\bk\b|\bR\b)\s*=\s*.*(len\(|nunique|unique\(|max\(.*(label|ground|layer|type))", re.I)
DROPNA = re.compile(r"isnull\(\)|isna\(\)|dropna|NA_labels|np\.delete\(.*(NA|nan|null)|is\.na\(|~.*isnull|notnull", re.I)
SECT = re.compile(r"\b(1515\d\d|15166\d|15167\d)\b")
SECT_BRANCH = re.compile(r"(if|elif|==|in \[|\{).*\b(1515\d\d|15166\d|15167\d)\b|\b(1515\d\d|15166\d|15167\d)\b\s*[:=]\s*[\d\[\(\{]")


def source_lines(path):
    if path.endswith(".ipynb"):
        import json
        try:
            nb = json.load(open(path, encoding="utf-8"))
        except Exception:
            return []
        out = []
        for ci, c in enumerate(nb.get("cells", [])):
            if c.get("cell_type") == "code":
                for li, l in enumerate("".join(c["source"]).splitlines()):
                    out.append((f"cell{ci}:{li + 1}", l))
        return out
    try:
        return [(str(i + 1), l.rstrip("\n")) for i, l in enumerate(open(path, encoding="utf-8", errors="ignore"))]
    except Exception:
        return []


def scan_repo(repo):
    hits = []
    for dp, dn, fn in os.walk(repo):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if not f.endswith(EXT):
                continue
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, repo)
            lines = source_lines(path)
            has_metric = any(METRIC.search(l) for _, l in lines)
            for i, (loc, l) in enumerate(lines):
                s = l.strip()
                if not s or s.startswith(("#", "//")):
                    continue
                ctx = " ".join(x for _, x in lines[max(0, i - 3): i + 4])
                if METRIC.search(l) and (SELECT.search(l) or SELECT.search(ctx)):
                    hits.append(("L1", rel, loc, s))
                if KFROM.search(l):
                    hits.append(("L2", rel, loc, s))
                if DROPNA.search(l):
                    hits.append(("L3", rel, loc, s))
                if SECT_BRANCH.search(l) and not re.search(r"read|path|load|\.h5|\.tsv|\.csv|sample_name\s*=|name\s*=|print|title", l):
                    hits.append(("L4", rel, loc, s))
                if has_metric and LOOP.search(l):
                    hits.append(("L5", rel, loc, s))
    return hits


def main():
    repos = sys.argv[1:] or sorted(os.path.join(METHODS, d) for d in os.listdir(METHODS) if os.path.isdir(os.path.join(METHODS, d, ".git")))
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for repo in repos:
        name = os.path.basename(repo.rstrip("/"))
        hits = scan_repo(repo)
        counts = {c: sum(1 for h in hits if h[0] == c) for c in ("L1", "L2", "L3", "L4", "L5")}
        rows.append({"repo": name, **counts})
        with open(os.path.join(OUT, f"{name}.md"), "w") as f:
            f.write(f"# Candidate leakage lines: {name}\n\nScreening output; unreviewed. {counts}\n\n")
            for cat in ("L1", "L2", "L3", "L4", "L5"):
                sel = [h for h in hits if h[0] == cat]
                if sel:
                    f.write(f"## {cat} ({len(sel)})\n")
                    for _, rel, loc, s in sel[:60]:
                        f.write(f"- `{rel}:{loc}` `{s[:160]}`\n")
                    f.write("\n")
        print(f"{name:<14}", counts)
    with open(os.path.join(OUT, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["repo", "L1", "L2", "L3", "L4", "L5"])
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
