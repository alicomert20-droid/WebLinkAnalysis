"""HITS hub ve authority algoritması modülü.

Yinelemeli güncelleme (her adımda birim L2 norm ile):
    authority:  a = A^T h     (bana bağlanan hub'ların toplamı)
    hub:        h = A a       (bağlandığım authority'lerin toplamı)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .graph import validate_adjacency


@dataclass
class HITSResult:
    hubs: np.ndarray
    authorities: np.ndarray
    iterations: int
    converged: bool
    residuals: list[float] = field(default_factory=list)  # max(||Δh||, ||Δa||)


def _unit(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x)
    return x / norm if norm > 0 else x


def hits(A: np.ndarray, tol: float = 1e-10, max_iter: int = 1000) -> HITSResult:
    """HITS algoritması; hub ve authority vektörleri birim L2 normludur."""
    A = validate_adjacency(A)
    n = A.shape[0]
    h = np.full(n, 1.0 / np.sqrt(n))
    a = np.full(n, 1.0 / np.sqrt(n))
    residuals: list[float] = []
    for k in range(1, max_iter + 1):
        a_new = _unit(A.T @ h)
        h_new = _unit(A @ a_new)
        diff = float(max(np.linalg.norm(a_new - a), np.linalg.norm(h_new - h)))
        residuals.append(diff)
        a, h = a_new, h_new
        if diff < tol:
            return HITSResult(h, a, k, True, residuals)
    return HITSResult(h, a, max_iter, False, residuals)
