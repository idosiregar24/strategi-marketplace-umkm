import json

import pytest

from umkm import config
from umkm import dashboard as db

PROGRESS = """
| Tahap | Nama | Status | Keluaran utama | Selesai pada |
|---|---|---|---|---|
| 1 | Cleaning | SELESAI | data/processed/data_clean.csv, reports/cleaning_log.md | 2026-10-14 |
| 3 | EDA | MENUNGGU PERSETUJUAN | reports/figures/eda_* | |
| 4 | Analisis pengaruh | BELUM | reports/tables/pengaruh_*.csv | |
"""

DECISIONS = """
| ID | Topik | Keputusan | Status | Tanggal |
|---|---|---|---|---|
| D01 | Tujuan | Opsi a | DISEPAKATI | 2026-10-13 |
| D08 | SEM | Opsional | BELUM DISEPAKATI | |
| D23 | Konvensi | Holm | DIUSULKAN | 2026-10-14 |
"""


def test_tahap_dari_progress():
    t = db.tahap_dari_progress(PROGRESS)
    assert [(x["n"], x["status"]) for x in t] == [(1, "done"), (3, "wait"), (4, "todo")]
    assert t[0]["keluaran"] == ["data/processed/data_clean.csv", "reports/cleaning_log.md"]
    assert t[0]["selesai"] == "2026-10-14" and t[1]["selesai"] == ""


def test_keputusan_terbuka_hanya_yang_belum_final():
    k = db.keputusan_terbuka(DECISIONS)
    assert [x["id"] for x in k] == ["D08", "D23"]


@pytest.mark.parametrize("nama", ["../config.yaml", "..%2Fx.png", "a/b.png", "x.csv", ""])
def test_figur_aman_menolak_nama_tidak_valid(nama):
    assert db.figur_aman(nama) is None


def test_bersih_nan_menjadi_none():
    out = db._bersih({"a": float("nan"), "b": [1.0, float("inf")]})
    assert out == {"a": None, "b": [1.0, None]}


_FEAT = config.path("processed") / "data_features.csv"


@pytest.mark.skipif(not _FEAT.exists(), reason="data_features.csv belum dibuat")
def test_bangun_data_valid_json_tanpa_data_per_responden():
    data = db.bangun_data()
    teks = json.dumps(data, allow_nan=False)
    assert "id_responden" not in teks and "R001" not in teks
    assert data["tahap"] and data["hasil"]["angka"]["n_semua"] == 149
