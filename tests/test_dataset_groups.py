"""Registering the new datasets must not change what the five existing datasets resolve to.

tests/fixtures/dataset_config_before.json was recorded with scripts/newdata_config_snapshot.py on the tree BEFORE the
new-datasets edits (spatialbench/data.py, scripts/run_r_method.R). The resolved configuration is: platform groups, loader branch,
BASS branch, GraphST datatype (what actually selects preprocessing and method settings by dataset name).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from newdata_config_snapshot import EXISTING, resolve  # noqa: E402


def test_existing_datasets_resolve_exactly_as_before():
    before = json.load(open(os.path.join(HERE, "fixtures", "dataset_config_before.json")))
    assert sorted(before) == sorted(EXISTING)
    assert resolve(EXISTING) == before


def test_simulated_datasets_take_the_whole_transcriptome_path_but_not_the_visium_one():
    for ds in ("sim_bands", "sim_blocks"):
        c = resolve([ds])[ds]
        assert c["whole_transcriptome_group"] and not c["visium_group"]     # same preprocessing as DLPFC/Stereo-seq; BayesSpace not run
        assert c["bass_branch"] == "whole_transcriptome(DLPFC settings)" and c["loader"] == "sim"
