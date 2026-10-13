"""Rule-based toy data for smoke tests ONLY (cationic + amphipathic => 'active').
Never report metrics from this; it exists to exercise the pipeline."""
import numpy as np
import pandas as pd

AA = list("ACDEFGHIKLMNPQRSTVWY")


def make(n=600, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        L = int(rng.integers(8, 40))
        p = np.ones(20)
        if rng.random() < 0.5:  # bias toward K/R/L/W/F
            for a in "KRLWF":
                p[AA.index(a)] = 4
        p /= p.sum()
        s = "".join(rng.choice(AA, size=L, p=p))
        charge = s.count("K") + s.count("R") - s.count("D") - s.count("E")
        hyd = sum(s.count(a) for a in "LWFIV") / L
        act = float(charge >= 2 and hyd > 0.2)
        rows.append(dict(sequence=s, activity=act,
                         toxicity=float(hyd > 0.35) if rng.random() < 0.7 else np.nan,
                         hemolysis=float(hyd > 0.3 and charge > 3) if rng.random() < 0.5 else np.nan))
    return pd.DataFrame(rows)
