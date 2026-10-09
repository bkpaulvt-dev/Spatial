"""Quality control of every registered section -> results/qc/section_qc.csv and docs/QC_REPORT.md.

python scripts/run_qc.py [dataset ...]
"""
import os, sys, warnings
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")
from spatialbench.data import load_registry, load_section, sections  # noqa: E402
from spatialbench.qc import section_qc, FLAG_RULES  # noqa: E402

want = set(sys.argv[1:])
reg = load_registry()
rows = []
for ds, sec, split in sections(reg):
    if want and ds not in want:
        continue
    a = load_section(ds, sec)
    r = section_qc(a, f"{ds}/{sec}")
    r.update(dataset=ds, section_id=sec, split=split, technology=reg["datasets"][ds]["technology"],
             label_class=reg["datasets"][ds]["label_provenance"]["class"])
    rows.append(r)
    print(f"{ds}/{sec:<24} n={r['n_obs']:>5} annotated={r['annotated_fraction']:.2f} K={r['n_domains']} "
          f"expr_purity={r['expression_knn_purity']:.2f} spatial={r['truth_edge_homophily']:.2f} flags={r['flags'] or '-'}", flush=True)
df = pd.DataFrame(rows)
os.makedirs(os.path.join(ROOT, "results", "qc"), exist_ok=True)
df.to_csv(os.path.join(ROOT, "results", "qc", "section_qc.csv"), index=False)
print("written", len(df), "sections")
