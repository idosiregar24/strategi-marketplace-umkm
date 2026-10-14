"""Memuat config.yaml dan menyelesaikan path proyek.

Base dir diambil dari env `UMKM_BASE_DIR`; jika kosong, dipakai folder proyek
(folder yang berisi config.yaml, dua tingkat di atas paket ini).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_PROJECT_DIR = Path(__file__).resolve().parents[2]


def project_dir() -> Path:
    """Folder kode proyek (tempat config.yaml berada)."""
    return _PROJECT_DIR


def base_dir() -> Path:
    """Folder data/keluaran: env UMKM_BASE_DIR, config base_dir, atau folder proyek."""
    env = os.environ.get("UMKM_BASE_DIR")
    if env:
        return Path(env)
    cfg_base = load_config().get("base_dir")
    return Path(cfg_base) if cfg_base else _PROJECT_DIR


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    """Baca config.yaml sekali dan simpan di cache."""
    with open(_PROJECT_DIR / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def path(key: str) -> Path:
    """Path absolut untuk kunci di bagian `paths` config (mis. 'raw', 'processed')."""
    return base_dir() / load_config()["paths"][key]
