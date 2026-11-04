"""Small helpers around the training pipeline.

    python -m amp.tools fasta peptides.csv peptides.fasta
    python -m amp.tools add-clusters peptides.csv clusters.tsv peptides_clustered.csv   # MMseqs2 *_cluster.tsv
    python -m amp.tools aggregate runs/*/metrics.json                                  # mean +- sd over seeds
"""
import argparse
import json

import numpy as np
import pandas as pd

from .data import TASKS


def write_fasta(csv, out):
    df = pd.read_csv(csv)
    with open(out, "w") as f:
        for i, s in enumerate(df["sequence"].astype(str).str.upper()):
            f.write(f">{s}\n{s}\n")  # header == sequence so cluster files map back unambiguously
    return len(df)


def add_clusters(csv, tsv, out):
    """MMseqs2 cluster TSV: representative<TAB>member (ids are the sequences themselves)."""
    df = pd.read_csv(csv)
    df["sequence"] = df["sequence"].astype(str).str.upper()
    pairs = pd.read_csv(tsv, sep="\t", header=None, names=["rep", "member"], dtype=str)
    rep_of = dict(zip(pairs.member, pairs.rep))
    missing = set(df.sequence) - set(rep_of)
    if missing:
        raise ValueError(f"{len(missing)} sequences absent from the cluster file, e.g. {sorted(missing)[:3]}")
    df["cluster"] = df.sequence.map(rep_of)
    df.to_csv(out, index=False)
    return df.cluster.nunique()


def aggregate(paths):
    runs = [json.load(open(p)) for p in paths]
    rows = []
    for key, label in (("logreg_test", "logreg"), ("esm_test", "ESM-2")):
        for t in TASKS:
            for m in ("auroc", "auprc", "mcc"):
                v = [r[key][t][m] for r in runs if r[key][t][m] is not None]
                if v:
                    rows.append(dict(model=label, task=t, metric=m, mean=np.mean(v), sd=np.std(v, ddof=1) if len(v) > 1 else np.nan, n_seeds=len(v)))
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("fasta"); a.add_argument("csv"); a.add_argument("out")
    b = sub.add_parser("add-clusters"); b.add_argument("csv"); b.add_argument("tsv"); b.add_argument("out")
    c = sub.add_parser("aggregate"); c.add_argument("metrics", nargs="+")
    args = ap.parse_args(argv)
    if args.cmd == "fasta":
        print(write_fasta(args.csv, args.out), "sequences written")
    elif args.cmd == "add-clusters":
        print(add_clusters(args.csv, args.tsv, args.out), "clusters")
    else:
        print(aggregate(args.metrics).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
