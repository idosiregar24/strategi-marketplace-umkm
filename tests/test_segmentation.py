import numpy as np
import pandas as pd
import pytest

from umkm import segmentation as sg
from umkm import stats


@pytest.fixture
def dua_kelompok():
    """Dua kelompok terpisah jelas: 40 UMKM kecil/baru dan 25 UMKM besar/lama."""
    rng = np.random.default_rng(42)
    kecil = pd.DataFrame(
        {
            "skala_omzet": rng.choice(["Q1_kecil", "Q2_menengah_bawah"], 40),
            "lama_usaha_pra_mp": rng.integers(0, 2, 40),
            "lama_di_mp": rng.integers(1, 3, 40),
            "jumlah_platform": rng.integers(1, 3, 40),
        }
    )
    besar = pd.DataFrame(
        {
            "skala_omzet": ["Q4_besar"] * 25,
            "lama_usaha_pra_mp": rng.integers(10, 20, 25),
            "lama_di_mp": rng.integers(8, 12, 25),
            "jumlah_platform": rng.integers(3, 5, 25),
        }
    )
    return pd.concat([besar, kecil], ignore_index=True)  # kelompok besar di depan


FITUR = ["skala_omzet_ord", "lama_usaha_pra_mp", "lama_di_mp", "jumlah_platform"]
LOG = ["lama_usaha_pra_mp", "lama_di_mp"]


def test_skala_ordinal():
    s = sg.skala_ordinal(pd.Series(["Q1_kecil", "Q4_besar", "Q3_menengah_atas"]))
    assert s.tolist() == [1.0, 4.0, 3.0]
    with pytest.raises(ValueError):
        sg.skala_ordinal(pd.Series(["Q5"]))


def test_siapkan_fitur_satu_baris_dan_log1p():
    baris = pd.DataFrame(
        [
            {
                "skala_omzet": "Q2_menengah_bawah",
                "lama_usaha_pra_mp": 0,
                "lama_di_mp": 3,
                "jumlah_platform": 2,
            }
        ]
    )
    x = sg.siapkan_fitur(baris, FITUR, LOG)
    assert list(x.columns) == FITUR
    assert x.iloc[0].tolist() == pytest.approx([2.0, 0.0, np.log1p(3), 2.0])


def test_segmen_terurut_dan_konsisten_untuk_data_baru(dua_kelompok):
    x = sg.siapkan_fitur(dua_kelompok, FITUR, LOG)
    pipa = sg.pipa_kmeans(2, n_init=10).fit(x)
    seg = sg.tetapkan_segmen(pipa, x, sg.urutan_segmen(pipa))
    # segmen 1 = kelompok kecil/baru walau barisnya di belakang
    assert (seg.iloc[25:] == 1).all() and (seg.iloc[:25] == 2).all()
    baru = sg.siapkan_fitur(dua_kelompok.iloc[[0, 30]], FITUR, LOG)
    assert sg.tetapkan_segmen(pipa, baru, sg.urutan_segmen(pipa)).tolist() == [2, 1]


def test_stabilitas_kelompok_terpisah_mendekati_satu(dua_kelompok):
    x = sg.siapkan_fitur(dua_kelompok, FITUR, LOG)
    lab = sg.pipa_kmeans(2, n_init=10).fit(x).predict(x)
    ari, jac = sg.stabilitas_bootstrap(x, 2, lab, n_boot=10, n_init=5)
    assert ari.min() > 0.95 and jac.shape == (10, 2) and jac.min() > 0.95


def _metrik(sil, ari, ukuran):
    return pd.DataFrame(
        {"k": [2, 3, 4], "silhouette": sil, "ari_boot_median": ari, "ukuran_min": ukuran}
    )


def test_pilih_k_stabil_lalu_silhouette():
    m = _metrik([0.20, 0.30, 0.40], [0.9, 0.7, 0.5], [50, 30, 20])
    assert sg.pilih_k(m, 15, 0.6) == (3, "stabil")  # k=4 silhouette tertinggi tapi tidak stabil


def test_pilih_k_cadangan_dan_ukuran_minimum():
    m = _metrik([0.20, 0.30, 0.40], [0.4, 0.5, 0.5], [50, 30, 10])
    assert sg.pilih_k(m, 15, 0.6) == (3, "cadangan_tidak_stabil")  # k=4 klaster < 15
    with pytest.raises(ValueError):
        sg.pilih_k(m, 100, 0.6)


def test_nama_segmen_deskriptor_dan_kembar():
    zp = pd.DataFrame(
        {
            "skala_omzet_ord": [-0.8, 0.0, 0.9, 0.9],
            "lama_usaha_pra_mp": [-0.5, 0.1, 0.6, 0.6],
            "lama_di_mp": [0.0, 0.0, 0.0, 0.0],
            "jumlah_platform": [0.0, 0.0, 0.4, 0.4],
        },
        index=[1, 2, 3, 4],
    )
    nama = sg.nama_segmen(zp, 0.25)
    assert nama[1] == "Omzet kecil, usaha muda"
    assert nama[2] == "Omzet menengah"
    assert nama[3] == "Omzet besar, usaha mapan, banyak platform (3)"
    assert nama[4].endswith("(4)")


def test_kruskal_eps_dan_chi2_cramer():
    a, b = pd.Series([1, 2, 3, 4, 5.0]), pd.Series([6, 7, 8, 9, 10.0])
    r = stats.kruskal_eps([a, b])
    assert r["n"] == 10 and r["efek"] == pytest.approx(r["H"] / 9) and r["p"] < 0.05
    x = pd.Series([1] * 10 + [2] * 10)
    y = pd.Series([1] * 10 + [0] * 10)
    c = stats.chi2_cramer(x, y)
    assert c["uji"] == "Fisher" and c["efek"] == pytest.approx(1.0)
