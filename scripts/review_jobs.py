"""Job lists for the review stages: one 'dataset:section:method:seed' per line.
  python scripts/review_jobs.py --methods cellcharter mender [--groups original newreal] [--datasets ds ...] [--seeds 0 1 2]
original = the 24 sections of configs/datasets.yaml; newreal = real (not simulated) datasets of configs/datasets_newdata.yaml whose data files exist now."""
import argparse, os, sys
import yaml
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def sections(group, only=None):
    out = []
    if group == "original":
        reg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets.yaml")))["datasets"]
        out = [(ds, str(s)) for ds, c in reg.items() for s in c["sections"]]
    elif group == "newreal":
        reg = yaml.safe_load(open(os.path.join(ROOT, "configs", "datasets_newdata.yaml")))["datasets"]
        for ds, c in reg.items():
            if ds.startswith("sim_"):
                continue
            for s in c["sections"]:
                if os.path.exists(os.path.join(ROOT, "data", "ext", "csv", f"{ds}_{s}_counts.csv")):
                    out.append((ds, str(s)))
    return [x for x in out if not only or x[0] in only]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--methods", nargs="+", required=True); ap.add_argument("--groups", nargs="+", default=["original", "newreal"])
    ap.add_argument("--datasets", nargs="+"); ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    a = ap.parse_args()
    for g in a.groups:
        for ds, sec in sections(g, a.datasets):
            for m in a.methods:
                for s in a.seeds:
                    print(f"{ds}:{sec}:{m}:{s}")
