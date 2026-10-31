import copy
import json

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from umkm import config
from umkm import recommend as rc
from umkm import rekomendasi as rk
from umkm import segmentation as sg
from umkm.cleaning import PLATFORM_COLS
from umkm.features import batas_skala_omzet, skala_omzet

STRATEGI = rc.STRATEGI


def test_hitung_prioritas_gap_dipotong_dan_peringkat():
    skor = pd.Series([2.0, 3.0, 3.0, 4.5], index=STRATEGI)
    acuan = pd.Series([2.5, 2.8, 3.6, 4.0], index=STRATEGI)
    bobot = pd.Series([0.6, 0.3, 1.0, 0.1], index=STRATEGI)
    t = rc.hitung_prioritas(skor, acuan, bobot, n=3)
    assert t["gap"].tolist() == pytest.approx([0.5, 0.0, 0.6, 0.0])
    assert t["prioritas"].tolist() == pytest.approx([0.3, 0.0, 0.6, 0.0])
    # hanya prioritas > 0 yang diberi peringkat
    assert t["peringkat"].tolist() == [2, 0, 1, 0]


def test_hitung_prioritas_seri_dipecah_bobot_dan_galat_float():
    skor = pd.Series([2.0, 2.0, 3.0, 3.0], index=STRATEGI)
    acuan = pd.Series([2.5, 3.0, 3.0 + 1e-12, 3.25], index=STRATEGI)
    bobot = pd.Series([0.4, 0.2, 1.0, 0.8], index=STRATEGI)
    t = rc.hitung_prioritas(skor, acuan, bobot, n=3)
    assert t.at["x3_komunikasi", "gap"] == 0.0  # selisih 1e-12 bukan gap
    # x1, x2, x4 seri (prioritas 0,2); urutan menurut bobot: x4 (0,8) > x1 (0,4) > x2 (0,2)
    assert t["peringkat"].tolist() == [2, 3, 0, 1]


def test_benchmark_cadangan_bila_umkm_naik_sedikit():
    seg = pd.DataFrame({s: [4.0, 4.0] for s in STRATEGI})
    semua = pd.DataFrame({s: [2.0, 3.0, 4.0] for s in STRATEGI})
    bm, sumber = rc.benchmark(seg, semua, STRATEGI, min_naik=5)
    assert sumber == "semua" and bm.iloc[0] == pytest.approx(3.0)
    bm, sumber = rc.benchmark(semua, semua, STRATEGI, min_naik=3, ukuran="median")
    assert sumber == "segmen" and bm.iloc[0] == pytest.approx(3.0)


def test_fokus_butir_dan_teks_tindakan():
    gap = pd.Series({b: 0.1 for cols in rc.BUTIR_STRATEGI.values() for b in cols})
    gap["x3_komunikasi_4"], gap["x3_komunikasi_2"] = 0.3, 0.2
    fokus = rc.fokus_butir(gap, n=2)
    assert fokus["x3_komunikasi"] == ["x3_komunikasi_4", "x3_komunikasi_2"]
    assert fokus["x1_unggah"] == ["x1_unggah_1", "x1_unggah_2"]  # seri: urutan butir
    teks = rc.teks_tindakan("x3_komunikasi", fokus["x3_komunikasi"], "kecil")
    assert teks.startswith("Utamakan menanggapi keluhan")
    assert rc.KONTEKS_SEGMEN["x3_komunikasi"]["kecil"] in teks
    assert rc.teks_tindakan("x3_komunikasi", fokus["x3_komunikasi"], None).endswith("sopan.")


def test_alasan_tanpa_bahasa_kausal():
    r = pd.Series({"skor": 2.3, "benchmark": 2.5, "gap": 0.2, "bobot": 0.3})
    for umkm in (False, True):
        t = rc.teks_alasan(r, "x2_promosi", False, "1 (omzet kecil)", umkm=umkm)
        assert "belum meyakinkan" in t and "0,20 poin" in t
        for kata in ("menyebabkan", "meningkatkan penjualan", "berdampak", "pasti"):
            assert kata not in t


# ---------------------------------------------------------------------------
# Ujung ke ujung dengan data sintetis: bangun artefak lalu panggil recommend()
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def data_sintetis():
    """80 UMKM rekaan: dua kelompok profil, skor strategi lebih tinggi pada yang naik."""
    rng = np.random.default_rng(42)
    n = 80
    besar = np.arange(n) < 40
    omzet = np.where(besar, rng.uniform(25e6, 80e6, n), rng.uniform(2e6, 15e6, n))
    naik = rng.integers(0, 2, n)
    d = pd.DataFrame(
        {
            "id_responden": [f"S{i:03d}" for i in range(n)],
            "sampel_utama": (rng.random(n) > 0.15).astype(int),
            "naik_penjualan": naik,
            "flag_jawaban_seragam": (rng.random(n) > 0.95).astype(int),
            "log_omzet_sebelum": np.log1p(omzet),
            "lama_usaha_pra_mp": np.where(besar, rng.integers(4, 12, n), rng.integers(0, 2, n)),
            "lama_di_mp": np.where(besar, rng.integers(3, 8, n), rng.integers(1, 3, n)),
        }
    )
    plat = rng.random((n, len(PLATFORM_COLS))) > 0.5
    plat[:, 0] = True  # minimal satu platform
    for j, c in enumerate(PLATFORM_COLS):
        d[c] = plat[:, j].astype(int)
    d["jumlah_platform"] = d[PLATFORM_COLS].sum(axis=1)
    d["skala_omzet"] = skala_omzet(pd.Series(omzet), batas_skala_omzet(pd.Series(omzet)))
    for s, cols in rc.BUTIR_STRATEGI.items():
        dasar = 2.5 + 0.6 * naik if s in ("x1_unggah", "x3_komunikasi") else 2.8 + 0.1 * naik
        for b in cols:
            d[b] = np.clip(np.round(dasar + rng.normal(0, 0.8, n)), 1, 5)
        d[s] = d[cols].mean(axis=1)

    cfg = copy.deepcopy(config.load_config())
    cfg["bootstrap_n"] = 50
    cfg["segmentation"]["n_init"] = 10
    c = cfg["segmentation"]
    x = sg.siapkan_fitur(d, c["fitur"], c["fitur_log1p"])
    pipa = sg.pipa_kmeans(2, cfg["seed"], c["n_init"]).fit(x)
    d["segmen"] = sg.tetapkan_segmen(pipa, x, sg.urutan_segmen(pipa)).to_numpy()

    gab = pd.DataFrame(
        {
            "strategi": STRATEGI,
            "nama": [rc.NAMA_STRATEGI[s] for s in STRATEGI],
            "bobot_rekomendasi": [0.6, 0.3, 1.0, 0.1],
            "pengaruh": [0.6, 0.35, 1.0, 0.0],
            "n_koef": [0.9, 0.2, 1.0, 0.0],
            "p_koef_positif": [0.99, 0.8, 1.0, 0.4],
            "meyakinkan": [True, False, True, False],
            "or_logit": [2.0, 1.2, 2.5, 0.9],
            "p_logit": [0.01, 0.3, 0.001, 0.7],
            "peringkat": [2, 3, 1, 4],
        }
    )
    cv = pd.DataFrame(
        {
            "target": "naik_penjualan",
            "model": ["dummy_mayoritas", "logistik", "random_forest"],
            "metrik": "auc",
            "rata_rata": [0.5, 0.75, 0.7],
            "sd": [0.0, 0.1, 0.1],
            "n_lipatan": 25,
        }
    )
    return d, gab, cv, cfg


@pytest.fixture(scope="module")
def artefak(data_sintetis, tmp_path_factory):
    d, gab, cv, cfg = data_sintetis
    rep = rk.analisis(d, gab, cv, cfg, {"data_features.csv": "abc"})
    dir_model = tmp_path_factory.mktemp("models") / "v1"
    rc.simpan_artefak(dir_model, rep.artefak)
    rc.muat_artefak.cache_clear()
    return rep, dir_model


def test_artefak_lengkap_dan_model_terbaik(artefak):
    rep, dir_model = artefak
    assert sorted(p.name for p in dir_model.iterdir()) == sorted(rc.NAMA_BERKAS.values())
    meta = json.loads((dir_model / "model_meta.json").read_text("utf-8"))
    assert meta["model_terbaik"] == "logistik"  # AUC CV tertinggi, bukan dummy
    assert meta["seed"] == 42 and meta["hash_data_sha256"] == {"data_features.csv": "abc"}
    # tiap segmen punya paling banyak 3 rekomendasi berurutan
    for _, g in rep.tabel["per_segmen"].groupby("segmen"):
        assert g["peringkat"].tolist() == list(range(1, len(g) + 1)) and len(g) <= 3


def test_recommend_cocok_dengan_tabel(artefak, data_sintetis):
    rep, dir_model = artefak
    d = data_sintetis[0]
    kons, _ = rk.cek_konsistensi(rep.tabel["per_segmen"], d, dir_model)
    assert kons["cocok"].all()


def test_recommend_tiga_contoh(artefak):
    _, dir_model = artefak
    for p in rk.CONTOH:
        h = rc.recommend(p, dir_model)
        json.dumps(h)  # JSON-serializable
        assert h["id_umkm"] == p["id_umkm"] and len(h["skor"]) == 4
        assert [q["peringkat"] for q in h["prioritas"]] == list(range(1, len(h["prioritas"]) + 1))
        prio = [q["prioritas"] for q in h["prioritas"]]
        assert prio == sorted(prio, reverse=True) and all(v > 0 for v in prio)


def test_recommend_tanpa_prioritas_dan_peringatan_rentang(artefak):
    _, dir_model = artefak
    p = {**rk.CONTOH[0], "omzet_bulanan": 5e9, "platform": ["GoFood ", "gofood"]}
    p |= {s: 5.0 for s in STRATEGI}
    h = rc.recommend(p, dir_model)
    assert h["prioritas"] == []
    assert any("tidak ada strategi prioritas" in w for w in h["peringatan"])
    assert any(w.startswith("omzet_bulanan") for w in h["peringatan"])


@pytest.mark.parametrize(
    "ubah",
    [
        {"x1_unggah": 5.5},
        {"platform": []},
        {"platform": ["tokopedia"]},
        {"lama_di_mp": -1},
        {"omzet": 1},  # field tak dikenal
    ],
)
def test_recommend_menolak_masukan_tidak_sah(artefak, ubah):
    _, dir_model = artefak
    with pytest.raises(ValidationError):
        rc.recommend({**rk.CONTOH[0], **ubah}, dir_model)


def test_recommend_artefak_hilang(tmp_path):
    with pytest.raises(FileNotFoundError, match="--stage 6"):
        rc.recommend(rk.CONTOH[0], tmp_path)
