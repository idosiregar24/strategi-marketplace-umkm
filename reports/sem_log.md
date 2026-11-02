# Log Analisis Pembanding: PLS-SEM

Dibuat oleh `umkm.sem` pada 2026-11-02 18:34. Seed 42, bootstrap 2000x, validasi silang 5x5.

## Spesifikasi

- Konstruk X1-X4 reflektif (Mode A) dengan butir kuesioner masing-masing; skema bobot jalur; indikator distandarkan.
- Profil usaha (lama usaha sebelum marketplace, lama di marketplace, jumlah platform, omzet sebelum log) masuk sebagai konstruk satu indikator, sama dengan kontrol pada regresi.
- Tiga model dengan prediktor yang sama:
  - `y_obj`: Kinerja objektif (y_obj), n = 116
  - `naik_penjualan`: Melaporkan kenaikan (naik_penjualan), n = 116
  - `persepsi`: Persepsi kinerja (Y1-Y8), n = 149
- Inferensi: bootstrap persentil 95% dan uji t (SE bootstrap); koreksi Holm untuk empat jalur strategi di tiap model.
- Daya prediksi (target satu indikator): Q2_predict terhadap rata-rata data latih dan RMSE dibandingkan regresi linear pada seluruh indikator.

## Model pengukuran

| model | konstruk | n_indikator | alpha | rho_a | rho_c | ave |
|---|---|---|---|---|---|---|
| y_obj | X1 Unggah produk | 4 | 0.951 | 0.997 | 0.964 | 0.869 |
| y_obj | X2 Promosi | 4 | 0.930 | 0.975 | 0.949 | 0.825 |
| y_obj | X3 Komunikasi pelanggan | 5 | 0.956 | 1.006 | 0.965 | 0.845 |
| y_obj | X4 Konsistensi toko | 5 | 0.950 | 1.017 | 0.961 | 0.830 |
| naik_penjualan | X1 Unggah produk | 4 | 0.951 | 0.956 | 0.964 | 0.872 |
| naik_penjualan | X2 Promosi | 4 | 0.930 | 0.976 | 0.950 | 0.825 |
| naik_penjualan | X3 Komunikasi pelanggan | 5 | 0.956 | 0.972 | 0.966 | 0.849 |
| naik_penjualan | X4 Konsistensi toko | 5 | 0.950 | 0.983 | 0.961 | 0.832 |
| persepsi | X1 Unggah produk | 4 | 0.957 | 0.961 | 0.969 | 0.886 |
| persepsi | X2 Promosi | 4 | 0.931 | 0.969 | 0.950 | 0.825 |
| persepsi | X3 Komunikasi pelanggan | 5 | 0.947 | 0.985 | 0.959 | 0.824 |
| persepsi | X4 Konsistensi toko | 5 | 0.952 | 0.954 | 0.963 | 0.840 |
| persepsi | Persepsi kinerja | 8 | 0.957 | 0.960 | 0.964 | 0.770 |


Ambang: alpha dan rho_C >= 0,70; AVE >= 0,50; loading >= 0,708.

### Validitas diskriminan (HTMT)

| konstruk_a | konstruk_b | htmt | htmt_ci_atas |
|---|---|---|---|
| X2 Promosi | X1 Unggah produk | 0.344 | 0.515 |
| X3 Komunikasi pelanggan | X1 Unggah produk | 0.071 | 0.226 |
| X3 Komunikasi pelanggan | X2 Promosi | 0.256 | 0.401 |
| X4 Konsistensi toko | X1 Unggah produk | 0.316 | 0.493 |
| X4 Konsistensi toko | X2 Promosi | 0.279 | 0.447 |
| X4 Konsistensi toko | X3 Komunikasi pelanggan | 0.371 | 0.528 |
| Persepsi kinerja | X1 Unggah produk | 0.444 | 0.591 |
| Persepsi kinerja | X2 Promosi | 0.272 | 0.428 |
| Persepsi kinerja | X3 Komunikasi pelanggan | 0.270 | 0.448 |
| Persepsi kinerja | X4 Konsistensi toko | 0.536 | 0.651 |


HTMT dan batas atas interval bootstrap 95% dibandingkan dengan ambang 0,85.

### Kriteria Fornell-Larcker (model y_obj)

| konstruk | x1_unggah | x2_promosi | x3_komunikasi | x4_konsistensi |
|---|---|---|---|---|
| X1 Unggah produk | 0.932 |  |  |  |
| X2 Promosi | 0.313 | 0.908 |  |  |
| X3 Komunikasi pelanggan | -0.051 | 0.254 | 0.919 |  |
| X4 Konsistensi toko | 0.310 | 0.270 | 0.347 | 0.911 |


Diagonal = akar AVE; harus lebih besar dari korelasi pada baris dan kolomnya.

## Model struktural

### Kinerja objektif (y_obj) (n = 116)

| Prediktor | Beta | SE | CI 95% | p | p Holm | f2 | VIF |
|---|---|---|---|---|---|---|---|
| X1 Unggah produk | 0.154 | 0.086 | [-0.02; 0.32] | 0.077 | 0.307 | 0.023 | 1.277 |
| X2 Promosi | 0.070 | 0.136 | [-0.19; 0.35] | 0.606 | 1.000 | 0.005 | 1.298 |
| X3 Komunikasi pelanggan | 0.166 | 0.104 | [-0.07; 0.37] | 0.115 | 0.344 | 0.026 | 1.306 |
| X4 Konsistensi toko | 0.034 | 0.101 | [-0.21; 0.20] | 0.735 | 1.000 | 0.001 | 1.348 |
| Lama usaha sebelum MP | 0.064 | 0.109 | [-0.14; 0.27] | 0.558 |  | 0.004 | 1.334 |
| Lama di marketplace | 0.168 | 0.119 | [-0.07; 0.38] | 0.160 |  | 0.025 | 1.375 |
| Jumlah platform | -0.093 | 0.075 | [-0.24; 0.05] | 0.218 |  | 0.010 | 1.058 |
| Omzet sebelum (log) | -0.278 | 0.070 | [-0.42; -0.14] | 0.000 |  | 0.089 | 1.053 |


R2 = 0,182 (adj. 0,121); algoritma konvergen dalam 2 iterasi; Q2_predict = 0,000; RMSE PLS 0,838 vs regresi linear 0,903. Sampel bootstrap gagal: 0.

### Melaporkan kenaikan (naik_penjualan) (n = 116)

| Prediktor | Beta | SE | CI 95% | p | p Holm | f2 | VIF |
|---|---|---|---|---|---|---|---|
| X1 Unggah produk | 0.272 | 0.084 | [0.10; 0.43] | 0.002 | 0.005 | 0.078 | 1.283 |
| X2 Promosi | 0.097 | 0.099 | [-0.09; 0.29] | 0.328 | 0.655 | 0.010 | 1.297 |
| X3 Komunikasi pelanggan | 0.342 | 0.085 | [0.17; 0.50] | 0.000 | 0.000 | 0.120 | 1.308 |
| X4 Konsistensi toko | -0.018 | 0.085 | [-0.18; 0.15] | 0.829 | 0.829 | 0.000 | 1.350 |
| Lama usaha sebelum MP | -0.002 | 0.098 | [-0.20; 0.18] | 0.984 |  | 0.000 | 1.334 |
| Lama di marketplace | 0.070 | 0.097 | [-0.12; 0.26] | 0.474 |  | 0.005 | 1.376 |
| Jumlah platform | -0.071 | 0.083 | [-0.23; 0.09] | 0.392 |  | 0.006 | 1.058 |
| Omzet sebelum (log) | -0.187 | 0.075 | [-0.34; -0.04] | 0.014 |  | 0.045 | 1.053 |


R2 = 0,257 (adj. 0,201); algoritma konvergen dalam 2 iterasi; Q2_predict = 0,106; RMSE PLS 0,472 vs regresi linear 0,517; AUC 0,720 (SD 0,118). Sampel bootstrap gagal: 0.

### Persepsi kinerja (Y1-Y8) (n = 149)

| Prediktor | Beta | SE | CI 95% | p | p Holm | f2 | VIF |
|---|---|---|---|---|---|---|---|
| X1 Unggah produk | 0.304 | 0.102 | [0.10; 0.51] | 0.003 | 0.013 | 0.098 | 1.505 |
| X2 Promosi | -0.018 | 0.080 | [-0.16; 0.14] | 0.822 | 0.822 | 0.000 | 1.402 |
| X3 Komunikasi pelanggan | 0.161 | 0.085 | [0.02; 0.34] | 0.060 | 0.120 | 0.033 | 1.251 |
| X4 Konsistensi toko | 0.329 | 0.113 | [0.07; 0.51] | 0.004 | 0.013 | 0.116 | 1.485 |
| Lama usaha sebelum MP | 0.030 | 0.086 | [-0.13; 0.21] | 0.726 |  | 0.001 | 1.247 |
| Lama di marketplace | 0.076 | 0.082 | [-0.08; 0.23] | 0.357 |  | 0.007 | 1.219 |
| Jumlah platform | 0.060 | 0.074 | [-0.10; 0.19] | 0.414 |  | 0.005 | 1.062 |
| Omzet sebelum (log) | 0.139 | 0.073 | [-0.02; 0.27] | 0.059 |  | 0.029 | 1.067 |


R2 = 0,371 (adj. 0,335); algoritma konvergen dalam 5 iterasi. Sampel bootstrap gagal: 0.

## Perbandingan dengan analisis utama

| Strategi | Logit (log-odds/SD) | PLS naik | OLS y_obj | PLS y_obj | PLS persepsi | RF importance | Peringkat gabungan | Peringkat PLS naik |
|---|---|---|---|---|---|---|---|---|
| X1 Unggah produk | 0.786 | 0.272 | 0.124 | 0.154 | 0.304 | 0.033 | 2 | 2 |
| X2 Promosi | 0.227 | 0.097 | 0.058 | 0.070 | -0.018 | 0.022 | 3 | 3 |
| X3 Komunikasi pelanggan | 0.913 | 0.342 | 0.125 | 0.166 | 0.161 | 0.115 | 1 | 1 |
| X4 Konsistensi toko | -0.075 | -0.018 | 0.029 | 0.034 | 0.329 | -0.001 | 4 | 4 |


Koefisien logit dalam log-odds per SD, PLS dan OLS terstandar; yang dibandingkan adalah arah dan urutan. Spearman rho peringkat = 1,00.

## Temuan

1. **Model pengukuran memadai.** Keempat konstruk strategi dan persepsi kinerja reliabel (Cronbach alpha 0,93-0,96, composite reliability 0,95-0,97), validitas konvergen terpenuhi (AVE 0,77-0,89; loading terendah 0,80), dan konstruk dapat dibedakan satu sama lain (HTMT tertinggi 0,54, batas atas interval bootstrap tertinggi 0,65 < 0,85).
2. **Melaporkan kenaikan penjualan.** Jalur terkuat berasal dari X3 Komunikasi pelanggan (beta = 0,34, p < 0,001, f2 = 0,12, kecil). Jalur yang intervalnya tidak mencakup nol: X1 Unggah produk dan X3 Komunikasi pelanggan. Urutan: X3 Komunikasi pelanggan > X1 Unggah produk > X2 Promosi > X4 Konsistensi toko. R2 = 0,26; AUC validasi silang 0,72 (SD 0,12).
3. **Besar kenaikan (y_obj).** Urutan jalur: X3 Komunikasi pelanggan > X1 Unggah produk > X2 Promosi > X4 Konsistensi toko; jalur yang intervalnya tidak mencakup nol: tidak ada; setelah koreksi Holm tidak ada yang bermakna (Holm p terkecil 0,307). R2 = 0,18, tetapi Q2_predict = 0,00: di luar sampel model hampir tidak lebih baik dari rata-rata, sejalan dengan R2 out-of-fold pada analisis utama.
4. **Persepsi kinerja (Y1-Y8).** Urutan jalur: X4 Konsistensi toko > X1 Unggah produk > X3 Komunikasi pelanggan > X2 Promosi (beta tertinggi 0,33); R2 = 0,37. Penilaian diri pelaku usaha paling dekat dengan X4 Konsistensi toko dan X1 Unggah produk, sedangkan laporan angka penjualan paling dekat dengan X3 Komunikasi pelanggan. Perbedaan ini sejalan dengan alasan persepsi tidak dipakai sebagai target utama.
5. **Konsisten dengan metode inti.** Urutan jalur PLS untuk naik_penjualan dibandingkan peringkat gabungan regresi logistik, Random Forest, dan SHAP: Spearman rho = 1,00. AUC validasi silang PLS 0,72, regresi logistik 0,72, Random Forest 0,73. X2 Promosi dan X4 Konsistensi toko belum meyakinkan berhubungan dengan pelaporan kenaikan, baik di PLS-SEM maupun di peringkat gabungan.

## Keterbatasan

- PLS-SEM di sini memakai data potong lintang yang sama dengan analisis utama, sehingga fungsinya sebagai pemeriksaan kekokohan, bukan bukti tambahan yang independen.
- naik_penjualan berupa 0/1; koefisien jalur PLS untuk target ini setara model peluang linear dan dibaca sebagai arah serta urutan, bukan besar peluang.
- Konstruk satu indikator (kinerja objektif dan profil usaha) dianggap terukur tanpa galat.
- rho_A sedikit di atas 1 pada X3 Komunikasi pelanggan dan X4 Konsistensi toko (maks 1,017). Ini muncul bila bobot indikator tidak seimbang relatif terhadap korelasi antarbutir; reliabilitas tetap dinilai dari alpha dan rho_C.
- Interval bootstrap loading lebar pada X2 Promosi, X3 Komunikasi pelanggan dan X4 Konsistensi toko (batas bawah terendah 0,38). Pada Mode A bobot butir mengikuti korelasinya dengan target; bila hubungan konstruk dengan target lemah, bobot di sampel ulang ikut tidak stabil. Estimasi titik tetap di atas ambang.
- Banyak butir didominasi jawaban netral dan ada responden dengan jawaban seragam; ini dapat menaikkan reliabilitas secara semu. CB-SEM tidak dipakai karena ukuran sampel kecil dan target utama hanya satu indikator.

## Grafik

- `figures/sem_jalur.png`: koefisien jalur strategi pada tiga model dengan interval bootstrap.
- `figures/sem_loading.png`: loading luar seluruh butir dengan ambang 0,708.
