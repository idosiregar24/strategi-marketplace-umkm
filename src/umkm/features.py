"""Tahap 2: konstruksi variabel (reliabilitas, skor konstruk, target kinerja, fitur profil).

Fitur strategi dan profil hanya dihitung dari jawaban strategi dan kondisi SEBELUM; target hanya
dari isian kinerja objektif. Dengan begitu tidak ada kebocoran target ke fitur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from umkm.cleaning import (
    PLATFORM_COLS,
    X1_COLS,
    X2_COLS,
    X3_COLS,
    X4_COLS,
    Y_PERSEPSI_COLS,
)

# Konstruk -> daftar butir. Y_persepsi hanya pendukung (D02), bukan target.
KONSTRUK: dict[str, list[str]] = {
    "x1_unggah": X1_COLS,
    "x2_promosi": X2_COLS,
    "x3_komunikasi": X3_COLS,
    "x4_konsistensi": X4_COLS,
    "y_persepsi": Y_PERSEPSI_COLS,
}
STRATEGI_COLS = ["x1_unggah", "x2_promosi", "x3_komunikasi", "x4_konsistensi"]
TARGET_COLS = ["naik_penjualan", "y_obj", "y_pelanggan_baru"]
PROFIL_COLS = [
    "lama_usaha_pra_mp",
    "lama_di_mp",
    "jumlah_platform",
    *PLATFORM_COLS,
    "log_omzet_sebelum",
    "skala_omzet",
]
SKALA_LABELS = ["Q1_kecil", "Q2_menengah_bawah", "Q3_menengah_atas", "Q4_besar"]

ALPHA_MIN = 0.70
ITEM_TOTAL_MIN = 0.30
RASIO_TURUN_TAJAM = 0.2  # omzet sesudah <= 20% omzet sebelum


def flag_kualitas(df: pd.DataFrame) -> pd.DataFrame:
    """Penanda kualitas jawaban (hanya ditandai, tidak diubah).

    - flag_jawaban_seragam: 18 butir strategi X dijawab dengan angka yang sama persis.
    - flag_omzet_turun_tajam: omzet sesudah <= 20% omzet sebelum (mis. turun tepat 10x,
      kemungkinan salah ketik nol).
    """
    x_items = X1_COLS + X2_COLS + X3_COLS + X4_COLS
    out = pd.DataFrame(index=df.index)
    out["flag_jawaban_seragam"] = (df[x_items].nunique(axis=1) == 1).astype(int)
    out["flag_omzet_turun_tajam"] = (
        (df["omzet_sebelum"] > 0) & (df["omzet_sesudah"] <= RASIO_TURUN_TAJAM * df["omzet_sebelum"])
    ).astype(int)
    return out


# ---------------------------------------------------------------------------
# Reliabilitas
# ---------------------------------------------------------------------------
def cronbach_alpha(items: pd.DataFrame) -> float:
    """Cronbach's alpha: k/(k-1) * (1 - jumlah varians butir / varians skor total)."""
    items = items.dropna()
    k = items.shape[1]
    if k < 2:
        return np.nan
    var_items = items.var(axis=0, ddof=1).sum()
    var_total = items.sum(axis=1).var(ddof=1)
    if var_total == 0:
        return np.nan
    return float(k / (k - 1) * (1 - var_items / var_total))


def reliabilitas_item(items: pd.DataFrame) -> pd.DataFrame:
    """Per butir: korelasi butir-total terkoreksi dan alpha jika butir dihapus."""
    rows = []
    for col in items.columns:
        sisa = items.drop(columns=col)
        rows.append(
            {
                "butir": col,
                "rata_rata": items[col].mean(),
                "sd": items[col].std(ddof=1),
                "korelasi_butir_total": items[col].corr(sisa.sum(axis=1)),
                "alpha_jika_dihapus": cronbach_alpha(sisa),
            }
        )
    return pd.DataFrame(rows)


def tabel_reliabilitas(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tabel reliabilitas tingkat konstruk dan tingkat butir untuk semua konstruk."""
    ringkas, per_butir = [], []
    for nama, cols in KONSTRUK.items():
        items = df[cols]
        alpha = cronbach_alpha(items)
        rel = reliabilitas_item(items)
        rel.insert(0, "konstruk", nama)
        rel["lolos_item_total"] = rel["korelasi_butir_total"] >= ITEM_TOTAL_MIN
        rel["alpha_naik_jika_dihapus"] = rel["alpha_jika_dihapus"] > alpha
        per_butir.append(rel)
        ringkas.append(
            {
                "konstruk": nama,
                "peran": "pendukung" if nama == "y_persepsi" else "strategi",
                "n_butir": len(cols),
                "n_responden": len(items.dropna()),
                "alpha": alpha,
                "lolos_alpha": alpha >= ALPHA_MIN,
                "min_korelasi_butir_total": rel["korelasi_butir_total"].min(),
                "butir_di_bawah_0_30": ", ".join(rel.loc[~rel["lolos_item_total"], "butir"]),
            }
        )
    return pd.DataFrame(ringkas), pd.concat(per_butir, ignore_index=True)


# ---------------------------------------------------------------------------
# Skor dan target
# ---------------------------------------------------------------------------
def skor_konstruk(df: pd.DataFrame) -> pd.DataFrame:
    """Skor konstruk = rata-rata butir (skala 1-5)."""
    return pd.DataFrame({nama: df[cols].mean(axis=1) for nama, cols in KONSTRUK.items()})


def arah(delta: pd.Series) -> pd.Series:
    """Kategori 'naik' / 'sama' / 'turun' / 'kosong' dari selisih."""
    return pd.Series(
        np.select(
            [delta.isna(), delta > 0, delta < 0],
            ["kosong", "naik", "turun"],
            "sama",
        ),
        index=delta.index,
    )


def pertumbuhan_persen(sebelum: pd.Series, sesudah: pd.Series) -> pd.Series:
    """Pertumbuhan persen untuk pelaporan; kosong jika sebelum = 0 atau tidak ada."""
    return ((sesudah - sebelum) / sebelum * 100).where(sebelum > 0)


def zscore(x: pd.Series, ref: pd.Series) -> pd.Series:
    """Standarkan x memakai rata-rata dan simpangan baku dari `ref`."""
    return (x - ref.mean()) / ref.std(ddof=1)


def target_kinerja(df: pd.DataFrame, sampel_ref: pd.Series) -> pd.DataFrame:
    """Hitung d_omzet, d_trx, naik_penjualan, y_obj, y_pelanggan_baru (D02, D04, D06, D13).

    - naik_penjualan = 1 jika d_omzet > 0 ATAU d_trx > 0; d_trx kosong (D17) dianggap
      tidak naik sehingga responden itu dinilai dari omzet saja.
    - y_obj = rata-rata z(d_omzet) dan z(d_trx), mengabaikan yang kosong. Standardisasi memakai
      sampel utama (`sampel_ref`) agar skalanya sesuai analisis utama (D14).
    """
    out = pd.DataFrame(index=df.index)
    out["d_omzet"] = np.log1p(df["omzet_sesudah_w"]) - np.log1p(df["omzet_sebelum_w"])
    out["d_trx"] = np.log1p(df["trx_sesudah_w"]) - np.log1p(df["trx_sebelum_w"])
    out["arah_omzet"] = arah(out["d_omzet"])
    out["arah_trx"] = arah(out["d_trx"])
    out["pct_omzet"] = pertumbuhan_persen(df["omzet_sebelum_w"], df["omzet_sesudah_w"])
    out["pct_trx"] = pertumbuhan_persen(df["trx_sebelum_w"], df["trx_sesudah_w"])
    out["naik_penjualan"] = ((out["d_omzet"] > 0) | (out["d_trx"] > 0)).astype(int)
    ref = sampel_ref.astype(bool)
    z_omzet = zscore(out["d_omzet"], out.loc[ref, "d_omzet"])
    z_trx = zscore(out["d_trx"], out.loc[ref, "d_trx"])
    out["y_obj"] = pd.concat([z_omzet, z_trx], axis=1).mean(axis=1, skipna=True)
    out["y_pelanggan_baru"] = np.log1p(df["pelanggan_baru"])
    return out


# ---------------------------------------------------------------------------
# Fitur profil
# ---------------------------------------------------------------------------
def batas_skala_omzet(omzet_sebelum: pd.Series) -> list[float]:
    """Batas kuartil omzet sebelum (Q1, median, Q3) untuk kategori skala_omzet."""
    return [float(q) for q in omzet_sebelum.quantile([0.25, 0.5, 0.75])]


def skala_omzet(omzet_sebelum: pd.Series, batas: list[float]) -> pd.Series:
    """Kategori skala usaha dari omzet sebelum, memakai batas kuartil yang sudah ditentukan."""
    edges = [-np.inf, *batas, np.inf]
    return pd.cut(omzet_sebelum, bins=edges, labels=SKALA_LABELS, right=True).astype("string")


def fitur_profil(df: pd.DataFrame, batas: list[float]) -> pd.DataFrame:
    """Fitur profil UMKM. Hanya memakai kondisi sebelum/umum, tidak memakai target."""
    out = df[["lama_usaha_pra_mp", "lama_di_mp", "jumlah_platform", *PLATFORM_COLS]].copy()
    out["log_omzet_sebelum"] = np.log1p(df["omzet_sebelum_w"])
    out["skala_omzet"] = skala_omzet(df["omzet_sebelum_w"], batas)
    return out


# ---------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------
@dataclass
class FeaturesReport:
    """Ringkasan Tahap 2 untuk ditulis ke reports/features_log.md."""

    reliabilitas: pd.DataFrame = field(default_factory=pd.DataFrame)
    reliabilitas_butir: pd.DataFrame = field(default_factory=pd.DataFrame)
    sebaran_arah: pd.DataFrame = field(default_factory=pd.DataFrame)
    kelas: pd.DataFrame = field(default_factory=pd.DataFrame)
    batas_skala: list[float] = field(default_factory=list)
    ringkas_target: pd.DataFrame = field(default_factory=pd.DataFrame)
    korelasi_strategi: pd.DataFrame = field(default_factory=pd.DataFrame)
    blok_seragam: pd.Series = field(default_factory=pd.Series)
    turun_tajam: pd.DataFrame = field(default_factory=pd.DataFrame)


def build_features(clean: pd.DataFrame) -> tuple[pd.DataFrame, FeaturesReport]:
    """Bangun data_features dari data_clean. Data masukan tidak diubah."""
    rep = FeaturesReport()
    rep.reliabilitas, rep.reliabilitas_butir = tabel_reliabilitas(clean)

    out = clean[["id_responden"]].copy()
    out["tanpa_baseline"] = (clean["lama_usaha_pra_mp"] == 0).astype(int)
    out["sampel_utama"] = 1 - out["tanpa_baseline"]

    out = out.join(skor_konstruk(clean))
    rep.batas_skala = batas_skala_omzet(clean["omzet_sebelum_w"])
    out = out.join(fitur_profil(clean, rep.batas_skala))
    out = out.join(target_kinerja(clean, out["sampel_utama"]))

    flags = [c for c in clean.columns if c.startswith("flag_")]
    out = out.join(clean[flags]).join(flag_kualitas(clean))
    out = out.join(clean[[c for c in clean.columns if c.startswith(("x1_", "x2_", "x3_", "x4_"))]])

    rep.sebaran_arah = _sebaran_arah(out)
    rep.kelas = _ukuran_kelas(out)
    rep.ringkas_target = _ringkas_target(out)
    rep.korelasi_strategi = out[STRATEGI_COLS].corr(method="spearman")
    rep.blok_seragam = (
        sum(
            (clean[cols].nunique(axis=1) == 1).astype(int)
            for cols in (X1_COLS, X2_COLS, X3_COLS, X4_COLS)
        )
        .value_counts()
        .sort_index()
    )
    tajam = out["flag_omzet_turun_tajam"] == 1
    rep.turun_tajam = clean.loc[
        tajam, ["id_responden", "omzet_sebelum", "omzet_sesudah", "trx_sebelum", "trx_sesudah"]
    ].assign(
        sampel_utama=out.loc[tajam, "sampel_utama"],
        naik_penjualan=out.loc[tajam, "naik_penjualan"],
        y_obj=out.loc[tajam, "y_obj"],
    )
    return out, rep


def _sebaran_arah(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sampel, sel in (("semua_149", df.index == df.index), ("utama", df["sampel_utama"] == 1)):
        for var in ("omzet", "trx"):
            vc = df.loc[sel, f"arah_{var}"].value_counts()
            rows.append(
                {
                    "sampel": sampel,
                    "variabel": var,
                    **{k: int(vc.get(k, 0)) for k in ("naik", "sama", "turun", "kosong")},
                }
            )
    return pd.DataFrame(rows)


def _ukuran_kelas(df: pd.DataFrame) -> pd.DataFrame:
    tab = pd.crosstab(
        df["tanpa_baseline"].map({0: "punya_baseline (utama)", 1: "tanpa_baseline"}),
        df["naik_penjualan"].map({1: "naik", 0: "tidak_naik"}),
        margins=True,
        margins_name="total",
    )
    return tab.reset_index().rename(columns={"tanpa_baseline": "kelompok"})


def _ringkas_target(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["d_omzet", "d_trx", "y_obj", "y_pelanggan_baru", *STRATEGI_COLS, "y_persepsi"]
    rows = []
    for sampel, sel in (("semua_149", df.index == df.index), ("utama", df["sampel_utama"] == 1)):
        desc = df.loc[sel, cols].describe().T
        desc.insert(0, "sampel", sampel)
        rows.append(desc.reset_index().rename(columns={"index": "variabel"}))
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------------------
# Log markdown
# ---------------------------------------------------------------------------
def _md(df: pd.DataFrame, floatfmt: str = "{:.2f}") -> str:
    if df.empty:
        return "_(tidak ada)_\n"
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (bool, np.bool_)):
                cells.append("ya" if v else "TIDAK")
            elif isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def build_log(rep: FeaturesReport, df: pd.DataFrame) -> str:
    """Susun reports/features_log.md."""
    s = ["# Log Konstruksi Variabel (Tahap 2)\n"]
    s.append(f"Dibuat oleh `umkm.features` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}.\n")
    s.append(
        f"- data_features.csv: {df.shape[0]} baris x {df.shape[1]} kolom. "
        f"Sampel utama (D14): {int(df['sampel_utama'].sum())} responden; "
        f"`tanpa_baseline` = {int(df['tanpa_baseline'].sum())}.\n"
    )

    s.append("## 1. Reliabilitas konstruk (semua 149 responden)\n")
    s.append(
        f"Kriteria: alpha >= {ALPHA_MIN:.2f}; korelasi butir-total terkoreksi >= "
        f"{ITEM_TOTAL_MIN:.2f}. Tidak ada butir yang dibuang otomatis.\n"
    )
    s.append(_md(rep.reliabilitas, "{:.3f}"))
    s.append("\n### Per butir\n")
    s.append(_md(rep.reliabilitas_butir, "{:.3f}"))

    s.append("\n## 2. Sebaran arah perubahan\n")
    s.append(_md(rep.sebaran_arah))
    s.append("\n## 3. Target utama `naik_penjualan` (D13)\n")
    s.append(_md(rep.kelas))
    s.append(
        "\n`y_obj` = rata-rata z(d_omzet) dan z(d_trx); z memakai rata-rata/SD sampel utama. "
        "Untuk responden dengan transaksi kosong (D17), `y_obj` dan `naik_penjualan` dari omzet "
        "saja. `y_pelanggan_baru` = log1p(pelanggan_baru), target tambahan (D06).\n"
    )
    s.append("\n## 4. Statistik deskriptif\n")
    s.append(_md(rep.ringkas_target, "{:.3f}"))

    s.append("\n## 5. Fitur profil\n")
    b = rep.batas_skala
    s.append(
        f"`skala_omzet` dari kuartil omzet_sebelum_w (149 responden): Q1 <= {b[0]:,.0f}; "
        f"Q2 <= {b[1]:,.0f}; Q3 <= {b[2]:,.0f}; Q4 di atasnya.\n"
    )
    vc = df["skala_omzet"].value_counts().sort_index()
    s.append(", ".join(f"{k} = {v}" for k, v in vc.items()) + ".\n")
    s.append(
        "\nCatatan: untuk responden `tanpa_baseline`, omzet sebelum praktis sama dengan omzet saat "
        "ini, jadi `skala_omzet` mereka mencerminkan omzet sekarang.\n"
    )

    s.append("\n## 6. Pemeriksaan kebocoran (leakage)\n")
    s.append(
        "- Fitur strategi (x1-x4) hanya dari butir Likert X; fitur profil hanya dari lama usaha, "
        "platform, dan omzet SEBELUM.\n"
        "- `y_persepsi` dan `pelanggan_baru` tidak dipakai sebagai fitur.\n"
        "- Catatan: `log_omzet_sebelum` ikut menyusun `d_omzet` (sebagai pengurang). Ini bukan "
        "kebocoran (kondisi awal), tetapi bisa memunculkan efek regresi ke rata-rata; di Tahap 4 "
        "dilaporkan model dengan dan tanpa variabel ini.\n"
    )

    s.append("\n## 7. Korelasi antar strategi (Spearman, 149 responden)\n")
    s.append(_md(rep.korelasi_strategi.round(2).reset_index().rename(columns={"index": ""})))
    s.append(
        "\nKorelasi rendah-sedang berarti keempat strategi terukur sebagai hal yang berbeda "
        "(validitas diskriminan memadai); VIF diperiksa di Tahap 3.\n"
    )

    s.append("\n## 8. Kualitas jawaban (hanya ditandai)\n")
    n_seragam = int(df["flag_jawaban_seragam"].sum())
    s.append(
        f"- `flag_jawaban_seragam`: {n_seragam} responden menjawab 18 butir strategi dengan angka "
        "yang sama persis (indikasi straightlining)."
    )
    s.append(
        "- Jumlah blok strategi (dari 4) yang dijawab seragam per responden: "
        + ", ".join(f"{k} blok = {v}" for k, v in rep.blok_seragam.items())
        + ". Pola ini ikut menjelaskan alpha yang sangat tinggi (> 0,9)."
    )
    s.append(
        f"- `flag_omzet_turun_tajam` (omzet sesudah <= {RASIO_TURUN_TAJAM:.0%} omzet sebelum):\n"
    )
    s.append(_md(rep.turun_tajam, "{:,.2f}"))
    s.append(
        "\nR065, R130 (turun tepat 10x) dan R106 sudah dikoreksi lewat konfirmasi responden (D25). "
        "Yang tersisa di tabel ini adalah isian yang dikonfirmasi responden sendiri; "
        "nilainya memengaruhi `y_obj`, tetapi tidak memengaruhi `naik_penjualan`.\n"
    )
    return "\n".join(s)


def run(cfg: dict[str, Any] | None = None) -> tuple[pd.DataFrame, FeaturesReport]:
    """Baca data_clean.csv, bangun fitur, tulis data_features.csv, tabel, dan log."""
    from umkm import config, io

    proc = config.path("processed")
    tables = config.path("reports") / "tables"
    clean = pd.read_csv(proc / "data_clean.csv")
    df, rep = build_features(clean)
    io.write_csv(df, proc / "data_features.csv")
    io.write_csv(rep.reliabilitas, tables / "reliabilitas.csv")
    io.write_csv(rep.reliabilitas_butir, tables / "reliabilitas_butir.csv")
    io.write_csv(rep.sebaran_arah, tables / "sebaran_arah_kinerja.csv")
    io.write_csv(rep.kelas, tables / "ukuran_kelas_naik_penjualan.csv")
    io.write_csv(rep.korelasi_strategi.reset_index(), tables / "korelasi_antar_strategi.csv")
    io.write_text(build_log(rep, df), config.path("reports") / "features_log.md")
    return df, rep
