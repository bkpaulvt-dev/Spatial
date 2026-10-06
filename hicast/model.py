"""HiCAST: Hierarchical Contrastive Adaptive Spatial Transcriptomics.

An improved successor to HiSTaR. Each component targets a weakness of
HiSTaR (see ``docs/HiCAST.md`` for the full motivation):

1. Expression-aware, self-refining graph   (HiSTaR: fixed binary KNN graph)
2. Node-adaptive hop attention             (HiSTaR: one global hop weight, pinned to [0.7, 0.3])
3. Cross-level InfoNCE                     (HiSTaR: cosine L_sim, needs per-dataset lambda tuning
                                            and pushes the levels to be redundant)
4. Spatial local-global contrast           (HiSTaR: no discriminative objective)
5. Attention fusion of levels              (HiSTaR: plain concatenation [F0, F1, F2])
6. Learned loss balancing                  (HiSTaR: hand-tuned lambda_rec/sim/DEC/GCN)
7. Batch-conditional decoder + MNN edges   (HiSTaR: no explicit batch model)
8. Deterministic inference, O(E) losses    (HiSTaR: random masking at inference, KL scaled by 1/N^2)
"""
from __future__ import annotations

import math

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F

from .graph import spatial_knn, expression_weights, mnn_edges, normalize_adj, to_torch_sparse


# --------------------------------------------------------------------------- layers
class AdaptiveHopPropagation(nn.Module):
    """Decoupled multi-hop propagation with per-spot hop attention.

    H_0 = X W,  H_k = A_hat H_{k-1}  (k = 1..K)
    a_ik = softmax_k( q . tanh(H_k[i]) ),   out_i = sum_k a_ik H_k[i]

    Spots deep inside a domain can draw on wide neighbourhoods while spots on
    a boundary can stay local, which a single global hop weight cannot do.
    """

    def __init__(self, in_dim: int, out_dim: int, hops: int, dropout: float = 0.1):
        super().__init__()
        self.lin = nn.Linear(in_dim, out_dim)
        self.q = nn.Linear(out_dim, 1, bias=False)
        self.hops, self.dropout = hops, dropout

    def forward(self, x, adj):
        h = self.lin(F.dropout(x, self.dropout, self.training))
        hs = [h]
        for _ in range(self.hops):
            hs.append(torch.sparse.mm(adj, hs[-1]))
        H = torch.stack(hs, 1)                                  # (N, K+1, d)
        a = torch.softmax(self.q(torch.tanh(H)).squeeze(-1), 1)  # (N, K+1)
        self.last_attention = a.detach()
        return (a.unsqueeze(-1) * H).sum(1)


class VariationalLevel(nn.Module):
    """One level of the hierarchy: adaptive propagation -> (mu, logvar)."""

    def __init__(self, in_dim, hid, z_dim, hops, dropout):
        super().__init__()
        self.prop = AdaptiveHopPropagation(in_dim, hid, hops, dropout)
        self.norm = nn.LayerNorm(hid)
        self.mu = nn.Linear(hid, z_dim)
        self.logvar = nn.Linear(hid, z_dim)

    def forward(self, x, adj):
        h = F.elu(self.norm(self.prop(x, adj)))
        return self.mu(h), self.logvar(h).clamp(-8, 8)


class LevelFusion(nn.Module):
    """Per-spot attention over hierarchy levels (replaces concatenation)."""

    def __init__(self, dims, out_dim):
        super().__init__()
        self.proj = nn.ModuleList(nn.Linear(d, out_dim) for d in dims)
        self.score = nn.Sequential(nn.Linear(out_dim, out_dim), nn.Tanh(),
                                   nn.Linear(out_dim, 1, bias=False))

    def forward(self, levels):
        P = torch.stack([p(h) for p, h in zip(self.proj, levels)], 1)  # (N, L, d)
        b = torch.softmax(self.score(P).squeeze(-1), 1)
        self.last_attention = b.detach()
        return (b.unsqueeze(-1) * P).sum(1)


class HiCASTModule(nn.Module):
    def __init__(self, input_dim, n_batches=1, hid=256, f0_dim=64, z_dim=32, out_dim=32,
                 hops=(3, 6), dropout=0.1, mask_rate=0.3):
        super().__init__()
        self.mask_rate, self.n_batches = mask_rate, n_batches
        self.encoder = nn.Sequential(nn.Linear(input_dim, hid), nn.LayerNorm(hid), nn.ELU(),
                                     nn.Dropout(dropout), nn.Linear(hid, f0_dim))
        self.level1 = VariationalLevel(f0_dim, 2 * z_dim, z_dim, hops[0], dropout)
        self.level2 = VariationalLevel(z_dim, 2 * z_dim, z_dim, hops[1], dropout)
        self.fusion = LevelFusion([f0_dim, z_dim, z_dim], out_dim)
        self.head1 = nn.Sequential(nn.Linear(z_dim, z_dim), nn.ELU(), nn.Linear(z_dim, z_dim))
        self.head2 = nn.Sequential(nn.Linear(z_dim, z_dim), nn.ELU(), nn.Linear(z_dim, z_dim))
        self.disc = nn.Bilinear(out_dim, out_dim, 1)
        self.decoder = nn.Linear(out_dim + (n_batches if n_batches > 1 else 0), input_dim)
        self.mask_token = nn.Parameter(torch.zeros(1, input_dim))

    def encode(self, x, adj):
        f0 = self.encoder(x)
        mu1, lv1 = self.level1(f0, adj)
        z1 = mu1 + torch.randn_like(mu1) * torch.exp(0.5 * lv1) if self.training else mu1
        mu2, lv2 = self.level2(z1, adj)
        z2 = mu2 + torch.randn_like(mu2) * torch.exp(0.5 * lv2) if self.training else mu2
        z = self.fusion([f0, z1, z2])
        return z, (f0, z1, z2), ((mu1, lv1), (mu2, lv2))

    def decode(self, z, adj, batch_onehot=None):
        if batch_onehot is not None:
            z = torch.cat([z, batch_onehot], 1)
        return torch.sparse.mm(adj, self.decoder(z))


# --------------------------------------------------------------------------- losses
def sce(x, y, alpha=2.0):
    return (1 - F.cosine_similarity(x, y, dim=-1)).pow(alpha).mean()


def info_nce(a, b, tau=0.5):
    a, b = F.normalize(a, dim=1), F.normalize(b, dim=1)
    logits = a @ b.t() / tau
    target = torch.arange(a.shape[0], device=a.device)
    return 0.5 * (F.cross_entropy(logits, target) + F.cross_entropy(logits.t(), target))


def kl_normal(mu, lv):
    return (-0.5 * (1 + lv - mu.pow(2) - lv.exp()).sum(1)).mean()


# --------------------------------------------------------------------------- trainer
class HiCAST:
    """Train HiCAST on one slice (or several slices with ``batch``) and return embeddings.

    Ablation switches (all True = full model):
      expr_graph, refine_graph, adaptive_hops, local_global, fusion,
      auto_balance, batch_decoder
    ``xlevel_mode`` selects the cross-level objective: "cos" (HiSTaR's cosine
    similarity, the tuned default), "nbr" (neighbourhood InfoNCE), "spot"
    (instance InfoNCE) or "none". Both InfoNCE variants were worse in tuning.
    """

    LOSSES = ("rec", "xlevel", "lg", "edge")

    def __init__(self, X, coords, batch=None, k=6, epochs=600, lr=1e-3, weight_decay=1e-4,
                 hops=(3, 6), z_dim=32, out_dim=32, beta_kl=1e-3, mask_rate=0.3,
                 refine_at=(0.5,), refine_mix=0.5, mnn_k=3, n_contrast=2048, tau=0.5,
                 xlevel_mode="cos", balance="kendall", device="cpu", seed=0, verbose=False,
                 **ablation):
        self.opts = dict(expr_graph=True, refine_graph=False, adaptive_hops=True,
                         local_global=True, fusion=True, auto_balance=True, batch_decoder=True)
        unknown = set(ablation) - set(self.opts)
        if unknown:
            raise TypeError(f"unknown options: {unknown}")
        self.opts.update(ablation)
        torch.manual_seed(seed)
        np.random.seed(seed)
        self.device, self.epochs, self.lr, self.wd = device, epochs, lr, weight_decay
        self.beta_kl, self.n_contrast, self.tau, self.verbose = beta_kl, n_contrast, tau, verbose
        self.xlevel_mode, self.balance, self.L0 = xlevel_mode, balance, None
        self.refine_epochs = {int(r * epochs) for r in refine_at} if self.opts["refine_graph"] else set()
        self.refine_mix = refine_mix
        self.X = torch.as_tensor(X, dtype=torch.float32, device=device)
        n = X.shape[0]

        batch = np.zeros(n, dtype=np.int64) if batch is None else np.asarray(batch)
        self.batch = batch
        nb = int(batch.max()) + 1
        self.batch_onehot = None
        if nb > 1 and self.opts["batch_decoder"]:
            self.batch_onehot = F.one_hot(torch.as_tensor(batch, device=device), nb).float()

        # --- graph: spatial KNN (+ cross-slice MNN edges), expression-aware weights
        A = spatial_knn(coords, k)
        if nb > 1:
            A = ((A + mnn_edges(X[:, :30], batch, mnn_k)) > 0).astype(np.float32)
        self.A_bin = A.tocsr()
        self.expr_w = (expression_weights(self.A_bin, X[:, :30]) if self.opts["expr_graph"]
                       else self.A_bin.copy())
        self._set_adj(self.expr_w)
        coo = self.A_bin.tocoo()
        self.pos_edges = torch.from_numpy(np.vstack([coo.row, coo.col]).astype(np.int64)).to(device)

        hops_eff = hops if self.opts["adaptive_hops"] else (1, 1)
        self.model = HiCASTModule(X.shape[1], n_batches=nb if self.batch_onehot is not None else 1,
                                  z_dim=z_dim, out_dim=out_dim, hops=hops_eff,
                                  mask_rate=mask_rate).to(device)
        if not self.opts["adaptive_hops"]:
            # Fixed-weight multi-hop GCN as in HiSTaR, kept for the ablation.
            for lvl, K in zip((self.model.level1, self.model.level2), hops):
                lvl.prop.hops = K
                nn.init.zeros_(lvl.prop.q.weight)
                lvl.prop.q.weight.requires_grad_(False)
        if not self.opts["fusion"]:
            self.model.fusion = _Concat()
            self.model.disc = nn.Bilinear(64 + 2 * z_dim, 64 + 2 * z_dim, 1).to(device)
            dec_in = 64 + 2 * z_dim + (nb if self.batch_onehot is not None else 0)
            self.model.decoder = nn.Linear(dec_in, X.shape[1]).to(device)
        # learned log-variances for uncertainty weighting (Kendall et al., 2018)
        self.log_vars = nn.Parameter(torch.zeros(len(self.LOSSES), device=device))
        self.history = []

    def _set_adj(self, W: sp.csr_matrix):
        self.W = W.tocsr()
        self.adj = to_torch_sparse(normalize_adj(self.W), self.device)

    # ------------------------------------------------------------------ objectives
    def _losses(self):
        m = self.model
        n = self.X.shape[0]
        # masked feature modelling: replace masked spots by a learnable token
        mask = torch.rand(n, device=self.device) < m.mask_rate
        x_in = torch.where(mask[:, None], m.mask_token.expand_as(self.X), self.X)
        z, (f0, z1, z2), posts = m.encode(x_in, self.adj)
        x_hat = m.decode(z, self.adj, self.batch_onehot)
        L = {"rec": sce(x_hat[mask], self.X[mask]) + 0.1 * F.mse_loss(x_hat, self.X)}

        idx = torch.randperm(n, device=self.device)[: self.n_contrast]
        if self.xlevel_mode == "none":
            L["xlevel"] = z.new_zeros(())
        elif self.xlevel_mode == "cos":      # HiSTaR's cosine similarity loss
            L["xlevel"] = -F.cosine_similarity(z1, z2, dim=1).mean()
        elif self.xlevel_mode == "spot":     # instance-level InfoNCE (same spot = positive)
            L["xlevel"] = info_nce(m.head1(z1[idx]), m.head2(z2[idx]), self.tau)
        elif self.xlevel_mode == "nbr":      # neighbourhood InfoNCE: fine spot <-> smoothed coarse context
            ctx = torch.sparse.mm(self.adj, z2)
            L["xlevel"] = info_nce(m.head1(z1[idx]), m.head2(ctx[idx]), self.tau)
        else:
            raise ValueError(f"unknown xlevel_mode {self.xlevel_mode!r}")

        if self.opts["local_global"]:
            perm = torch.randperm(n, device=self.device)
            z_c, _, _ = m.encode(x_in[perm], self.adj)        # corrupted view
            s = torch.sigmoid(torch.sparse.mm(self.adj, z))    # local neighbourhood summary
            s_c = torch.sigmoid(torch.sparse.mm(self.adj, z_c))
            pos = torch.cat([m.disc(z, s), m.disc(z_c, s_c)])
            neg = torch.cat([m.disc(z_c, s), m.disc(z, s_c)])
            L["lg"] = (F.binary_cross_entropy_with_logits(pos, torch.ones_like(pos))
                       + F.binary_cross_entropy_with_logits(neg, torch.zeros_like(neg)))
        else:
            L["lg"] = z.new_zeros(())

        # edge reconstruction with negative sampling: O(|E|), not O(N^2)
        e = self.pos_edges
        neg_col = torch.randint(0, n, (e.shape[1],), device=self.device)
        zn = F.normalize(z, dim=1)
        pos_l = (zn[e[0]] * zn[e[1]]).sum(1) / self.tau
        neg_l = (zn[e[0]] * zn[neg_col]).sum(1) / self.tau
        L["edge"] = (F.binary_cross_entropy_with_logits(pos_l, torch.ones_like(pos_l))
                     + F.binary_cross_entropy_with_logits(neg_l, torch.zeros_like(neg_l)))

        kl = sum(kl_normal(mu, lv) for mu, lv in posts)
        return L, kl

    def _total(self, L, kl, epoch):
        beta = self.beta_kl * min(1.0, epoch / max(1, self.epochs // 4))  # KL warm-up
        if self.opts["auto_balance"] and self.balance == "init":
            # scale-free: every loss is measured relative to its value at the start
            if self.L0 is None:
                self.L0 = {k: max(float(v.detach()), 1e-3) for k, v in L.items()}
            tot = sum(L[k] / self.L0[k] for k in self.LOSSES)
        elif self.opts["auto_balance"]:
            tot = sum(torch.exp(-self.log_vars[i]) * L[k] + self.log_vars[i]
                      for i, k in enumerate(self.LOSSES) if L[k].requires_grad)
        else:
            tot = 10 * L["rec"] + 0.3 * L["xlevel"] + L["lg"] + 0.1 * L["edge"]
        return tot + beta * kl

    # ------------------------------------------------------------------ training
    def fit(self):
        params = list(self.model.parameters()) + [self.log_vars]
        opt = torch.optim.Adam([p for p in params if p.requires_grad], lr=self.lr,
                               weight_decay=self.wd)
        for ep in range(self.epochs):
            if ep in self.refine_epochs:
                self._refine_graph()
            self.model.train()
            opt.zero_grad()
            L, kl = self._losses()
            loss = self._total(L, kl, ep)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 5.0)
            opt.step()
            if self.verbose and (ep % 100 == 0 or ep == self.epochs - 1):
                print(ep, f"{loss.item():.4f}", {k: round(v.item(), 4) for k, v in L.items()})
            self.history.append({k: v.item() for k, v in L.items()})
        return self

    @torch.no_grad()
    def _refine_graph(self):
        """Re-weight spatial edges with the current embedding (blended with the old weights)."""
        Z = self.embed()
        if self.opts["expr_graph"]:
            new = expression_weights(self.A_bin, Z)
            mixed = self.refine_mix * new + (1 - self.refine_mix) * self.W
            self._set_adj(mixed)

    @torch.no_grad()
    def embed(self) -> np.ndarray:
        self.model.eval()
        z, _, _ = self.model.encode(self.X, self.adj)   # deterministic: no mask, posterior means
        return z.cpu().numpy()

    @torch.no_grad()
    def attention(self) -> dict:
        self.model.eval()
        self.model.encode(self.X, self.adj)
        out = {"hop_level1": self.model.level1.prop.last_attention.cpu().numpy(),
               "hop_level2": self.model.level2.prop.last_attention.cpu().numpy()}
        if hasattr(self.model.fusion, "last_attention"):
            out["levels"] = self.model.fusion.last_attention.cpu().numpy()
        return out


class _Concat(nn.Module):
    def forward(self, levels):
        return torch.cat(levels, 1)
