import numpy as np
import pytest

from src.experiments import (
    DEAD_NODES,
    TRAP_NODES,
    _base_graph,
    validate_against_networkx,
)
from src.graph import add_dead_end, add_spider_trap, create_random_web_graph, example_graph
from src.hits import hits
from src.pagerank import build_transition_matrix, pagerank


def test_graf_uretimi_deterministik_ve_deadendsiz():
    A1 = create_random_web_graph(30, 0.1, seed=1)
    A2 = create_random_web_graph(30, 0.1, seed=1)
    assert (A1 == A2).all()
    assert (A1.sum(axis=1) > 0).all()
    assert np.trace(A1) == 0


def test_gecis_matrisi_stokastik():
    P = build_transition_matrix(add_dead_end(example_graph(), [3]))
    assert np.allclose(P.sum(axis=1), 1.0)


def test_pagerank_toplami_bir_ve_yakinsar():
    res = pagerank(_base_graph(), 0.85)
    assert res.converged
    assert res.total_mass == pytest.approx(1.0)
    assert (res.scores > 0).all()


def test_pagerank_elle_hesap_ornek_graf():
    # 4 düğümlü örnek: 2 numaralı sayfa en çok bağlantı alır
    res = pagerank(example_graph(), 0.85)
    assert np.argmax(res.scores) == 2


def test_spider_trap_rank_emer_ve_alpha_dusunce_azalir():
    base = _base_graph()
    trapped = add_spider_trap(base, TRAP_NODES, seed=1)
    shares = {}
    for alpha in (0.5, 0.85, 0.99):
        shares[alpha] = pagerank(trapped, alpha).scores[TRAP_NODES].sum()
        assert shares[alpha] > pagerank(base, alpha).scores[TRAP_NODES].sum()
    assert shares[0.5] < shares[0.85] < shares[0.99]


def test_spider_trap_cozumu_teleportation():
    from src.experiments import trap_mass_without_teleportation

    trapped = add_spider_trap(_base_graph(), TRAP_NODES, seed=1)
    no_tp = trap_mass_without_teleportation(trapped, TRAP_NODES)
    with_tp = pagerank(trapped, 0.85).scores[TRAP_NODES].sum()
    assert no_tp > 0.99          # teleportation yoksa tüm kütle tuzağa gider
    assert with_tp < 0.5         # teleportation tuzağı sınırlar
    # α = 0: tekdüze dağılım, tuzak adil payını (3/50) alır
    assert pagerank(trapped, 0.0).scores[TRAP_NODES].sum() == pytest.approx(3 / 50)


def test_dead_end_sizinti_ve_duzeltme():
    dead = add_dead_end(_base_graph(), DEAD_NODES)
    leak = pagerank(dead, 0.85, dead_end="leak")
    fixed = pagerank(dead, 0.85, dead_end="redistribute")
    assert leak.total_mass < 0.99
    assert fixed.total_mass == pytest.approx(1.0)


def test_alpha_buyudukce_iterasyon_artar():
    base = _base_graph()
    its = [pagerank(base, a, max_iter=5000).iterations for a in (0.5, 0.85, 0.99)]
    assert its[0] < its[1] < its[2]


def test_hits_birim_norm_ve_yakinsama():
    res = hits(_base_graph())
    assert res.converged
    assert np.linalg.norm(res.hubs) == pytest.approx(1.0)
    assert np.linalg.norm(res.authorities) == pytest.approx(1.0)


def test_networkx_ile_uyum():
    diffs = validate_against_networkx()
    assert diffs["pagerank_max_diff"] < 1e-8
    assert diffs["hub_max_diff"] < 1e-6
    assert diffs["authority_max_diff"] < 1e-6


def test_gecersiz_parametreler():
    with pytest.raises(ValueError):
        pagerank(example_graph(), alpha=1.0)
    with pytest.raises(ValueError):
        build_transition_matrix(example_graph(), dead_end="x")
