"""Tahap 6 (sisi inferensi): benchmark, gap, skor prioritas, template teks, dan `recommend()`.

prioritas_s = bobot_s x gap_s, dengan gap_s = max(0, benchmark_s - skor_s); benchmark = rata-rata
skor UMKM yang melaporkan kenaikan penjualan (sampel utama) di segmen yang sama, skor = rata-rata
segmen atau skor satu UMKM (D28). Bobot dari Tahap 4 (D26), sama untuk semua segmen.

Modul ini hanya butuh pandas, numpy, scikit-learn, joblib, dan pydantic. `recommend()` tidak
membaca data survei; ia hanya memuat artefak di models/<versi>/ yang ditulis Tahap 6
(`umkm.rekomendasi`). CLI: `python -m umkm.recommend profil.json` (atau `-` untuk stdin).
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from umkm.cleaning import PLATFORM_COLS, X1_COLS, X2_COLS, X3_COLS, X4_COLS
from umkm.features import skala_omzet
from umkm.schemas import HasilRekomendasi, ProfilUMKM
from umkm.segmentation import siapkan_fitur, tetapkan_segmen

STRATEGI = ["x1_unggah", "x2_promosi", "x3_komunikasi", "x4_konsistensi"]
BUTIR_STRATEGI = {
    "x1_unggah": X1_COLS,
    "x2_promosi": X2_COLS,
    "x3_komunikasi": X3_COLS,
    "x4_konsistensi": X4_COLS,
}
NAMA_STRATEGI = {
    "x1_unggah": "X1 Unggah produk",
    "x2_promosi": "X2 Promosi",
    "x3_komunikasi": "X3 Komunikasi pelanggan",
    "x4_konsistensi": "X4 Konsistensi toko",
}
NAMA_BERKAS = {
    "segmen": "segmen.joblib",
    "model": "model.joblib",
    "benchmark": "benchmark_per_segmen.json",
    "pengaruh": "pengaruh_strategi.json",
    "meta": "model_meta.json",
}
TOLERANSI = 1e-9  # gap lebih kecil dari ini dianggap 0 (galat pembulatan float)

# ---------------------------------------------------------------------------
# Template teks (diubah/diterjemahkan di sini, bukan di notebook)
# ---------------------------------------------------------------------------
# Tindakan per butir kuesioner (data_dictionary.md); dipilih butir dengan gap terbesar.
TINDAKAN_BUTIR = {
    "x1_unggah_1": "menjadwalkan unggah produk rutin setiap minggu",
    "x1_unggah_2": "menambah produk atau varian baru secara berkala",
    "x1_unggah_3": "mengunggah ulang produk lama agar tetap terlihat pembeli",
    "x1_unggah_4": "memantau produk yang sepi dan perlu diunggah ulang",
    "x2_promosi_1": "memakai voucher, diskon, atau cashback dengan anggaran yang ditetapkan",
    "x2_promosi_2": "mencoba iklan berbayar atau promosi internal marketplace dalam skala kecil",
    "x2_promosi_3": "memanfaatkan fitur promosi bawaan marketplace",
    "x2_promosi_4": "mengevaluasi hasil tiap promosi (pesanan sebelum vs selama promo)",
    "x3_komunikasi_1": "membalas chat pelanggan dengan cepat",
    "x3_komunikasi_2": "menjawab pertanyaan pelanggan dengan jelas dan sopan",
    "x3_komunikasi_3": "membalas semua pesan pelanggan pada hari yang sama",
    "x3_komunikasi_4": "menanggapi keluhan atau komplain pelanggan segera",
    "x3_komunikasi_5": "menjaga komunikasi sampai pesanan diterima pelanggan",
    "x4_konsistensi_1": "menjaga toko tetap aktif dan terkelola",
    "x4_konsistensi_2": "memperbarui stok produk secara rutin",
    "x4_konsistensi_3": "memperbarui foto dan deskripsi produk",
    "x4_konsistensi_4": "memastikan informasi harga dan stok selalu akurat",
    "x4_konsistensi_5": "tetap mengelola toko saat sedang sibuk",
}
# Penyesuaian menurut kondisi usaha segmen: "kecil" = omzet kecil/baru, "besar" = omzet besar/mapan
KONTEKS_SEGMEN = {
    "x1_unggah": {
        "kecil": "Mulai dari jadwal tetap 1-2 kali seminggu dan lengkapi katalog secara bertahap, "
        "dimulai dari produk terlaris.",
        "besar": "Tunjuk penanggung jawab katalog; segarkan produk lama secara bergilir di setiap "
        "platform yang dipakai dan pantau produk yang sepi tiap minggu.",
    },
    "x2_promosi": {
        "kecil": "Mulai dari fitur promosi gratis dari platform dan voucher bernilai kecil; catat "
        "jumlah pesanan selama promo untuk dibandingkan dengan minggu biasa.",
        "besar": "Uji iklan berbayar dengan anggaran terbatas pada produk andalan; bandingkan hasil "
        "antar-platform setiap bulan dan hentikan promosi yang tidak menambah pesanan.",
    },
    "x3_komunikasi": {
        "kecil": "Siapkan template jawaban untuk pertanyaan yang sering muncul dan tetapkan jam "
        "cek chat beberapa kali sehari.",
        "besar": "Bagi tugas membalas chat dan komplain (per platform atau per shift) dengan batas "
        "waktu respons; tinjau komplain yang berulang setiap minggu.",
    },
    "x4_konsistensi": {
        "kecil": "Cek stok dan harga setiap pagi sebelum toko buka; nonaktifkan sementara menu yang "
        "habis agar pesanan tidak dibatalkan.",
        "besar": "Samakan stok, harga, dan foto di semua platform dengan daftar periksa harian; "
        "tunjuk pengganti agar toko tetap dikelola saat sibuk.",
    },
}
HUBUNGAN = {
    True: "strategi ini termasuk yang paling berhubungan dengan laporan kenaikan penjualan "
    "(bobot {bobot})",
    False: "hubungannya dengan laporan kenaikan penjualan belum meyakinkan, sehingga bobotnya "
    "diturunkan menjadi {bobot}",
}
ALASAN_SEGMEN = (
    "Untuk segmen {segmen}, {strategi} menjadi prioritas karena skor rata-ratanya {skor} berada "
    "{gap} poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama ({benchmark}); "
    "{hubungan}."
)
ALASAN_SEMUA = (
    "Untuk seluruh UMKM, {strategi} menjadi prioritas karena skor rata-ratanya {skor} berada "
    "{gap} poin di bawah rata-rata UMKM yang penjualannya naik ({benchmark}); {hubungan}."
)
ALASAN_UMKM = (
    "Skor {strategi} UMKM ini {skor} berada {gap} poin di bawah rata-rata UMKM yang penjualannya "
    "naik pada segmen yang sama (segmen {segmen}: {benchmark}); {hubungan}."
)
TINDAKAN = "Utamakan {butir}. {konteks}"
CATATAN = (
    "Prioritas disusun dari pola asosiasi pada {n} UMKM responden survei satu waktu, bukan jaminan "
    "hasil. Benchmark = rata-rata skor UMKM yang melaporkan kenaikan penjualan di segmen yang sama."
)
TANPA_PRIORITAS = (
    "Semua skor strategi sudah setara atau di atas benchmark segmen; tidak ada strategi prioritas. "
    "Pertahankan kebiasaan yang ada."
)


def _a(x: float, d: int = 2) -> str:
    """Angka format Indonesia (koma desimal)."""
    return f"{x:.{d}f}".replace(".", ",")


def _daftar(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " dan " + items[-1]


# ---------------------------------------------------------------------------
# Benchmark, gap, prioritas (fungsi murni)
# ---------------------------------------------------------------------------
def agregat(df: pd.DataFrame, cols: list[str], ukuran: str = "rata_rata") -> pd.Series:
    """Rata-rata (D28) atau median kolom skor."""
    if ukuran == "rata_rata":
        return df[cols].mean()
    if ukuran == "median":
        return df[cols].median()
    raise ValueError(f"ukuran tidak dikenal: {ukuran}")


def benchmark(
    naik_segmen: pd.DataFrame,
    naik_semua: pd.DataFrame,
    cols: list[str],
    min_naik: int,
    ukuran: str = "rata_rata",
) -> tuple[pd.Series, str]:
    """Skor acuan dari UMKM naik_penjualan = 1 di segmen; bila kurang dari `min_naik` UMKM,
    pakai seluruh UMKM yang naik (plan/06 langkah 1). Mengembalikan (benchmark, sumber)."""
    if len(naik_segmen) >= min_naik:
        return agregat(naik_segmen, cols, ukuran), "segmen"
    return agregat(naik_semua, cols, ukuran), "semua"


def hitung_prioritas(
    skor: pd.Series, acuan: pd.Series, bobot: pd.Series, n: int = 3
) -> pd.DataFrame:
    """Tabel per strategi (indeks): skor, benchmark, gap, bobot, prioritas, peringkat.

    gap = max(0, benchmark - skor); prioritas = bobot x gap. Peringkat 1..n hanya untuk strategi
    dengan prioritas > 0 (seri dipecah oleh bobot yang lebih besar); lainnya 0.
    """
    gap = (acuan - skor).where(lambda g: g > TOLERANSI, 0.0)
    out = pd.DataFrame(
        {"skor": skor, "benchmark": acuan, "gap": gap, "bobot": bobot, "prioritas": bobot * gap}
    )
    urut = out[out["prioritas"] > 0].sort_values(["prioritas", "bobot"], ascending=False)
    out["peringkat"] = 0
    out.loc[urut.index[:n], "peringkat"] = range(1, min(n, len(urut)) + 1)
    return out


def fokus_butir(gap_butir: pd.Series, n: int = 2) -> dict[str, list[str]]:
    """Per strategi: `n` butir dengan gap (benchmark - skor) terbesar; indeks = nama butir."""
    return {
        s: gap_butir[cols].sort_values(ascending=False, kind="stable").index[:n].tolist()
        for s, cols in BUTIR_STRATEGI.items()
    }


def konteks_segmen(z_skala_omzet: float) -> str:
    """'kecil' bila pusat segmen di bawah rata-rata skala omzet, selain itu 'besar'."""
    return "kecil" if z_skala_omzet < 0 else "besar"


def label_segmen(id_segmen: int, nama: str) -> str:
    """'1 (omzet kecil, ...)' agar koma di nama segmen tidak membingungkan kalimat."""
    return f"{id_segmen} ({nama[:1].lower() + nama[1:]})"


def teks_alasan(
    r: pd.Series, strategi: str, meyakinkan: bool, segmen: str | None, umkm: bool = False
) -> str:
    """Kalimat alasan berbasis angka; `segmen` None = seluruh UMKM."""
    isi = {
        "strategi": NAMA_STRATEGI[strategi],
        "skor": _a(r["skor"]),
        "gap": _a(r["gap"]),
        "benchmark": _a(r["benchmark"]),
        "segmen": segmen,
        "hubungan": HUBUNGAN[bool(meyakinkan)].format(bobot=_a(r["bobot"])),
    }
    templat = ALASAN_UMKM if umkm else ALASAN_SEMUA if segmen is None else ALASAN_SEGMEN
    return templat.format(**isi)


def teks_tindakan(strategi: str, butir: list[str], konteks: str | None) -> str:
    """Tindakan konkret: butir fokus + penyesuaian menurut kondisi usaha segmen (None = tanpa
    penyesuaian, untuk seluruh UMKM)."""
    return TINDAKAN.format(
        butir=_daftar([TINDAKAN_BUTIR[b] for b in butir]),
        konteks=KONTEKS_SEGMEN[strategi][konteks] if konteks else "",
    ).strip()


def selisih_prediksi(
    model: Any, x: pd.DataFrame, strategi: list[str], tambah: float = 1.0
) -> pd.Series:
    """Rata-rata selisih peluang prediksi kelas 1 (poin persen) bila satu strategi dinaikkan
    `tambah` poin (maksimum 5), strategi lain dan profil tetap. Ilustrasi model, bukan dampak."""
    p0 = model.predict_proba(x)[:, 1]
    out = {}
    for s in strategi:
        x1 = x.copy()
        x1[s] = np.minimum(x1[s] + tambah, 5.0)
        out[s] = float((model.predict_proba(x1)[:, 1] - p0).mean() * 100)
    return pd.Series(out)


# ---------------------------------------------------------------------------
# Artefak models/<versi>/
# ---------------------------------------------------------------------------
def dir_model_default(versi: str | None = None) -> Path:
    """models/<versi> di bawah base dir (versi dari config `recommendation.versi_model`)."""
    from umkm import config

    versi = versi or config.load_config()["recommendation"]["versi_model"]
    return config.path("models") / versi


def simpan_artefak(dir_model: Path, artefak: dict[str, Any]) -> dict[str, Path]:
    """Tulis lima artefak (kunci = NAMA_BERKAS); joblib untuk objek sklearn, JSON untuk lainnya."""
    dir_model.mkdir(parents=True, exist_ok=True)
    out = {}
    for kunci, berkas in NAMA_BERKAS.items():
        p = dir_model / berkas
        if berkas.endswith(".joblib"):
            joblib.dump(artefak[kunci], p)
        else:
            p.write_text(json.dumps(artefak[kunci], ensure_ascii=False, indent=2), encoding="utf-8")
        out[kunci] = p
    return out


@lru_cache(maxsize=4)
def muat_artefak(dir_model: str) -> dict[str, Any]:
    """Muat artefak sekali per folder (cache). Error jelas bila Tahap 6 belum dijalankan.

    joblib = pickle: memuat berkas bisa menjalankan kode. Hanya muat folder artefak yang dibuat
    sendiri oleh pipeline proyek ini, jangan berkas kiriman pihak lain.
    """
    d = Path(dir_model)
    hilang = [b for b in NAMA_BERKAS.values() if not (d / b).exists()]
    if hilang:
        raise FileNotFoundError(
            f"Artefak tidak lengkap di {d} ({', '.join(hilang)}). "
            "Jalankan `python -m umkm.pipeline --stage 6`."
        )
    out = {}
    for kunci, berkas in NAMA_BERKAS.items():
        p = d / berkas
        out[kunci] = (
            joblib.load(p) if berkas.endswith(".joblib") else json.loads(p.read_text("utf-8"))
        )
    return out


def baris_profil(p: ProfilUMKM, batas_skala: list[float]) -> pd.DataFrame:
    """Satu baris dengan kolom yang sama seperti data_features (profil + skor strategi)."""
    omzet = pd.Series([p.omzet_bulanan], dtype=float)
    baris = {
        "omzet_bulanan": p.omzet_bulanan,
        "skala_omzet": skala_omzet(omzet, batas_skala).iloc[0],
        "lama_usaha_pra_mp": p.lama_usaha_pra_mp,
        "lama_di_mp": p.lama_di_mp,
        "jumlah_platform": len(p.platform),
        "log_omzet_sebelum": float(np.log1p(p.omzet_bulanan)),
        **{c: int(c.removeprefix("mp_") in p.platform) for c in PLATFORM_COLS},
        **{s: getattr(p, s) for s in STRATEGI},
    }
    return pd.DataFrame([baris])


def _peringatan_rentang(baris: pd.DataFrame, rentang: dict[str, list[float]]) -> list[str]:
    out = []
    for kol, (lo, hi) in rentang.items():
        v = float(baris[kol].iloc[0])
        if v < lo or v > hi:
            out.append(
                f"{kol} = {v:g} di luar rentang data latih ({lo:g} sampai {hi:g}); segmen dan "
                "ilustrasi model kurang andal."
            )
    return out


def _peringatan_versi(meta: dict[str, Any]) -> list[str]:
    import sklearn

    v = meta["versi_pustaka"]["scikit-learn"]
    if v != sklearn.__version__:
        return [
            (
                f"Artefak dibuat dengan scikit-learn {v}, sekarang {sklearn.__version__}; hasil "
                "bisa sedikit berbeda."
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Pintu masuk inferensi
# ---------------------------------------------------------------------------
def recommend(profil: dict[str, Any], dir_model: str | Path | None = None) -> dict[str, Any]:
    """Rekomendasi strategi untuk satu UMKM (masukan dan keluaran JSON-serializable).

    Masukan divalidasi dengan `ProfilUMKM` (pydantic.ValidationError, turunan ValueError, bila
    tidak sah). Keluaran mengikuti `HasilRekomendasi`; lihat reports/integration_contract.md.
    """
    p = ProfilUMKM.model_validate(profil)
    art = muat_artefak(str(Path(dir_model) if dir_model else dir_model_default()))
    seg_art, bm_art, peng, meta = art["segmen"], art["benchmark"], art["pengaruh"], art["meta"]

    baris = baris_profil(p, bm_art["batas_skala_omzet"])
    x_seg = siapkan_fitur(baris, seg_art["fitur"], seg_art["fitur_log1p"])
    seg = int(tetapkan_segmen(seg_art["pipa"], x_seg, seg_art["urutan"]).iloc[0])
    info = bm_art["segmen"][str(seg)]

    bobot = pd.Series({s: peng["strategi"][s]["bobot"] for s in STRATEGI})
    tab = hitung_prioritas(
        baris[STRATEGI].iloc[0].astype(float),
        pd.Series(info["benchmark"])[STRATEGI],
        bobot,
        bm_art["n_prioritas"],
    )
    m = art["model"]
    delta = selisih_prediksi(m["model"], baris[m["fitur"]], STRATEGI, meta["whatif_tambah"])

    skor = [
        {
            "strategi": s,
            "nama": NAMA_STRATEGI[s],
            **{k: round(float(tab.at[s, k]), 4) for k in ("skor", "benchmark", "gap", "bobot")},
            "prioritas": round(float(tab.at[s, "prioritas"]), 4),
        }
        for s in STRATEGI
    ]
    prioritas = []
    for s in tab[tab["peringkat"] > 0].sort_values("peringkat").index:
        meyakinkan = bool(peng["strategi"][s]["meyakinkan"])
        butir = info["fokus_butir"][s]
        prioritas.append(
            {
                **next(r for r in skor if r["strategi"] == s),
                "peringkat": int(tab.at[s, "peringkat"]),
                "hubungan_meyakinkan": meyakinkan,
                "selisih_prediksi_plus1": round(float(delta[s]), 2),
                "fokus_butir": butir,
                "alasan": teks_alasan(tab.loc[s], s, meyakinkan, str(seg), umkm=True),
                "tindakan": teks_tindakan(s, butir, info["konteks"]),
            }
        )
    peringatan = _peringatan_rentang(baris, meta["rentang_latih"]) + _peringatan_versi(meta)
    if not prioritas:
        peringatan.append(TANPA_PRIORITAS)
    hasil = HasilRekomendasi(
        versi_model=meta["versi_model"],
        id_umkm=p.id_umkm,
        segmen={"id": seg, "nama": info["nama"]},
        skor=skor,
        prioritas=prioritas,
        peringatan=peringatan,
        catatan=CATATAN.format(n=meta["n_responden"]),
    )
    return hasil.model_dump()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rekomendasi strategi untuk satu profil UMKM.")
    parser.add_argument("profil", help="berkas JSON profil UMKM, atau - untuk stdin")
    parser.add_argument("--dir-model", default=None, help="folder artefak (default models/v1)")
    args = parser.parse_args(argv)
    teks = sys.stdin.read() if args.profil == "-" else Path(args.profil).read_text("utf-8")
    hasil = recommend(json.loads(teks), args.dir_model)
    print(json.dumps(hasil, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
