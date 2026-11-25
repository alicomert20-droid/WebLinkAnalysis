from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_simulator_varsayilan_ayarlarla_calisir():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert at.metric[2].value == "1.0000"  # toplam kütle


def test_simulator_tuzak_ve_olu_yol_birlikte():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.slider[2].set_value(3)  # Spider Trap düğüm sayısı
    at.sidebar.slider[3].set_value(3)  # Dead End düğüm sayısı
    at.run()
    assert not at.exception
    assert at.info, "Tuzak bilgisi gösterilmeli"
    # Tuzağa giriş bağlantıları ölü yollar tarafından silinmemeli: pay adil paydan büyük
    share = float(at.info[0].value.split("%")[1].split(" ")[0])
    assert share > 10.0
