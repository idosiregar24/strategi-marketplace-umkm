import numpy as np
import pandas as pd
import pytest

from umkm import features as ft


def test_cronbach_alpha_rumus():
    # Butir sejajar sempurna: varians butir 1, 1, 1; varians total 9 -> 3/2*(1-3/9) = 1
    items = pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3], "c": [2, 3, 4]})
    total_var = items.sum(axis=1).var(ddof=1)
    expected = 3 / 2 * (1 - 3 / total_var)
    assert ft.cronbach_alpha(items) == pytest.approx(expected)
    assert ft.cronbach_alpha(items) == pytest.approx(1.0)


def test_cronbach_alpha_butir_acak_rendah():
    rng = np.random.default_rng(42)
    items = pd.DataFrame(rng.integers(1, 6, size=(200, 4)))
    assert ft.cronbach_alpha(items) < 0.3


def test_reliabilitas_item_kolom():
    items = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 2, 3, 5], "c": [1, 3, 3, 4]})
    rel = ft.reliabilitas_item(items)
    assert list(rel["butir"]) == ["a", "b", "c"]
    assert rel["korelasi_butir_total"].between(-1, 1).all()


def _kinerja(**kw):
    base = {
        "omzet_sebelum_w": [100.0, 100.0, 0.0, 100.0, 200.0],
        "omzet_sesudah_w": [150.0, 100.0, 50.0, 100.0, 100.0],
        "trx_sebelum_w": [10.0, 10.0, 0.0, np.nan, 20.0],
        "trx_sesudah_w": [10.0, 20.0, 5.0, np.nan, 10.0],
        "pelanggan_baru": [0.0, 10.0, 5.0, 3.0, 1.0],
    }
    base.update(kw)
    return pd.DataFrame(base)


def test_naik_penjualan_omzet_atau_trx():
    df = _kinerja()
    out = ft.target_kinerja(df, pd.Series([1] * 5))
    # omzet naik | trx naik | dari 0 naik | trx kosong & omzet sama | keduanya turun
    assert out["naik_penjualan"].tolist() == [1, 1, 1, 0, 0]
    assert out["arah_trx"].tolist() == ["sama", "naik", "naik", "kosong", "turun"]


def test_log1p_terdefinisi_saat_nol_dan_pct_kosong():
    out = ft.target_kinerja(_kinerja(), pd.Series([1] * 5))
    assert np.isfinite(out.loc[2, "d_omzet"])
    assert np.isnan(out.loc[2, "pct_omzet"])
    assert out.loc[0, "pct_omzet"] == pytest.approx(50.0)


def test_y_obj_hanya_omzet_saat_trx_kosong():
    df = _kinerja()
    out = ft.target_kinerja(df, pd.Series([1] * 5))
    d = out["d_omzet"]
    z = (d - d.mean()) / d.std(ddof=1)
    assert out.loc[3, "y_obj"] == pytest.approx(z[3])


def test_flag_kualitas():
    from umkm.cleaning import X1_COLS, X2_COLS, X3_COLS, X4_COLS

    x_items = X1_COLS + X2_COLS + X3_COLS + X4_COLS
    df = pd.DataFrame({c: [3, 3, 3] for c in x_items})
    df.loc[1, x_items[0]] = 4
    df["omzet_sebelum"] = [90e6, 10e6, 0.0]
    df["omzet_sesudah"] = [9e6, 10e6, 5e6]
    out = ft.flag_kualitas(df)
    assert out["flag_jawaban_seragam"].tolist() == [1, 0, 1]
    assert out["flag_omzet_turun_tajam"].tolist() == [1, 0, 0]


def test_skala_omzet_batas_tetap():
    batas = [10.0, 20.0, 30.0]
    s = ft.skala_omzet(pd.Series([5.0, 10.0, 25.0, 31.0]), batas)
    assert s.tolist() == ["Q1_kecil", "Q1_kecil", "Q3_menengah_atas", "Q4_besar"]
