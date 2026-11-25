"""PageRank ve teleportation algoritması modülü.

Model: ``r_{k+1} = alpha * P^T r_k + (1 - alpha) * v`` (Power Iteration)

* ``P``: satır-stokastik geçiş matrisi (``P[i, j] = 1/outdeg(i)`` eğer i -> j)
* ``alpha``: sönümleme faktörü (bağlantıyı izleme olasılığı, örn. 0.85)
* ``v``: teleportation dağılımı (varsayılan: tekdüze 1/n)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .graph import validate_adjacency

DEAD_END_MODES = ("redistribute", "leak")


@dataclass
class PageRankResult:
    scores: np.ndarray
    iterations: int
    converged: bool
    residuals: list[float] = field(default_factory=list)  # her adımdaki L1 fark

    @property
    def total_mass(self) -> float:
        """Toplam rank kütlesi. 'leak' modunda Dead End yüzünden 1'in altına düşer."""
        return float(self.scores.sum())

    @property
    def normalized(self) -> np.ndarray:
        """Toplamı 1 olacak şekilde ölçeklenmiş skorlar."""
        total = self.scores.sum()
        return self.scores / total if total > 0 else self.scores


def build_transition_matrix(
    A: np.ndarray,
    dead_end: str = "redistribute",
    dangling: np.ndarray | None = None,
) -> np.ndarray:
    """Satır-stokastik geçiş matrisi ``P`` oluşturur.

    ``dead_end`` (çıkışı olmayan sayfalar):
      * ``"redistribute"``: satır ``dangling`` dağılımıyla (varsayılan tekdüze 1/n)
        doldurulur; rastgele gezgin oradan atlar ve P stokastik kalır.
      * ``"leak"``: satır sıfır bırakılır; rank kütlesi sızar (naif model).
    """
    if dead_end not in DEAD_END_MODES:
        raise ValueError(f"dead_end şunlardan biri olmalı: {DEAD_END_MODES}")
    A = validate_adjacency(A)
    n = A.shape[0]
    out = A.sum(axis=1)
    P = np.zeros_like(A)
    has_out = out > 0
    P[has_out] = A[has_out] / out[has_out, None]
    if dead_end == "redistribute":
        P[~has_out] = 1.0 / n if dangling is None else dangling
    return P


def pagerank(
    A: np.ndarray,
    alpha: float = 0.85,
    tol: float = 1e-10,
    max_iter: int = 10_000,
    dead_end: str = "redistribute",
    teleport: np.ndarray | None = None,
) -> PageRankResult:
    """Power Iteration ile PageRank hesaplar.

    Durma ölçütü: ardışık iki vektör arasındaki L1 fark < ``tol``.
    Hata her adımda en çok α kat küçülür; α → 1 iken (özellikle Spider Trap
    gibi periyodik yapılarda) binlerce iterasyon gerekebilir, bu yüzden
    ``max_iter`` varsayılanı yüksektir. Sonucu kullanmadan önce ``converged``
    alanını kontrol edin.
    """
    if not 0.0 <= alpha < 1.0:
        raise ValueError("alpha, [0, 1) aralığında olmalıdır.")
    n = validate_adjacency(A).shape[0]

    if teleport is None:
        v = np.full(n, 1.0 / n)
    else:
        v = np.asarray(teleport, dtype=float)
        if v.shape != (n,) or (v < 0).any() or not np.isclose(v.sum(), 1.0):
            raise ValueError("teleport, uzunluğu n olan ve toplamı 1 olan bir dağılım olmalı.")

    # Ölü yollardan atlama, teleportation dağılımıyla tutarlı olsun
    P = build_transition_matrix(A, dead_end, dangling=v)
    r = np.full(n, 1.0 / n)
    residuals: list[float] = []
    PT = P.T
    for k in range(1, max_iter + 1):
        r_new = alpha * (PT @ r) + (1.0 - alpha) * v
        diff = float(np.abs(r_new - r).sum())
        residuals.append(diff)
        r = r_new
        if diff < tol:
            return PageRankResult(r, k, True, residuals)
    return PageRankResult(r, max_iter, False, residuals)
