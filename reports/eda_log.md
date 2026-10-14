# Log EDA (Tahap 3)

Dibuat oleh `umkm.eda` pada 2026-10-14 22:26.

- Analisis yang menyangkut kinerja memakai **sampel utama** (n = 116, D14); semua 149 responden dilaporkan sebagai pembanding. Profil dan skor strategi memakai 149 responden.
- Uji nonparametrik: Wilcoxon signed-rank (pasangan tanpa beda dibuang), Mann-Whitney U (pendekatan normal dengan koreksi ties), Spearman (CI 95% Fisher-z, SE Bonett-Wright). Koreksi Holm per keluarga uji. Ukuran efek: r = Z/sqrt(N) dan rank-biserial; label Cohen (0,1 kecil; 0,3 sedang; 0,5 besar).
- Semua hasil adalah **asosiasi**, bukan sebab-akibat.
- Tabel lengkap: `reports/tables/eda_*.csv`.

## 1. Profil responden

| platform | n_utama | pct_utama | n_semua_149 | pct_semua_149 |
|---|---|---|---|---|
| GoFood | 86 | 0.74 | 112 | 0.75 |
| Shopee | 78 | 0.67 | 100 | 0.67 |
| GrabFood | 63 | 0.54 | 80 | 0.54 |
| Maxim | 5 | 0.04 | 8 | 0.05 |
| TikTok Shop | 2 | 0.02 | 5 | 0.03 |


Kombinasi platform (5 teratas):

| kombinasi | n | pct |
|---|---|---|
| GoFood + GrabFood + Shopee | 53 | 0.36 |
| GoFood | 25 | 0.17 |
| Shopee | 22 | 0.15 |
| GoFood + Shopee | 15 | 0.10 |
| GoFood + GrabFood | 12 | 0.08 |


![eda_profil_platform](figures/eda_profil_platform.png)

**Interpretasi:** GoFood (75%) dan Shopee (67%) paling banyak dipakai dan kombinasi terbanyak adalah GoFood + GrabFood + Shopee (53 UMKM); Maxim dan TikTok Shop hanya dipakai 8 dan 5 UMKM sehingga terlalu sedikit untuk dianalisis sebagai kelompok tersendiri.


| variabel | sampel | count | mean | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|---|---|
| lama_usaha_pra_mp | utama | 116.00 | 4.77 | 3.84 | 0.08 | 2.00 | 4.00 | 6.00 | 22.00 |
| lama_di_mp | utama | 116.00 | 3.75 | 2.21 | 0.08 | 2.00 | 3.00 | 5.00 | 10.00 |
| jumlah_platform | utama | 116.00 | 2.02 | 0.93 | 1.00 | 1.00 | 2.00 | 3.00 | 4.00 |
| omzet_sebelum_juta | utama | 116.00 | 41.30 | 66.75 | 0.40 | 11.81 | 20.00 | 35.62 | 330.00 |
| lama_usaha_pra_mp | semua_149 | 149.00 | 3.71 | 3.92 | 0.00 | 1.00 | 3.00 | 5.00 | 22.00 |
| lama_di_mp | semua_149 | 149.00 | 3.65 | 2.34 | 0.08 | 2.00 | 3.00 | 5.00 | 13.00 |
| jumlah_platform | semua_149 | 149.00 | 2.05 | 0.94 | 1.00 | 1.00 | 2.00 | 3.00 | 4.00 |
| omzet_sebelum_juta | semua_149 | 149.00 | 38.50 | 65.02 | 0.00 | 9.00 | 18.00 | 30.00 | 330.00 |


![eda_profil_lama_usaha](figures/eda_profil_lama_usaha.png)

**Interpretasi:** Median lama usaha sebelum marketplace 3 tahun dan median lama berjualan di marketplace 3 tahun; 33 UMKM (22%) berdiri bersamaan dengan masuk marketplace sehingga tidak punya kondisi 'sebelum' yang bermakna dan dikeluarkan dari analisis utama (D14).


| skala_omzet | rentang_omzet_sebelum | n_utama | n_semua_149 |
|---|---|---|---|
| Q1_kecil | <= Rp9 jt | 26 | 41 |
| Q2_menengah_bawah | Rp9-18 jt | 30 | 37 |
| Q3_menengah_atas | Rp18-30 jt | 30 | 36 |
| Q4_besar | > Rp30 jt | 30 | 35 |


![eda_profil_skala_omzet](figures/eda_profil_skala_omzet.png)

**Interpretasi:** Keempat kelompok skala usaha berukuran mirip (35-41 UMKM) karena dibentuk dari kuartil; separuh UMKM beromzet sebelum marketplace paling banyak Rp18,0 jt per bulan.


## 2. Distribusi skor konstruk

Efek lantai/atap: > 15% responden di skor 1 atau 5. Dominasi: > 50% responden pada satu nilai skor.


| sampel | konstruk | n | rata_rata | sd | median | skewness | pct_floor | pct_ceiling | nilai_dominan | pct_nilai_dominan | efek_floor | efek_ceiling | dominasi_satu_nilai |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| utama | x1_unggah | 116 | 2.34 | 0.64 | 2.00 | 0.13 | 0.05 | 0.00 | 2.00 | 0.43 | TIDAK | TIDAK | TIDAK |
| utama | x2_promosi | 116 | 2.34 | 0.74 | 2.38 | -0.18 | 0.09 | 0.00 | 3.00 | 0.24 | TIDAK | TIDAK | TIDAK |
| utama | x3_komunikasi | 116 | 3.50 | 0.62 | 3.20 | 0.86 | 0.00 | 0.06 | 3.00 | 0.47 | TIDAK | TIDAK | TIDAK |
| utama | x4_konsistensi | 116 | 3.22 | 0.61 | 3.00 | -0.86 | 0.02 | 0.00 | 3.00 | 0.49 | TIDAK | TIDAK | TIDAK |
| utama | y_persepsi | 116 | 3.18 | 0.44 | 3.00 | 0.48 | 0.00 | 0.00 | 3.00 | 0.66 | TIDAK | TIDAK | ya |
| semua_149 | x1_unggah | 149 | 2.36 | 0.68 | 2.00 | 0.40 | 0.05 | 0.00 | 2.00 | 0.45 | TIDAK | TIDAK | TIDAK |
| semua_149 | x2_promosi | 149 | 2.38 | 0.73 | 2.50 | -0.14 | 0.09 | 0.00 | 3.00 | 0.24 | TIDAK | TIDAK | TIDAK |
| semua_149 | x3_komunikasi | 149 | 3.51 | 0.62 | 3.20 | 0.84 | 0.00 | 0.05 | 3.00 | 0.44 | TIDAK | TIDAK | TIDAK |
| semua_149 | x4_konsistensi | 149 | 3.19 | 0.65 | 3.00 | -0.90 | 0.03 | 0.00 | 3.00 | 0.46 | TIDAK | TIDAK | TIDAK |
| semua_149 | y_persepsi | 149 | 3.16 | 0.47 | 3.00 | 0.23 | 0.00 | 0.00 | 3.00 | 0.67 | TIDAK | TIDAK | ya |


![eda_distribusi_konstruk](figures/eda_distribusi_konstruk.png)

**Interpretasi:** Skor unggah produk (X1) (median 2,00) dan promosi (X2) (median 2,50) tergolong rendah, sedangkan konsistensi kelola toko (X4) (median 3,00) dan komunikasi pelanggan (X3) (median 3,20) berada di sekitar titik tengah; tidak ada efek lantai/atap (> 15% responden di skor 1 atau 5), tetapi skor menumpuk di satu nilai, paling ekstrem pada persepsi kinerja (67% responden tepat 3).


| label | pct_1 | pct_2 | pct_3 | pct_4 | pct_5 | dominasi_netral |
|---|---|---|---|---|---|---|
| X1.1 Unggah rutin mingguan | 0.10 | 0.50 | 0.34 | 0.05 | 0.01 | TIDAK |
| X1.2 Unggah produk baru | 0.06 | 0.57 | 0.34 | 0.03 | 0.00 | TIDAK |
| X1.3 Unggah ulang produk | 0.08 | 0.57 | 0.28 | 0.07 | 0.00 | TIDAK |
| X1.4 Pantau produk unggahan | 0.07 | 0.53 | 0.32 | 0.07 | 0.01 | TIDAK |
| X2.1 Voucher/diskon | 0.12 | 0.32 | 0.49 | 0.07 | 0.00 | TIDAK |
| X2.2 Iklan berbayar | 0.21 | 0.42 | 0.32 | 0.04 | 0.01 | TIDAK |
| X2.3 Fitur promosi | 0.13 | 0.40 | 0.40 | 0.07 | 0.00 | TIDAK |
| X2.4 Evaluasi promosi | 0.14 | 0.37 | 0.46 | 0.03 | 0.00 | TIDAK |
| X3.1 Respon cepat | 0.00 | 0.01 | 0.62 | 0.27 | 0.10 | ya |
| X3.2 Jelas dan sopan | 0.00 | 0.01 | 0.55 | 0.34 | 0.11 | ya |
| X3.3 Balas di hari yang sama | 0.00 | 0.02 | 0.56 | 0.34 | 0.07 | ya |
| X3.4 Tangani komplain | 0.00 | 0.01 | 0.52 | 0.36 | 0.10 | ya |
| X3.5 Jaga komunikasi | 0.00 | 0.01 | 0.54 | 0.36 | 0.09 | ya |
| X4.1 Toko selalu aktif | 0.05 | 0.03 | 0.62 | 0.29 | 0.01 | ya |
| X4.2 Stok diperbarui | 0.03 | 0.10 | 0.58 | 0.28 | 0.01 | ya |
| X4.3 Foto/deskripsi terjaga | 0.03 | 0.07 | 0.62 | 0.26 | 0.01 | ya |
| X4.4 Harga akurat | 0.03 | 0.03 | 0.60 | 0.34 | 0.01 | ya |
| X4.5 Tetap kelola saat sibuk | 0.03 | 0.06 | 0.60 | 0.30 | 0.01 | ya |
| Y1 Omzet naik | 0.01 | 0.03 | 0.74 | 0.19 | 0.03 | ya |
| Y2 Penjualan tumbuh | 0.01 | 0.03 | 0.74 | 0.19 | 0.02 | ya |
| Y3 Pesanan naik | 0.01 | 0.03 | 0.74 | 0.20 | 0.01 | ya |
| Y4 Transaksi lebih sering | 0.01 | 0.05 | 0.77 | 0.15 | 0.01 | ya |
| Y5 Pelanggan baru | 0.01 | 0.03 | 0.76 | 0.19 | 0.01 | ya |
| Y6 Jangkauan luar daerah | 0.02 | 0.05 | 0.74 | 0.17 | 0.01 | ya |
| Y7 Usaha berkembang | 0.01 | 0.03 | 0.76 | 0.20 | 0.00 | ya |
| Y8 Kontribusi marketplace | 0.01 | 0.03 | 0.77 | 0.18 | 0.01 | ya |


![eda_butir_likert](figures/eda_butir_likert.png)

**Interpretasi:** Jawaban netral (3) dipilih lebih dari separuh responden pada 18 dari 26 butir, termasuk 8 dari 8 butir persepsi kinerja (74%-77%); sebaliknya butir unggah dan promosi didominasi skor 1-2 (44%-65% responden), terutama iklan berbayar.


## 3. Sebelum vs sesudah (nilai terwinsor)

| sampel | variabel | n_pasangan | n_naik | n_sama | n_turun | median_sebelum | median_sesudah | median_selisih | z | p | r | r_semua_pasangan | r_rank_biserial | efek |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| utama | omzet (Rp) | 116 | 58 | 54 | 4 | 2e+07 | 2.1e+07 | 5e+04 | 5.3 | 1.13e-07 | 0.674 | 0.492 | 0.774 | besar |
| utama | transaksi | 112 | 57 | 55 | 0 | 900 | 1.02e+03 | 3.5 | 6.57 | 4.89e-11 | 0.871 | 0.621 | 1 | besar |
| semua_149 | omzet (Rp) | 149 | 60 | 85 | 4 | 1.8e+07 | 2e+07 | 0 | 5.45 | 5.01e-08 | 0.681 | 0.447 | 0.783 | besar |
| semua_149 | transaksi | 145 | 61 | 84 | 0 | 900 | 900 | 0 | 6.8 | 1.06e-11 | 0.87 | 0.565 | 1 | besar |


Catatan: Wilcoxon membuang pasangan tanpa beda, sehingga r dihitung dari UMKM yang berubah saja; `r_semua_pasangan` (pembagi = semua pasangan) lebih konservatif. Transaksi tidak punya satu pun penurunan, jadi rank-biserial = 1. Perbandingan sebelum-sesudah ini tidak punya kelompok pembanding, sehingga tidak dapat dipakai untuk menyimpulkan bahwa kenaikan disebabkan oleh marketplace.


![eda_arah_perubahan](figures/eda_arah_perubahan.png)

**Interpretasi:** Di sampel utama, 50% UMKM mencatat omzet naik dan 51% transaksi naik, hampir separuh tidak berubah, dan penurunan jarang (omzet 4 UMKM, transaksi 0); bila 33 UMKM tanpa baseline ikut dihitung, porsi 'sama' membesar karena mereka umumnya mengisi angka sebelum = sesudah.


![eda_sebelum_sesudah](figures/eda_sebelum_sesudah.png)

**Interpretasi:** Hampir semua titik berada pada atau sedikit di atas garis diagonal: perubahan umumnya kecil (median selisih omzet Rp50 ribu, transaksi 3,5), tetapi di antara UMKM yang berubah, arahnya hampir selalu naik (Wilcoxon: omzet r = 0,67, transaksi r = 0,87, keduanya p < 0,001); titik merah jauh di bawah garis adalah kasus omzet turun tajam (D21).


## 4. Korelasi Spearman strategi vs kinerja

| sampel | x | y | n | rho | ci_bawah | ci_atas | p | p_holm |
|---|---|---|---|---|---|---|---|---|
| utama | x1_unggah | d_omzet | 116 | 0.289 | 0.109 | 0.451 | 0.002 | 0.018 |
| utama | x1_unggah | d_trx | 112 | 0.249 | 0.063 | 0.417 | 0.008 | 0.074 |
| utama | x1_unggah | y_obj | 116 | 0.266 | 0.084 | 0.430 | 0.004 | 0.040 |
| utama | x1_unggah | y_pelanggan_baru | 116 | 0.060 | -0.123 | 0.240 | 0.519 | 0.678 |
| utama | x2_promosi | d_omzet | 116 | 0.349 | 0.173 | 0.504 | 0.000 | 0.002 |
| utama | x2_promosi | d_trx | 112 | 0.325 | 0.144 | 0.486 | 0.000 | 0.006 |
| utama | x2_promosi | y_obj | 116 | 0.325 | 0.147 | 0.483 | 0.000 | 0.005 |
| utama | x2_promosi | y_pelanggan_baru | 116 | 0.130 | -0.054 | 0.306 | 0.164 | 0.656 |
| utama | x3_komunikasi | d_omzet | 116 | 0.238 | 0.055 | 0.405 | 0.010 | 0.082 |
| utama | x3_komunikasi | d_trx | 112 | 0.319 | 0.138 | 0.480 | 0.001 | 0.008 |
| utama | x3_komunikasi | y_obj | 116 | 0.302 | 0.122 | 0.462 | 0.001 | 0.012 |
| utama | x3_komunikasi | y_pelanggan_baru | 116 | -0.197 | -0.367 | -0.013 | 0.034 | 0.241 |
| utama | x4_konsistensi | d_omzet | 116 | 0.097 | -0.088 | 0.275 | 0.302 | 0.678 |
| utama | x4_konsistensi | d_trx | 112 | 0.176 | -0.011 | 0.352 | 0.063 | 0.378 |
| utama | x4_konsistensi | y_obj | 116 | 0.141 | -0.043 | 0.316 | 0.131 | 0.654 |
| utama | x4_konsistensi | y_pelanggan_baru | 116 | 0.113 | -0.071 | 0.290 | 0.226 | 0.678 |
| semua_149 | x1_unggah | d_omzet | 149 | 0.256 | 0.096 | 0.402 | 0.002 | 0.021 |
| semua_149 | x1_unggah | d_trx | 145 | 0.238 | 0.076 | 0.388 | 0.004 | 0.043 |
| semua_149 | x1_unggah | y_obj | 149 | 0.255 | 0.096 | 0.402 | 0.002 | 0.021 |
| semua_149 | x1_unggah | y_pelanggan_baru | 149 | 0.106 | -0.056 | 0.263 | 0.198 | 0.513 |
| semua_149 | x2_promosi | d_omzet | 149 | 0.280 | 0.122 | 0.424 | 0.001 | 0.009 |
| semua_149 | x2_promosi | d_trx | 145 | 0.266 | 0.105 | 0.413 | 0.001 | 0.017 |
| semua_149 | x2_promosi | y_obj | 149 | 0.264 | 0.106 | 0.410 | 0.001 | 0.017 |
| semua_149 | x2_promosi | y_pelanggan_baru | 149 | 0.162 | 0.000 | 0.316 | 0.048 | 0.271 |
| semua_149 | x3_komunikasi | d_omzet | 149 | 0.178 | 0.017 | 0.331 | 0.029 | 0.206 |
| semua_149 | x3_komunikasi | d_trx | 145 | 0.214 | 0.051 | 0.366 | 0.010 | 0.098 |
| semua_149 | x3_komunikasi | y_obj | 149 | 0.200 | 0.039 | 0.351 | 0.014 | 0.129 |
| semua_149 | x3_komunikasi | y_pelanggan_baru | 149 | -0.094 | -0.251 | 0.068 | 0.253 | 0.513 |
| semua_149 | x4_konsistensi | d_omzet | 149 | 0.116 | -0.046 | 0.272 | 0.159 | 0.513 |
| semua_149 | x4_konsistensi | d_trx | 145 | 0.200 | 0.036 | 0.353 | 0.016 | 0.129 |
| semua_149 | x4_konsistensi | y_obj | 149 | 0.164 | 0.003 | 0.318 | 0.045 | 0.271 |
| semua_149 | x4_konsistensi | y_pelanggan_baru | 149 | 0.125 | -0.037 | 0.281 | 0.128 | 0.513 |


![eda_spearman_heatmap](figures/eda_spearman_heatmap.png)

**Interpretasi:** Promosi (X2), komunikasi pelanggan (X3) dan unggah produk (X1) berkorelasi positif lemah-sedang dengan kinerja gabungan Y_obj (rho 0,27-0,33, Holm p < 0,05), sedangkan konsistensi kelola toko (X4) paling lemah (rho 0,14, tidak bermakna); tidak satu pun strategi berkorelasi positif bermakna dengan jumlah pelanggan baru.


### Persepsi sebagai pembanding

| sampel | x | y | n | rho | ci_bawah | ci_atas | p | p_holm | jenis |
|---|---|---|---|---|---|---|---|---|---|
| utama | y_persepsi | d_omzet | 116 | 0.197 | 0.013 | 0.367 | 0.034 | 0.206 | persepsi_vs_angka |
| utama | y_persepsi | d_trx | 112 | 0.274 | 0.090 | 0.440 | 0.003 | 0.028 | persepsi_vs_angka |
| utama | y_persepsi | y_obj | 116 | 0.245 | 0.063 | 0.411 | 0.008 | 0.057 | persepsi_vs_angka |
| utama | y_persepsi | y_pelanggan_baru | 116 | -0.053 | -0.233 | 0.131 | 0.571 | 1.000 | persepsi_vs_angka |
| utama | y_persepsi_1 | d_omzet | 116 | 0.194 | 0.011 | 0.365 | 0.037 | 0.206 | butir_vs_padanan |
| utama | y_persepsi_4 | d_trx | 112 | 0.164 | -0.024 | 0.340 | 0.084 | 0.336 | butir_vs_padanan |
| utama | y_persepsi_5 | y_pelanggan_baru | 116 | -0.025 | -0.207 | 0.158 | 0.789 | 1.000 | butir_vs_padanan |
| utama | y_persepsi | x1_unggah | 116 | 0.297 | 0.117 | 0.458 | 0.001 | 0.011 | persepsi_vs_strategi |
| utama | y_persepsi | x2_promosi | 116 | 0.129 | -0.055 | 0.305 | 0.167 | 0.501 | persepsi_vs_strategi |
| utama | y_persepsi | x3_komunikasi | 116 | 0.375 | 0.200 | 0.526 | 0.000 | 0.000 | persepsi_vs_strategi |
| utama | y_persepsi | x4_konsistensi | 116 | 0.374 | 0.199 | 0.525 | 0.000 | 0.000 | persepsi_vs_strategi |
| semua_149 | y_persepsi | d_omzet | 149 | 0.169 | 0.007 | 0.322 | 0.039 | 0.200 | persepsi_vs_angka |
| semua_149 | y_persepsi | d_trx | 145 | 0.195 | 0.031 | 0.348 | 0.019 | 0.150 | persepsi_vs_angka |
| semua_149 | y_persepsi | y_obj | 149 | 0.174 | 0.013 | 0.327 | 0.033 | 0.200 | persepsi_vs_angka |
| semua_149 | y_persepsi | y_pelanggan_baru | 149 | -0.008 | -0.169 | 0.153 | 0.923 | 1.000 | persepsi_vs_angka |
| semua_149 | y_persepsi_1 | d_omzet | 149 | 0.159 | -0.003 | 0.312 | 0.053 | 0.213 | butir_vs_padanan |
| semua_149 | y_persepsi_4 | d_trx | 145 | 0.134 | -0.031 | 0.291 | 0.108 | 0.325 | butir_vs_padanan |
| semua_149 | y_persepsi_5 | y_pelanggan_baru | 149 | 0.033 | -0.129 | 0.193 | 0.692 | 1.000 | butir_vs_padanan |
| semua_149 | y_persepsi | x1_unggah | 149 | 0.352 | 0.198 | 0.489 | 0.000 | 0.000 | persepsi_vs_strategi |
| semua_149 | y_persepsi | x2_promosi | 149 | 0.181 | 0.019 | 0.333 | 0.027 | 0.192 | persepsi_vs_strategi |
| semua_149 | y_persepsi | x3_komunikasi | 149 | 0.266 | 0.107 | 0.412 | 0.001 | 0.009 | persepsi_vs_strategi |
| semua_149 | y_persepsi | x4_konsistensi | 149 | 0.379 | 0.227 | 0.513 | 0.000 | 0.000 | persepsi_vs_strategi |


`persepsi_vs_angka`: apakah persepsi selaras dengan angka nyata; `butir_vs_padanan`: butir persepsi vs ukuran objektif padanannya; `persepsi_vs_strategi`: persepsi vs skor strategi.


## 5. Perbandingan kelompok (Mann-Whitney U)

### naik_penjualan = 1 vs 0

Holm dihitung per varian atas 4 strategi; baris y_persepsi diuji terpisah (pembanding). `utama_tanpa_seragam` = sampel utama tanpa `flag_jawaban_seragam` (D20).


| varian | variabel | n_1 | n_0 | median_1 | median_0 | z | p | p_holm | r | r_rank_biserial | efek |
|---|---|---|---|---|---|---|---|---|---|---|---|
| utama | x1_unggah | 61 | 55 | 2.250 | 2.000 | 2.696 | 0.007 | 0.014 | 0.250 | 0.277 | kecil |
| utama | x2_promosi | 61 | 55 | 2.750 | 2.000 | 3.130 | 0.002 | 0.007 | 0.291 | 0.333 | kecil |
| utama | x3_komunikasi | 61 | 55 | 3.600 | 3.000 | 3.089 | 0.002 | 0.007 | 0.287 | 0.314 | kecil |
| utama | x4_konsistensi | 61 | 55 | 3.000 | 3.000 | 1.144 | 0.253 | 0.253 | 0.106 | 0.116 | kecil |
| utama | y_persepsi | 61 | 55 | 3.000 | 3.000 | 2.321 | 0.020 | 0.020 | 0.216 | 0.212 | kecil |
| utama_tanpa_seragam | x1_unggah | 53 | 54 | 2.000 | 2.000 | 1.928 | 0.054 | 0.108 | 0.186 | 0.204 | kecil |
| utama_tanpa_seragam | x2_promosi | 53 | 54 | 2.500 | 2.000 | 2.467 | 0.014 | 0.041 | 0.238 | 0.274 | kecil |
| utama_tanpa_seragam | x3_komunikasi | 53 | 54 | 3.800 | 3.000 | 3.673 | 0.000 | 0.001 | 0.355 | 0.393 | sedang |
| utama_tanpa_seragam | x4_konsistensi | 53 | 54 | 3.000 | 3.000 | 1.352 | 0.176 | 0.176 | 0.131 | 0.144 | kecil |
| utama_tanpa_seragam | y_persepsi | 53 | 54 | 3.000 | 3.000 | 2.489 | 0.013 | 0.013 | 0.241 | 0.241 | kecil |
| semua_149 | x1_unggah | 65 | 84 | 2.250 | 2.000 | 2.807 | 0.005 | 0.020 | 0.230 | 0.255 | kecil |
| semua_149 | x2_promosi | 65 | 84 | 2.750 | 2.250 | 2.698 | 0.007 | 0.021 | 0.221 | 0.255 | kecil |
| semua_149 | x3_komunikasi | 65 | 84 | 3.600 | 3.200 | 2.214 | 0.027 | 0.054 | 0.181 | 0.202 | kecil |
| semua_149 | x4_konsistensi | 65 | 84 | 3.000 | 3.000 | 1.729 | 0.084 | 0.084 | 0.142 | 0.157 | kecil |
| semua_149 | y_persepsi | 65 | 84 | 3.000 | 3.000 | 2.046 | 0.041 | 0.041 | 0.168 | 0.164 | kecil |


![eda_boxplot_naik_penjualan](figures/eda_boxplot_naik_penjualan.png)

**Interpretasi:** UMKM yang penjualannya naik cenderung memiliki skor promosi (X2), komunikasi pelanggan (X3) dan unggah produk (X1) lebih tinggi (rank-biserial 0,28-0,33, efek kecil-sedang, Holm p < 0,05), sedangkan skor konsistensi kelola toko (X4) tidak berbeda nyata antara kedua kelompok.


### tanpa_baseline (1) vs punya baseline (0), 149 responden

| varian | variabel | n_1 | n_0 | median_1 | median_0 | z | p | p_holm | r | r_rank_biserial | efek |
|---|---|---|---|---|---|---|---|---|---|---|---|
| strategi | x1_unggah | 33 | 116 | 2.000 | 2.000 | 0.217 | 0.828 | 1.000 | 0.018 | 0.024 | sangat kecil |
| strategi | x2_promosi | 33 | 116 | 2.500 | 2.375 | 0.883 | 0.377 | 1.000 | 0.072 | 0.100 | sangat kecil |
| strategi | x3_komunikasi | 33 | 116 | 3.400 | 3.200 | 0.914 | 0.361 | 1.000 | 0.075 | 0.100 | sangat kecil |
| strategi | x4_konsistensi | 33 | 116 | 3.000 | 3.000 | -1.229 | 0.219 | 0.876 | -0.101 | -0.133 | kecil |
| profil_dan_lainnya | y_persepsi | 33 | 116 | 3.000 | 3.000 | -1.129 | 0.259 | 0.518 | -0.092 | -0.108 | sangat kecil |
| profil_dan_lainnya | lama_di_mp | 33 | 116 | 3.000 | 3.000 | -1.670 | 0.095 | 0.285 | -0.137 | -0.189 | kecil |
| profil_dan_lainnya | jumlah_platform | 33 | 116 | 2.000 | 2.000 | 0.738 | 0.460 | 0.518 | 0.060 | 0.080 | sangat kecil |
| profil_dan_lainnya | log_omzet_sebelum | 33 | 116 | 16.118 | 16.811 | -2.181 | 0.029 | 0.146 | -0.179 | -0.249 | kecil |
| profil_dan_lainnya | y_pelanggan_baru | 33 | 116 | 4.615 | 3.932 | 2.053 | 0.040 | 0.160 | 0.168 | 0.234 | kecil |


![eda_boxplot_tanpa_baseline](figures/eda_boxplot_tanpa_baseline.png)

**Interpretasi:** Skor keempat strategi UMKM tanpa baseline tidak berbeda nyata dari UMKM lainnya (semua Holm p > 0,05, rank-biserial -0,13 sampai 0,10), sehingga mengeluarkan mereka dari analisis utama kecil kemungkinannya menggeser gambaran strategi sampel.


## 6. VIF

Batas waspada VIF > 5. VIF maksimum: semua_149 / A_strategi = 1,44; semua_149 / B_strategi_profil = 1,50; semua_149 / C_strategi_profil_dummy_platform = 1,57; utama / A_strategi = 1,31; utama / B_strategi_profil = 1,37; utama / C_strategi_profil_dummy_platform = 1,49. `jumlah_platform` dan dummy platform tidak dimasukkan bersamaan (kolinear sempurna).


| sampel | set | variabel | vif | waspada |
|---|---|---|---|---|
| utama | A_strategi | x1_unggah | 1.26 | TIDAK |
| utama | A_strategi | x2_promosi | 1.22 | TIDAK |
| utama | A_strategi | x3_komunikasi | 1.25 | TIDAK |
| utama | A_strategi | x4_konsistensi | 1.31 | TIDAK |
| utama | B_strategi_profil | x1_unggah | 1.29 | TIDAK |
| utama | B_strategi_profil | x2_promosi | 1.29 | TIDAK |
| utama | B_strategi_profil | x3_komunikasi | 1.31 | TIDAK |
| utama | B_strategi_profil | x4_konsistensi | 1.35 | TIDAK |
| utama | B_strategi_profil | lama_usaha_pra_mp | 1.32 | TIDAK |
| utama | B_strategi_profil | lama_di_mp | 1.37 | TIDAK |
| utama | B_strategi_profil | jumlah_platform | 1.06 | TIDAK |
| utama | B_strategi_profil | log_omzet_sebelum | 1.05 | TIDAK |
| utama | C_strategi_profil_dummy_platform | x1_unggah | 1.44 | TIDAK |
| utama | C_strategi_profil_dummy_platform | x2_promosi | 1.31 | TIDAK |
| utama | C_strategi_profil_dummy_platform | x3_komunikasi | 1.43 | TIDAK |
| utama | C_strategi_profil_dummy_platform | x4_konsistensi | 1.42 | TIDAK |
| utama | C_strategi_profil_dummy_platform | lama_usaha_pra_mp | 1.49 | TIDAK |
| utama | C_strategi_profil_dummy_platform | lama_di_mp | 1.37 | TIDAK |
| utama | C_strategi_profil_dummy_platform | log_omzet_sebelum | 1.07 | TIDAK |
| utama | C_strategi_profil_dummy_platform | mp_gofood | 1.26 | TIDAK |
| utama | C_strategi_profil_dummy_platform | mp_grabfood | 1.25 | TIDAK |
| utama | C_strategi_profil_dummy_platform | mp_shopee | 1.30 | TIDAK |
| utama | C_strategi_profil_dummy_platform | mp_maxim | 1.14 | TIDAK |
| utama | C_strategi_profil_dummy_platform | mp_tiktok | 1.16 | TIDAK |
