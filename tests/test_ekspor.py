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
    assert set(sheets) == {"Petunjuk", "Data bersih", "Data siap analisis", "Kamus data"}
    assert not any("nama_usaha" in df.columns for df in sheets.values())
    assert sheets["Kamus data"]["Keterangan"].notna().all()
    assert len(sheets["Data bersih"]) == len(sheets["Data siap analisis"]) == 149
