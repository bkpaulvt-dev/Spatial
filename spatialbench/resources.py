"""Runtime, peak-memory and energy measurement for any command (plan section 11).

``measure_command`` runs a command in a subprocess and samples the whole process tree (so R
subprocesses started by Python wrappers are included). Reported per run:

wall_s            elapsed wall-clock seconds
cpu_s             CPU seconds (user+system) of the process tree
peak_rss_gb       peak resident memory of the whole tree (sum over processes, sampled)
peak_gpu_mem_gb   peak GPU memory (nvidia-smi), NaN if no GPU
energy_kwh        energy; measured from Intel RAPL when readable, else ESTIMATED from CPU seconds
                  (``cpu_watts_per_core`` x cpu_s) and GPU power; ``energy_source`` says which
oom_killed        True if the process was killed by the kernel (exit code -9)
exit_code, timed_out

The energy estimate is a coarse model (default 10 W per busy core), reported as such; it is only
suitable for comparing methods run on the same machine.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time

import psutil

RAPL = "/sys/class/powercap/intel-rapl:0/energy_uj"


def _gpu_sample():
    if shutil.which("nvidia-smi") is None:
        return float("nan"), float("nan")
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,power.draw", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout.strip().splitlines()
        mem = sum(float(l.split(",")[0]) for l in out) / 1024
        pw = sum(float(l.split(",")[1]) for l in out)
        return mem, pw
    except Exception:
        return float("nan"), float("nan")


def _tree(p: psutil.Process):
    try:
        return [p] + p.children(recursive=True)
    except psutil.Error:
        return []


def measure_command(cmd, timeout: float | None = None, interval: float = 0.25, cpu_watts_per_core: float = 10.0,
                    env=None, cwd=None, capture: bool = True) -> dict:
    """Run ``cmd`` (list) and return a resource record plus ``stdout`` / ``stderr`` tails."""
    rapl0 = None
    if os.access(RAPL, os.R_OK):
        try:
            rapl0 = int(open(RAPL).read())
        except Exception:
            rapl0 = None
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None,
                            text=True, env=env, cwd=cwd)
    ps = psutil.Process(proc.pid)
    stats = {"peak_rss": 0, "cpu": {}, "gpu_mem": float("nan"), "gpu_wh": 0.0}
    stop = threading.Event()

    def sampler():
        last = time.time()
        while not stop.is_set():
            rss = 0
            for q in _tree(ps):
                try:
                    rss += q.memory_info().rss
                    ct = q.cpu_times()
                    stats["cpu"][q.pid] = ct.user + ct.system
                except psutil.Error:
                    pass
            stats["peak_rss"] = max(stats["peak_rss"], rss)
            gm, gp = _gpu_sample()
            if gm == gm:
                stats["gpu_mem"] = gm if stats["gpu_mem"] != stats["gpu_mem"] else max(stats["gpu_mem"], gm)
                now = time.time()
                stats["gpu_wh"] += gp * (now - last) / 3600
            last = time.time()
            stop.wait(interval)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        for q in _tree(ps)[::-1]:
            try:
                q.kill()
            except psutil.Error:
                pass
        out, err = proc.communicate()
    stop.set()
    th.join(timeout=2)
    wall = time.time() - t0
    cpu_s = float(sum(stats["cpu"].values()))
    energy, src = None, "estimate"
    if rapl0 is not None:
        try:
            d = int(open(RAPL).read()) - rapl0
            if d > 0:
                energy, src = d / 1e6 / 3600 / 1000, "RAPL (package, whole machine)"
        except Exception:
            pass
    if energy is None:
        energy = cpu_s * cpu_watts_per_core / 3600 / 1000 + stats["gpu_wh"] / 1000
        src = f"estimate ({cpu_watts_per_core:g} W per busy core" + (" + GPU power)" if stats["gpu_wh"] else ")")
    return {"wall_s": wall, "cpu_s": cpu_s, "peak_rss_gb": stats["peak_rss"] / 2 ** 30, "peak_gpu_mem_gb": stats["gpu_mem"],
            "energy_kwh": energy, "energy_source": src, "exit_code": proc.returncode,
            "oom_killed": proc.returncode == -9, "timed_out": timed_out,
            "stdout": (out or "")[-2000:], "stderr": (err or "")[-2000:]}


def cloud_cost(wall_s: float, hourly_usd: float) -> float:
    """Cost of a run at a given hourly price of the machine (e.g. a GPU instance)."""
    return wall_s / 3600 * hourly_usd


def scaling_exponent(sizes, times):
    """Fit time ~ a * n^b on log-log axes; returns (b, a). Needs >= 3 sizes."""
    import numpy as np
    x, y = np.log(np.asarray(sizes, float)), np.log(np.asarray(times, float))
    b, loga = np.polyfit(x, y, 1)
    return float(b), float(np.exp(loga))


if __name__ == "__main__":
    import json, sys
    print(json.dumps({k: v for k, v in measure_command(sys.argv[1:]).items() if k not in ("stdout", "stderr")}, indent=1))
