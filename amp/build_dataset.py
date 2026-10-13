"""Merge peptide tables from several sources into one training CSV for amp.train.

    python -m amp.build_dataset inspect apd3.csv                 # see columns / first rows
    python -m amp.build_dataset build --spec spec.json --out peptides.csv

spec.json -- one entry per source file; you map columns because export layouts differ by
database and version (we do not hard-code any):

{"sources": [
  {"name": "apd3",   "path": "apd3.csv", "seq_col": "Sequence", "labels": {"activity": 1}},
  {"name": "hemopi", "path": "hemopi.tsv", "sep": "\\t", "seq_col": "seq", "task": "hemolysis",
   "label_col": "label", "map": {"positive": 1, "negative": 0}},
  {"name": "dbaasp_hc50", "path": "hc50.csv", "seq_col": "SEQUENCE", "task": "hemolysis",
   "label_col": "HC50_uM", "threshold": {"op": "<=", "value": 100, "label": 1, "else": 0}},
  {"name": "tested_inactive", "path": "inactive.fasta", "labels": {"activity": 0}}
]}

Label rules per source: "labels" (constant for every row, e.g. positives-only lists), or "task" +
"label_col" with either "map" (cell text -> 0/1) or "threshold" (numeric cell; non-numeric such as
">100" is dropped, not guessed). FASTA files take "labels" only. Rows whose label can't be resolved
are dropped and counted. Duplicates are merged; conflicting 0/1 for a sequence+task become blank.
"""
import argparse
import json
import sys
from collections import Counter

import numpy as np
import pandas as pd

from .data import AA, TASKS

OPS = {"<=": np.less_equal, "<": np.less, ">=": np.greater_equal, ">": np.greater}


def read_fasta(path):
    seqs, cur = [], []
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            if cur:
                seqs.append("".join(cur)); cur = []
        elif line:
            cur.append(line)
    if cur:
        seqs.append("".join(cur))
    return pd.DataFrame({"sequence": seqs})


def read_source(spec):
    """Return long-format rows: sequence, task, label, source (+ drop counts in .attrs)."""
    path, name = spec["path"], spec["name"]
    if spec.get("format") == "fasta" or path.lower().endswith((".fa", ".fasta", ".faa")):
        df, seq_col = read_fasta(path), "sequence"
        if "labels" not in spec:
            raise ValueError(f"{name}: FASTA sources need constant 'labels'")
    else:
        sep = spec.get("sep") or ("\t" if path.lower().endswith((".tsv", ".txt")) else ",")
        df = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)
        seq_col = spec["seq_col"]
        if seq_col not in df:
            raise ValueError(f"{name}: column {seq_col!r} not in {list(df.columns)}")
    seqs = df[seq_col]
    unresolved = 0
    if "labels" in spec:
        rows = [(s, t, float(v)) for s in seqs for t, v in spec["labels"].items()]
    else:
        task, col = spec["task"], spec["label_col"]
        if col not in df:
            raise ValueError(f"{name}: column {col!r} not in {list(df.columns)}")
        rows = []
        for s, cell in zip(seqs, df[col]):
            if "map" in spec:
                v = spec["map"].get(str(cell).strip())
            else:
                th, x = spec["threshold"], pd.to_numeric(cell, errors="coerce")
                v = None if pd.isna(x) else (th["label"] if OPS[th["op"]](x, th["value"]) else th["else"])
            if v is None:
                unresolved += 1
            else:
                rows.append((s, task, float(v)))
    out = pd.DataFrame(rows, columns=["sequence", "task", "label"])
    out["source"] = name
    out.attrs["unresolved"] = unresolved
    return out


def clean(seqs, min_len, max_len):
    s = seqs.astype(str).str.strip().str.upper().str.replace("-", "", regex=False)
    ok_aa = s.map(lambda x: set(x) <= AA)
    ok_len = s.str.len().between(min_len, max_len)
    reason = np.where(~ok_aa, "non-standard/empty", np.where(~ok_len, "length", "ok"))
    return s, reason


def build(spec, min_len=5, max_len=100):
    parts, report = [], {}
    for src in spec["sources"]:
        d = read_source(src)
        d["sequence"], reason = clean(d["sequence"], min_len, max_len)
        report[src["name"]] = dict(rows=len(d), unresolved_labels=d.attrs["unresolved"],
                                   dropped=dict(Counter(r for r in reason if r != "ok")))
        parts.append(d[reason == "ok"])
    long = pd.concat(parts, ignore_index=True)
    g = long.groupby(["sequence", "task"])["label"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else np.nan)
    conflicts = int(g.isna().sum())
    wide = g.unstack("task").reindex(columns=TASKS).reset_index()
    wide["source"] = wide["sequence"].map(long.groupby("sequence")["source"].agg(lambda x: ";".join(sorted(set(x)))))
    summary = dict(sequences=len(wide), label_conflicts_set_to_unknown=conflicts, per_source=report,
                   labelled={t: int(wide[t].notna().sum()) for t in TASKS},
                   positives={t: int((wide[t] == 1).sum()) for t in TASKS})
    return wide, summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("inspect"); pi.add_argument("path"); pi.add_argument("--sep")
    pb = sub.add_parser("build"); pb.add_argument("--spec", required=True); pb.add_argument("--out", required=True)
    pb.add_argument("--min-len", type=int, default=5); pb.add_argument("--max-len", type=int, default=100)
    a = ap.parse_args(argv)
    if a.cmd == "inspect":
        sep = a.sep or ("\t" if a.path.lower().endswith((".tsv", ".txt")) else ",")
        df = pd.read_csv(a.path, sep=sep, dtype=str, keep_default_na=False, nrows=2000)
        print("columns:", list(df.columns))
        print(df.head(5).to_string())
        for c in df.columns:
            if df[c].nunique() <= 12:
                print(f"\n{c!r} values:", dict(df[c].value_counts()))
        return
    wide, summary = build(json.load(open(a.spec)), a.min_len, a.max_len)
    wide.to_csv(a.out, index=False)
    json.dump(summary, open(a.out + ".report.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
