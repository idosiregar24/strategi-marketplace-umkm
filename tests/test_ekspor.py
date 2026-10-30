import pandas as pd
import pytest

from umkm import config
from umkm import ekspor as ek


@pytest.mark.parametrize(
    "kolom, harus_memuat",
    [
        ("x2_promosi_2", "iklan berbayar"),
        ("y_persepsi_8", "kontribusi marketplace"),
        ("x3_komunikasi", "rata-rata butir"),
        ("mp_tiktok", "TikTok Shop"),
        ("omzet_sesudah_w", "persentil 99"),
        ("trx_sebelum_raw", "isian asli"),
        ("flag_winsor_trx_sesudah", "trx_sesudah"),
        ("naik_penjualan", "TARGET UTAMA"),
    ],
)
def test_keterangan_pola_kolom(kolom, harus_memuat):
    assert harus_memuat in ek.keterangan(kolom)


def test_keterangan_kolom_tak_dikenal_kosong():
    assert ek.keterangan("kolom_baru_xyz") == ""


_PROC = config.path("processed")


@pytest.mark.skipif(not (_PROC / "data_features.csv").exists(), reason="data belum dibuat")
def test_ekspor_tanpa_nama_usaha_dan_kamus_lengkap(tmp_path):
    out = ek.ekspor_xlsx(tmp_path / "x.xlsx")
    sheets = pd.read_excel(out, sheet_name=None)
    assert set(sheets) == {
        "Petunjuk",
        "Data terkoreksi",
        "Catatan koreksi",
        "Data bersih",
        "Data siap analisis",
        "Kamus data",
    }
    assert not any("nama_usaha" in df.columns for df in sheets.values())
    assert sheets["Kamus data"]["Keterangan"].notna().all()
    assert len(sheets["Data bersih"]) == len(sheets["Data siap analisis"]) == 149
    assert len(sheets["Data terkoreksi"]) == 149
    kolom_final = set(sheets["Data terkoreksi"].columns) - {"platform_raw"}
    assert not any(c.endswith(("_raw", "_w")) for c in kolom_final)


def test_tabel_koreksi_gabung_koreksi_dan_trx_kosong():
    clean = pd.DataFrame(
        {
            "id_responden": ["R001", "R002"],
            "omzet_sesudah": [90.0, 5.0],
            "omzet_sesudah_raw": ["9", "5"],
            "trx_sebelum": [float("nan"), 3.0],
            "trx_sebelum_raw": ["2.5", "3"],
            "trx_sesudah": [float("nan"), 4.0],
            "trx_sesudah_raw": ["540", "4"],
            "flag_trx_dikosongkan": [1, 0],
            "flag_trx_pecahan": [1, 0],
        }
    )
    koreksi = [
        {"id": "R001", "kolom": "omzet_sesudah", "keterangan": "kurang nol"},
        {"id": "R001", "kolom": "trx_sesudah", "keterangan": "dikonfirmasi"},
    ]
    t = ek.tabel_koreksi(clean, koreksi).set_index("kolom")
    assert len(t) == 3 and set(t["id_responden"]) == {"R001"}
    assert t.at["omzet_sesudah", "nilai_dipakai"] == 90
    assert t.at["trx_sebelum", "nilai_dipakai"] == "kosong"
    assert t.at["trx_sesudah", "keterangan"] == "dikonfirmasi"
    assert "pecahan" in t.at["trx_sebelum", "keterangan"]
