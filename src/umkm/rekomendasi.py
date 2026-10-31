"""Tahap 6: rekomendasi strategi per segmen, artefak inferensi, dan kontrak integrasi.

Membaca data_features.csv (skor dan butir strategi), data_segmen.csv (nomor segmen Tahap 5),
reports/tables/pengaruh_gabungan.csv (bobot, D26) dan pengaruh_cv_ringkas.csv (model terbaik).
Menulis reports/tables/rekomendasi_*.csv, reports/figures/rekomendasi_*.png, models/<versi>/,
reports/rekomendasi_log.md, rekomendasi_ringkas.md, dan integration_contract.md.

Rumus (D28): gap = max(0, rata-rata skor UMKM naik di segmen - rata-rata skor segmen);
prioritas = bobot x gap. Rekomendasi adalah prioritas berbasis asosiasi, bukan jaminan hasil.
"""

from __future__ import annotations

import hashlib
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as st

from umkm import models
from umkm import recommend as rc
from umkm import segmentation as sg
from umkm.features import batas_skala_omzet, skala_omzet

STRATEGI = rc.STRATEGI
SEMUA = "Semua"
KOL_BUTIR = [b for cols in rc.BUTIR_STRATEGI.values() for b in cols]
KODE = {s: rc.NAMA_STRATEGI[s].split()[0] for s in STRATEGI}  # "X1".."X4"
VARIAN = {
    "utama": "rata-rata vs rata-rata, bobot D26 (utama)",
    "bobot_sama": "bobot sama rata (1 untuk semua strategi)",
    "bobot_logit": "bobot dari koefisien logit saja",
    "skor_sampel_utama": "skor segmen hanya dari sampel utama",
    "tanpa_seragam": "tanpa jawaban seragam (D20)",
    "median_vs_median": "median UMKM naik vs median segmen",
    "median_vs_rata": "median UMKM naik vs rata-rata segmen (rumus plan awal)",
    "benchmark_semua": "benchmark dari semua UMKM naik (tanpa segmen)",
}
# Tiga profil contoh (rekaan, bukan responden); C = sketsa di backend_architecture.md
CONTOH = [
    {
        "id_umkm": "contoh_A_kecil_baru",
        "omzet_bulanan": 6_000_000,
        "lama_usaha_pra_mp": 1,
        "lama_di_mp": 1,
        "platform": ["gofood"],
        "x1_unggah": 2.0,
        "x2_promosi": 2.25,
        "x3_komunikasi": 3.0,
        "x4_konsistensi": 3.0,
    },
    {
        "id_umkm": "contoh_B_besar_mapan",
        "omzet_bulanan": 50_000_000,
        "lama_usaha_pra_mp": 8,
        "lama_di_mp": 5,
        "platform": ["gofood", "grabfood", "shopee"],
        "x1_unggah": 3.0,
        "x2_promosi": 2.0,
        "x3_komunikasi": 3.4,
        "x4_konsistensi": 3.6,
    },
    {
        "id_umkm": "contoh_C_sketsa_kontrak",
        "omzet_bulanan": 18_000_000,
        "lama_usaha_pra_mp": 3,
        "lama_di_mp": 2,
        "platform": ["gofood", "shopee"],
        "x1_unggah": 2.0,
        "x2_promosi": 2.5,
        "x3_komunikasi": 4.2,
        "x4_konsistensi": 3.0,
    },
]


# ---------------------------------------------------------------------------
# Data dan segmen
# ---------------------------------------------------------------------------
def siapkan_data(feat: pd.DataFrame, seg: pd.DataFrame) -> pd.DataFrame:
    """data_features (sudah memuat butir strategi) + nomor segmen dari data_segmen, per id."""
    d = feat.merge(seg[["id_responden", "segmen"]], on="id_responden", validate="1:1")
    if len(d) != len(feat) or d[KOL_BUTIR].isna().any().any():
        raise ValueError("Butir strategi atau segmen tidak lengkap untuk semua responden.")
    return d


def latih_segmen(d: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    """Latih ulang pipa Tahap 5 (fitur, k, seed sama) dan pastikan segmennya identik dengan
    data_segmen.csv. Mengembalikan artefak segmen + nama, konteks, dan batas skala omzet."""
    c = cfg["segmentation"]
    k = int(d["segmen"].nunique())
    x = sg.siapkan_fitur(d, c["fitur"], c["fitur_log1p"])
    pipa = sg.pipa_kmeans(k, cfg["seed"], c["n_init"]).fit(x)
    urutan = sg.urutan_segmen(pipa)
    segmen = sg.tetapkan_segmen(pipa, x, urutan)
    beda = int((segmen.to_numpy() != d["segmen"].to_numpy()).sum())
    if beda:
        raise ValueError(
            f"{beda} UMKM berbeda segmen dari data_segmen.csv; jalankan ulang Tahap 5."
        )
    zp = sg.z_pusat(x, segmen)
    omzet = np.expm1(d["log_omzet_sebelum"])
    batas = batas_skala_omzet(omzet)
    if not (skala_omzet(omzet, batas).to_numpy() == d["skala_omzet"].to_numpy()).all():
        raise ValueError("Batas kuartil omzet tidak mereproduksi skala_omzet di data_features.")
    return {
        "artefak": {
            "pipa": pipa,
            "urutan": urutan,
            "fitur": c["fitur"],
            "fitur_log1p": c["fitur_log1p"],
        },
        "nama": sg.nama_segmen(zp, c["batas_deskriptor"]),
        "konteks": {int(s): rc.konteks_segmen(zp.at[s, "skala_omzet_ord"]) for s in zp.index},
        "batas_skala": batas,
        "z_pusat": zp,
    }


def kelompok(d: pd.DataFrame) -> list[tuple[Any, pd.DataFrame]]:
    """(segmen, baris) untuk tiap segmen, lalu (Semua, seluruh baris)."""
    return [(int(s), g) for s, g in d.groupby("segmen")] + [(SEMUA, d)]


def _naik(g: pd.DataFrame) -> pd.Series:
    return (g["sampel_utama"] == 1) & (g["naik_penjualan"] == 1)


# ---------------------------------------------------------------------------
# Bobot, gap, prioritas
# ---------------------------------------------------------------------------
def tabel_bobot(gab: pd.DataFrame) -> pd.DataFrame:
    """Kolom Tahap 4 yang dipakai Tahap 6 (indeks = strategi)."""
    kol = ["nama", "bobot_rekomendasi", "pengaruh", "n_koef", "p_koef_positif", "meyakinkan"]
    kol += ["or_logit", "p_logit", "peringkat"]
    return (
        gab.set_index("strategi").loc[STRATEGI, kol].rename(columns={"bobot_rekomendasi": "bobot"})
    )


def tabel_gap(
    d: pd.DataFrame,
    bobot: pd.Series,
    r: dict[str, Any],
    ukuran_bm: str | None = None,
    ukuran_skor: str | None = None,
    skor_utama: bool = False,
    bm_semua: bool = False,
) -> pd.DataFrame:
    """Skor, benchmark, gap, prioritas, peringkat per kelompok x strategi (bentuk panjang).

    Benchmark dari UMKM naik di sampel utama (D14); skor dari semua anggota segmen (149, D27)
    kecuali `skor_utama`. `bm_semua` = benchmark seluruh UMKM naik untuk semua segmen.
    """
    ukuran_bm = ukuran_bm or r["ukuran_gap"]
    ukuran_skor = ukuran_skor or r["ukuran_gap"]
    naik_semua = d[_naik(d)]
    rows = []
    for key, g in kelompok(d):
        naik = naik_semua if bm_semua else g[_naik(g)]
        acuan, sumber = rc.benchmark(naik, naik_semua, STRATEGI, r["min_naik_benchmark"], ukuran_bm)
        dasar = g[g["sampel_utama"] == 1] if skor_utama else g
        skor = rc.agregat(dasar, STRATEGI, ukuran_skor)
        t = rc.hitung_prioritas(skor, acuan, bobot, r["n_prioritas"])
        t = t.assign(
            gap_mentah=acuan - skor,
            segmen=key,
            n=len(g),
            n_skor=len(dasar),
            n_naik=int(_naik(g).sum()),
            sumber_benchmark=sumber,
        )
        rows.append(t.rename_axis("strategi").reset_index())
    out = pd.concat(rows, ignore_index=True)
    return out[["segmen", "strategi", *[c for c in out.columns if c not in ("segmen", "strategi")]]]


def bootstrap_gap(
    d: pd.DataFrame, bobot: pd.Series, r: dict[str, Any], n_boot: int, seed: int = 42
) -> pd.DataFrame:
    """Bootstrap baris di dalam tiap kelompok: CI 95% gap mentah (benchmark - skor), peluang
    gap > 0, peluang peringkat 1, dan peluang masuk tiga besar (prioritas > 0). Bobot tetap."""
    rng = np.random.default_rng(seed)
    w = bobot.loc[STRATEGI].to_numpy()
    rows = []
    for key, g in kelompok(d):
        v = g[STRATEGI].to_numpy()
        naik = _naik(g).to_numpy()
        gaps = []
        for _ in range(n_boot):
            i = rng.integers(0, len(g), len(g))
            if naik[i].sum() < r["min_naik_benchmark"]:
                continue
            gaps.append(v[i][naik[i]].mean(axis=0) - v[i].mean(axis=0))
        gp = np.array(gaps)
        prio = np.where(gp > rc.TOLERANSI, gp, 0.0) * w
        rank = (-prio).argsort(axis=1, kind="stable").argsort(axis=1) + 1
        for j, s in enumerate(STRATEGI):
            positif = prio[:, j] > 0
            rows.append(
                {
                    "segmen": key,
                    "strategi": s,
                    "gap_ci_bawah": np.percentile(gp[:, j], 2.5),
                    "gap_ci_atas": np.percentile(gp[:, j], 97.5),
                    "p_gap_positif": positif.mean(),
                    "p_peringkat_1": (positif & (rank[:, j] == 1)).mean(),
                    "p_tiga_besar": (positif & (rank[:, j] <= r["n_prioritas"])).mean(),
                    "n_boot": len(gp),
                }
            )
    return pd.DataFrame(rows)


def tabel_butir(d: pd.DataFrame) -> pd.DataFrame:
    """Skor rata-rata tiap butir strategi: segmen vs UMKM naik di segmen yang sama."""
    rows = []
    for key, g in kelompok(d):
        bm, sk = g.loc[_naik(g), KOL_BUTIR].mean(), g[KOL_BUTIR].mean()
        for s, cols in rc.BUTIR_STRATEGI.items():
            for b in cols:
                rows.append(
                    {
                        "segmen": key,
                        "strategi": s,
                        "butir": b,
                        "tindakan": rc.TINDAKAN_BUTIR[b],
                        "skor": sk[b],
                        "benchmark": bm[b],
                        "gap": bm[b] - sk[b],
                    }
                )
    out = pd.DataFrame(rows)
    out["fokus"] = False
    for (key, s), g in out.groupby(["segmen", "strategi"], sort=False):
        out.loc[g.index, "peringkat_butir"] = (
            g["gap"].rank(ascending=False, method="first").astype(int)
        )
    return out


def fokus_per_kelompok(butir: pd.DataFrame, n: int) -> dict[Any, dict[str, list[str]]]:
    """Butir fokus (gap terbesar) per kelompok x strategi."""
    return {
        key: rc.fokus_butir(g.set_index("butir")["gap"], n)
        for key, g in butir.groupby("segmen", sort=False)
    }


def _urutan(t: pd.DataFrame) -> str:
    u = t[t["peringkat"] > 0].sort_values("peringkat")["strategi"]
    return " > ".join(KODE[s] for s in u) or "-"


def sensitivitas(
    d: pd.DataFrame, bob: pd.DataFrame, r: dict[str, Any], minimum: float
) -> pd.DataFrame:
    """Urutan prioritas tiap kelompok pada varian rumus, bobot, dan sampel; dibanding utama."""
    utama = bob["bobot"]
    varian = {
        "utama": (d, utama, {}),
        "bobot_sama": (d, pd.Series(1.0, index=STRATEGI), {}),
        "bobot_logit": (d, bob["n_koef"].clip(lower=minimum), {}),
        "skor_sampel_utama": (d, utama, {"skor_utama": True}),
        "tanpa_seragam": (d[d["flag_jawaban_seragam"] == 0], utama, {}),
        "median_vs_median": (d, utama, {"ukuran_bm": "median", "ukuran_skor": "median"}),
        "median_vs_rata": (d, utama, {"ukuran_bm": "median", "ukuran_skor": "rata_rata"}),
        "benchmark_semua": (d, utama, {"bm_semua": True}),
    }
    ref = tabel_gap(d, utama, r)
    rows = []
    for nm, (data, w, kw) in varian.items():
        t = tabel_gap(data, w, r, **kw)
        for key, g in t.groupby("segmen", sort=False):
            g0 = ref[ref["segmen"] == key].set_index("strategi")
            g = g.set_index("strategi")
            rho = st.spearmanr(g.loc[STRATEGI, "prioritas"], g0.loc[STRATEGI, "prioritas"])[0]
            rows.append(
                {
                    "varian": nm,
                    "keterangan": VARIAN[nm],
                    "segmen": key,
                    "n": int(g["n"].iloc[0]),
                    "n_naik": int(g["n_naik"].iloc[0]),
                    "urutan": _urutan(g.reset_index()),
                    "n_prioritas": int((g["peringkat"] > 0).sum()),
                    "sama_dengan_utama": _urutan(g.reset_index()) == _urutan(g0.reset_index()),
                    "rho_vs_utama": rho,
                    **{f"prioritas_{KODE[s]}": g.at[s, "prioritas"] for s in STRATEGI},
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Model terbaik dan simulasi what-if
# ---------------------------------------------------------------------------
def pilih_model(cv_ringkas: pd.DataFrame, metrik: str = "auc") -> str:
    """Model non-dummy dengan rata-rata metrik CV tertinggi untuk naik_penjualan (Tahap 4)."""
    m = cv_ringkas[
        (cv_ringkas["target"] == "naik_penjualan")
        & (cv_ringkas["metrik"] == metrik)
        & ~cv_ringkas["model"].str.startswith("dummy")
    ]
    return str(m.loc[m["rata_rata"].idxmax(), "model"])


def latih_model(utama: pd.DataFrame, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Kandidat non-dummy Tahap 4 dilatih pada seluruh sampel utama (target naik_penjualan)."""
    c = cfg["influence"]
    fitur = c["strategi"] + c["kontrol"]
    kand = models.kandidat_klasifikasi(c["rf"], cfg["seed"])
    x, y = utama[fitur], utama["naik_penjualan"]
    return {nm: m.fit(x, y) for nm, m in kand.items() if not nm.startswith("dummy")}, fitur


def tabel_whatif(
    fitted: dict[str, Any], utama: pd.DataFrame, fitur: list[str], tambah: float
) -> pd.DataFrame:
    """Rata-rata selisih peluang prediksi (poin persen) bila satu strategi +`tambah` poin,
    per kelompok sampel utama x model x strategi."""
    rows = []
    for key, g in kelompok(utama):
        for nm, m in fitted.items():
            delta = rc.selisih_prediksi(m, g[fitur], STRATEGI, tambah)
            p0 = float(m.predict_proba(g[fitur])[:, 1].mean() * 100)
            rows += [
                {
                    "segmen": key,
                    "model": nm,
                    "strategi": s,
                    "n": len(g),
                    "peluang_dasar_persen": p0,
                    "selisih_pp": delta[s],
                    "persen_skor_sudah_5": float((g[s] >= 5).mean()),
                }
                for s in STRATEGI
            ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tabel rekomendasi dan artefak
# ---------------------------------------------------------------------------
def tabel_rekomendasi(
    gap: pd.DataFrame,
    boot: pd.DataFrame,
    whatif: pd.DataFrame,
    fokus: dict[Any, dict[str, list[str]]],
    seg: dict[str, Any],
    bob: pd.DataFrame,
) -> pd.DataFrame:
    """segmen | strategi prioritas 1-3 | angka | alasan | tindakan (plan/06 langkah 5)."""
    t = gap[gap["peringkat"] > 0].merge(boot, on=["segmen", "strategi"], how="left")
    t = t.merge(whatif[["segmen", "strategi", "selisih_pp"]], on=["segmen", "strategi"], how="left")
    rows = []
    for _, r in t.sort_values(["segmen", "peringkat"], key=lambda c: c.astype(str)).iterrows():
        key, s = r["segmen"], r["strategi"]
        semua = key == SEMUA
        meyakinkan = bool(bob.at[s, "meyakinkan"])
        butir = fokus[key][s]
        label = None if semua else rc.label_segmen(key, seg["nama"][key])
        rows.append(
            {
                "segmen": key,
                "nama_segmen": "Semua UMKM" if semua else seg["nama"][key],
                "peringkat": int(r["peringkat"]),
                "strategi": s,
                "nama_strategi": rc.NAMA_STRATEGI[s],
                "skor_segmen": r["skor"],
                "benchmark": r["benchmark"],
                "gap": r["gap"],
                "bobot": r["bobot"],
                "prioritas": r["prioritas"],
                "gap_ci_bawah": r["gap_ci_bawah"],
                "gap_ci_atas": r["gap_ci_atas"],
                "p_gap_positif": r["p_gap_positif"],
                "p_tiga_besar": r["p_tiga_besar"],
                "hubungan_meyakinkan": meyakinkan,
                "selisih_prediksi_plus1_pp": r["selisih_pp"],
                "fokus_butir": "; ".join(butir),
                "alasan": rc.teks_alasan(r, s, meyakinkan, label),
                "tindakan": rc.teks_tindakan(s, butir, None if semua else seg["konteks"][key]),
                "n": int(r["n"]),
                "n_naik": int(r["n_naik"]),
                "sumber_benchmark": r["sumber_benchmark"],
            }
        )
    return pd.DataFrame(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _versi_pustaka() -> dict[str, str]:
    import joblib
    import pydantic
    import sklearn

    return {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit-learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "pydantic": pydantic.__version__,
    }


def bangun_artefak(
    d: pd.DataFrame,
    seg: dict[str, Any],
    gap: pd.DataFrame,
    fokus: dict[Any, dict[str, list[str]]],
    bob: pd.DataFrame,
    model: Any,
    nama_model: str,
    fitur_model: list[str],
    cv_ringkas: pd.DataFrame,
    cfg: dict[str, Any],
    hash_data: dict[str, str],
) -> dict[str, Any]:
    """Isi lima artefak models/<versi>/ (lihat backend_architecture.md, Kesiapan Integrasi)."""
    r = cfg["recommendation"]
    utama = d[d["sampel_utama"] == 1]

    def blok(key: Any) -> dict[str, Any]:
        g = gap[gap["segmen"] == key].set_index("strategi").loc[STRATEGI]
        anggota = d if key == SEMUA else d[d["segmen"] == key]
        naik = anggota[_naik(anggota)]
        out = {
            "n": int(g["n"].iloc[0]),
            "n_sampel_utama": int((anggota["sampel_utama"] == 1).sum()),
            "n_naik": int(g["n_naik"].iloc[0]),
            "sumber_benchmark": str(g["sumber_benchmark"].iloc[0]),
            "benchmark": {s: float(g.at[s, "benchmark"]) for s in STRATEGI},
            "skor_rata": {s: float(g.at[s, "skor"]) for s in STRATEGI},
            "benchmark_median": {s: float(naik[s].median()) for s in STRATEGI},
            "fokus_butir": fokus[key],
        }
        if key != SEMUA:
            out = {"nama": seg["nama"][key], "konteks": seg["konteks"][key], **out}
        return out

    cv = cv_ringkas[cv_ringkas["target"] == "naik_penjualan"]
    metrik_cv = {
        m: {
            r_["metrik"]: {"rata_rata": float(r_["rata_rata"]), "sd": float(r_["sd"])}
            for _, r_ in g.iterrows()
        }
        for m, g in cv.groupby("model", sort=False)
    }
    omzet = np.expm1(d["log_omzet_sebelum"])
    return {
        "segmen": seg["artefak"],
        "model": {
            "model": model,
            "nama": nama_model,
            "fitur": fitur_model,
            "target": "naik_penjualan",
        },
        "benchmark": {
            "versi_model": r["versi_model"],
            "ukuran_gap": r["ukuran_gap"],
            "n_prioritas": r["n_prioritas"],
            "min_naik_benchmark": r["min_naik_benchmark"],
            "batas_skala_omzet": seg["batas_skala"],
            "segmen": {str(s): blok(s) for s in sorted(seg["nama"])},
            "semua": blok(SEMUA),
        },
        "pengaruh": {
            "sumber": "reports/tables/pengaruh_gabungan.csv (Tahap 4, D26)",
            "target": "naik_penjualan",
            "rumus_bobot": "pengaruh gabungan x p_koef_positif, minimal bobot_minimum",
            "bobot_minimum": cfg["influence"]["bobot_minimum"],
            "strategi": {
                s: {
                    "nama": rc.NAMA_STRATEGI[s],
                    "bobot": float(bob.at[s, "bobot"]),
                    "pengaruh": float(bob.at[s, "pengaruh"]),
                    "p_koef_positif": float(bob.at[s, "p_koef_positif"]),
                    "meyakinkan": bool(bob.at[s, "meyakinkan"]),
                    "or_logit": float(bob.at[s, "or_logit"]),
                    "p_logit": float(bob.at[s, "p_logit"]),
                    "peringkat": int(bob.at[s, "peringkat"]),
                }
                for s in STRATEGI
            },
        },
        "meta": {
            "versi_model": r["versi_model"],
            "dibuat": pd.Timestamp.now().isoformat(timespec="seconds"),
            "seed": cfg["seed"],
            "versi_pustaka": _versi_pustaka(),
            "n_responden": len(d),
            "k_segmen": len(seg["nama"]),
            "fitur_segmen": seg["artefak"]["fitur"],
            "fitur_segmen_log1p": seg["artefak"]["fitur_log1p"],
            "model_terbaik": nama_model,
            "fitur_model": fitur_model,
            "target_model": "naik_penjualan",
            "n_latih_model": len(utama),
            "n_naik_latih": int(utama["naik_penjualan"].sum()),
            "metrik_cv_naik_penjualan": metrik_cv,
            "skema_cv": f"RepeatedStratifiedKFold {cfg['cv']['n_splits']}x{cfg['cv']['n_repeats']}",
            "whatif_tambah": r["whatif_tambah"],
            "rentang_latih": {
                "omzet_bulanan": [float(omzet.min()), float(omzet.max())],
                "lama_usaha_pra_mp": [
                    float(d["lama_usaha_pra_mp"].min()),
                    float(d["lama_usaha_pra_mp"].max()),
                ],
                "lama_di_mp": [float(d["lama_di_mp"].min()), float(d["lama_di_mp"].max())],
                "jumlah_platform": [
                    float(d["jumlah_platform"].min()),
                    float(d["jumlah_platform"].max()),
                ],
            },
            "hash_data_sha256": hash_data,
            "keputusan": ["D14", "D26", "D27", "D28"],
        },
    }


# ---------------------------------------------------------------------------
# Contoh masukan dan pengecekan kecocokan recommend() dengan tabel
# ---------------------------------------------------------------------------
def profil_wakil(d: pd.DataFrame, key: int) -> dict[str, Any]:
    """Profil median segmen + skor rata-rata segmen (untuk mencocokkan recommend() dengan tabel).

    Platform = `jumlah_platform` median teratas menurut proporsi pemakaian di segmen.
    """
    g = d[d["segmen"] == key]
    n_plat = max(1, round(g["jumlah_platform"].median()))
    plat = g[[f"mp_{p}" for p in ("gofood", "grabfood", "shopee", "maxim", "tiktok")]].mean()
    return {
        "id_umkm": f"wakil_segmen_{key}",
        "omzet_bulanan": float(np.expm1(g["log_omzet_sebelum"]).median()),
        "lama_usaha_pra_mp": float(g["lama_usaha_pra_mp"].median()),
        "lama_di_mp": float(g["lama_di_mp"].median()),
        "platform": [
            c.removeprefix("mp_") for c in plat.sort_values(ascending=False).index[:n_plat]
        ],
        **{s: float(g[s].mean()) for s in STRATEGI},
    }


def cek_konsistensi(
    rek: pd.DataFrame, d: pd.DataFrame, dir_model: Path
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """recommend() pada profil wakil tiap segmen harus memberi segmen, urutan, dan angka
    prioritas yang sama dengan tabel rekomendasi_per_segmen."""
    rows, hasil = [], []
    for key in sorted(d["segmen"].unique()):
        p = profil_wakil(d, int(key))
        h = rc.recommend(p, dir_model)
        hasil.append({"masukan": p, "keluaran": h})
        t = rek[rek["segmen"] == key].sort_values("peringkat")
        urut_t = [KODE[s] for s in t["strategi"]]
        urut_r = [KODE[q["strategi"]] for q in h["prioritas"]]
        selisih = max(
            (abs(q["prioritas"] - v) for q, v in zip(h["prioritas"], t["prioritas"])), default=0.0
        )
        rows.append(
            {
                "segmen": int(key),
                "segmen_recommend": h["segmen"]["id"],
                "urutan_tabel": " > ".join(urut_t),
                "urutan_recommend": " > ".join(urut_r),
                "selisih_prioritas_maks": selisih,
                "cocok": h["segmen"]["id"] == key and urut_t == urut_r and selisih < 1e-3,
            }
        )
    return pd.DataFrame(rows), hasil


# ---------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------
@dataclass
class RekomendasiReport:
    """Tabel, info, artefak, contoh, dan path grafik Tahap 6."""

    tabel: dict[str, pd.DataFrame] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    artefak: dict[str, Any] = field(default_factory=dict)
    contoh: list[dict[str, Any]] = field(default_factory=list)
    grafik: dict[str, Any] = field(default_factory=dict)


def analisis(
    d: pd.DataFrame,
    gab: pd.DataFrame,
    cv_ringkas: pd.DataFrame,
    cfg: dict[str, Any],
    hash_data: dict[str, str] | None = None,
) -> RekomendasiReport:
    """Jalankan Tahap 6 (tanpa menulis berkas): tabel, artefak (belum disimpan), info."""
    r = cfg["recommendation"]
    rep = RekomendasiReport()
    t = rep.tabel
    seg = latih_segmen(d, cfg)
    bob = tabel_bobot(gab)

    t["gap"] = tabel_gap(d, bob["bobot"], r)
    t["bootstrap"] = bootstrap_gap(d, bob["bobot"], r, cfg["bootstrap_n"], cfg["seed"])
    t["butir"] = tabel_butir(d)
    fokus = fokus_per_kelompok(t["butir"], r["n_butir_fokus"])
    for key, per_s in fokus.items():
        for bs in per_s.values():
            t["butir"].loc[
                (t["butir"]["segmen"] == key) & t["butir"]["butir"].isin(bs), "fokus"
            ] = True
    t["sensitivitas"] = sensitivitas(d, bob, r, cfg["influence"]["bobot_minimum"])

    utama = d[d["sampel_utama"] == 1].reset_index(drop=True)
    fitted, fitur = latih_model(utama, cfg)
    terbaik = pilih_model(cv_ringkas)
    t["whatif"] = tabel_whatif(fitted, utama, fitur, r["whatif_tambah"])
    wf = t["whatif"][t["whatif"]["model"] == terbaik]
    t["per_segmen"] = tabel_rekomendasi(t["gap"], t["bootstrap"], wf, fokus, seg, bob)
    t["bobot"] = bob.reset_index()

    rep.artefak = bangun_artefak(
        d,
        seg,
        t["gap"],
        fokus,
        bob,
        fitted[terbaik],
        terbaik,
        fitur,
        cv_ringkas,
        cfg,
        hash_data or {},
    )
    rep.info = {
        "nama": seg["nama"],
        "konteks": seg["konteks"],
        "model_terbaik": terbaik,
        "fitur_model": fitur,
        "n": len(d),
        "n_utama": len(utama),
        "n_naik": int(utama["naik_penjualan"].sum()),
        "n_boot": cfg["bootstrap_n"],
        "z_pusat": seg["z_pusat"],
        "auc": cv_ringkas.query("target == 'naik_penjualan' and metrik == 'auc'")
        .set_index("model")["rata_rata"]
        .to_dict(),
    }
    return rep


def buat_grafik(rep: RekomendasiReport) -> dict[str, Any]:
    """Heatmap prioritas per kelompok x strategi dan gap dengan interval bootstrap."""
    from umkm import viz

    t = rep.tabel
    g = t["gap"]
    nama_kol = {
        **{
            s: f"Segmen {s}\n(n={int(g.loc[g['segmen'] == s, 'n'].iloc[0])})"
            for s in rep.info["nama"]
        },
        SEMUA: f"Semua UMKM\n(n={rep.info['n']})",
    }
    kol = [*sorted(rep.info["nama"]), SEMUA]
    # dibangun per kolom: pivot akan mengurutkan label campuran int/str dan gagal
    piv = pd.DataFrame(
        {k: g[g["segmen"] == k].set_index("strategi")["prioritas"] for k in kol}
    ).loc[STRATEGI]

    def anot(s: str, key: Any) -> str:
        r = g[(g["segmen"] == key) & (g["strategi"] == s)].iloc[0]
        urut = f"#{int(r['peringkat'])} " if r["peringkat"] > 0 else ""
        return f"{urut}{r['prioritas']:.3f}\ngap {r['gap']:.2f} x bobot {r['bobot']:.2f}".replace(
            ".", ","
        )

    anotasi = pd.DataFrame(
        [[anot(s, k) for k in kol] for s in STRATEGI], index=piv.index, columns=kol
    )
    piv.index = anotasi.index = [rc.NAMA_STRATEGI[s] for s in STRATEGI]
    piv.columns = anotasi.columns = [nama_kol[k] for k in kol]
    figs = {
        "rekomendasi_prioritas": viz.heatmap(
            piv,
            "Skor prioritas strategi per segmen",
            "Kelompok",
            "",
            subjudul="Prioritas = bobot (Tahap 4) x gap terhadap rata-rata UMKM yang naik di segmen "
            "yang sama; #n = peringkat",
            anotasi=anotasi,
            label_skala="skor prioritas",
        )
    }
    b = t["bootstrap"].merge(g[["segmen", "strategi", "gap_mentah"]], on=["segmen", "strategi"])
    b = b[b["segmen"] != SEMUA]
    label = [f"Segmen {k} · {rc.NAMA_STRATEGI[s]}" for k, s in zip(b["segmen"], b["strategi"])]
    meyakinkan = t["bobot"].set_index("strategi")["meyakinkan"]
    figs["rekomendasi_gap"] = viz.dot_ci(
        pd.Series(b["gap_mentah"].to_numpy(), index=label),
        b["gap_ci_bawah"],
        b["gap_ci_atas"],
        "Selisih skor segmen dari UMKM yang penjualannya naik",
        "Gap (poin skala 1-5; positif = segmen di bawah UMKM yang naik)",
        subjudul=f"Titik = gap; garis = interval bootstrap 95% ({rep.info['n_boot']}x); biru = "
        "hubungan strategi meyakinkan di Tahap 4",
        sorot=[bool(meyakinkan[s]) for s in b["strategi"]],
        referensi=0.0,
        teks_tambahan=[f"P(gap > 0) {p:.0%}" for p in b["p_gap_positif"]],
    )
    return figs


def run(cfg: dict[str, Any] | None = None) -> RekomendasiReport:
    """Baca keluaran Tahap 2-5, jalankan Tahap 6, tulis tabel, grafik, artefak, log, kontrak."""
    from umkm import config, io, viz
    from umkm.rekomendasi_teks import build_kontrak, build_log, build_ringkasan

    cfg = cfg or config.load_config()
    proc, reports = config.path("processed"), config.path("reports")
    berkas = {nm: proc / nm for nm in ("data_features.csv", "data_segmen.csv")}
    d = siapkan_data(*(pd.read_csv(p) for p in berkas.values()))
    gab = pd.read_csv(reports / "tables" / "pengaruh_gabungan.csv")
    cv_ringkas = pd.read_csv(reports / "tables" / "pengaruh_cv_ringkas.csv")
    rep = analisis(d, gab, cv_ringkas, cfg, {nm: _sha256(p) for nm, p in berkas.items()})

    dir_model = config.path("models") / cfg["recommendation"]["versi_model"]
    rep.info["path_artefak"] = rc.simpan_artefak(dir_model, rep.artefak)
    rc.muat_artefak.cache_clear()  # artefak baru saja ditulis ulang
    rep.tabel["konsistensi"], rep.info["wakil"] = cek_konsistensi(
        rep.tabel["per_segmen"], d, dir_model
    )
    rep.contoh = [{"masukan": p, "keluaran": rc.recommend(p, dir_model)} for p in CONTOH]

    io.write_csv(rep.tabel["per_segmen"], reports / "tables" / "rekomendasi_per_segmen.csv")
    for nm, tab in rep.tabel.items():
        if nm != "per_segmen":
            io.write_csv(tab, reports / "tables" / f"rekomendasi_{nm}.csv")
    for nm, fig in buat_grafik(rep).items():
        rep.grafik[nm] = viz.simpan(fig, reports / "figures" / f"{nm}.png")
    io.write_text(build_log(rep, cfg), reports / "rekomendasi_log.md")
    io.write_text(build_ringkasan(rep, cfg), reports / "rekomendasi_ringkas.md")
    io.write_text(build_kontrak(rep, cfg), reports / "integration_contract.md")
    return rep
