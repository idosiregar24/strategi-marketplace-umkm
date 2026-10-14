"""Baca data mentah dan tulis keluaran tabel/teks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from umkm import config

SHEET_RAW = "Form Responses 1"


def read_raw(path: Path | None = None) -> pd.DataFrame:
    """Baca xlsx kuesioner apa adanya (semua kolom sebagai object, tanpa konversi)."""
    path = path or config.path("raw")
    return pd.read_excel(path, sheet_name=SHEET_RAW, dtype=object)


def write_csv(df: pd.DataFrame, path: Path) -> Path:
    """Tulis CSV UTF-8; folder induk dibuat bila belum ada."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def write_text(text: str, path: Path) -> Path:
    """Tulis berkas teks (mis. log markdown); folder induk dibuat bila belum ada."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
