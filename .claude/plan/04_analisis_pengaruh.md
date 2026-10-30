# Tahap 4: Analisis Pengaruh (inti tujuan)

Rujukan: guides/statistical_guidelines.md, guides/ml_guidelines.md
Modul: src/umkm/stats.py, src/umkm/models.py
Keluaran: reports/tables/pengaruh_*.csv, reports/figures/shap_*.png

## Langkah
1. Regresi OLS: Y_obj ~ X1..X4 + kontrol profil. Prediktor distandarkan. Galat baku robust (HC3).
2. Regresi logistik (statsmodels Logit) untuk naik_penjualan; laporkan odds ratio dan CI 95%.
   Bandingkan arah dan signifikansi dengan OLS.
3. Random Forest (klasifikasi untuk naik_penjualan, regresi untuk Y_obj) dengan
   RepeatedStratifiedKFold(5 lipat x 5 ulangan). Bandingkan dengan baseline (rata-rata/mayoritas) dan Logistic Regression.
4. Interpretasi: permutation importance (pada data uji CV) dan SHAP (global + per segmen kelas).
5. Tabel gabungan peringkat strategi dari tiga sumber: |koefisien terstandar|, permutation importance, mean|SHAP|.
   Laporkan konsistensi (korelasi peringkat, Spearman). Jika tidak konsisten, laporkan apa adanya.
6. Moderasi sederhana: interaksi strategi x skala_omzet / jumlah_platform / lama_di_mp.
7. Sensitivitas: ulang model utama (a) tanpa baris terwinsor, (b) tanpa responden omzet sebelum=sesudah,
   (c) DENGAN semua 149 responden (analisis utama memakai `sampel_utama` = 1, n=116; D14),
   (d) target alternatif: hanya d_omzet, hanya d_trx, dan y_pelanggan_baru,
   (e) tanpa `flag_jawaban_seragam` (D20), (f) tanpa R021 untuk y_obj dan d_trx (D25: transaksi
   naik 150x, y_obj 4,76 jauh di atas responden lain); `flag_omzet_turun_tajam` (D21) kini 0,
   (g) dengan dan tanpa `log_omzet_sebelum` sebagai kontrol (efek regresi ke rata-rata).
   Laporkan apakah peringkat berubah.

## Kriteria selesai
- Peringkat pengaruh X1-X4 dengan interval ketidakpastian (bootstrap 1000x).
- Metrik CV dibandingkan dengan baseline; jika model tidak mengalahkan baseline, katakan terus terang.
- Kalimat temuan memakai bahasa asosiasi.
