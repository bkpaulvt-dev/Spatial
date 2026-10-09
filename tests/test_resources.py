import sys, numpy as np, pytest
from spatialbench import resources as R


def test_measure_memory_time_and_children():
    code = "import numpy as np, time; a = np.ones(60_000_000); time.sleep(0.8); print('ok')"   # ~480 MB
    r = R.measure_command([sys.executable, "-c", code])
    assert r["exit_code"] == 0 and "ok" in r["stdout"]
    assert r["peak_rss_gb"] > 0.4 and r["wall_s"] >= 0.8
    # a child process' memory is included
    code2 = ("import subprocess, sys; subprocess.run([sys.executable, '-c', "
             "'import numpy as np, time; a = np.ones(60_000_000); time.sleep(0.8)'])")
    r2 = R.measure_command([sys.executable, "-c", code2])
    assert r2["peak_rss_gb"] > 0.4


def test_failure_modes_are_reported_not_raised():
    r = R.measure_command([sys.executable, "-c", "import sys; sys.exit(3)"])
    assert r["exit_code"] == 3 and not r["oom_killed"]
    r = R.measure_command([sys.executable, "-c", "import time; time.sleep(30)"], timeout=1)
    assert r["timed_out"]
    assert r["energy_kwh"] >= 0 and "estimate" in r["energy_source"] or "RAPL" in r["energy_source"]


def test_scaling_exponent_and_cost():
    b, a = R.scaling_exponent([1e3, 1e4, 1e5], [2, 20, 200])
    assert b == pytest.approx(1.0, abs=1e-6)
    b2, _ = R.scaling_exponent([1e3, 1e4, 1e5], [1, 100, 10000])
    assert b2 == pytest.approx(2.0, abs=1e-6)
    assert R.cloud_cost(3600, 2.5) == pytest.approx(2.5)
