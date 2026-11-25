"""Link Analizi Simülatörü (Streamlit).

Çalıştırma:  streamlit run app.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import streamlit as st

from src.graph import (
    add_dead_end,
    add_spider_trap,
    create_random_web_graph,
    in_degrees,
    out_degrees,
    to_networkx,
)
from src.hits import hits
from src.pagerank import pagerank

st.set_page_config(page_title="Link Analizi Simülatörü", layout="wide")
st.title("Link Analizi Simülatörü: PageRank & HITS")
st.caption("Proje 4.3 – Web Arama ve Bağlantı Analizi")


def build_graph(n, p, seed, trap_size, dead_count):
    """Kenar çubuğundaki ayarlara göre grafı kurar; (A, tuzak, ölü yol) döndürür."""
    A = create_random_web_graph(n, p, seed=seed)
    trap = list(range(n - trap_size, n)) if trap_size > 0 else []
    if trap:
        A = add_spider_trap(A, trap, seed=seed)
    dead = []
    if dead_count > 0:
        # Ölü yollar tuzağın hemen önündeki düğümlerden seçilir (çakışmasın)
        end = n - trap_size
        dead = list(range(max(0, end - dead_count), end))
        A = add_dead_end(A, dead)
    return A, trap, dead


# ------------------------------------------------------------ kenar çubuğu
with st.sidebar:
    st.header("Graf ayarları")
    n = st.slider("Düğüm sayısı (n)", 5, 100, 30)
    p = st.slider("Bağlantı olasılığı (p)", 0.02, 0.5, 0.1, 0.01)
    seed = st.number_input("Rastgele tohum (seed)", 0, 9999, 42)
    trap_size = st.slider("Spider Trap düğüm sayısı", 0, min(10, n // 2), 0)
    dead_count = st.slider("Dead End düğüm sayısı", 0, min(10, n // 2), 0)

    st.header("PageRank ayarları")
    alpha = st.slider("Sönümleme faktörü α", 0.0, 0.99, 0.85, 0.01)
    dead_mode = st.radio(
        "Dead End yönetimi",
        ["redistribute", "leak"],
        format_func=lambda m: "Tekdüze yeniden dağıt (çözüm)" if m == "redistribute"
        else "Sızıntıya izin ver (naif)",
    )
    tol = 10 ** st.slider("Durma toleransı (10^x)", -12, -4, -10)

A, trap, dead = build_graph(n, p, int(seed), trap_size, dead_count)
pr = pagerank(A, alpha, tol=tol, dead_end=dead_mode)
ht = hits(A, tol=tol)

# ------------------------------------------------------------ özet
c1, c2, c3, c4 = st.columns(4)
c1.metric("Düğüm / Kenar", f"{n} / {int(A.sum())}")
c2.metric("PageRank iterasyon", pr.iterations)
c3.metric("PageRank toplam kütle", f"{pr.total_mass:.4f}")
c4.metric("HITS iterasyon", ht.iterations)
if trap:
    st.info(f"Tuzak düğümleri {trap} – bu düğümlerin PageRank payı: "
            f"%{100 * pr.scores[trap].sum():.1f} (adil pay: %{100 * len(trap) / n:.1f})")
if dead and dead_mode == "leak":
    st.warning("Dead End var ve sızıntı açık: toplam kütle 1'in altına düşebilir.")
if not pr.converged or not ht.converged:
    st.warning("Algoritmalardan biri max iterasyonda yakınsamadı.")

tab_graph, tab_pr, tab_hits, tab_conv = st.tabs(["Graf", "PageRank", "HITS", "Yakınsama"])

# ------------------------------------------------------------ graf
with tab_graph:
    G = to_networkx(A)
    pos = nx.spring_layout(G, seed=int(seed))
    sizes = 300 + 6000 * pr.normalized
    colors = ["tab:red" if v in trap else "tab:orange" if v in dead else "tab:blue"
              for v in G.nodes]
    fig, ax = plt.subplots(figsize=(8, 6))
    nx.draw_networkx(G, pos, ax=ax, node_size=sizes, node_color=colors, alpha=0.85,
                     font_size=7, arrows=True, arrowsize=8, edge_color="gray", width=0.6)
    ax.set_axis_off()
    ax.set_title("Düğüm boyutu = PageRank | kırmızı: tuzak, turuncu: ölü yol")
    st.pyplot(fig)
    plt.close(fig)

# ------------------------------------------------------------ pagerank
with tab_pr:
    top_k = min(15, n)
    order = np.argsort(-pr.scores)[:top_k]
    left, right = st.columns([1, 1])
    with left:
        st.dataframe(
            {
                "Düğüm": [int(i) for i in order],
                "PageRank": [float(pr.scores[i]) for i in order],
                "Giriş": [int(in_degrees(A)[i]) for i in order],
                "Çıkış": [int(out_degrees(A)[i]) for i in order],
            },
            hide_index=True,
        )
    with right:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar([str(i) for i in order], pr.scores[order],
               color=["tab:red" if i in trap else "tab:blue" for i in order])
        ax.set_xlabel("Düğüm")
        ax.set_ylabel("PageRank")
        ax.set_title(f"En yüksek {top_k} PageRank (α={alpha})")
        st.pyplot(fig)
        plt.close(fig)

# ------------------------------------------------------------ hits
with tab_hits:
    top_k = min(15, n)
    oh = np.argsort(-ht.hubs)[:top_k]
    oa = np.argsort(-ht.authorities)[:top_k]
    c_l, c_r = st.columns(2)
    with c_l:
        st.subheader("Hub (merkez)")
        st.dataframe({"Düğüm": [int(i) for i in oh],
                      "Hub skoru": [float(ht.hubs[i]) for i in oh]}, hide_index=True)
    with c_r:
        st.subheader("Authority (otorite)")
        st.dataframe({"Düğüm": [int(i) for i in oa],
                      "Authority skoru": [float(ht.authorities[i]) for i in oa]},
                     hide_index=True)
    st.caption(f"‖h‖₂ = {np.linalg.norm(ht.hubs):.4f}, "
               f"‖a‖₂ = {np.linalg.norm(ht.authorities):.4f} (birim norm)")

# ------------------------------------------------------------ yakınsama
with tab_conv:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for a in (0.50, 0.85, 0.99):
        res = pagerank(A, a, tol=tol, max_iter=5000, dead_end=dead_mode)
        axes[0].semilogy(range(1, len(res.residuals) + 1), res.residuals,
                         label=f"α={a} ({res.iterations} it.)")
    axes[0].set_title("PageRank yakınsaması")
    axes[0].set_xlabel("İterasyon")
    axes[0].set_ylabel("L1 fark")
    axes[0].legend()
    axes[0].grid(True, which="both", alpha=0.3)

    axes[1].semilogy(range(1, len(ht.residuals) + 1), ht.residuals)
    axes[1].set_title(f"HITS yakınsaması ({ht.iterations} it.)")
    axes[1].set_xlabel("İterasyon")
    axes[1].set_ylabel("Değişim")
    axes[1].grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
