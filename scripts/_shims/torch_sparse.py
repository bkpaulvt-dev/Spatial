"""Minimal stand-in for the compiled `torch_sparse` extension (its wheel host is unreachable here).

STAGATE_pyG imports `SparseTensor` and `set_diag` but, as called by `train_STAGATE`, always passes
a dense `edge_index` tensor, so the SparseTensor branches are never taken. `SparseTensor` is
torch_geometric's own placeholder class; `set_diag` raises if it is ever reached.
"""
from torch_geometric.typing import SparseTensor  # noqa: F401


def set_diag(*args, **kwargs):
    raise NotImplementedError("torch_sparse is not installed; SparseTensor inputs are not supported")
