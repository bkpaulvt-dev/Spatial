"""Assemble docs/NEWDATA_HANDOFF.md from the result files of the new-datasets extension (for the session that maintains the paper).

Everything numeric is read from files, nothing is typed in by hand; items that need a human decision are listed at the end.
    python scripts/newdata_handoff.py
"""
import collections, glob, json, os, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
R = lambda *p: os.path.join(ROOT, "results", *p)
rd = lambda f: open(f).read() if os.path.exists(f) else ""


def main():
    last = {}
    for f in sorted(glob.glob(R("newdata_runs_*.jsonl"))):
        for l in open(f):
            r = json.loads(l); last[r["id"]] = r
    by = collections.defaultdict(collections.Counter)
    for r in last.values():
        by[(r["dataset"], r.get("design", "full"))][r.get("outcome", r["status"])] += 1
    hosts = sorted({r.get("host", "?") for r in last.values()})
    try: commit = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    except Exception: commit = "unknown"
    o = ["# New-datasets extension: handoff", "",
         f"Branch `new-datasets`, commit `{commit}`. Written by `scripts/newdata_handoff.py` from the result files; the paper and all existing results are untouched.",
         "Rules and decisions: `docs/NEWDATA_COMMAND.md`, `docs/PREREGISTERED_SIM.md` (with Amendment 1), `docs/NEWDATA_REPORT.md` (deviations, skipped datasets with reasons).", "",
         "## Files produced", f"- Run records: `results/newdata_runs_<host>.jsonl` (host tag(s): {', '.join(hosts)}); {len(last)} jobs (newest record per id); per-job files in `results/newdata_runs/` (git-ignored, copy by hand).",
         "  Run times are NOT comparable with the paper's timing table (other host); accuracy and peak memory are reportable.", "",
         "| dataset | design | outcomes |", "|---|---|---|"]
    for (ds, dz), c in sorted(by.items()):
        o.append(f"| {ds} | {dz} | " + ", ".join(f"{k}: {v}" for k, v in sorted(c.items())) + " |")
    o += ["", "Other files: `results/newdata_sim_manifest.json` (45 tissues, checks, hashes), `results/newdata_allen_sections.json` (section-selection rule output), "
          "`results/newdata_sim_*.csv|json|md`, `results/newdata_g3_*.csv|json|md|jsonl`, `docs/figures/newdata_sim_examples.png`, `docs/figures/newdata_sim_ari.png`.", "",
          "## Simulation: primary analysis (pre-registered; headline from the FULL design only)", rd(R("newdata_sim_summary.md")) or "_not produced_", "",
          "## G3 re-tests (replicates / weakens / reverses)", rd(R("newdata_g3_summary.md")) or "_not produced_", "", "## Failures (every job that is not ok)"]
    bad = [r for r in last.values() if r["status"] != "ok"]
    if not bad: o.append("none")
    for r in sorted(bad, key=lambda r: r["id"]):
        o.append(f"- `{r['id']}`: {r.get('outcome', 'error')}; peak {r.get('resources', {}).get('peak_rss_gb', 0):.1f} GB; {str(r.get('error', ''))[:110]}")
    o += ["", "## Datasets that were not run, and dataset outcomes", rd(R("newdata_dataset_outcomes.txt")) or "(see `docs/NEWDATA_REPORT.md`)", "",
          "## To verify by the owner",
          "- Allen MERFISH licence/terms (no licence statement found); label provenance is CCF registration (reference_atlas); derived CSVs are not committed.",
          "- Simulation reference profiles come from DLPFC 151507 (public spatialLIBD; label class of the layers: expert, as in the registry).",
          "- Skipped datasets and why: HER2+ (Zenodo 3957257, CC-BY-4.0, files encrypted, passwords published in the authors' README were not used), prostate (Mendeley 10.17632/svw96g68dv, CC BY-NC; spot annotations by two uropathologists exist per the paper but are not confirmed in the deposit), osmFISH (region labels described only as 'inferred regions'; the paper's Methods could not be read from this server), BaristaSeq (SDMBench pages give no tissue or label provenance; SDMBench is Nature Methods 2024), Visium HD / Xenium (no domain labels).",
          "", "## Not done",
          "- The extended hierarchical bootstrap with the new real-data group next to the original 7-group result (G4) and the novelty check were not implemented.",
          "- Cells of the full simulation design that were not run are absent from the tables, not imputed."]
    open(os.path.join(ROOT, "docs", "NEWDATA_HANDOFF.md"), "w").write("\n".join(o) + "\n"); print("wrote docs/NEWDATA_HANDOFF.md")


if __name__ == "__main__":
    main()
