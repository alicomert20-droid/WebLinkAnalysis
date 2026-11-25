"""Spider Trap, Dead End ve alpha deneyleri modülü.

Çalıştırma (proje kökünden):  python -m src.experiments
Çıktılar ``results/`` klasörüne PNG ve CSV olarak yazılır.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .graph import (  # noqa: E402
    add_dead_end,
    add_spider_trap,
    create_random_web_graph,
    to_networkx,
)
from .hits import hits  # noqa: E402
from .pagerank import pagerank  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
ALPHAS = (0.50, 0.85, 0.99)
N_NODES = 50
SEED = 42
TRAP_NODES = [N_NODES - 3, N_NODES - 2, N_NODES - 1]  # 3 düğümlü tuzak
DEAD_NODES = [N_NODES - 3, N_NODES - 2, N_NODES - 1]  # 3 ölü yol


def _save_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _base_graph() -> np.ndarray:
    return create_random_web_graph(N_NODES, p=0.08, seed=SEED)


def _pr(A: np.ndarray, alpha: float, **kwargs):
    """PageRank'i çalıştırır; yakınsamadıysa sessizce devam etmek yerine hata verir."""
    res = pagerank(A, alpha, **kwargs)
    if not res.converged:
        raise RuntimeError(f"PageRank α={alpha} için {res.iterations} iterasyonda yakınsamadı.")
    return res


# ---------------------------------------------------------------- doğrulama
def validate_against_networkx(A: np.ndarray | None = None) -> dict[str, float]:
    """Kendi PageRank/HITS uygulamamızı networkx ile karşılaştırır."""
    import networkx as nx

    A = _base_graph() if A is None else A
    G = to_networkx(A)
    mine_pr = _pr(A, 0.85, tol=1e-12).scores
    nx_pr = nx.pagerank(G, alpha=0.85, tol=1e-12, max_iter=1000)
    pr_diff = max(abs(mine_pr[i] - nx_pr[i]) for i in range(len(mine_pr)))

    res = hits(A, tol=1e-12)
    if not res.converged:
        raise RuntimeError("HITS yakınsamadı.")
    nx_h, nx_a = nx.hits(G, tol=1e-12, max_iter=1000, normalized=True)
    h = res.hubs / res.hubs.sum()
    a = res.authorities / res.authorities.sum()
    hub_diff = max(abs(h[i] - nx_h[i]) for i in range(len(h)))
    auth_diff = max(abs(a[i] - nx_a[i]) for i in range(len(a)))
    return {"pagerank_max_diff": pr_diff, "hub_max_diff": hub_diff, "authority_max_diff": auth_diff}


# ---------------------------------------------------------------- deney 1
def experiment_spider_trap(out_dir: Path = RESULTS_DIR) -> list[list]:
    """Spider Trap'in rank'i nasıl 'emdiğini' ve alpha'nın etkisini gösterir."""
    base = _base_graph()
    trapped = add_spider_trap(base, TRAP_NODES, seed=1)
    rows = []
    for alpha in ALPHAS:
        s_base = _pr(base, alpha).scores
        s_trap = _pr(trapped, alpha).scores
        rows.append([
            alpha,
            round(float(s_base[TRAP_NODES].sum()), 6),
            round(float(s_trap[TRAP_NODES].sum()), 6),
        ])
    _save_csv(out_dir / "spider_trap_paylari.csv",
              ["alpha", "tuzak_payi_normal_graf", "tuzak_payi_tuzakli_graf"], rows)

    # Grafik 1: alpha'ya göre tuzağın toplam PageRank payı
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(ALPHAS))
    ax.bar(x - 0.2, [r[1] for r in rows], 0.4, label="Tuzaksız graf")
    ax.bar(x + 0.2, [r[2] for r in rows], 0.4, label="Spider Trap'li graf", color="tab:red")
    ax.set_xticks(x, [f"α={a}" for a in ALPHAS])
    ax.set_ylabel("3 düğümün toplam PageRank payı")
    ax.set_title("Spider Trap etkisi (n=50, tuzak = 3 düğüm)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "spider_trap_alpha.png", dpi=150)
    plt.close(fig)

    # Grafik 2: düğüm bazında PageRank (α=0.85)
    fig, ax = plt.subplots(figsize=(9, 4))
    idx = np.arange(N_NODES)
    ax.bar(idx - 0.2, _pr(base, 0.85).scores, 0.4, label="Tuzaksız")
    ax.bar(idx + 0.2, _pr(trapped, 0.85).scores, 0.4, label="Tuzaklı", color="tab:red")
    ax.set_xlabel("Düğüm")
    ax.set_ylabel("PageRank (α=0.85)")
    ax.set_title("Düğüm bazında PageRank: son 3 düğüm tuzak")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "spider_trap_dugumler.png", dpi=150)
    plt.close(fig)
    return rows


# ---------------------------------------------------------------- deney 1b
def trap_mass_without_teleportation(A: np.ndarray, trap_nodes: list[int], steps: int = 300) -> float:
    """Teleportation olmadan (α = 1) rastgele gezginin tuzaktaki olasılık kütlesi.

    Saf Markov zinciri: r_{k+1} = Pᵀ r_k. Tuzak periyodik bir döngü olabileceği için
    vektör yakınsamaz; ancak tuzaktaki toplam kütle 1'e doğru artar.
    """
    from .pagerank import build_transition_matrix

    PT = build_transition_matrix(A).T
    r = np.full(A.shape[0], 1.0 / A.shape[0])
    for _ in range(steps):
        r = PT @ r
    return float(r[trap_nodes].sum())


def experiment_spider_trap_solution(out_dir: Path = RESULTS_DIR) -> list[list]:
    """Spider Trap çözümü: teleportation (α < 1) tuzağın payını sınırlar.

    α'yı 0'dan 0.99'a tarar; teleportation'sız (α = 1) durumla karşılaştırır.
    """
    base = _base_graph()
    trapped = add_spider_trap(base, TRAP_NODES, seed=1)
    alphas = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99]
    rows = []
    for alpha in alphas:
        share_trap = float(_pr(trapped, alpha).scores[TRAP_NODES].sum())
        share_base = float(_pr(base, alpha).scores[TRAP_NODES].sum())
        rows.append([alpha, round(share_base, 6), round(share_trap, 6)])
    no_tp = trap_mass_without_teleportation(trapped, TRAP_NODES)
    rows.append([1.0, "-", round(no_tp, 6)])
    _save_csv(out_dir / "spider_trap_cozum.csv",
              ["alpha", "tuzak_payi_tuzaksiz_graf", "tuzak_payi_tuzakli_graf"], rows)

    fig, ax = plt.subplots(figsize=(7, 4))
    xs = [r[0] for r in rows[:-1]]
    ax.plot(xs, [r[2] for r in rows[:-1]], "o-", color="tab:red", label="Tuzaklı graf")
    ax.plot(xs, [r[1] for r in rows[:-1]], "s--", color="tab:blue", label="Tuzaksız graf")
    ax.scatter([1.0], [no_tp], color="k", marker="X", s=80, zorder=5,
               label="Teleportation yok (α=1)")
    ax.axhline(len(TRAP_NODES) / N_NODES, color="gray", ls=":", lw=1,
               label="Adil pay (3/50)")
    ax.set_xlabel("Sönümleme faktörü α")
    ax.set_ylabel("Tuzaktaki 3 düğümün toplam PageRank payı")
    ax.set_title("Spider Trap çözümü: teleportation tuzağı sınırlar")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "spider_trap_cozum.png", dpi=150)
    plt.close(fig)
    return rows


# ---------------------------------------------------------------- deney 2
def experiment_dead_end(out_dir: Path = RESULTS_DIR) -> list[list]:
    """Dead End: rank kütlesi sızıntısı ve tekdüze yeniden dağıtım çözümü."""
    base = _base_graph()
    dead = add_dead_end(base, DEAD_NODES)
    rows = []
    for alpha in ALPHAS:
        leak = _pr(dead, alpha, dead_end="leak")
        fixed = _pr(dead, alpha, dead_end="redistribute")
        rows.append([
            alpha,
            round(leak.total_mass, 6),
            round(fixed.total_mass, 6),
            leak.iterations,
            fixed.iterations,
        ])
    _save_csv(out_dir / "dead_end_kutle.csv",
              ["alpha", "toplam_kutle_sizinti", "toplam_kutle_duzeltilmis",
               "iter_sizinti", "iter_duzeltilmis"], rows)

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(ALPHAS))
    ax.bar(x - 0.2, [r[1] for r in rows], 0.4, label="Naif (sızıntı)", color="tab:red")
    ax.bar(x + 0.2, [r[2] for r in rows], 0.4, label="Yeniden dağıtım", color="tab:green")
    ax.axhline(1.0, color="k", ls="--", lw=1)
    ax.set_xticks(x, [f"α={a}" for a in ALPHAS])
    ax.set_ylabel("Toplam PageRank kütlesi")
    ax.set_title("Dead End: kütle kaybı (n=50, 3 ölü yol)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "dead_end_kutle.png", dpi=150)
    plt.close(fig)
    return rows


# ---------------------------------------------------------------- deney 3
def experiment_alpha_convergence(out_dir: Path = RESULTS_DIR) -> list[list]:
    """α'nın yakınsama hızına etkisi (0.50, 0.85, 0.99)."""
    base = _base_graph()
    rows = []
    fig, ax = plt.subplots(figsize=(7, 4))
    for alpha in ALPHAS:
        res = _pr(base, alpha, tol=1e-10)
        rows.append([alpha, res.iterations, res.converged, f"{res.residuals[-1]:.2e}"])
        ax.semilogy(range(1, len(res.residuals) + 1), res.residuals, label=f"α={alpha}")
    _save_csv(out_dir / "alpha_yakinsama.csv",
              ["alpha", "iterasyon", "yakinsadi_mi", "son_artik"], rows)
    ax.set_xlabel("İterasyon")
    ax.set_ylabel("L1 fark (log)")
    ax.set_title("Sönümleme faktörü ve yakınsama hızı")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "alpha_yakinsama.png", dpi=150)
    plt.close(fig)
    return rows


# ---------------------------------------------------------------- deney 4
def experiment_hits(out_dir: Path = RESULTS_DIR, top_k: int = 10) -> list[list]:
    """HITS hub/authority skorları ve yakınsama."""
    base = _base_graph()
    res = hits(base)
    if not res.converged:
        raise RuntimeError("HITS yakınsamadı.")
    order_h = np.argsort(-res.hubs)[:top_k]
    order_a = np.argsort(-res.authorities)[:top_k]
    rows = [[int(i), round(float(res.hubs[i]), 6), int(j), round(float(res.authorities[j]), 6)]
            for i, j in zip(order_h, order_a)]
    _save_csv(out_dir / "hits_ilk10.csv",
              ["hub_dugum", "hub_skor", "authority_dugum", "authority_skor"], rows)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar([str(i) for i in order_h], res.hubs[order_h], color="tab:blue")
    axes[0].set_title(f"En yüksek {top_k} Hub")
    axes[0].set_xlabel("Düğüm")
    axes[1].bar([str(i) for i in order_a], res.authorities[order_a], color="tab:orange")
    axes[1].set_title(f"En yüksek {top_k} Authority")
    axes[1].set_xlabel("Düğüm")
    fig.tight_layout()
    fig.savefig(out_dir / "hits_skorlar.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.semilogy(range(1, len(res.residuals) + 1), res.residuals)
    ax.set_xlabel("İterasyon")
    ax.set_ylabel("Değişim (log)")
    ax.set_title(f"HITS yakınsama ({res.iterations} iterasyon)")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "hits_yakinsama.png", dpi=150)
    plt.close(fig)
    return rows


def run_all(out_dir: Path = RESULTS_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    print("== networkx doğrulaması ==")
    for k, v in validate_against_networkx().items():
        print(f"  {k}: {v:.2e}")
    print("== Spider Trap ==")
    for r in experiment_spider_trap(out_dir):
        print(f"  alpha={r[0]}: tuzaksız={r[1]}  tuzaklı={r[2]}")
    print("== Spider Trap çözümü (alpha taraması) ==")
    for r in experiment_spider_trap_solution(out_dir):
        print(f"  alpha={r[0]}: tuzaklı graf payı={r[2]}")
    print("== Dead End ==")
    for r in experiment_dead_end(out_dir):
        print(f"  alpha={r[0]}: sızıntılı kütle={r[1]}  düzeltilmiş={r[2]}")
    print("== Alpha yakınsama ==")
    for r in experiment_alpha_convergence(out_dir):
        print(f"  alpha={r[0]}: {r[1]} iterasyon")
    print("== HITS ==")
    experiment_hits(out_dir)
    print(f"Çıktılar: {out_dir}")


if __name__ == "__main__":
    run_all()
