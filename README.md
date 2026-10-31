# strategi-marketplace-umkm

Analisis strategi penjualan marketplace (unggah produk, promosi, komunikasi pelanggan, konsistensi kelola toko)
dan hubungannya dengan kinerja penjualan 149 UMKM di Pekanbaru, sebagai dasar rekomendasi strategi per segmen UMKM.

Hasil bersifat **asosiasi**, bukan sebab-akibat.

## Status

| Tahap | Nama | Status |
|---|---|---|
| 1 | Cleaning | Selesai |
| 2 | Konstruksi variabel | Selesai |
| 3 | EDA | Selesai |
| 4 | Analisis pengaruh (regresi, Random Forest, SHAP) | Selesai |
| 5 | Segmentasi | Selesai |
| 6 | Rekomendasi | Selesai |
| 7 | Pelaporan (Laporan Akhir) | Selesai |

Laporan akhir lengkap: [reports/laporan_final.md](reports/laporan_final.md) | Ringkasan awal: [reports/hasil_utama.md](reports/hasil_utama.md).

## Struktur

| Folder | Isi |
|---|---|
| `src/umkm/` | Kode analisis (cleaning, fitur, statistik, grafik, pipeline) |
| `notebooks/` | Notebook untuk menampilkan hasil (lokal dan Google Colab) |
| `reports/` | Log tiap tahap, ringkasan, tabel (`tables/`), grafik (`figures/`) |
| `tests/` | Tes otomatis (pytest) |
| `data/` | Tidak disertakan di repo (data kuesioner berisi identitas usaha) |

## Menjalankan

```
python -m venv .venv
.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -e ".[analysis]"
```

Letakkan file kuesioner di `data/raw/Kuesioner_Penelitian__Responses_.xlsx`, lalu:

```
python -m umkm.pipeline --all     # atau --stage N
pytest
```

## Rekomendasi untuk satu UMKM

Tahap 6 menyimpan artefak di `models/v1/`; `recommend()` hanya memuat artefak itu (tanpa data survei).

```
python -m umkm.recommend profil.json      # atau: cat profil.json | python -m umkm.recommend -
```

Skema masukan/keluaran dan contoh JSON: [reports/integration_contract.md](reports/integration_contract.md).

## Dashboard ringkasan (lokal)

```
python -m umkm.dashboard              # buka http://localhost:8000 (mendukung mode Umum & Developer)
python -m umkm.dashboard --port 8050  # port lain
```

Halaman menampilkan alur tahap, angka kunci, grafik hasil, keputusan terbuka, dan galeri grafik. Angka dibaca
langsung dari `reports/` dan `.claude/progress.md` setiap kali halaman dimuat. Server hanya bisa diakses dari
komputer sendiri (127.0.0.1). Hentikan dengan Ctrl+C.
