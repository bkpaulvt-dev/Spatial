"""Diagnostic: does CIPHER's efficacy model converge with more training? Tracks, every 10 epochs,
the per-cell escape AUROC, learned-vs-true effect slope (direct term D vs beta) and efficacy error."""
import sys, os, json
import numpy as np, torch
from sklearn.metrics import roc_auc_score
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from sim_escape import simulate
from cipher.model import CIPHER

d, rho, on, truth, beta = simulate(0)
K = len(d.targets)
has = d.P >= 0
out = []
for init in ["zero"]:
    m = CIPHER(d, seed=0, epochs=10, verbose=False, basal=False, adversary=False, direct=True, lr=0.01)
    for block in range(12):
        m.fit()  # each call trains 10 more epochs (fresh Adam state)
        D = m.net.D.detach().numpy()
        sl = [np.polyfit(beta[k][beta[k] != 0], D[k][beta[k] != 0], 1)[0] for k in range(K)]
        eff = torch.sigmoid(m.net.eff_logit).detach().numpy()
        pp = m.escape_posterior(np.arange(len(d.conds)))
        row = {"epoch": 10 * (block + 1), "auroc": float(roc_auc_score(on[has], pp[has])),
               "D_slope": float(np.mean(sl)), "eff_mae": float(np.mean(np.abs(eff - rho))),
               "eff_corr": float(np.corrcoef(eff, rho)[0, 1])}
        print(row, flush=True)
        out.append(row)
json.dump(out, open("results/sim/diag_trajectory.json", "w"), indent=1)
