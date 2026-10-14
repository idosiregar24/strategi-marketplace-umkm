# Tahap 3: EDA

Modul: src/umkm/viz.py, notebooks/03_eda.ipynb
Keluaran: reports/figures/eda_*.png, reports/tables/eda_*.csv

## Langkah
1. Profil responden: sebaran platform, lama usaha, skala omzet.
2. Distribusi tiap skor konstruk; periksa ceiling/floor effect dan dominasi "Netral".
3. Sebelum vs sesudah (omzet, transaksi): statistik deskriptif + Wilcoxon signed-rank; ukuran efek.
   Laporkan persentase responden naik / sama / turun.
4. Korelasi Spearman X1-X4 vs d_omzet, d_trx, Y_obj, y_pelanggan_baru; heatmap.
   Y_persepsi dilaporkan terpisah sebagai pembanding (apakah persepsi selaras dengan angka nyata).
5. Boxplot skor strategi untuk naik_penjualan = 1 vs 0; uji Mann-Whitney + ukuran efek.
   Bandingkan juga kelompok `tanpa_baseline` vs lainnya.
6. VIF antar X1-X4 dan profil.
7. Ringkas 5-8 temuan awal dalam bahasa awam di `reports/eda_ringkasan.md`.

## Kriteria selesai
Setiap grafik punya judul, sumbu berlabel, dan satu kalimat interpretasi.
