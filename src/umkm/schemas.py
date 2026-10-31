"""Kontrak data inferensi (Pydantic): masukan `ProfilUMKM` dan keluaran `HasilRekomendasi`.

Kontrak yang sama dicatat di reports/integration_contract.md (dibuat ulang oleh Tahap 6).
Hanya butuh pydantic; tidak memuat pustaka analisis.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Platform = Literal["gofood", "grabfood", "shopee", "maxim", "tiktok"]
Strategi = Literal["x1_unggah", "x2_promosi", "x3_komunikasi", "x4_konsistensi"]


class ProfilUMKM(BaseModel):
    """Profil satu UMKM: kondisi usaha + skor rata-rata empat strategi (skala Likert 1-5)."""

    model_config = ConfigDict(extra="forbid")

    id_umkm: str | None = Field(None, description="Penanda opsional; dikembalikan apa adanya")
    omzet_bulanan: float = Field(
        ...,
        ge=0,
        description="Omzet per bulan (Rp). Di data latih: omzet sebelum masuk marketplace",
    )
    lama_usaha_pra_mp: float = Field(
        ..., ge=0, le=100, description="Lama usaha sebelum masuk marketplace (tahun)"
    )
    lama_di_mp: float = Field(
        ..., ge=0, le=100, description="Lama berjualan di marketplace (tahun)"
    )
    platform: list[Platform] = Field(
        ..., min_length=1, description="Platform yang dipakai (huruf kecil, tanpa duplikat)"
    )
    x1_unggah: float = Field(..., ge=1, le=5, description="Rata-rata 4 butir X1 unggah produk")
    x2_promosi: float = Field(..., ge=1, le=5, description="Rata-rata 4 butir X2 promosi")
    x3_komunikasi: float = Field(
        ..., ge=1, le=5, description="Rata-rata 5 butir X3 komunikasi pelanggan"
    )
    x4_konsistensi: float = Field(
        ..., ge=1, le=5, description="Rata-rata 5 butir X4 konsistensi toko"
    )

    @field_validator("platform", mode="before")
    @classmethod
    def _rapikan_platform(cls, v: object) -> object:
        """Huruf kecil, buang spasi, dan buang duplikat (urutan pertama dipertahankan)."""
        if isinstance(v, str):
            v = [v]
        if isinstance(v, list):
            return list(dict.fromkeys(str(p).strip().lower() for p in v))
        return v


class Segmen(BaseModel):
    """Segmen kondisi usaha hasil Tahap 5."""

    id: int
    nama: str


class SkorStrategi(BaseModel):
    """Penilaian satu strategi: skor UMKM, benchmark segmen, gap, bobot, dan prioritas."""

    strategi: Strategi
    nama: str
    skor: float = Field(..., ge=1, le=5)
    benchmark: float = Field(..., ge=1, le=5)
    gap: float = Field(..., ge=0)
    bobot: float = Field(..., ge=0, le=1)
    prioritas: float = Field(..., ge=0)


class Prioritas(SkorStrategi):
    """Strategi prioritas (prioritas > 0), lengkap dengan alasan dan tindakan."""

    peringkat: int = Field(..., ge=1)
    hubungan_meyakinkan: bool
    selisih_prediksi_plus1: float | None = Field(
        None, description="Ilustrasi model: selisih peluang prediksi (poin persen) bila skor +1"
    )
    fokus_butir: list[str]
    alasan: str
    tindakan: str


class HasilRekomendasi(BaseModel):
    """Keluaran `recommend()`; `model_dump()` menghasilkan dict JSON-serializable."""

    versi_model: str
    id_umkm: str | None = None
    segmen: Segmen
    skor: list[SkorStrategi]
    prioritas: list[Prioritas]
    peringatan: list[str]
    catatan: str
