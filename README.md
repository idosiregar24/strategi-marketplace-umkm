# strategi-marketplace-umkm

Analisis strategi penjualan marketplace (unggah produk, promosi, komunikasi pelanggan, konsistensi kelola toko)
dan hubungannya dengan kinerja penjualan 149 UMKM di Pekanbaru, sebagai dasar rekomendasi strategi per segmen UMKM.

Hasil bersifat **asosiasi**, bukan sebab-akibat.

## Status

| Tahap | Nama | Status |
|---|---|---|
| 1 | Cleaning | Selesai |
| 2 | Konstruksi variabel | Selesai |
| 3 | EDA | Menunggu persetujuan |
| 4 | Analisis pengaruh (regresi, Random Forest, SHAP) | Belum |
| 5 | Segmentasi | Belum |
| 6 | Rekomendasi | Belum |
| 7 | Pelaporan | Belum |

Ringkasan hasil sejauh ini: [reports/hasil_utama.md](reports/hasil_utama.md).

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
