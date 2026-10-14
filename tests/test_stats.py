import numpy as np
import pandas as pd
import pytest

from umkm import config
from umkm import stats as sx


def test_wilcoxon_semua_sama_kosong():
    s = pd.Series([1.0, 2.0, 3.0])
    r = sx.wilcoxon_berpasangan(s, s)
    assert r["n_sama"] == 3 and r["n_naik"] == 0
    assert np.isnan(r["p"]) and np.isnan(r["r"])


def test_wilcoxon_semua_naik():
    seb = pd.Series([10.0, 20, 30, 40, 50, 60, 70, 80])
    ses = seb + pd.Series([1.0, 2, 3, 4, 5, 6, 7, 8])
    r = sx.wilcoxon_berpasangan(seb, ses)
    assert r["n_naik"] == 8 and r["n_turun"] == 0
    assert r["r_rank_biserial"] == pytest.approx(1.0)
    assert r["z"] > 0 and r["r"] > 0
    assert r["p"] < 0.05


def test_wilcoxon_pasangan_sama_dibuang_dan_nan_diabaikan():
    seb = pd.Series([1.0, 1, 1, 1, np.nan, 5, 5, 5, 5, 5])
    ses = pd.Series([2.0, 3, 4, 5, 9.0, 5, 5, 5, 5, 0])
    r = sx.wilcoxon_berpasangan(seb, ses)
    assert r["n_pasangan"] == 9  # baris NaN dibuang
    assert (r["n_naik"], r["n_sama"], r["n_turun"]) == (4, 4, 1)
    # r_semua_pasangan memakai pembagi semua pasangan -> lebih kecil dari r
    assert abs(r["r_semua_pasangan"]) < abs(r["r"])


def test_mann_whitney_arah_dan_rank_biserial():
    tinggi = pd.Series([4.0, 4.5, 5.0, 4.2, 4.8])
    rendah = pd.Series([1.0, 1.5, 2.0, 1.2, 1.8])
    r = sx.mann_whitney(tinggi, rendah)
    assert r["r_rank_biserial"] == pytest.approx(1.0)
    assert r["z"] > 0
    r2 = sx.mann_whitney(rendah, tinggi)
    assert r2["r_rank_biserial"] == pytest.approx(-1.0)
    assert r2["z"] < 0


def test_mann_whitney_kelompok_identik():
    x = pd.Series([1.0, 2, 3, 3, 3, 4])
    r = sx.mann_whitney(x, x.copy())
    assert r["r_rank_biserial"] == pytest.approx(0.0)
    assert r["p"] == pytest.approx(1.0)


def test_holm_menjaga_nan():
    p = pd.Series([0.01, np.nan, 0.04, 0.03])
    out = sx.holm(p)
    assert np.isnan(out.iloc[1])
    assert out.iloc[0] == pytest.approx(0.03)  # 0,01 x 3 uji
    assert (out.dropna() >= p.dropna()).all()


def test_spearman_ci_memuat_rho_dan_tepi():
    lo, hi = sx.spearman_ci(0.3, 100)
    assert lo < 0.3 < hi
    assert all(np.isnan(v) for v in sx.spearman_ci(0.3, 3))
    assert all(np.isnan(v) for v in sx.spearman_ci(1.0, 50))


def test_spearman_tabel_pairwise_complete():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 6], "y": [1, 2, 3, 4, np.nan, 6]})
    t = sx.spearman_tabel(df, ["x"], ["y"])
    assert t.loc[0, "n"] == 5
    assert t.loc[0, "rho"] == pytest.approx(1.0)


def test_vif_independen_dan_kolinear():
    rng = np.random.default_rng(42)
    a, b = rng.normal(size=200), rng.normal(size=200)
    bebas = sx.vif(pd.DataFrame({"a": a, "b": b}), ["a", "b"])
    assert (bebas["vif"] < 1.2).all()
    c = a + rng.normal(scale=0.05, size=200)
    kolinear = sx.vif(pd.DataFrame({"a": a, "b": b, "c": c}), ["a", "b", "c"])
    assert kolinear.set_index("variabel").loc["a", "vif"] > 10


def test_ringkas_skor_floor_ceiling_dominan():
    x = pd.Series([1.0, 1, 3, 3, 3, 3, 5, 2])
    r = sx.ringkas_skor(x)
    assert r["pct_floor"] == pytest.approx(2 / 8)
    assert r["pct_ceiling"] == pytest.approx(1 / 8)
    assert r["nilai_dominan"] == 3 and r["pct_nilai_dominan"] == pytest.approx(0.5)


def test_sebaran_butir_proporsi_dan_netral():
    items = pd.DataFrame({"a": [3, 3, 3, 1, 5], "b": [1, 2, 2, 4, 5]})
    out = sx.sebaran_butir(items).set_index("butir")
    pct = [f"pct_{k}" for k in range(1, 6)]
    assert out[pct].sum(axis=1).to_numpy() == pytest.approx([1.0, 1.0])
    assert bool(out.loc["a", "dominasi_netral"]) is True
    assert bool(out.loc["b", "dominasi_netral"]) is False
    assert out.loc["b", "kategori_dominan"] == 2


@pytest.mark.parametrize(
    "r, label",
    [(0.05, "sangat kecil"), (-0.2, "kecil"), (0.35, "sedang"), (0.7, "besar"), (np.nan, "")],
)
def test_label_efek(r, label):
    assert sx.label_efek(r) == label


_FEAT = config.path("processed") / "data_features.csv"


@pytest.mark.skipif(not _FEAT.exists(), reason="data_features.csv belum dibuat (Tahap 2)")
def test_eda_tabel_dan_interpretasi_lengkap():
    from umkm import eda
    from umkm.eda_teks import interpretasi, temuan

    df = pd.read_csv(_FEAT)
    clean = pd.read_csv(config.path("processed") / "data_clean.csv")
    t = eda.build_tables(df, clean, eda.batas_dari_data(df, clean))
    assert t["profil_platform"]["n_semua_149"].max() <= len(df)
    assert set(t["sebelum_sesudah"]["sampel"]) == {"utama", "semua_149"}
    # 4 strategi x 4 ukuran kinerja x 2 sampel
    assert len(t["spearman_kinerja"]) == 32
    interp = interpretasi(t, df)
    assert all(isinstance(v, str) and v for v in interp.values())
    assert 5 <= len(temuan(t, df)) <= 8
    # bahasa sebab-akibat tidak boleh muncul sebagai klaim
    teks = " ".join([*interp.values(), *temuan(t, df)]).lower()
    for kata in ("menyebabkan", "berdampak", "mengakibatkan"):
        assert kata not in teks
