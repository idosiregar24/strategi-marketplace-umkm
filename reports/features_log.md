# Log Konstruksi Variabel (Tahap 2)

Dibuat oleh `umkm.features` pada 2026-10-30 09:53.

- data_features.csv: 149 baris x 59 kolom. Sampel utama (D14): 116 responden; `tanpa_baseline` = 33.

## 1. Reliabilitas konstruk (semua 149 responden)

Kriteria: alpha >= 0.70; korelasi butir-total terkoreksi >= 0.30. Tidak ada butir yang dibuang otomatis.

| konstruk | peran | n_butir | n_responden | alpha | lolos_alpha | min_korelasi_butir_total | butir_di_bawah_0_30 |
|---|---|---|---|---|---|---|---|
| x1_unggah | strategi | 4 | 149 | 0.955 | ya | 0.885 |  |
| x2_promosi | strategi | 4 | 149 | 0.930 | ya | 0.749 |  |
| x3_komunikasi | strategi | 5 | 149 | 0.947 | ya | 0.804 |  |
| x4_konsistensi | strategi | 5 | 149 | 0.952 | ya | 0.843 |  |
| y_persepsi | pendukung | 8 | 149 | 0.955 | ya | 0.738 |  |


### Per butir

| konstruk | butir | rata_rata | sd | korelasi_butir_total | alpha_jika_dihapus | lolos_item_total | alpha_naik_jika_dihapus |
|---|---|---|---|---|---|---|---|
| x1_unggah | x1_unggah_1 | 2.369 | 0.765 | 0.885 | 0.944 | ya | TIDAK |
| x1_unggah | x1_unggah_2 | 2.336 | 0.633 | 0.887 | 0.946 | ya | TIDAK |
| x1_unggah | x1_unggah_3 | 2.336 | 0.722 | 0.892 | 0.941 | ya | TIDAK |
| x1_unggah | x1_unggah_4 | 2.403 | 0.753 | 0.914 | 0.934 | ya | TIDAK |
| x2_promosi | x2_promosi_1 | 2.503 | 0.794 | 0.825 | 0.913 | ya | TIDAK |
| x2_promosi | x2_promosi_2 | 2.215 | 0.843 | 0.749 | 0.939 | ya | ya |
| x2_promosi | x2_promosi_3 | 2.403 | 0.805 | 0.910 | 0.884 | ya | TIDAK |
| x2_promosi | x2_promosi_4 | 2.383 | 0.768 | 0.870 | 0.899 | ya | TIDAK |
| x3_komunikasi | x3_komunikasi_1 | 3.463 | 0.683 | 0.847 | 0.936 | ya | TIDAK |
| x3_komunikasi | x3_komunikasi_2 | 3.544 | 0.692 | 0.804 | 0.943 | ya | TIDAK |
| x3_komunikasi | x3_komunikasi_3 | 3.470 | 0.663 | 0.837 | 0.938 | ya | TIDAK |
| x3_komunikasi | x3_komunikasi_4 | 3.550 | 0.692 | 0.885 | 0.929 | ya | TIDAK |
| x3_komunikasi | x3_komunikasi_5 | 3.530 | 0.663 | 0.902 | 0.926 | ya | TIDAK |
| x4_konsistensi | x4_konsistensi_1 | 3.188 | 0.729 | 0.880 | 0.939 | ya | TIDAK |
| x4_konsistensi | x4_konsistensi_2 | 3.134 | 0.741 | 0.862 | 0.942 | ya | TIDAK |
| x4_konsistensi | x4_konsistensi_3 | 3.148 | 0.711 | 0.895 | 0.936 | ya | TIDAK |
| x4_konsistensi | x4_konsistensi_4 | 3.282 | 0.669 | 0.843 | 0.945 | ya | TIDAK |
| x4_konsistensi | x4_konsistensi_5 | 3.181 | 0.698 | 0.859 | 0.942 | ya | TIDAK |
| y_persepsi | y_persepsi_1 | 3.201 | 0.569 | 0.768 | 0.954 | ya | TIDAK |
| y_persepsi | y_persepsi_2 | 3.168 | 0.574 | 0.919 | 0.944 | ya | TIDAK |
| y_persepsi | y_persepsi_3 | 3.181 | 0.533 | 0.908 | 0.945 | ya | TIDAK |
| y_persepsi | y_persepsi_4 | 3.107 | 0.547 | 0.753 | 0.954 | ya | TIDAK |
| y_persepsi | y_persepsi_5 | 3.161 | 0.508 | 0.847 | 0.949 | ya | TIDAK |
| y_persepsi | y_persepsi_6 | 3.114 | 0.587 | 0.738 | 0.956 | ya | ya |
| y_persepsi | y_persepsi_7 | 3.154 | 0.489 | 0.887 | 0.947 | ya | TIDAK |
| y_persepsi | y_persepsi_8 | 3.161 | 0.521 | 0.866 | 0.947 | ya | TIDAK |


## 2. Sebaran arah perubahan

| sampel | variabel | naik | sama | turun | kosong |
|---|---|---|---|---|---|
| semua_149 | omzet | 61 | 87 | 1 | 0 |
| semua_149 | trx | 64 | 85 | 0 | 0 |
| utama | omzet | 59 | 56 | 1 | 0 |
| utama | trx | 60 | 56 | 0 | 0 |


## 3. Target utama `naik_penjualan` (D13)

| kelompok | naik | tidak_naik | total |
|---|---|---|---|
| punya_baseline (utama) | 62 | 54 | 116 |
| tanpa_baseline | 4 | 29 | 33 |
| total | 66 | 83 | 149 |


`y_obj` = rata-rata z(d_omzet) dan z(d_trx); z memakai rata-rata/SD sampel utama. Untuk responden dengan transaksi kosong (D17), `y_obj` dan `naik_penjualan` dari omzet saja. `y_pelanggan_baru` = log1p(pelanggan_baru), target tambahan (D06).


## 4. Statistik deskriptif

| variabel | sampel | count | mean | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|---|---|
| d_omzet | semua_149 | 149.000 | 0.243 | 1.545 | -0.095 | 0.000 | 0.000 | 0.182 | 18.826 |
| d_trx | semua_149 | 149.000 | 0.250 | 0.854 | 0.000 | 0.000 | 0.000 | 0.223 | 8.700 |
| y_obj | semua_149 | 149.000 | 0.248 | 4.348 | -0.566 | -0.566 | -0.566 | 0.118 | 52.097 |
| y_pelanggan_baru | semua_149 | 149.000 | 4.071 | 1.448 | 0.000 | 3.045 | 4.394 | 5.303 | 7.314 |
| x1_unggah | semua_149 | 149.000 | 2.361 | 0.676 | 1.000 | 2.000 | 2.000 | 3.000 | 4.500 |
| x2_promosi | semua_149 | 149.000 | 2.376 | 0.730 | 1.000 | 2.000 | 2.500 | 3.000 | 4.250 |
| x3_komunikasi | semua_149 | 149.000 | 3.511 | 0.617 | 2.000 | 3.000 | 3.200 | 4.000 | 5.000 |
| x4_konsistensi | semua_149 | 149.000 | 3.187 | 0.650 | 1.000 | 3.000 | 3.000 | 3.800 | 4.600 |
| y_persepsi | semua_149 | 149.000 | 3.156 | 0.473 | 1.250 | 3.000 | 3.000 | 3.125 | 4.750 |
| d_omzet | utama | 116.000 | 0.150 | 0.213 | -0.095 | 0.000 | 0.059 | 0.223 | 1.099 |
| d_trx | utama | 116.000 | 0.221 | 0.515 | 0.000 | 0.000 | 0.078 | 0.286 | 4.785 |
| y_obj | utama | 116.000 | -0.000 | 0.835 | -0.566 | -0.566 | -0.285 | 0.237 | 4.759 |
| y_pelanggan_baru | utama | 116.000 | 3.924 | 1.494 | 0.000 | 2.773 | 3.932 | 5.303 | 7.314 |
| x1_unggah | utama | 116.000 | 2.341 | 0.640 | 1.000 | 2.000 | 2.000 | 3.000 | 4.000 |
| x2_promosi | utama | 116.000 | 2.341 | 0.740 | 1.000 | 2.000 | 2.375 | 3.000 | 4.000 |
| x3_komunikasi | utama | 116.000 | 3.498 | 0.624 | 2.000 | 3.000 | 3.200 | 4.000 | 5.000 |
| x4_konsistensi | utama | 116.000 | 3.222 | 0.610 | 1.000 | 3.000 | 3.000 | 3.800 | 4.600 |
| y_persepsi | utama | 116.000 | 3.178 | 0.441 | 1.875 | 3.000 | 3.000 | 3.375 | 4.375 |


## 5. Fitur profil

`skala_omzet` dari kuartil omzet_sebelum_w (149 responden): Q1 <= 9,000,000; Q2 <= 18,000,000; Q3 <= 30,000,000; Q4 di atasnya.

Q1_kecil = 41, Q2_menengah_bawah = 37, Q3_menengah_atas = 36, Q4_besar = 35.


Catatan: untuk responden `tanpa_baseline`, omzet sebelum praktis sama dengan omzet saat ini, jadi `skala_omzet` mereka mencerminkan omzet sekarang.


## 6. Pemeriksaan kebocoran (leakage)

- Fitur strategi (x1-x4) hanya dari butir Likert X; fitur profil hanya dari lama usaha, platform, dan omzet SEBELUM.
- `y_persepsi` dan `pelanggan_baru` tidak dipakai sebagai fitur.
- Catatan: `log_omzet_sebelum` ikut menyusun `d_omzet` (sebagai pengurang). Ini bukan kebocoran (kondisi awal), tetapi bisa memunculkan efek regresi ke rata-rata; di Tahap 4 dilaporkan model dengan dan tanpa variabel ini.


## 7. Korelasi antar strategi (Spearman, 149 responden)

|  | x1_unggah | x2_promosi | x3_komunikasi | x4_konsistensi |
|---|---|---|---|---|
| x1_unggah | 1.00 | 0.38 | -0.04 | 0.39 |
| x2_promosi | 0.38 | 1.00 | 0.21 | 0.29 |
| x3_komunikasi | -0.04 | 0.21 | 1.00 | 0.38 |
| x4_konsistensi | 0.39 | 0.29 | 0.38 | 1.00 |


Korelasi rendah-sedang berarti keempat strategi terukur sebagai hal yang berbeda (validitas diskriminan memadai); VIF diperiksa di Tahap 3.


## 8. Kualitas jawaban (hanya ditandai)

- `flag_jawaban_seragam`: 10 responden menjawab 18 butir strategi dengan angka yang sama persis (indikasi straightlining).
- Jumlah blok strategi (dari 4) yang dijawab seragam per responden: 0 blok = 3, 1 blok = 29, 2 blok = 33, 3 blok = 48, 4 blok = 36. Pola ini ikut menjelaskan alpha yang sangat tinggi (> 0,9).
- `flag_omzet_turun_tajam` (omzet sesudah <= 20% omzet sebelum):

_(tidak ada)_


R065, R130 (turun tepat 10x) dan R106 sudah dikoreksi lewat konfirmasi responden (D25). Yang tersisa di tabel ini adalah isian yang dikonfirmasi responden sendiri; nilainya memengaruhi `y_obj`, tetapi tidak memengaruhi `naik_penjualan`.
