"""Resolve, for a dataset name, every place where the name selects preprocessing or method settings.

The benchmark selects settings by dataset NAME (platform groups in spatialbench/data.py, the whole-transcriptome list of
scripts/run_r_method.R, the loader branch, the GraphST datatype). This prints / compares that resolved configuration so that
registering new datasets can be shown not to change what the existing ones resolve to.

    python scripts/newdata_config_snapshot.py --write tests/fixtures/dataset_config_before.json   # record (on the unedited tree)
    python scripts/newdata_config_snapshot.py --show sim_bands osmfish                           # resolve any names now
Used by tests/test_dataset_groups.py.
"""
import argparse, ast, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EXISTING = ["dlpfc", "starmap", "merfish", "brca", "stereo"]


def _loader_branches(src: str) -> list[str]:
    """Names with their own `if ds == "<name>":` branch in load_section (all others use the CSV fallback)."""
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "load_section")
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) and n.test.left.id == "ds":
            out += [c.value for c in n.test.comparators if isinstance(c, ast.Constant)]
    return out


def resolve(names, root=ROOT):
    sys.path.insert(0, root)
    import importlib
    import spatialbench.data as D
    importlib.reload(D)
    r_src = open(os.path.join(root, "scripts", "run_r_method.R")).read()
    r_whole = re.search(r'ds %in% c\(([^)]*)\)', r_src).group(1)
    r_whole = [s.strip().strip('"') for s in r_whole.split(",")]
    a_src = open(os.path.join(root, "scripts", "adapters.py")).read()
    stereo_dt = re.search(r'datatype="([^"]+)" if ds == "([^"]+)" else "([^"]+)"', a_src).groups()
    loaders = _loader_branches(open(os.path.join(root, "spatialbench", "data.py")).read())
    out = {}
    for ds in names:
        out[ds] = {
            "visium_group": ds in D.VISIUM,                      # BayesSpace allowed; SpaGCN axis order; STAGATE radius rule
            "whole_transcriptome_group": ds in D.WHOLE_TRANSCRIPTOME,   # filter 50 spots / 10 counts, 2000 HVG; STAGATE/SEDR settings; SpaceFlow lam 0.3
            "bass_branch": "whole_transcriptome(DLPFC settings)" if ds in r_whole else ("targeted(C=15)" if ds == "starmap" else "targeted(C=20)"),
            "loader": ds if ds in loaders else ("sim" if ds in getattr(D, "SIM", set()) else "csv_fallback"),
            "graphst_datatype": stereo_dt[0] if ds == stereo_dt[1] else stereo_dt[2],
        }
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write"); ap.add_argument("--show", nargs="*")
    a = ap.parse_args()
    if a.write:
        os.makedirs(os.path.dirname(a.write), exist_ok=True)
        json.dump(resolve(EXISTING), open(a.write, "w"), indent=1, sort_keys=True)
        print("wrote", a.write)
    for k, v in resolve(a.show or []).items():
        print(k, json.dumps(v))
