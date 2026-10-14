"""Tahap 3: analisis data eksploratif (EDA).

Profil responden, distribusi skor konstruk, perbandingan sebelum-sesudah, korelasi strategi dengan
kinerja, perbandingan kelompok, dan VIF. Analisis yang menyangkut kinerja memakai sampel utama
(n=116, D14) dengan 149 responden sebagai pembanding. Semua hasil bersifat asosiasi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from umkm import stats, viz
from umkm.cleaning import PLATFORM_COLS, X1_COLS, X2_COLS, X3_COLS, X4_COLS, Y_PERSEPSI_COLS
from umkm.features import KONSTRUK, SKALA_LABELS, STRATEGI_COLS

NAMA_KONSTRUK = {
    "x1_unggah": "X1 Unggah produk",
    "x2_promosi": "X2 Promosi",
    "x3_komunikasi": "X3 Komunikasi pelanggan",
    "x4_konsistensi": "X4 Konsistensi toko",
    "y_persepsi": "Y Persepsi kinerja (pembanding)",
}
NAMA_PENDEK = {
    "x1_unggah": "X1 Unggah",
    "x2_promosi": "X2 Promosi",
    "x3_komunikasi": "X3 Komunikasi",
    "x4_konsistensi": "X4 Konsistensi",
    "y_persepsi": "Y Persepsi",
}
KINERJA_COLS = ["d_omzet", "d_trx", "y_obj", "y_pelanggan_baru"]
NAMA_KINERJA = {
    "d_omzet": "Perubahan omzet",
    "d_trx": "Perubahan transaksi",
    "y_obj": "Y_obj (gabungan)",
    "y_pelanggan_baru": "Pelanggan baru",
}
NAMA_PLATFORM = {
    "mp_gofood": "GoFood",
    "mp_grabfood": "GrabFood",
    "mp_shopee": "Shopee",
    "mp_maxim": "Maxim",
    "mp_tiktok": "TikTok Shop",
}
LABEL_BUTIR = {
    "x1_unggah_1": "X1.1 Unggah rutin mingguan",
    "x1_unggah_2": "X1.2 Unggah produk baru",
    "x1_unggah_3": "X1.3 Unggah ulang produk",
    "x1_unggah_4": "X1.4 Pantau produk unggahan",
    "x2_promosi_1": "X2.1 Voucher/diskon",
    "x2_promosi_2": "X2.2 Iklan berbayar",
    "x2_promosi_3": "X2.3 Fitur promosi",
    "x2_promosi_4": "X2.4 Evaluasi promosi",
    "x3_komunikasi_1": "X3.1 Respon cepat",
    "x3_komunikasi_2": "X3.2 Jelas dan sopan",
    "x3_komunikasi_3": "X3.3 Balas di hari yang sama",
    "x3_komunikasi_4": "X3.4 Tangani komplain",
    "x3_komunikasi_5": "X3.5 Jaga komunikasi",
    "x4_konsistensi_1": "X4.1 Toko selalu aktif",
    "x4_konsistensi_2": "X4.2 Stok diperbarui",
    "x4_konsistensi_3": "X4.3 Foto/deskripsi terjaga",
    "x4_konsistensi_4": "X4.4 Harga akurat",
    "x4_konsistensi_5": "X4.5 Tetap kelola saat sibuk",
    "y_persepsi_1": "Y1 Omzet naik",
    "y_persepsi_2": "Y2 Penjualan tumbuh",
    "y_persepsi_3": "Y3 Pesanan naik",
    "y_persepsi_4": "Y4 Transaksi lebih sering",
    "y_persepsi_5": "Y5 Pelanggan baru",
    "y_persepsi_6": "Y6 Jangkauan luar daerah",
    "y_persepsi_7": "Y7 Usaha berkembang",
    "y_persepsi_8": "Y8 Kontribusi marketplace",
}
# Butir persepsi yang punya padanan objektif langsung (untuk cek keselarasan persepsi vs angka)
PADANAN_PERSEPSI = {
    "y_persepsi_1": "d_omzet",
    "y_persepsi_4": "d_trx",
    "y_persepsi_5": "y_pelanggan_baru",
}
PROFIL_NUMERIK = ["lama_usaha_pra_mp", "lama_di_mp", "jumlah_platform", "log_omzet_sebelum"]
VIF_BATAS = 5.0
ALPHA = 0.05


def _sampel(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Penanda baris untuk sampel utama (D14) dan semua 149 responden."""
    return {"utama": df["sampel_utama"] == 1, "semua_149": pd.Series(True, index=df.index)}


# ---------------------------------------------------------------------------
# 1. Profil responden
# ---------------------------------------------------------------------------
def profil_platform(df: pd.DataFrame) -> pd.DataFrame:
    """Jumlah dan persentase pengguna tiap platform (multi-pilihan), 149 dan sampel utama."""
    rows = []
    for col in PLATFORM_COLS:
        row: dict[str, Any] = {"platform": NAMA_PLATFORM.get(col, col)}
        for nm, sel in _sampel(df).items():
            row[f"n_{nm}"] = int(df.loc[sel, col].sum())
            row[f"pct_{nm}"] = df.loc[sel, col].mean()
        rows.append(row)
    return pd.DataFrame(rows).sort_values("n_semua_149", ascending=False, ignore_index=True)


def kombinasi_platform(df: pd.DataFrame) -> pd.DataFrame:
    """Sebaran kombinasi platform yang dipakai bersamaan (149 responden)."""
    nama = [NAMA_PLATFORM[c] for c in PLATFORM_COLS]
    combo = df[PLATFORM_COLS].apply(
        lambda r: " + ".join(n for n, v in zip(nama, r) if v == 1) or "(tidak ada)", axis=1
    )
    vc = combo.value_counts()
    return pd.DataFrame({"kombinasi": vc.index, "n": vc.values, "pct": vc.values / len(df)})


def profil_numerik(df: pd.DataFrame, omzet_sebelum: pd.Series) -> pd.DataFrame:
    """Statistik deskriptif lama usaha, lama di marketplace, jumlah platform, omzet sebelum."""
    data = df[["lama_usaha_pra_mp", "lama_di_mp", "jumlah_platform"]].assign(
        omzet_sebelum_juta=omzet_sebelum / 1e6
    )
    out = []
    for nm, sel in _sampel(df).items():
        desc = data.loc[sel].describe().T
        desc.insert(0, "sampel", nm)
        out.append(desc.reset_index().rename(columns={"index": "variabel"}))
    return pd.concat(out, ignore_index=True)


def profil_skala(df: pd.DataFrame, batas: list[float]) -> pd.DataFrame:
    """Jumlah responden per kategori skala_omzet beserta rentang omzet sebelum."""
    tepi = [0.0, *batas]
    rentang = (
        [f"<= Rp{batas[0] / 1e6:.0f} jt"]
        + [f"Rp{lo / 1e6:.0f}-{hi / 1e6:.0f} jt" for lo, hi in zip(tepi[1:-1], batas[1:])]
        + [f"> Rp{batas[-1] / 1e6:.0f} jt"]
    )
    rows = []
    for lab, rg in zip(SKALA_LABELS, rentang):
        row: dict[str, Any] = {"skala_omzet": lab, "rentang_omzet_sebelum": rg}
        for nm, sel in _sampel(df).items():
            row[f"n_{nm}"] = int((df.loc[sel, "skala_omzet"] == lab).sum())
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. Distribusi skor konstruk
# ---------------------------------------------------------------------------
def distribusi_konstruk(df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan skor tiap konstruk + penanda floor/ceiling (> 15%) untuk 149 dan sampel utama."""
    rows = []
    for nm, sel in _sampel(df).items():
        for k in KONSTRUK:
            r = stats.ringkas_skor(df.loc[sel, k])
            rows.append({"sampel": nm, "konstruk": k, **r})
    out = pd.DataFrame(rows)
    out["efek_floor"] = out["pct_floor"] > stats.BATAS_CEILING_FLOOR
    out["efek_ceiling"] = out["pct_ceiling"] > stats.BATAS_CEILING_FLOOR
    out["dominasi_satu_nilai"] = out["pct_nilai_dominan"] > stats.BATAS_DOMINASI
    return out


def sebaran_butir_semua(clean: pd.DataFrame) -> pd.DataFrame:
    """Proporsi jawaban 1-5 untuk semua butir X dan Y (149 responden)."""
    cols = X1_COLS + X2_COLS + X3_COLS + X4_COLS + Y_PERSEPSI_COLS
    out = stats.sebaran_butir(clean[cols])
    out.insert(1, "label", out["butir"].map(LABEL_BUTIR))
    return out


# ---------------------------------------------------------------------------
# 3. Sebelum vs sesudah
# ---------------------------------------------------------------------------
def uji_sebelum_sesudah(clean: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Wilcoxon signed-rank omzet dan transaksi (nilai terwinsor), sampel utama dan 149."""
    rows = []
    for nm, sel in _sampel(df).items():
        for var, label in (("omzet", "omzet (Rp)"), ("trx", "transaksi")):
            seb, ses = clean.loc[sel, f"{var}_sebelum_w"], clean.loc[sel, f"{var}_sesudah_w"]
            r = stats.wilcoxon_berpasangan(seb, ses)
            n = r["n_pasangan"]
            rows.append(
                {
                    "sampel": nm,
                    "variabel": label,
                    "rata_sebelum": seb.mean(),
                    "rata_sesudah": ses.mean(),
                    **r,
                    "pct_naik": r["n_naik"] / n,
                    "pct_sama": r["n_sama"] / n,
                    "pct_turun": r["n_turun"] / n,
                    "efek": stats.label_efek(r["r"]),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Korelasi strategi vs kinerja
# ---------------------------------------------------------------------------
def korelasi_kinerja(df: pd.DataFrame) -> pd.DataFrame:
    """Spearman X1-X4 vs d_omzet, d_trx, y_obj, y_pelanggan_baru; Holm per sampel (16 uji)."""
    out = []
    for nm, sel in _sampel(df).items():
        t = stats.spearman_tabel(df.loc[sel], STRATEGI_COLS, KINERJA_COLS)
        t.insert(0, "sampel", nm)
        out.append(t)
    return pd.concat(out, ignore_index=True)


def korelasi_persepsi(df: pd.DataFrame, clean: pd.DataFrame) -> pd.DataFrame:
    """Keselarasan persepsi dengan angka nyata dan dengan strategi (sampel utama dan 149).

    Baris: y_persepsi vs 4 ukuran kinerja objektif, butir persepsi vs padanan objektifnya,
    dan y_persepsi vs X1-X4 (apakah persepsi lebih dekat ke strategi daripada ke angka).
    """
    data = df.join(clean[list(PADANAN_PERSEPSI)])
    out = []
    for nm, sel in _sampel(df).items():
        sub = data.loc[sel]
        parts = [
            stats.spearman_tabel(sub, ["y_persepsi"], KINERJA_COLS).assign(
                jenis="persepsi_vs_angka"
            ),
            pd.concat(
                [stats.spearman_tabel(sub, [b], [y]) for b, y in PADANAN_PERSEPSI.items()],
                ignore_index=True,
            ).assign(jenis="butir_vs_padanan"),
            stats.spearman_tabel(sub, ["y_persepsi"], STRATEGI_COLS).assign(
                jenis="persepsi_vs_strategi"
            ),
        ]
        t = pd.concat(parts, ignore_index=True)
        t["p_holm"] = stats.holm(t["p"])
        t.insert(0, "sampel", nm)
        out.append(t)
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# 5. Perbandingan kelompok
# ---------------------------------------------------------------------------
def _uji_kelompok(df: pd.DataFrame, cols: list[str], grup: str, varian: str) -> pd.DataFrame:
    rows = []
    for c in cols:
        r = stats.mann_whitney(df.loc[df[grup] == 1, c], df.loc[df[grup] == 0, c])
        rows.append({"varian": varian, "variabel": c, **r, "efek": stats.label_efek(r["r"])})
    out = pd.DataFrame(rows)
    out["p_holm"] = stats.holm(out["p"])
    return out


def uji_naik_penjualan(df: pd.DataFrame) -> pd.DataFrame:
    """Mann-Whitney skor strategi (dan persepsi) naik_penjualan 1 vs 0.

    Varian: sampel utama (analisis utama), sampel utama tanpa `flag_jawaban_seragam` (D20),
    dan 149 responden. Holm dihitung per varian atas 4 strategi; y_persepsi dilaporkan terpisah.
    """
    utama = df[df["sampel_utama"] == 1]
    varian = {
        "utama": utama,
        "utama_tanpa_seragam": utama[utama["flag_jawaban_seragam"] == 0],
        "semua_149": df,
    }
    out = []
    for nm, sub in varian.items():
        out.append(_uji_kelompok(sub, STRATEGI_COLS, "naik_penjualan", nm))
        out.append(_uji_kelompok(sub, ["y_persepsi"], "naik_penjualan", nm))
    return pd.concat(out, ignore_index=True)


def uji_tanpa_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """Mann-Whitney kelompok `tanpa_baseline` (1) vs punya baseline (0), 149 responden."""
    strategi = _uji_kelompok(df, STRATEGI_COLS, "tanpa_baseline", "strategi")
    lain = _uji_kelompok(
        df,
        ["y_persepsi", "lama_di_mp", "jumlah_platform", "log_omzet_sebelum", "y_pelanggan_baru"],
        "tanpa_baseline",
        "profil_dan_lainnya",
    )
    return pd.concat([strategi, lain], ignore_index=True)


# ---------------------------------------------------------------------------
# 6. VIF
# ---------------------------------------------------------------------------
def tabel_vif(df: pd.DataFrame) -> pd.DataFrame:
    """VIF tiga set prediktor kandidat Tahap 4 (sampel utama dan 149).

    `jumlah_platform` dan dummy platform tidak dimasukkan bersamaan karena jumlah_platform =
    jumlah dummy (kolinear sempurna).
    """
    set_pred = {
        "A_strategi": STRATEGI_COLS,
        "B_strategi_profil": STRATEGI_COLS + PROFIL_NUMERIK,
        "C_strategi_profil_dummy_platform": STRATEGI_COLS
        + ["lama_usaha_pra_mp", "lama_di_mp", "log_omzet_sebelum", *PLATFORM_COLS],
    }
    out = []
    for nm, sel in _sampel(df).items():
        for s, cols in set_pred.items():
            t = stats.vif(df.loc[sel], cols)
            t.insert(0, "set", s)
            t.insert(0, "sampel", nm)
            out.append(t)
    res = pd.concat(out, ignore_index=True)
    res["waspada"] = res["vif"] > VIF_BATAS
    return res


# ---------------------------------------------------------------------------
# Grafik
# ---------------------------------------------------------------------------
def _p_teks(p: float) -> str:
    return "p < 0,001" if p < 0.001 else f"p = {p:.3f}".replace(".", ",")


def _angka(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def buat_grafik(
    df: pd.DataFrame, clean: pd.DataFrame, t: dict[str, pd.DataFrame], batas: list[float]
) -> dict[str, Any]:
    """Buat semua Figure EDA; kunci = nama berkas tanpa ekstensi."""
    figs: dict[str, Any] = {}
    n_all, n_utama = len(df), int(df["sampel_utama"].sum())

    plat = t["profil_platform"].set_index("platform")
    figs["eda_profil_platform"] = viz.bar_horizontal(
        plat["pct_semua_149"] * 100,
        "Platform marketplace yang dipakai UMKM",
        "Persentase responden (%)",
        subjudul=f"n = {n_all}; satu UMKM bisa memakai lebih dari satu platform",
        label_fmt="{:.0f}%",
        teks_tambahan=[f"({n} UMKM)" for n in plat["n_semua_149"]],
    )
    figs["eda_profil_lama_usaha"] = viz.histogram_panel(
        df,
        ["lama_usaha_pra_mp", "lama_di_mp"],
        ["Lama usaha sebelum marketplace", "Lama berjualan di marketplace"],
        "Lama usaha responden",
        "Tahun (dibulatkan)",
        bins=np.arange(-0.5, 23.5, 1),
        subjudul=f"n = {n_all}; batang 0 = kurang dari 6 bulan, termasuk "
        f"{int(df['tanpa_baseline'].sum())} usaha yang berdiri bersamaan dengan masuk marketplace",
    )
    skala = t["profil_skala_omzet"].set_index("skala_omzet")
    figs["eda_profil_skala_omzet"] = viz.bar_horizontal(
        skala["n_semua_149"].rename(lambda s: s.split("_", 1)[1].replace("_", " ")),
        "Skala usaha menurut omzet bulanan sebelum marketplace",
        "Jumlah responden",
        subjudul=f"n = {n_all}; kategori dari kuartil omzet sebelum",
        teks_tambahan=list(skala["rentang_omzet_sebelum"]),
    )
    figs["eda_distribusi_konstruk"] = viz.histogram_panel(
        df,
        list(KONSTRUK),
        [NAMA_KONSTRUK[k] for k in KONSTRUK],
        "Sebaran skor strategi dan persepsi kinerja",
        "Skor rata-rata butir (1-5)",
        bins=np.arange(0.875, 5.2, 0.25),
        ncol=3,
        subjudul=f"n = {n_all}; skor 3 = jawaban tengah/netral",
    )
    butir = t["sebaran_butir"].set_index("label")
    prop = butir[[f"pct_{k}" for k in range(1, 6)]]
    prop.columns = ["1", "2", "3 (netral)", "4", "5"]
    figs["eda_butir_likert"] = viz.stacked_100(
        prop,
        viz.LIKERT_WARNA,
        "Sebaran jawaban per butir kuesioner",
        subjudul=f"n = {n_all}; 1 = tidak pernah/sangat tidak sesuai, 5 = sangat sering/sangat sesuai",
        legend_judul="Skor jawaban",
    )

    arah_rows = {}
    for nm, sel in (("Sampel utama", df["sampel_utama"] == 1), ("Semua 149", df.index == df.index)):
        for var, lab in (("omzet", "Omzet"), ("trx", "Transaksi")):
            vc = df.loc[sel, f"arah_{var}"].value_counts(normalize=True)
            arah_rows[f"{lab} - {nm} (n={int(sel.sum())})"] = {
                k: vc.get(k, 0.0) for k in ("naik", "sama", "turun", "kosong")
            }
    arah = pd.DataFrame(arah_rows).T
    arah = arah.loc[:, arah.sum() > 0]
    figs["eda_arah_perubahan"] = viz.stacked_100(
        arah,
        [viz.ARAH_WARNA[c] for c in arah.columns],
        "Arah perubahan omzet dan transaksi sesudah masuk marketplace",
        subjudul="Sampel utama = responden yang punya kondisi sebelum (D14); kosong = transaksi "
        "janggal (D17)",
        label_min=0.04,
    )
    utama = df["sampel_utama"] == 1
    figs["eda_sebelum_sesudah"] = viz.scatter_sebelum_sesudah(
        [
            (
                "Omzet (Rp/bulan)",
                clean.loc[utama, "omzet_sebelum_w"],
                clean.loc[utama, "omzet_sesudah_w"],
            ),
            ("Transaksi", clean.loc[utama, "trx_sebelum_w"], clean.loc[utama, "trx_sesudah_w"]),
        ],
        "Nilai sebelum vs sesudah per UMKM",
        subjudul=f"Sampel utama, n = {n_utama}; titik di atas garis diagonal = naik",
    )

    kor = t["spearman_kinerja"].query("sampel == 'utama'")
    pers = t["spearman_persepsi"].query("sampel == 'utama' and jenis == 'persepsi_vs_angka'")
    tab = pd.concat([kor, pers])
    rho = tab.pivot(index="x", columns="y", values="rho").loc[
        [*STRATEGI_COLS, "y_persepsi"], KINERJA_COLS
    ]
    pv = tab.pivot(index="x", columns="y", values="p").loc[rho.index, rho.columns]
    anot = rho.map(lambda v: _angka(v)) + pv.map(
        lambda p: "**" if p < 0.01 else ("*" if p < 0.05 else "")
    )
    figs["eda_spearman_heatmap"] = viz.heatmap(
        rho.rename(index=NAMA_PENDEK, columns=NAMA_KINERJA),
        "Korelasi Spearman strategi dengan kinerja penjualan",
        "Ukuran kinerja objektif",
        "Skor strategi",
        subjudul=f"Sampel utama, n = {n_utama} (d_trx n = {int(df.loc[utama, 'd_trx'].notna().sum())});"
        " * p < 0,05, ** p < 0,01 (belum dikoreksi); baris bawah = persepsi sebagai pembanding",
        anotasi=anot,
        batas=0.5,
        garis_pemisah=[len(STRATEGI_COLS)],
    )

    mw = t["mw_naik_penjualan"].query("varian == 'utama' and variabel in @STRATEGI_COLS")
    figs["eda_boxplot_naik_penjualan"] = viz.boxplot_kelompok(
        df[utama],
        STRATEGI_COLS,
        [NAMA_PENDEK[c] for c in STRATEGI_COLS],
        "naik_penjualan",
        {1: "Naik", 0: "Tidak naik"},
        "Skor strategi menurut status kenaikan penjualan",
        "Skor (1-5)",
        subjudul=f"Sampel utama, n = {n_utama}; naik = omzet atau transaksi naik",
        teks_panel=[
            f"r_rb = {_angka(r.r_rank_biserial)}\n{_p_teks(r.p)} (Holm {_angka(r.p_holm, 3)})"
            for r in mw.itertuples()
        ],
    )
    mwb = t["mw_tanpa_baseline"].query("varian == 'strategi'")
    figs["eda_boxplot_tanpa_baseline"] = viz.boxplot_kelompok(
        df,
        STRATEGI_COLS,
        [NAMA_PENDEK[c] for c in STRATEGI_COLS],
        "tanpa_baseline",
        {1: "Tanpa baseline", 0: "Punya baseline"},
        "Skor strategi: UMKM tanpa baseline vs punya baseline",
        "Skor (1-5)",
        subjudul=f"n = {n_all}; tanpa baseline = usaha berdiri bersamaan dengan masuk marketplace",
        teks_panel=[
            f"r_rb = {_angka(r.r_rank_biserial)}\n{_p_teks(r.p)} (Holm {_angka(r.p_holm, 3)})"
            for r in mwb.itertuples()
        ],
    )
    return figs


# ---------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------
@dataclass
class EdaReport:
    """Hasil Tahap 3: tabel (nama berkas tanpa .csv -> DataFrame) dan path grafik."""

    tabel: dict[str, pd.DataFrame] = field(default_factory=dict)
    grafik: dict[str, Path] = field(default_factory=dict)
    batas_skala: list[float] = field(default_factory=list)


def build_tables(
    df: pd.DataFrame, clean: pd.DataFrame, batas: list[float]
) -> dict[str, pd.DataFrame]:
    """Hitung semua tabel EDA (tanpa menulis berkas)."""
    if not (df["id_responden"].values == clean["id_responden"].values).all():
        raise ValueError("Urutan id_responden data_features dan data_clean berbeda.")
    return {
        "profil_platform": profil_platform(df),
        "profil_kombinasi_platform": kombinasi_platform(df),
        "profil_numerik": profil_numerik(df, clean["omzet_sebelum_w"]),
        "profil_skala_omzet": profil_skala(df, batas),
        "distribusi_konstruk": distribusi_konstruk(df),
        "sebaran_butir": sebaran_butir_semua(clean),
        "sebelum_sesudah": uji_sebelum_sesudah(clean, df),
        "spearman_kinerja": korelasi_kinerja(df),
        "spearman_persepsi": korelasi_persepsi(df, clean),
        "mw_naik_penjualan": uji_naik_penjualan(df),
        "mw_tanpa_baseline": uji_tanpa_baseline(df),
        "vif": tabel_vif(df),
    }


def batas_dari_data(df: pd.DataFrame, clean: pd.DataFrame) -> list[float]:
    """Batas kuartil skala_omzet yang dipakai Tahap 2 (dihitung ulang dari omzet_sebelum_w)."""
    from umkm.features import batas_skala_omzet

    return batas_skala_omzet(clean["omzet_sebelum_w"])


def run(cfg: dict[str, Any] | None = None) -> EdaReport:
    """Baca data_features + data_clean, tulis tabel eda_*.csv, grafik eda_*.png, dan ringkasan."""
    from umkm import config, io
    from umkm.eda_teks import build_log, build_ringkasan, interpretasi

    proc = config.path("processed")
    reports = config.path("reports")
    df = pd.read_csv(proc / "data_features.csv")
    clean = pd.read_csv(proc / "data_clean.csv")

    rep = EdaReport(batas_skala=batas_dari_data(df, clean))
    rep.tabel = build_tables(df, clean, rep.batas_skala)
    for nm, tab in rep.tabel.items():
        io.write_csv(tab, reports / "tables" / f"eda_{nm}.csv")
    for nm, fig in buat_grafik(df, clean, rep.tabel, rep.batas_skala).items():
        rep.grafik[nm] = viz.simpan(fig, reports / "figures" / f"{nm}.png")

    interp = interpretasi(rep.tabel, df)
    io.write_text(build_log(rep, df, interp), reports / "eda_log.md")
    io.write_text(build_ringkasan(rep, df, interp), reports / "eda_ringkasan.md")
    return rep
