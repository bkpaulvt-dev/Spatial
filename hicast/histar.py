"""Faithful re-implementation of the HiSTaR baseline.

Ported from the official code (https://github.com/Anglejuebi/HiSTaR, MIT
licence, files ``HiSTaR_module.py`` / ``HiSTaR_model.py`` / ``graph_func.py``)
so that the benchmark compares against what the authors actually ran. Default
behaviour is kept unchanged, including details that differ from the paper:

* the mask token is *added* to 80 % of spots, and ``forward`` also applies it
  in eval mode, so inference embeddings are stochastic;
* hop weights are pulled towards a fixed [0.7, 0.3] prior by a KL term;
* the VAE KL term is divided by N twice (``-0.5 / n_nodes * mean(...)``);
* edge reconstruction uses all positive edges plus one random node per edge.

The only change is that the O(N^2) Python loop that draws negative edges is
vectorised (same distribution: one uniformly random node per positive edge).
``deterministic_eval=True`` is an opt-in fix used in the ablation study.
"""
from __future__ import annotations

from functools import partial

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.cluster import KMeans

from .graph import spatial_knn, normalize_adj, to_torch_sparse

DT = torch.float64


def sce_loss(x, y, alpha=3):
    x = F.normalize(x, p=2, dim=-1)
    y = F.normalize(y, p=2, dim=-1)
    return (1 - (x * y).sum(dim=-1)).pow_(alpha).mean()


def full_block(i, o, p):
    return nn.Sequential(nn.Linear(i, o, dtype=DT),
                         nn.BatchNorm1d(o, momentum=0.01, eps=0.001, dtype=DT),
                         nn.ELU(), nn.Dropout(p=p))


class MultiHopGraphConvolution(nn.Module):
    def __init__(self, i, o, num_hops=2, dropout=0.1, act=F.relu):
        super().__init__()
        self.num_hops, self.dropout, self.act = num_hops, dropout, act
        self.weight = nn.Parameter(torch.empty(i, o, dtype=DT))
        self.hop_weights = nn.Parameter(torch.tensor([1.2, 0.0], dtype=DT))
        self.res_proj = nn.Linear(i, o, dtype=DT) if i != o else nn.Identity()
        nn.init.xavier_uniform_(self.weight)
        if isinstance(self.res_proj, nn.Linear):
            nn.init.xavier_uniform_(self.res_proj.weight)

    def forward(self, x, adj):
        residual = self.res_proj(x)
        x = F.dropout(x, self.dropout, self.training)
        support = x @ self.weight
        powers = [adj]
        for _ in range(1, self.num_hops):
            powers.append(torch.sparse.mm(powers[-1], adj))
        w = F.softmax(self.hop_weights, 0)
        out = sum(w[k] * torch.sparse.mm(powers[k], support) for k in range(self.num_hops))
        return self.act(out + residual)


class GraphConvolution(nn.Module):
    def __init__(self, i, o, dropout=0.1, act=F.relu):
        super().__init__()
        self.dropout, self.act = dropout, act
        self.weight = nn.Parameter(torch.empty(i, o, dtype=DT))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x, adj):
        x = F.dropout(x, self.dropout, self.training)
        return self.act(torch.sparse.mm(adj, x @ self.weight))


class HiSTaRBlock(nn.Module):
    def __init__(self, i, o, g, dropout=0.1):
        super().__init__()
        self.mh = MultiHopGraphConvolution(i, o, 2, dropout)
        self.mu = GraphConvolution(o, g, dropout, act=lambda x: x)
        self.lv = GraphConvolution(o, g, dropout, act=lambda x: x)

    def forward(self, x, adj):
        h = self.mh(x, adj)
        return self.mu(h, adj), self.lv(h, adj)


class HiSTaRModule(nn.Module):
    def __init__(self, input_dim, feat_hidden1=64, feat_hidden2=16, gcn_hidden1=64,
                 gcn_hidden2=12, p_drop=0.2, alpha=1.0, n_clusters=10, lambda_sim=0.3,
                 deterministic_eval=False):
        super().__init__()
        self.alpha, self.lambda_sim = alpha, lambda_sim
        self.deterministic_eval = deterministic_eval
        self.latent_dim = feat_hidden2 + 2 * gcn_hidden2
        self.encoder = nn.Sequential(full_block(input_dim, feat_hidden1, p_drop),
                                     full_block(feat_hidden1, feat_hidden2, p_drop))
        self.block1 = HiSTaRBlock(feat_hidden2, gcn_hidden1, gcn_hidden2, p_drop)
        self.block2 = HiSTaRBlock(gcn_hidden2, gcn_hidden1, gcn_hidden2, p_drop)
        self.decoder = GraphConvolution(self.latent_dim, input_dim, p_drop, act=lambda x: x)
        self.cluster_layer = nn.Parameter(torch.empty(n_clusters, self.latent_dim, dtype=DT))
        nn.init.xavier_normal_(self.cluster_layer.data)
        self.enc_mask_token = nn.Parameter(torch.zeros(1, input_dim, dtype=DT))
        self.mask_rate = 0.8
        self.criterion = partial(sce_loss, alpha=3)

    def _reparam(self, mu, logvar):
        if self.training:
            return torch.randn_like(mu) * torch.exp(logvar) + mu
        return mu

    def forward(self, x, adj):
        n = x.shape[0]
        perm = torch.randperm(n, device=x.device)
        mask_nodes = perm[: int(self.mask_rate * n)]
        x_in = x.clone()
        if self.training or not self.deterministic_eval:
            x_in[mask_nodes] += self.enc_mask_token
        feat_x = self.encoder(x_in)
        mu1, lv1 = self.block1(feat_x, adj)
        z1 = self._reparam(mu1, lv1)
        mu2, lv2 = self.block2(z1, adj)
        g1, g2 = self._reparam(mu1, lv1), self._reparam(mu2, lv2)
        sim_loss = -F.cosine_similarity(g1, g2, dim=1).mean()
        z = torch.cat([feat_x, g1, g2], 1)
        de_feat = self.decoder(z, adj)
        q = 1.0 / (1.0 + torch.sum((z.unsqueeze(1) - self.cluster_layer) ** 2, 2) / self.alpha)
        q = q.pow((self.alpha + 1.0) / 2.0)
        q = (q.t() / q.sum(1)).t()
        target = torch.tensor([0.7, 0.3], dtype=DT, device=x.device)
        hop_kl = sum(F.kl_div(F.softmax(m.hop_weights, 0).log(), target, reduction="sum")
                     for m in self.modules() if isinstance(m, MultiHopGraphConvolution))
        rec = self.criterion(de_feat[mask_nodes], x_in[mask_nodes])
        loss_self = rec + self.lambda_sim * sim_loss + 0.15 * hop_kl
        return z, (mu1, mu2), (lv1, lv2), de_feat, q, loss_self


def _target_distribution(q):
    w = q ** 2 / q.sum(0)
    return (w.t() / w.sum(1)).t()


def _gcn_loss(preds, labels, mus, lvs, n, norm):
    cost = norm * F.binary_cross_entropy_with_logits(preds, labels)
    kld = sum(-0.5 / n * torch.mean(torch.sum(1 + 2 * l - m.pow(2) - l.exp().pow(2), 1))
              for m, l in zip(mus, lvs))
    return cost + kld


class HiSTaR:
    """Trainer mirroring ``histar`` from the official code (200 pre-train + 200 DEC epochs)."""

    def __init__(self, X, coords, n_clusters, k=6, rec_w=10, gcn_w=0.1, self_w=1,
                 dec_kl_w=1, lambda_sim=0.3, gcn_hidden2=12, device="cpu",
                 deterministic_eval=False, seed=0):
        self.device = device
        self.rng = torch.Generator(device="cpu").manual_seed(seed)
        A = spatial_knn(coords, k)
        n = A.shape[0]
        self.adj_norm = to_torch_sparse(normalize_adj(A), device, DT)
        A_label = (A + sp.eye(n)).tocoo()
        self.norm_value = n * n / float((n * n - A_label.sum()) * 2)
        self.pos = torch.from_numpy(np.vstack([A_label.row, A_label.col]).astype(np.int64)).to(device)
        self.X = torch.as_tensor(X, dtype=DT, device=device)
        self.n = n
        self.rec_w, self.gcn_w, self.self_w, self.dec_kl_w = rec_w, gcn_w, self_w, dec_kl_w
        self.model = HiSTaRModule(X.shape[1], gcn_hidden2=gcn_hidden2, n_clusters=n_clusters,
                                  lambda_sim=lambda_sim,
                                  deterministic_eval=deterministic_eval).to(device)
        self.n_clusters = n_clusters
        # Same distribution as the official ``mask_generator(N=1)``, drawn once.
        neg_col = torch.randint(0, n, (self.pos.shape[1],), generator=self.rng).to(device)
        self.edges = torch.cat([self.pos, torch.stack([self.pos[0], neg_col])], 1)
        self.edge_labels = torch.cat([torch.ones(self.pos.shape[1]),
                                      torch.zeros(self.pos.shape[1])]).to(device, DT)

    def _edge_logits(self, z):
        return (z[self.edges[0]] * z[self.edges[1]]).sum(1)

    def fit(self, pre_epochs=200, dec_epochs=200, lr=0.005, decay=0.01, dec_interval=20):
        opt = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=decay)
        self.model.train()
        for _ in range(pre_epochs):
            opt.zero_grad()
            z, mu, lv, de_feat, _, loss_self = self.model(self.X, self.adj_norm)
            lg = _gcn_loss(self._edge_logits(z), self.edge_labels, mu, lv, self.n, self.norm_value)
            loss = self.rec_w * F.mse_loss(de_feat, self.X) + self.gcn_w * lg + self.self_w * loss_self
            loss.backward()
            opt.step()

        km = KMeans(self.n_clusters, n_init=self.n_clusters * 2, random_state=42)
        km.fit(self.embed())
        self.model.cluster_layer.data = torch.tensor(km.cluster_centers_, dtype=DT, device=self.device)
        self.model.train()
        for ep in range(dec_epochs):
            if ep % dec_interval == 0:
                self.model.eval()
                with torch.no_grad():
                    q = self.model(self.X, self.adj_norm)[4]
                p = _target_distribution(q).detach()
                self.model.train()
            opt.zero_grad()
            z, mu, lv, de_feat, q, _ = self.model(self.X, self.adj_norm)
            lg = _gcn_loss(self._edge_logits(z), self.edge_labels, mu, lv, self.n, self.norm_value)
            loss = (self.gcn_w * lg + self.dec_kl_w * F.kl_div(q.log(), p)
                    + self.rec_w * F.mse_loss(de_feat, self.X))
            loss.backward()
            opt.step()
        return self

    @torch.no_grad()
    def embed(self) -> np.ndarray:
        self.model.eval()
        z = self.model(self.X, self.adj_norm)[0]
        return z.cpu().numpy().astype(np.float32)
