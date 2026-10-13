import torch
import torch.nn as nn
from transformers import AutoConfig, AutoModel, EsmConfig, EsmModel

from .data import TASKS


class MultiTaskESM(nn.Module):
    """ESM-2 encoder -> masked mean pool over residues -> one linear logit per task."""

    def __init__(self, model_name=None, config=None, tasks=TASKS, dropout=0.1, freeze_layers=0):
        super().__init__()
        if model_name:
            self.encoder = AutoModel.from_pretrained(model_name, add_pooling_layer=False)
        else:  # randomly initialised (tests / smoke runs)
            self.encoder = EsmModel(config, add_pooling_layer=False)
        h = self.encoder.config.hidden_size
        self.tasks = list(tasks)
        self.drop = nn.Dropout(dropout)
        self.heads = nn.ModuleList([nn.Linear(h, 1) for _ in self.tasks])
        self.set_frozen(freeze_layers)

    def set_frozen(self, n_layers):
        """Freeze embeddings + the first n_layers transformer blocks (n_layers<0: whole encoder)."""
        blocks = self.encoder.encoder.layer
        for p in self.encoder.parameters():
            p.requires_grad = True
        if n_layers == 0:
            return
        k = len(blocks) if n_layers < 0 else n_layers
        for p in self.encoder.embeddings.parameters():
            p.requires_grad = False
        for b in blocks[:k]:
            for p in b.parameters():
                p.requires_grad = False
        if k == len(blocks):
            for p in self.encoder.parameters():
                p.requires_grad = False

    def forward(self, ids, attn, res_mask):
        h = self.encoder(input_ids=ids, attention_mask=attn).last_hidden_state
        m = res_mask.unsqueeze(-1).to(h.dtype)
        pooled = (h * m).sum(1) / m.sum(1).clamp(min=1)
        pooled = self.drop(pooled)
        return torch.cat([head(pooled) for head in self.heads], dim=1)  # (B, n_tasks)


def masked_bce(logits, y, mask, task_weights=None):
    """BCE averaged over observed labels only; per-task means so sparse tasks aren't swamped."""
    loss = nn.functional.binary_cross_entropy_with_logits(logits, torch.nan_to_num(y), reduction="none")
    loss = loss * mask
    per_task = loss.sum(0) / mask.sum(0).clamp(min=1)
    present = (mask.sum(0) > 0).to(per_task.dtype)
    w = present if task_weights is None else present * task_weights
    return (per_task * w).sum() / w.sum().clamp(min=1e-8)
