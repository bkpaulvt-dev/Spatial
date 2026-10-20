"""CIPHER: a VAE for single-cell CRISPR screens.

Ideas taken from the five source papers:

* Count likelihood with a log link, so perturbation effects multiply by default
  (GLiMMIRS: enhancer effects combine multiplicatively, interactions are rare).
* A per-cell latent "did this guide work?" variable, marginalised exactly over all
  on/off masks of the guides a cell carries (Perturb-seq/MIMOSCA's EM for effective
  perturbation, GLiMMIRS guide-efficiency probabilities). Efficacy is learned per guide.
* Perturbations act on a small regulatory state h that settles to the steady state of a
  nonlinear cyclic network  h = tanh(W h + u(z) + sum_k pi_k a_k)  (LLCB's cyclic
  steady-state model, made nonlinear). ||W||_2 < 1 makes the map a contraction, so the
  steady state exists and is unique; this replaces LLCB's spectral-radius prior.
  With the network, joint perturbations interact through saturation and feedback,
  rather than through a free parameter per pair, so interactions can be predicted for
  pairs never seen together.
* The target gene's own expression gets a direct (cis) term; every other change must
  pass through the network (trans), as in LLCB's direct-vs-total effect split.
* Gene programs: sparse loadings V map h to genes (scBC-style modules), with L1.
* Optional adversary with gradient reversal removes perturbation information from the
  basal latent z (the CPA idea), so control cells' z can be reused for counterfactuals.
"""
import itertools
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def nb_loglik(x, mu, theta, eps=1e-8):
    lt = torch.log(theta + eps)
    lm = torch.log(mu + theta + eps)
    return (theta * (lt - lm) + x * (torch.log(mu + eps) - lm)
            + torch.lgamma(x + theta) - torch.lgamma(theta) - torch.lgamma(x + 1)).sum(-1)


class _GradReverse(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, lam):
        ctx.lam = lam
        return x.view_as(x)

    @staticmethod
    def backward(ctx, g):
        return -ctx.lam * g, None


class CIPHERNet(nn.Module):
    def __init__(self, n_genes, n_units, n_batch, cis_index, d_z=32, d_h=64, hidden=256,
                 activation="tanh", gamma=0.9, n_iter=20, escape=True, init_eff=0.9, basal=True, direct=False):
        super().__init__()
        self.basal = basal
        self.explain_away = False   # set after the basal latent has been learned on controls
        # optional per-unit direct log-scale gene effects: the multiplicative null
        self.D = nn.Parameter(torch.zeros(n_units, n_genes)) if direct else None
        self.G, self.K, self.d_h = n_genes, n_units, d_h
        self.activation, self.gamma, self.n_iter, self.escape = activation, gamma, n_iter, escape
        self.enc = nn.Sequential(nn.Linear(n_genes, hidden), nn.LayerNorm(hidden), nn.GELU(),
                                 nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.enc_mu = nn.Linear(hidden, d_z)
        self.enc_lv = nn.Linear(hidden, d_z)
        # basal decoder
        self.dec = nn.Sequential(nn.Linear(d_z + n_batch, hidden), nn.GELU(), nn.Linear(hidden, n_genes))
        self.n_batch = n_batch
        # regulatory state
        self.U = nn.Linear(d_z, d_h)
        self.W_raw = nn.Parameter(torch.randn(d_h, d_h) * 0.01)
        self.register_buffer("_u", F.normalize(torch.randn(d_h), dim=0))
        self.A = nn.Parameter(torch.randn(n_units, d_h) * 0.01)       # direct effects on h
        self.V = nn.Parameter(torch.randn(d_h, n_genes) * 0.01)       # program loadings
        cis = torch.as_tensor(cis_index, dtype=torch.long)
        self.register_buffer("cis_index", cis)                       # target gene per unit (-1 none)
        self.cis = nn.Parameter(torch.zeros(n_units))
        self.eff_logit = nn.Parameter(torch.full((n_units,), math.log(init_eff / (1 - init_eff))))
        self.log_theta = nn.Parameter(torch.zeros(n_genes))
        self.adv = nn.Sequential(nn.Linear(d_z, hidden), nn.GELU(), nn.Linear(hidden, n_units + 1))

    # ---- network -------------------------------------------------------------
    def W(self):
        with torch.no_grad():  # one power-iteration step per call keeps sigma estimate fresh
            v = F.normalize(self.W_raw.T @ self._u, dim=0)
            self._u.copy_(F.normalize(self.W_raw @ v, dim=0))
        sigma = (self._u @ self.W_raw @ v).abs() + 1e-8
        return self.W_raw * torch.clamp(self.gamma / sigma, max=1.0)

    def act(self, x):
        return torch.tanh(x) if self.activation == "tanh" else x

    def steady_state(self, inp, W):
        h = torch.zeros_like(inp)
        if self.activation == "linear":     # closed form: h = (I - W)^-1 inp
            I = torch.eye(self.d_h, device=inp.device)
            return torch.linalg.solve(I - W, inp.T).T
        for _ in range(self.n_iter):
            h = self.act(h @ W.T + inp)
        return h

    # ---- masks over guides ---------------------------------------------------
    @staticmethod
    def masks(m, device):
        return torch.tensor(list(itertools.product([0, 1], repeat=m)), dtype=torch.float32, device=device)

    def log_prior(self, P, M):
        """P: B x m unit indices (-1 pad); M: S x m masks -> S x B log prior of each mask."""
        valid = (P >= 0).float()                                  # B x m
        logit = self.eff_logit[P.clamp(min=0)]                    # B x m
        if not self.escape:
            lp_on, lp_off = torch.zeros_like(logit), torch.full_like(logit, -1e4)
        else:
            lp_on, lp_off = F.logsigmoid(logit), F.logsigmoid(-logit)
        Mx = M[:, None, :]                                        # S x 1 x m
        lp = Mx * lp_on + (1 - Mx) * lp_off                       # S x B x m
        lp = lp * valid + (Mx * (1 - valid)) * (-1e4)             # padded slot must be off
        return lp.sum(-1)

    def logits(self, z, b1h, P, M, W):
        """Gene logits for every mask. Returns S x B x G and S x B x d_h steady states."""
        B = z.shape[0]
        valid = (P >= 0).float()
        a = self.A[P.clamp(min=0)] * valid[..., None]             # B x m x d_h
        on = M[:, None, :] * valid[None]                          # S x B x m
        drive = torch.einsum("sbm,bmh->sbh", on, a)               # S x B x d_h
        u = self.U(z)                                             # B x d_h
        S = M.shape[0]
        h = self.steady_state((u[None] + drive).reshape(S * B, -1), W).reshape(S, B, -1)
        base = self.dec(torch.cat([z, b1h], -1))                  # B x G
        lg = base[None] + h @ self.V                              # S x B x G
        # cis effect on the targeted gene
        ci = self.cis_index[P.clamp(min=0)]                       # B x m
        has = (ci >= 0).float() * valid
        add = torch.zeros(S, B, self.G, device=z.device)
        idx = ci.clamp(min=0)[None].expand(S, -1, -1)
        add.scatter_add_(2, idx, on * has[None] * self.cis[P.clamp(min=0)][None])
        if self.D is not None:
            lg = lg + torch.einsum("sbm,bmg->sbg", on, self.D[P.clamp(min=0)] * valid[..., None])
        return lg + add, h

    def forward(self, x, lib, b, P, kl_w=1.0, adv_lam=1.0):
        B = x.shape[0]
        b1h = F.one_hot(b, self.n_batch).float()
        xn = torch.log1p(x / lib[:, None] * 1e4)
        m = P.shape[1]
        M = self.masks(m, x.device)
        W = self.W()
        if self.explain_away:
            # remove each mask's predicted perturbation effect before inferring the basal state,
            # so the basal latent cannot absorb the perturbation (encoder is frozen here)
            with torch.no_grad():
                z0 = torch.zeros(B, self.enc_mu.out_features, device=x.device)
                lg0, _ = self.logits(z0, b1h, P, M, W)
                delta = lg0 - lg0[:1]                                 # S x B x G, mask 0 = all off
                xs = x[None] * torch.exp(-delta)
                xn_s = torch.log1p(xs / lib[None, :, None] * 1e4)
                mu = self.enc_mu(self.enc(xn_s))                      # S x B x d_z
            lg = torch.stack([self.logits(mu[s], b1h, P, M[s:s + 1], W)[0][0] for s in range(M.shape[0])])
            kl = torch.zeros(B, device=x.device)
            lv = None
        else:
            hid = self.enc(xn)
            mu, lv = self.enc_mu(hid), self.enc_lv(hid).clamp(-8, 8)
            z = mu + torch.randn_like(mu) * torch.exp(0.5 * lv)
            if not self.basal:
                z = z * 0.0
            lg, _ = self.logits(z, b1h, P, M, W)
            kl = 0.5 * (mu.pow(2) + lv.exp() - 1 - lv).sum(-1)
        rate = torch.softmax(lg, -1) * lib[None, :, None]
        theta = torch.exp(self.log_theta)
        ll = torch.stack([nb_loglik(x, rate[s], theta) for s in range(M.shape[0])])   # S x B
        lp = self.log_prior(P, M)
        joint = ll + lp
        marg = torch.logsumexp(joint, 0)
        resp = torch.softmax(joint, 0).detach()                   # posterior over masks
        loss = (-marg + kl_w * kl).mean()
        out = {"nll": (-marg).mean().item(), "kl": kl.mean().item()}
        if adv_lam > 0:
            target = torch.zeros(B, self.K + 1, device=x.device)
            valid = P >= 0
            target[torch.arange(B, device=x.device)[:, None].expand_as(P)[valid], P[valid]] = 1.0
            target[:, -1] = (~valid).all(1).float()
            logit = self.adv(_GradReverse.apply(mu if mu.dim() == 2 else mu[0], adv_lam))
            adv = F.binary_cross_entropy_with_logits(logit, target)
            loss = loss + adv * x.shape[1] / 100.0
            out["adv"] = adv.item()
        out["resp"] = resp
        out["M"] = M
        return loss, out

    def penalty(self):
        p = self.V.abs().sum() + self.W_raw.abs().sum()
        return p + (self.D.abs().sum() if self.D is not None else 0.0)


class CIPHER:
    """Fit / predict wrapper."""

    def __init__(self, data, seed=0, d_z=32, d_h=64, activation="tanh", escape=True,
                 adversary=True, adv_weight=1.0, basal=True, direct=False, n_iter=20, epochs=30, batch_size=256, lr=1e-3, l1=1e-4, device="cpu",
                 threads=None, verbose=True, train_idx=None, control_basal=False):
        self.d, self.seed = data, seed
        # control_basal: learn the basal latent (encoder + basal decoder) on control cells only,
        # then freeze it, so cell-to-cell variation is modelled but cannot absorb perturbation effects
        self.control_basal = control_basal
        self.epochs, self.bs, self.lr, self.l1 = epochs, batch_size, lr, l1
        self.adversary, self.verbose, self.device = adversary, verbose, device
        self.adv_weight = adv_weight
        self.train_idx = np.arange(data.X.shape[0]) if train_idx is None else np.asarray(train_idx)
        if threads:
            torch.set_num_threads(threads)
        torch.manual_seed(seed)
        np.random.seed(seed)
        gidx = {g: i for i, g in enumerate(data.genes)}
        cis = [gidx.get(data.target_of.get(u, u), -1) for u in data.targets]
        nb = int(data.batch.max()) + 1
        self.net = CIPHERNet(len(data.genes), len(data.targets), nb, cis, d_z=d_z, d_h=d_h,
                             activation=activation, escape=escape, basal=basal, direct=direct, n_iter=n_iter).to(device)

    def _tensors(self, idx):
        X = torch.tensor(self.d.X[idx].toarray(), device=self.device)
        lib = X.sum(1).clamp(min=1.0)
        b = torch.tensor(self.d.batch[idx], device=self.device)
        P = torch.tensor(self.d.P[idx], device=self.device)
        return X, lib, b, P

    def fit(self):
        net = self.net
        self.history = []
        if self.control_basal:
            ctrl = self.train_idx[(self.d.P[self.train_idx] < 0).all(1)]
            basal_params = (list(net.enc.parameters()) + list(net.enc_mu.parameters()) +
                            list(net.enc_lv.parameters()) + list(net.dec.parameters()) + [net.log_theta])
            self._run(ctrl, self.epochs, basal_params, adversary=False)
            for mod in (net.enc, net.enc_mu, net.enc_lv, net.dec):
                for q in mod.parameters():
                    q.requires_grad_(False)
            net.explain_away = True
        params = [q for q in net.parameters() if q.requires_grad]
        self._run(self.train_idx, self.epochs, params, adversary=self.adversary,
                  kl_warmup=not self.control_basal)
        return self

    def _run(self, idx_all, epochs, params, adversary, kl_warmup=True):
        net = self.net
        opt = torch.optim.Adam(params, lr=self.lr)
        n_it = int(math.ceil(len(idx_all) / self.bs))
        total = epochs * n_it
        step = 0
        for ep in range(epochs):
            perm = np.random.permutation(idx_all)
            agg = {"nll": 0.0, "kl": 0.0, "adv": 0.0}
            net.train()
            for it in range(n_it):
                bi = np.sort(perm[it * self.bs:(it + 1) * self.bs])
                X, lib, b, P = self._tensors(bi)
                kl_w = min(1.0, step / (0.3 * total)) if kl_warmup else 1.0
                loss, out = net(X, lib, b, P, kl_w=kl_w, adv_lam=self.adv_weight if adversary else 0.0)
                loss = loss + self.l1 * net.penalty()
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(params, 10.0)
                opt.step()
                step += 1
                for k in agg:
                    agg[k] += out.get(k, 0.0) / n_it
            self.history.append(agg)
            if self.verbose:
                print(f"  ep {ep:3d} nll {agg['nll']:.1f} kl {agg['kl']:.1f} adv {agg['adv']:.3f}", flush=True)

    @torch.no_grad()
    def embed(self, idx):
        self.net.eval()
        out = []
        for s in range(0, len(idx), 2048):
            X, lib, b, P = self._tensors(idx[s:s + 2048])
            zz = self.net.enc_mu(self.net.enc(torch.log1p(X / lib[:, None] * 1e4)))
            out.append(zz if self.net.basal else zz * 0.0)
        return torch.cat(out)

    @torch.no_grad()
    def predict_mean(self, units, ctrl_idx, mixture=True):
        """Predicted mean normalised expression (1e4 * mu / lib) for a perturbation set."""
        net = self.net
        net.eval()
        z = self.embed(ctrl_idx)
        dev = self.device
        b1h = F.one_hot(torch.tensor(self.d.batch[ctrl_idx], device=dev), net.n_batch).float()
        ix = {u: i for i, u in enumerate(self.d.targets)}
        P = torch.tensor([[ix[u] for u in units]] * len(ctrl_idx), device=dev) if units else \
            -torch.ones(len(ctrl_idx), 1, dtype=torch.long, device=dev)
        M = net.masks(P.shape[1], z.device)
        W = net.W()
        lp = net.log_prior(P, M) if mixture else None
        acc = torch.zeros(net.G, device=dev)
        for s in range(0, len(ctrl_idx), 1024):
            sl = slice(s, s + 1024)
            lg, _ = net.logits(z[sl], b1h[sl], P[sl], M, W)
            pr = torch.softmax(lg, -1)                                  # S x B x G
            if mixture:
                w = torch.softmax(lp[:, sl], 0)                          # S x B
            else:
                w = torch.zeros(M.shape[0], pr.shape[1], device=dev)
                w[-1] = 1.0
            acc += (w[..., None] * pr).sum((0, 1))
        return (acc / len(ctrl_idx) * 1e4).cpu().numpy()

    def efficacy(self):
        return dict(zip(self.d.targets, torch.sigmoid(self.net.eff_logit).detach().cpu().numpy()))

    @torch.no_grad()
    def escape_posterior(self, idx):
        """Per-cell posterior probability that each carried guide was effective."""
        self.net.eval()
        res = []
        for s in range(0, len(idx), 1024):
            X, lib, b, P = self._tensors(idx[s:s + 1024])
            _, out = self.net(X, lib, b, P, adv_lam=0.0)
            res.append((out["resp"].T @ out["M"]).cpu().numpy())          # B x m
        return np.concatenate(res)
