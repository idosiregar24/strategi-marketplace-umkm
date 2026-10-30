import numpy as np
import pandas as pd
import pytest

from umkm import cleaning as cl


@pytest.mark.parametrize(
    "value, expected",
    [
        ("3.500.000", 3_500_000),
        ("100.000.000", 100_000_000),
        ("60000000", 60_000_000),
        (60000000.0, 60_000_000),
        ("Rp 1.500.000", 1_500_000),
        ("2.65", 2.65),
        ("2,5", 2.5),
        (0, 0),
    ],
)
def test_parse_angka(value, expected):
    assert cl.parse_angka(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", [None, np.nan, "", "tidak tahu", "3,5 juta"])
def test_parse_angka_tak_terbaca(value):
    assert np.isnan(cl.parse_angka(value))


@pytest.mark.parametrize(
    "value, expected",
    [
        ("3 bulan", (0.25, 0)),
        ("1 Bulan", (1 / 12, 0)),
        (2018, (8.0, 1)),
        ("2023", (3.0, 1)),
        (5.0, (5.0, 0)),
        ("4 tahun", (4.0, 0)),
        (0, (0.0, 0)),
    ],
)
def test_parse_lama(value, expected):
    tahun, flag = cl.parse_lama(value, 2026)
    assert tahun == pytest.approx(expected[0])
    assert flag == expected[1]


def test_parse_lama_kosong():
    tahun, flag = cl.parse_lama(None, 2026)
    assert np.isnan(tahun) and flag == 0


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1.Tidak Pernah", (1.0, "tidak pernah")),
        ("1. Tidak Pernah", (1.0, "tidak pernah")),
        ("3. Cukup Sering Memanfaatkan", (3.0, "cukup sering memanfaatkan")),
        ("2.Tidak  Setuju", (2.0, "tidak setuju")),
        ("  5. Sangat Konsisten", (5.0, "sangat konsisten")),
    ],
)
def test_parse_likert(value, expected):
    assert cl.parse_likert(value) == expected


def test_parse_likert_kosong():
    num, label = cl.parse_likert(None)
    assert np.isnan(num) and label == ""


def test_parse_platform():
    flags = cl.parse_platform("GoFood (Gojek), GrabFood (Grab), Shopee, MaximFood (Maxim)")
    assert flags == {
        "mp_gofood": 1,
        "mp_grabfood": 1,
        "mp_shopee": 1,
        "mp_maxim": 1,
        "mp_tiktok": 0,
    }
    assert cl.parse_platform("TikTok Shop")["mp_tiktok"] == 1
    assert cl.unknown_platforms("Shopee, Tokopedia") == ["Tokopedia"]


def test_audit_label_tidak_cocok():
    benar = {c: [f"3. {cl.EXPECTED_LABELS[cl.likert_block(c)][3].title()}"] for c in cl.LIKERT_COLS}
    df = pd.DataFrame(benar)
    df["x4_konsistensi_1"] = ["2. Sangat Tidak Konsisten"]
    df["x1_unggah_4"] = ["1.Tidak Pernah"]
    out, mm = cl.parse_likert_columns(df)
    assert out.loc[0, "x4_konsistensi_1"] == 2
    assert out.loc[0, "x1_unggah_4"] == 1
    assert mm["kolom"].tolist() == ["x4_konsistensi_1"]


def test_winsor_gabungan_menjaga_nilai_sama():
    df = pd.DataFrame(
        {
            "omzet_sebelum": [1.0, 2.0, 3.0, 4.0, 1000.0],
            "omzet_sesudah": [1.0, 2.0, 3.0, 5.0, 1000.0],
            "trx_sebelum": [10.0, 20.0, 30.0, 40.0, 50.0],
            "trx_sesudah": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )
    wb = cl.fit_winsor_bounds(df, 0.01, 0.8)
    out = cl.apply_winsor(df, wb)
    assert out.loc[4, "omzet_sebelum_w"] == out.loc[4, "omzet_sesudah_w"]
    assert out.loc[4, "omzet_sebelum_w"] < 1000
    assert out.loc[4, "flag_outlier"] == 1


def test_winsor_tanpa_ekor_bawah_menjaga_nol():
    df = pd.DataFrame(
        {
            "omzet_sebelum": [0.0, 2.0, 3.0, 4.0, 1000.0],
            "omzet_sesudah": [5.0, 2.0, 3.0, 5.0, 1000.0],
            "trx_sebelum": [0.0, 20.0, 30.0, 40.0, 50.0],
            "trx_sesudah": [2.5, 20.0, 30.0, 40.0, 50.0],
        }
    )
    out = cl.apply_winsor(df, cl.fit_winsor_bounds(df, None, 0.8))
    assert out.loc[0, "omzet_sebelum_w"] == 0
    assert out.loc[0, "trx_sesudah_w"] == 2.5
    assert out.loc[4, "omzet_sebelum_w"] < 1000


def test_parse_timestamp_serial_dan_datetime():
    import datetime as dt

    expected = pd.Timestamp("2026-09-20 13:39:34")
    for series in (
        pd.Series([46285.56914], dtype=object),
        pd.Series([dt.datetime(2026, 9, 20, 13, 39, 34)], dtype=object),
        pd.Series(["2026-09-20 13:39:34"], dtype=object),
    ):
        out = cl.parse_timestamp(series)
        assert abs(out.iloc[0] - expected) < pd.Timedelta(seconds=1)


def test_flag_trx_tidak_wajar():
    df = pd.DataFrame(
        {
            "omzet_sebelum": [3e7, 5e6, 1e6],
            "omzet_sesudah": [3e7, 5e6, 1e6],
            "trx_sebelum": [3e7, 2.5, 300],
            "trx_sesudah": [300, 3.0, 300],
        }
    )
    out = cl.flag_trx_tidak_wajar(df, 100_000)
    assert out["flag_trx_tidak_wajar"].tolist() == [1, 0, 0]
    assert out["flag_trx_pecahan"].tolist() == [0, 1, 0]


def test_apply_koreksi():
    df = pd.DataFrame(
        {
            "id_responden": ["R001", "R002"],
            "nama_usaha": ["Warung A", "Toko B"],
            "omzet_sesudah": [9_000_000.0, 5_000_000.0],
        }
    )
    koreksi = [{"id": "R001", "nama_usaha": "warung a ", "kolom": "omzet_sesudah", "nilai": 9e7}]
    out, log = cl.apply_koreksi(df, koreksi)
    assert out["omzet_sesudah"].tolist() == [90_000_000, 5_000_000]
    assert out["flag_dikoreksi"].tolist() == [1, 0]
    assert log.loc[0, "nilai_lama"] == 9_000_000
    assert df.at[0, "omzet_sesudah"] == 9_000_000  # masukan tidak diubah


@pytest.mark.parametrize(
    "entri",
    [
        {"id": "R001", "nama_usaha": "Toko B", "kolom": "omzet_sesudah", "nilai": 1},
        {"id": "R009", "nama_usaha": "Warung A", "kolom": "omzet_sesudah", "nilai": 1},
        {"id": "R001", "nama_usaha": "Warung A", "kolom": "x1_unggah_1", "nilai": 1},
    ],
)
def test_apply_koreksi_menolak_entri_salah(entri):
    df = pd.DataFrame(
        {"id_responden": ["R001"], "nama_usaha": ["Warung A"], "omzet_sesudah": [1.0]}
    )
    with pytest.raises(ValueError):
        cl.apply_koreksi(df, [entri])
