"""Sentetik yönlü web grafikleri oluşturma ve yönetme modülü.

Gösterim: ``A`` bir (n x n) komşuluk matrisidir; ``A[i, j] == 1`` ise
``i`` sayfasından ``j`` sayfasına bir bağlantı vardır (i -> j).
"""

from __future__ import annotations

import numpy as np


def validate_adjacency(A: np.ndarray) -> np.ndarray:
    """Matrisin kare ve 0/1 değerli olduğunu doğrular, float dizi döndürür."""
    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("Komşuluk matrisi kare (n x n) olmalıdır.")
    if not np.isin(A, (0.0, 1.0)).all():
        raise ValueError("Komşuluk matrisi yalnızca 0 ve 1 içermelidir.")
    return A


def create_random_web_graph(
    n: int = 50,
    p: float = 0.08,
    seed: int | None = 42,
    ensure_out_links: bool = True,
) -> np.ndarray:
    """Rastgele (Erdős–Rényi tipi) yönlü web grafiği üretir.

    Kendine bağlantı (self-loop) yoktur. ``ensure_out_links=True`` ise
    çıkış bağlantısı olmayan her sayfaya rastgele bir hedef eklenir; böylece
    temel graf Dead End içermez ve deneylerde bozucu etkiler kontrollü
    biçimde sonradan eklenebilir.
    """
    if n < 2:
        raise ValueError("n en az 2 olmalıdır.")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p, [0, 1] aralığında olmalıdır.")
    rng = np.random.default_rng(seed)
    A = (rng.random((n, n)) < p).astype(float)
    np.fill_diagonal(A, 0.0)
    if ensure_out_links:
        for i in np.flatnonzero(A.sum(axis=1) == 0):
            targets = [j for j in range(n) if j != i]
            A[i, rng.choice(targets)] = 1.0
    return A


def add_spider_trap(
    A: np.ndarray,
    trap_nodes: list[int],
    entry_sources: list[int] | None = None,
    n_entries: int = 3,
    seed: int | None = 0,
) -> np.ndarray:
    """Grafa bir Spider Trap (örümcek kapanı) ekler ve yeni matris döndürür.

    ``trap_nodes`` kümesindeki sayfaların çıkış bağlantıları silinir ve
    yalnızca küme içindeki bir döngüye bağlanır (a -> b -> c -> a). Kümeye
    dışarıdan girilebilmesi için ``entry_sources`` sayfalarından kümenin ilk
    düğümüne bağlantı eklenir. Rank bu kümeye girince dışarı çıkamaz.
    """
    A = validate_adjacency(A).copy()
    n = A.shape[0]
    trap = list(dict.fromkeys(trap_nodes))
    if not trap or any(not 0 <= t < n for t in trap):
        raise ValueError("trap_nodes geçerli düğüm indeksleri içermelidir.")

    for t in trap:
        A[t, :] = 0.0
    for k, t in enumerate(trap):
        A[t, trap[(k + 1) % len(trap)]] = 1.0  # tek düğümde self-loop olur

    if entry_sources is None:
        rng = np.random.default_rng(seed)
        outside = [i for i in range(n) if i not in trap]
        k = min(n_entries, len(outside))
        entry_sources = [int(x) for x in rng.choice(outside, size=k, replace=False)]
    for s in entry_sources:
        if s in trap:
            raise ValueError("entry_sources, tuzak düğümlerinden olmamalıdır.")
        A[s, trap[0]] = 1.0
    return A


def add_dead_end(A: np.ndarray, nodes: list[int]) -> np.ndarray:
    """Verilen sayfaların çıkış bağlantılarını silerek Dead End (ölü yol) yapar."""
    A = validate_adjacency(A).copy()
    n = A.shape[0]
    if any(not 0 <= v < n for v in nodes):
        raise ValueError("nodes geçerli düğüm indeksleri içermelidir.")
    for v in nodes:
        A[v, :] = 0.0
    return A


def out_degrees(A: np.ndarray) -> np.ndarray:
    """Her sayfanın çıkış derecesi."""
    return validate_adjacency(A).sum(axis=1)


def in_degrees(A: np.ndarray) -> np.ndarray:
    """Her sayfanın giriş derecesi."""
    return validate_adjacency(A).sum(axis=0)


def to_networkx(A: np.ndarray):
    """Doğrulama ve görselleştirme için ``networkx.DiGraph`` döndürür."""
    import networkx as nx

    return nx.from_numpy_array(validate_adjacency(A), create_using=nx.DiGraph)


def example_graph() -> np.ndarray:
    """Derste kullanılabilecek küçük 4 düğümlü örnek graf.

    0 -> 1, 2 ;  1 -> 2 ;  2 -> 0 ;  3 -> 2
    """
    A = np.zeros((4, 4))
    A[0, [1, 2]] = 1
    A[1, 2] = 1
    A[2, 0] = 1
    A[3, 2] = 1
    return A
