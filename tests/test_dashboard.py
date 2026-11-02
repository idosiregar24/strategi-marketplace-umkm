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


def test_tahap_dari_progress():
    t = db.tahap_dari_progress(PROGRESS)
    assert [(x["n"], x["status"]) for x in t] == [(1, "done"), (3, "wait"), (4, "todo")]
    assert t[0]["keluaran"] == ["data/processed/data_clean.csv", "reports/cleaning_log.md"]
    assert t[0]["selesai"] == "2026-10-14" and t[1]["selesai"] == ""


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


@pytest.mark.skipif(not _FEAT.exists(), reason="data_features.csv belum dibuat")
def test_bangun_data_memuat_hasil_random_forest():
    h = db.bangun_data()["hasil"]
    imp = h["rf_importance"]
    assert len(imp) == 8 and {d["jenis"] for d in imp} == {"strategi", "profil"}
    assert imp == sorted(imp, key=lambda d: -d["mean"])
    assert set(h["rf_confusion"]) == {"tn", "fp", "fn", "tp"}
    assert {s["segmen"] for s in h["segmen"]} >= {"1", "2", "Semua"}


_MODEL = config.path("models")


@pytest.mark.skipif(not (_MODEL / "v1" / "model.joblib").exists(), reason="artefak model belum ada")
def test_simulasi_menambah_peluang_rf_tanpa_mengubah_kontrak():
    profil = {
        "omzet_bulanan": 15_000_000,
        "lama_usaha_pra_mp": 2.5,
        "lama_di_mp": 1.5,
        "platform": ["gofood", "shopee"],
        "x1_unggah": 2.5,
        "x2_promosi": 2.5,
        "x3_komunikasi": 3.0,
        "x4_konsistensi": 3.0,
    }
    out = db.simulasi(profil)
    il = out.pop("ilustrasi_model")
    assert 0 <= il["peluang_naik_persen"] <= 100
    assert set(il["selisih_plus1_pp"]) == {
        "x1_unggah",
        "x2_promosi",
        "x3_komunikasi",
        "x4_konsistensi",
    }
    from umkm.recommend import recommend

    assert out == recommend(profil)


@pytest.mark.skipif(not _FEAT.exists(), reason="data_features.csv belum dibuat")
def test_bangun_data_memuat_rangkuman_aktivitas():
    d = db.bangun_data()
    akt = d["aktivitas"]
    assert akt["n_tabel"] > 0 and akt["n_figur"] > 0
    assert "keputusan_terbuka" not in d
    sem = d["hasil"].get("sem")
    if sem is not None:
        assert {j["model"] for j in sem["jalur"]} == {"y_obj", "naik_penjualan", "persepsi"}
    if d["model"] is not None:
        assert d["model"]["nama"] == "random_forest" and d["model"]["n_latih"] > 0


def test_keluaran_hilang_dan_siapkan_tanpa_data_mentah(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("UMKM_BASE_DIR", str(tmp_path))
    hilang = db.keluaran_hilang()
    assert any("data_features.csv" in h for h in hilang) and any(
        "model_meta.json" in h for h in hilang
    )
    db.siapkan()  # data mentah tidak ada: hanya peringatan, pipeline tidak dijalankan
    assert "Peringatan" in capsys.readouterr().out


@pytest.mark.skipif(not _FEAT.exists(), reason="data_features.csv belum dibuat")
def test_ekspor_situs_statis(tmp_path):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "usang.png").write_bytes(b"x")
    out = db.ekspor(tmp_path / ".", pipeline=False)
    data = json.loads((out / "data.json").read_text(encoding="utf-8"))
    assert data["statis"] and data["hasil"]
    assert "keputusan_terbuka" not in data
    assert (out / "index.html").read_bytes() == db.STATIC.read_bytes()
    assert sorted(p.name for p in (out / "figures").glob("*.png")) == data["figur"]
    assert (out / ".nojekyll").exists()
