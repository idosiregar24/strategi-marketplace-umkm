"""Tahap 1: cleaning data kuesioner.

Semua fungsi parsing bersifat murni dan menerima satu nilai; fungsi tingkat DataFrame
menerima satu baris maupun banyak baris sehingga dapat dipakai ulang untuk data baru.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Nama kolom (urutan sesuai .claude/guides/data_dictionary.md)
# ---------------------------------------------------------------------------
X1_COLS = [f"x1_unggah_{i}" for i in range(1, 5)]
X2_COLS = [f"x2_promosi_{i}" for i in range(1, 5)]
X3_COLS = [f"x3_komunikasi_{i}" for i in range(1, 6)]
X4_COLS = [f"x4_konsistensi_{i}" for i in range(1, 6)]
Y_PERSEPSI_COLS = [f"y_persepsi_{i}" for i in range(1, 9)]
LIKERT_COLS = X1_COLS + X2_COLS + X3_COLS + X4_COLS + Y_PERSEPSI_COLS

RAW_COLUMNS = (
    ["timestamp", "score", "nama_usaha", "lama_usaha_pra_mp", "lama_di_mp", "platform_raw"]
    + LIKERT_COLS
    + [
        "omzet_sebelum_raw",
        "omzet_sesudah_raw",
        "trx_sebelum_raw",
        "trx_sesudah_raw",
        "pelanggan_baru",
    ]
)

OMZET_COLS = ["omzet_sebelum", "omzet_sesudah"]
TRX_COLS = ["trx_sebelum", "trx_sesudah"]
LAMA_COLS = ["lama_usaha_pra_mp", "lama_di_mp"]

# Label yang diharapkan per blok Likert (angka -> teks label, huruf kecil).
_SERING = {1: "tidak pernah", 2: "jarang", 3: "cukup sering", 4: "sering", 5: "sangat sering"}
EXPECTED_LABELS: dict[str, dict[int, str]] = {
    "x1": _SERING,
    "x2": {k: f"{v} memanfaatkan" for k, v in _SERING.items()},
    "x3": {
        1: "sangat tidak sesuai",
        2: "tidak sesuai",
        3: "cukup sesuai",
        4: "sesuai",
        5: "sangat sesuai",
    },
    "x4": {
        1: "sangat tidak konsisten",
        2: "tidak konsisten",
        3: "cukup konsisten",
        4: "konsisten",
        5: "sangat konsisten",
    },
    "y": {
        1: "sangat tidak setuju",
        2: "tidak setuju",
        3: "netral",
        4: "setuju",
        5: "sangat setuju",
    },
}

# Kata kunci teks platform -> nama kolom biner.
PLATFORM_KEYWORDS: dict[str, str] = {
    "gofood": "mp_gofood",
    "grabfood": "mp_grabfood",
    "shopee": "mp_shopee",
    "maxim": "mp_maxim",
    "tiktok": "mp_tiktok",
}
PLATFORM_COLS = list(PLATFORM_KEYWORDS.values())

_LIKERT_RE = re.compile(r"^\s*(\d)\s*\.?\s*(.*)$")
_BULAN_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*bulan\s*$", re.IGNORECASE)
_TAHUN_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*(?:tahun|thn)?\s*$", re.IGNORECASE)
_RIBUAN_RE = re.compile(r"^\d{1,3}(?:[.,]\d{3})+$")
_DESIMAL_RE = re.compile(r"^\d+(?:[.,]\d+)?$")


# ---------------------------------------------------------------------------
# Parser nilai tunggal
# ---------------------------------------------------------------------------
def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and np.isnan(value)) or value is pd.NA


def parse_likert(value: Any) -> tuple[float, str]:
    """Ambil angka 1-5 di depan label Likert. Mengembalikan (angka, teks label huruf kecil)."""
    if _is_missing(value):
        return np.nan, ""
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value), ""
    m = _LIKERT_RE.match(str(value))
    if not m:
        return np.nan, ""
    label = re.sub(r"\s+", " ", m.group(2)).strip().lower()
    return float(m.group(1)), label


def parse_angka(value: Any) -> float:
    """Ubah isian angka (omzet/transaksi) ke float.

    Menangani pemisah ribuan titik/koma ("3.500.000"), awalan "Rp", dan angka desimal
    ("2.65"). Nilai yang tak terbaca menjadi NaN.
    """
    if _is_missing(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    s = re.sub(r"(?i)rp", "", str(value)).replace(" ", "").strip()
    if not s:
        return np.nan
    if _RIBUAN_RE.match(s):
        return float(re.sub(r"[.,]", "", s))
    if _DESIMAL_RE.match(s):
        return float(s.replace(",", "."))
    return np.nan


def parse_lama(value: Any, tahun_referensi: int) -> tuple[float, int]:
    """Ubah isian lama usaha ke tahun. Mengembalikan (tahun, flag_tahun_kalender).

    - "N bulan" -> N/12
    - angka >= 1900 dianggap tahun kalender -> tahun_referensi - angka, flag 1
    - angka lain -> tahun
    """
    if _is_missing(value):
        return np.nan, 0
    if isinstance(value, (int, float, np.integer, np.floating)):
        num = float(value)
    else:
        s = str(value).strip()
        m = _BULAN_RE.match(s)
        if m:
            return float(m.group(1).replace(",", ".")) / 12, 0
        m = _TAHUN_RE.match(s)
        if not m:
            return np.nan, 0
        num = float(m.group(1).replace(",", "."))
    if num >= 1900:
        return float(tahun_referensi - num), 1
    return num, 0


def parse_platform(value: Any) -> dict[str, int]:
    """Pecah teks multi-pilihan platform menjadi dict kolom biner mp_*."""
    teks = "" if _is_missing(value) else str(value).lower()
    return {col: int(kw in teks) for kw, col in PLATFORM_KEYWORDS.items()}


def unknown_platforms(value: Any) -> list[str]:
    """Daftar pilihan platform yang tidak dikenali kata kuncinya."""
    if _is_missing(value):
        return []
    parts = [p.strip() for p in str(value).split(",") if p.strip()]
    return [p for p in parts if not any(kw in p.lower() for kw in PLATFORM_KEYWORDS)]


# ---------------------------------------------------------------------------
# Transformasi DataFrame
# ---------------------------------------------------------------------------
def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ganti nama 37 kolom mentah berdasarkan urutan posisi."""
    if df.shape[1] != len(RAW_COLUMNS):
        raise ValueError(f"Diharapkan {len(RAW_COLUMNS)} kolom, didapat {df.shape[1]}")
    out = df.copy()
    out.columns = RAW_COLUMNS
    return out


def parse_timestamp(series: pd.Series) -> pd.Series:
    """Timestamp bisa berupa datetime, teks, atau serial Excel; semuanya diubah ke datetime.

    Versi pandas berbeda membaca sel tanggal Excel sebagai datetime atau sebagai angka serial,
    jadi angka dipisahkan dulu agar datetime tidak ikut dikonversi sebagai jumlah hari.
    """
    is_num = series.map(
        lambda v: isinstance(v, (int, float, np.integer, np.floating)) and not pd.isna(v)
    ).astype(bool)
    serial = pd.to_numeric(series.where(is_num), errors="coerce").astype(float)
    from_serial = pd.to_datetime(serial, unit="D", origin="1899-12-30", errors="coerce")
    from_other = pd.to_datetime(series.where(~is_num), errors="coerce")
    return from_serial.where(is_num, from_other).dt.round("s")


def likert_block(col: str) -> str:
    """Blok Likert dari nama kolom: 'x1'..'x4' atau 'y'."""
    return "y" if col.startswith("y_") else col[:2]


def parse_likert_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ubah semua kolom Likert ke angka; kembalikan juga tabel audit label vs angka."""
    out = df.copy()
    mismatches = []
    for col in LIKERT_COLS:
        expected = EXPECTED_LABELS[likert_block(col)]
        parsed = out[col].map(parse_likert)
        for idx, (num, label), raw in zip(out.index, parsed, out[col]):
            if label and not np.isnan(num) and label != expected.get(int(num)):
                mismatches.append(
                    {
                        "baris": idx,
                        "kolom": col,
                        "nilai_asli": raw,
                        "angka_dipakai": int(num),
                        "label_harapan": expected.get(int(num), "?"),
                    }
                )
        out[col] = parsed.map(lambda t: t[0])
    return out, pd.DataFrame(
        mismatches, columns=["baris", "kolom", "nilai_asli", "angka_dipakai", "label_harapan"]
    )


def parse_lama_columns(df: pd.DataFrame, tahun_referensi: int) -> pd.DataFrame:
    """Ubah kolom lama usaha ke tahun; simpan nilai asli di *_raw dan flag tahun kalender."""
    out = df.copy()
    flag = pd.Series(0, index=out.index)
    for col in LAMA_COLS:
        out[f"{col}_raw"] = out[col].astype("string")
        parsed = out[col].map(lambda v: parse_lama(v, tahun_referensi))
        out[col] = parsed.map(lambda t: t[0])
        out[f"flag_kalender_{col}"] = parsed.map(lambda t: t[1]).astype(int)
        flag = flag | out[f"flag_kalender_{col}"]
    out["flag_lama_tahun_kalender"] = flag.astype(int)
    return out


def parse_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Parse omzet, transaksi, dan pelanggan baru ke angka; nilai asli tetap di *_raw."""
    out = df.copy()
    for col in OMZET_COLS + TRX_COLS:
        out[f"{col}_raw"] = out[f"{col}_raw"].astype("string")
        out[col] = out[f"{col}_raw"].map(parse_angka)
    out["pelanggan_baru"] = out["pelanggan_baru"].map(parse_angka)
    return out


def add_platform_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Tambah kolom biner mp_* dan jumlah_platform dari platform_raw."""
    out = df.copy()
    flags = pd.DataFrame(out["platform_raw"].map(parse_platform).tolist(), index=out.index)
    out[PLATFORM_COLS] = flags[PLATFORM_COLS].astype(int)
    out["jumlah_platform"] = out[PLATFORM_COLS].sum(axis=1).astype(int)
    return out


def flag_trx_tidak_wajar(df: pd.DataFrame, trx_maks_wajar: float) -> pd.DataFrame:
    """Tandai transaksi pecahan, di atas batas wajar, atau sama persis dengan omzet baris itu."""
    out = df.copy()
    pecahan = pd.Series(False, index=out.index)
    besar = pd.Series(False, index=out.index)
    sama_omzet = pd.Series(False, index=out.index)
    for trx, omzet in zip(TRX_COLS, OMZET_COLS):
        v = out[trx]
        pecahan |= v.notna() & (v % 1 != 0)
        besar |= v > trx_maks_wajar
        sama_omzet |= v.notna() & (v > 0) & (v == out[omzet])
    out["flag_trx_pecahan"] = pecahan.astype(int)
    out["flag_trx_tidak_wajar"] = (besar | sama_omzet).astype(int)
    return out


@dataclass
class WinsorBounds:
    """Batas winsorizing per variabel (dihitung gabungan sebelum + sesudah)."""

    bounds: dict[str, tuple[float | None, float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, dict[str, float]]:
        return {k: {"bawah": lo, "atas": hi} for k, (lo, hi) in self.bounds.items()}


def fit_winsor_bounds(df: pd.DataFrame, lower: float | None, upper: float) -> WinsorBounds:
    """Hitung batas persentil untuk omzet dan transaksi.

    Sebelum dan sesudah digabung agar satu variabel memakai batas yang sama; dengan begitu
    responden yang nilainya tidak berubah tetap tidak berubah setelah winsorizing.
    `lower=None` berarti ekor bawah tidak dibatasi (D16).
    """
    wb = WinsorBounds()
    for nama, cols in (("omzet", OMZET_COLS), ("trx", TRX_COLS)):
        pooled = pd.concat([df[c] for c in cols]).dropna().to_numpy()
        wb.bounds[nama] = (
            None if lower is None else float(np.quantile(pooled, lower)),
            float(np.quantile(pooled, upper)),
        )
    return wb


def apply_winsor(df: pd.DataFrame, wb: WinsorBounds) -> pd.DataFrame:
    """Tambah kolom *_w (terwinsor), flag per kolom, dan flag_outlier gabungan."""
    out = df.copy()
    any_flag = pd.Series(False, index=out.index)
    for nama, cols in (("omzet", OMZET_COLS), ("trx", TRX_COLS)):
        lo, hi = wb.bounds[nama]
        for col in cols:
            out[f"{col}_w"] = out[col].clip(lower=lo, upper=hi)
            changed = out[col].notna() & (out[col] != out[f"{col}_w"])
            out[f"flag_winsor_{col}"] = changed.astype(int)
            any_flag |= changed
    out["flag_outlier"] = any_flag.astype(int)
    return out


def arah_perubahan(sebelum: pd.Series, sesudah: pd.Series) -> pd.Series:
    """Kategori 'naik' / 'sama' / 'turun' dari pasangan nilai sebelum dan sesudah."""
    return pd.Series(
        np.select([sesudah > sebelum, sesudah < sebelum], ["naik", "turun"], "sama"),
        index=sebelum.index,
    )


def arah_berubah(df: pd.DataFrame) -> pd.DataFrame:
    """Responden yang kategori naik/sama/turun-nya berbeda antara nilai asli dan terwinsor."""
    rows = []
    for nama in ("omzet", "trx"):
        asli = arah_perubahan(df[f"{nama}_sebelum"], df[f"{nama}_sesudah"])
        w = arah_perubahan(df[f"{nama}_sebelum_w"], df[f"{nama}_sesudah_w"])
        for idx in df.index[asli != w]:
            rows.append(
                {
                    "id_responden": df.at[idx, "id_responden"],
                    "variabel": nama,
                    "arah_asli": asli[idx],
                    "arah_terwinsor": w[idx],
                }
            )
    return pd.DataFrame(rows, columns=["id_responden", "variabel", "arah_asli", "arah_terwinsor"])


def find_duplicates(df: pd.DataFrame) -> dict[str, list[list[Any]]]:
    """Kelompok id_responden dengan nama usaha sama, dan dengan pola jawaban identik."""
    nama = df["nama_usaha"].astype("string").str.strip().str.lower()
    jawaban_cols = LIKERT_COLS + OMZET_COLS + TRX_COLS + ["pelanggan_baru"] + LAMA_COLS
    by_nama = df.groupby(nama, dropna=True)
    by_pola = df.groupby(jawaban_cols, dropna=False)
    return {
        key: [g["id_responden"].tolist() for _, g in grouped if len(g) > 1]
        for key, grouped in (("nama_usaha", by_nama), ("pola_jawaban", by_pola))
    }


# ---------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------
@dataclass
class CleaningReport:
    """Ringkasan kejadian selama cleaning, dipakai untuk menulis cleaning_log.md."""

    shape_raw: tuple[int, int]
    shape_clean: tuple[int, int] = (0, 0)
    likert_mismatch: pd.DataFrame = field(default_factory=pd.DataFrame)
    likert_out_of_range: int = 0
    lama_bulan: dict[str, int] = field(default_factory=dict)
    lama_kalender: pd.DataFrame = field(default_factory=pd.DataFrame)
    angka_teks_ribuan: dict[str, int] = field(default_factory=dict)
    angka_tak_terbaca: pd.DataFrame = field(default_factory=pd.DataFrame)
    nol: dict[str, int] = field(default_factory=dict)
    platform_tak_dikenal: list[str] = field(default_factory=list)
    trx_flagged: pd.DataFrame = field(default_factory=pd.DataFrame)
    winsor: WinsorBounds = field(default_factory=WinsorBounds)
    winsor_rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    winsor_bawah_mengubah_nol: dict[str, int] = field(default_factory=dict)
    duplikat: dict[str, list[list[Any]]] = field(default_factory=dict)
    missing: dict[str, int] = field(default_factory=dict)
    score_konstan: bool = True


def clean(raw: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, CleaningReport]:
    """Jalankan seluruh langkah cleaning Tahap 1. Data masukan tidak diubah."""
    c = cfg["cleaning"]
    rep = CleaningReport(shape_raw=raw.shape)
    df = rename_columns(raw)

    rep.score_konstan = df["score"].nunique(dropna=False) == 1
    df = df.drop(columns=["score"])
    df.insert(0, "id_responden", [f"R{i:03d}" for i in range(1, len(df) + 1)])
    df["timestamp"] = parse_timestamp(df["timestamp"])
    df["nama_usaha"] = df["nama_usaha"].astype("string").str.strip()

    # Likert
    df, mismatch = parse_likert_columns(df)
    mismatch["id_responden"] = df.loc[mismatch["baris"], "id_responden"].to_numpy()
    rep.likert_mismatch = mismatch.drop(columns="baris")
    rep.likert_out_of_range = int((~df[LIKERT_COLS].isin([1, 2, 3, 4, 5])).sum().sum())

    # Lama usaha
    for col in LAMA_COLS:
        rep.lama_bulan[col] = int(
            df[col].astype("string").str.contains("bulan", case=False, na=False).sum()
        )
    df = parse_lama_columns(df, c["tahun_referensi"])
    kal_rows = []
    for col in LAMA_COLS:
        sel = df[f"flag_kalender_{col}"] == 1
        for _, r in df[sel].iterrows():
            kal_rows.append(
                {
                    "id_responden": r["id_responden"],
                    "kolom": col,
                    "nilai_asli": r[f"{col}_raw"],
                    "hasil_tahun": r[col],
                }
            )
    rep.lama_kalender = pd.DataFrame(
        kal_rows, columns=["id_responden", "kolom", "nilai_asli", "hasil_tahun"]
    )

    # Omzet, transaksi, pelanggan baru
    for col in OMZET_COLS + TRX_COLS:
        raw_col = df[f"{col}_raw"]
        rep.angka_teks_ribuan[col] = int(
            raw_col.map(lambda v: isinstance(v, str) and bool(_RIBUAN_RE.match(v.strip()))).sum()
        )
    df = parse_numeric_columns(df)
    unread = []
    for col in OMZET_COLS + TRX_COLS:
        sel = df[col].isna() & df[f"{col}_raw"].notna()
        for _, r in df[sel].iterrows():
            unread.append(
                {"id_responden": r["id_responden"], "kolom": col, "nilai": r[f"{col}_raw"]}
            )
    rep.angka_tak_terbaca = pd.DataFrame(unread, columns=["id_responden", "kolom", "nilai"])
    rep.nol = {col: int((df[col] == 0).sum()) for col in OMZET_COLS + TRX_COLS + ["pelanggan_baru"]}

    # Platform
    rep.platform_tak_dikenal = sorted({p for v in df["platform_raw"] for p in unknown_platforms(v)})
    df = add_platform_columns(df)

    # Transaksi tidak wajar: ditandai, lalu dikosongkan bila diatur di config (D17)
    df = flag_trx_tidak_wajar(df, c["trx_maks_wajar"])
    sel = (df["flag_trx_tidak_wajar"] == 1) | (df["flag_trx_pecahan"] == 1)
    rep.trx_flagged = df.loc[
        sel,
        ["id_responden", *OMZET_COLS, *TRX_COLS, "flag_trx_pecahan", "flag_trx_tidak_wajar"],
    ].reset_index(drop=True)
    kosongkan = sel if c.get("kosongkan_trx_janggal", False) else pd.Series(False, index=df.index)
    df.loc[kosongkan, TRX_COLS] = np.nan
    df["flag_trx_dikosongkan"] = kosongkan.astype(int)

    # Winsorizing (D03)
    rep.winsor = fit_winsor_bounds(df, c["winsor_lower"], c["winsor_upper"])
    df = apply_winsor(df, rep.winsor)
    rep.winsor_rows = df.loc[
        df["flag_outlier"] == 1,
        ["id_responden"] + [x for col in OMZET_COLS + TRX_COLS for x in (col, f"{col}_w")],
    ].reset_index(drop=True)
    rep.winsor_bawah_mengubah_nol = {
        col: int(((df[col] == 0) & (df[f"{col}_w"] > 0)).sum()) for col in OMZET_COLS + TRX_COLS
    }

    # Duplikat (hanya dilaporkan)
    rep.duplikat = find_duplicates(df)

    df = df[_ordered_columns(df)]
    rep.missing = {k: int(v) for k, v in df.isna().sum().items() if v > 0}
    rep.shape_clean = df.shape
    return df, rep


def _ordered_columns(df: pd.DataFrame) -> list[str]:
    """Urutan kolom keluaran: ID, profil, Likert, angka kinerja, flag."""
    first = ["id_responden", "timestamp", "nama_usaha"]
    profil = [
        "lama_usaha_pra_mp",
        "lama_usaha_pra_mp_raw",
        "lama_di_mp",
        "lama_di_mp_raw",
        "platform_raw",
        *PLATFORM_COLS,
        "jumlah_platform",
    ]
    angka = [x for col in OMZET_COLS + TRX_COLS for x in (f"{col}_raw", col, f"{col}_w")] + [
        "pelanggan_baru"
    ]
    used = set(first + profil + LIKERT_COLS + angka)
    flags = sorted(c for c in df.columns if c.startswith("flag_") and c not in used)
    rest = [c for c in df.columns if c not in used and c not in flags]
    return first + profil + LIKERT_COLS + angka + flags + rest


# ---------------------------------------------------------------------------
# Log markdown
# ---------------------------------------------------------------------------
def _md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_(tidak ada)_\n"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(_fmt(r[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def _fmt(v: Any) -> str:
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return ""
        return f"{v:,.0f}" if abs(v) >= 1000 or v == int(v) else f"{v:.2f}"
    return str(v)


def build_log(rep: CleaningReport, df: pd.DataFrame, cfg: dict[str, Any]) -> str:
    """Susun reports/cleaning_log.md dari CleaningReport."""
    c = cfg["cleaning"]
    mm = rep.likert_mismatch
    mm_summary = (
        mm.groupby(["kolom", "nilai_asli", "angka_dipakai", "label_harapan"])
        .size()
        .reset_index(name="jumlah")
        if not mm.empty
        else mm
    )
    wb = rep.winsor.bounds
    winsor_counts = {col: int(df[f"flag_winsor_{col}"].sum()) for col in OMZET_COLS + TRX_COLS}
    dup = rep.duplikat

    s = []
    s.append("# Log Cleaning (Tahap 1)\n")
    s.append(f"Dibuat oleh `umkm.cleaning` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}.\n")
    s.append("## Ringkasan\n")
    s.append(f"- Data mentah: {rep.shape_raw[0]} baris x {rep.shape_raw[1]} kolom.")
    s.append(f"- Data bersih: {rep.shape_clean[0]} baris x {rep.shape_clean[1]} kolom.")
    s.append(
        f"- Kolom `score` {'konstan, dibuang' if rep.score_konstan else 'TIDAK konstan (periksa!)'}."
    )
    s.append("- `nama_usaha` hanya sebagai pengenal; laporan memakai `id_responden` (R001-R149).")
    s.append(f"- Nilai Likert di luar 1-5 atau kosong: {rep.likert_out_of_range}.")
    s.append(
        "- Missing setelah cleaning: "
        + (", ".join(f"`{k}`={v}" for k, v in rep.missing.items()) or "tidak ada")
        + ".\n"
    )

    s.append("## 1. Likert: audit label vs angka\n")
    s.append(
        f"Ditemukan {len(mm)} sel dengan label yang tidak cocok dengan angkanya "
        f"({mm['id_responden'].nunique() if not mm.empty else 0} responden). "
        "Sesuai rencana, yang dipakai adalah ANGKA.\n"
    )
    s.append(_md_table(mm_summary))
    if not mm.empty:
        s.append("\nResponden terdampak: " + ", ".join(sorted(mm["id_responden"].unique())) + "\n")
    s.append(
        '\nVariasi format seperti "1.Tidak Pernah" (tanpa spasi) ditangani regex dan tidak '
        "dihitung sebagai ketidaksesuaian.\n"
    )

    s.append("## 2. Lama usaha\n")
    s.append(
        '- Isian "N bulan" diubah ke N/12 tahun: '
        + ", ".join(f"`{k}` = {v}" for k, v in rep.lama_bulan.items())
        + "."
    )
    s.append(
        f"- Isian tahun kalender (>= 1900) diubah ke {c['tahun_referensi']} - tahun "
        "(D10, DISEPAKATI), ditandai `flag_lama_tahun_kalender`:\n"
    )
    s.append(_md_table(rep.lama_kalender))
    for col in LAMA_COLS:
        s.append(
            f"- `{col}`: min {df[col].min():.2f}, median {df[col].median():.2f}, "
            f"maks {df[col].max():.2f}; bernilai 0 = {int((df[col] == 0).sum())}."
        )
    s.append("")

    s.append("## 3. Omzet, transaksi, pelanggan baru\n")
    s.append(
        "- Teks dengan titik pemisah ribuan yang diubah ke angka: "
        + ", ".join(f"`{k}` = {v}" for k, v in rep.angka_teks_ribuan.items())
        + "."
    )
    s.append(
        "- Nilai tak terbaca: "
        + (
            "tidak ada."
            if rep.angka_tak_terbaca.empty
            else "\n\n" + _md_table(rep.angka_tak_terbaca)
        )
    )
    s.append("- Jumlah nilai 0: " + ", ".join(f"`{k}` = {v}" for k, v in rep.nol.items()) + ".\n")

    s.append("### Transaksi tidak wajar (D17)\n")
    s.append(
        f"Kriteria `flag_trx_tidak_wajar`: transaksi > {c['trx_maks_wajar']:,} atau sama persis "
        "dengan omzet di baris yang sama. `flag_trx_pecahan`: transaksi bukan bilangan bulat.\n"
    )
    s.append(_md_table(rep.trx_flagged))
    n_kosong = int(df["flag_trx_dikosongkan"].sum())
    if n_kosong:
        s.append(
            f"\nTransaksi sebelum dan sesudah {n_kosong} responden di atas DIKOSONGKAN (NaN), "
            "ditandai `flag_trx_dikosongkan`. Nilai asli tetap di `trx_*_raw`; omzet dan jawaban "
            "lain responden ini tetap dipakai. Inilah satu-satunya sumber missing di data bersih.\n"
        )
    else:
        s.append("\nTransaksi di atas hanya ditandai, tidak diubah.\n")

    s.append("\n## 4. Platform\n")
    counts = df[PLATFORM_COLS].sum().astype(int)
    s.append(
        "- Pengguna per platform: " + ", ".join(f"`{k}` = {v}" for k, v in counts.items()) + "."
    )
    jp = df["jumlah_platform"].value_counts().sort_index()
    s.append(
        "- Sebaran `jumlah_platform`: "
        + ", ".join(f"{k} platform = {v}" for k, v in jp.items())
        + "."
    )
    s.append(
        "- Pilihan tak dikenal: "
        + (", ".join(rep.platform_tak_dikenal) if rep.platform_tak_dikenal else "tidak ada")
        + ".\n"
    )

    s.append("## 5. Winsorizing (D03, D16)\n")
    bawah = (
        "ekor bawah tidak dibatasi (D16)"
        if c["winsor_lower"] is None
        else f"persentil bawah {c['winsor_lower']:.0%}"
    )
    s.append(
        f"Persentil atas {c['winsor_upper']:.0%}; {bawah}. Batas dihitung dari gabungan "
        "nilai sebelum + sesudah per variabel (D15, DIUSULKAN) agar responden yang nilainya tidak "
        "berubah tetap tidak berubah. Kolom asli disimpan; kolom terwinsor berakhiran `_w`.\n"
    )
    s.append("| Variabel | Batas bawah | Batas atas |\n|---|---|---|")
    for k, (lo, hi) in wb.items():
        s.append(f"| {k} | {'-' if lo is None else _fmt(lo)} | {_fmt(hi)} |")
    s.append("")
    s.append(
        "- Sel yang berubah: " + ", ".join(f"`{k}` = {v}" for k, v in winsor_counts.items()) + "."
    )
    s.append(f"- Responden dengan `flag_outlier` = 1: {int(df['flag_outlier'].sum())}.")
    s.append(
        "- Nilai 0 yang terangkat oleh batas bawah: "
        + ", ".join(f"`{k}` = {v}" for k, v in rep.winsor_bawah_mengubah_nol.items())
        + ".\n"
    )
    s.append(_md_table(rep.winsor_rows))
    s.append("\n### Dampak winsorizing pada arah perubahan (naik/sama/turun)\n")
    s.append(_md_table(arah_berubah(df)))

    s.append("\n## 6. Duplikat (hanya dilaporkan, tidak dibuang)\n")
    s.append(
        f"- Nama usaha sama: {len(dup['nama_usaha'])} kelompok"
        + (": " + "; ".join(", ".join(g) for g in dup["nama_usaha"]) if dup["nama_usaha"] else "")
        + "."
    )
    s.append(
        f"- Pola jawaban identik (Likert + angka + lama usaha): {len(dup['pola_jawaban'])} kelompok"
        + (
            ": " + "; ".join(", ".join(g) for g in dup["pola_jawaban"])
            if dup["pola_jawaban"]
            else ""
        )
        + ".\n"
    )
    return "\n".join(s)


def run(cfg: dict[str, Any] | None = None) -> tuple[pd.DataFrame, CleaningReport]:
    """Baca xlsx mentah, cleaning, tulis data_clean.csv dan reports/cleaning_log.md."""
    from umkm import config, io

    cfg = cfg or config.load_config()
    raw = io.read_raw()
    df, rep = clean(raw, cfg)
    io.write_csv(df, config.path("processed") / "data_clean.csv")
    io.write_text(build_log(rep, df, cfg), config.path("reports") / "cleaning_log.md")
    return df, rep
