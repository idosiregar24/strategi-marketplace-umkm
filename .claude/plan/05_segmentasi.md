# Tahap 5: Segmentasi Kondisi UMKM

Modul: src/umkm/segmentation.py
Keluaran: data/processed/data_segmen.csv, reports/tables/profil_segmen.csv

## Langkah
1. Fitur klaster: skala_omzet (numerik terstandar), lama_usaha_pra_mp, lama_di_mp, jumlah_platform,
   skor X1-X4. JANGAN masukkan Y ke fitur klaster (hindari sirkularitas).
2. K-Means dengan k = 2..6; pilih berdasarkan silhouette, elbow, dan ukuran klaster (minimal 15 responden).
   Pembanding: Agglomerative (Ward) dan Gaussian Mixture.
3. Uji stabilitas: bootstrap 100x, hitung Adjusted Rand Index terhadap solusi utama.
4. Profilkan klaster: rata-rata fitur, sebaran platform, proporsi naik_penjualan = 1 dan rata-rata Y_obj.
5. Beri nama tiap segmen yang bermakna bisnis (mis. "Pemula, 1 platform, aktivitas rendah").
6. Simpan segmen ke data_segmen.csv.

## Kriteria selesai
Silhouette dilaporkan; tiap segmen punya nama dan deskripsi satu paragraf; stabilitas dilaporkan.
