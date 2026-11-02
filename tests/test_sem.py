import numpy as np
import pandas as pd
import pytest

from umkm import sem


def _data(n: int = 400, seed: int = 42) -> tuple[pd.DataFrame, sem.ModelPLS]:
    """Dua konstruk laten (3 butir, loading 0,8) -> y = 0,5 A + 0 B + galat."""
    rng = np.random.default_rng(seed)
    a, b = rng.normal(size=n), rng.normal(size=n)
    d = {}
    for k, lv in (("a", a), ("b", b)):
        for i in range(3):
            d[f"{k}{i}"] = 0.8 * lv + 0.6 * rng.normal(size=n)
    d["y"] = 0.5 * a + np.sqrt(0.75) * rng.normal(size=n)
    m = sem.ModelPLS(
        {"A": ["a0", "a1", "a2"], "B": ["b0", "b1", "b2"], "y": ["y"]}, {"y": ["A", "B"]}
    )
    return pd.DataFrame(d), m


def test_estimasi_memulihkan_jalur_dan_loading():
    df, m = _data()
    f = sem.estimasi(df, m)
    assert f["konvergen"]
    # skor komposit sedikit melemahkan jalur (galat pengukuran), tetapi arahnya jelas
    assert 0.35 < f["jalur"][("A", "y")] < 0.55
    assert abs(f["jalur"][("B", "y")]) < 0.1
    assert np.all(f["loading"]["A"] > 0.75) and np.all(f["loading"]["B"] > 0.6)
    assert f["skor"]["A"].std(ddof=0) == pytest.approx(1)


def test_tanda_konstruk_mengikuti_loading_positif():
    df, m = _data()
    df[["a0", "a1", "a2"]] *= -1
    f = sem.estimasi(df, m)
    assert f["loading"]["A"].sum() > 0 and f["jalur"][("A", "y")] < 0


def test_reliabilitas_dan_htmt():
    df, m = _data()
    rel = sem.reliabilitas(df, m, sem.estimasi(df, m)).set_index("konstruk")
    assert set(rel.index) == {"A", "B"}
    assert (rel["alpha"] > 0.8).all() and (rel["rho_c"] > rel["alpha"] - 0.01).all()
    assert (rel["ave"] > 0.5).all()
    h = sem.htmt(df, m.blok)
    assert h.loc["B", "A"] < 0.2  # konstruk independen


def test_bootstrap_deterministik_dan_daya_prediksi():
    df, m = _data(n=150)
    j1, _, _, gagal = sem.bootstrap(df, m, 30, seed=42)
    j2, _, _, _ = sem.bootstrap(df, m, 30, seed=42)
    pd.testing.assert_frame_equal(j1, j2)
    assert gagal == 0 and len(j1) == 30
    dp = sem.daya_prediksi(df, m, "y", seed=42, k=5, ulang=2)
    assert dp["q2_predict"] > 0.1


def test_spesifikasi_persepsi_reflektif():
    m = sem.spesifikasi("persepsi", ["jumlah_platform"])
    assert m.blok["persepsi"] == sem.BUTIR_Y
    assert m.jalur["persepsi"] == sem.STRATEGI + ["jumlah_platform"]
