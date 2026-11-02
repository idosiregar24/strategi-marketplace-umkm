# Ringkasan: PLS-SEM sebagai Analisis Pembanding

PLS-SEM menguji hubungan keempat strategi dengan kinerja penjualan sambil memperhitungkan galat pengukuran butir kuesioner. Hasilnya dibandingkan dengan regresi logistik, Random Forest, dan SHAP pada analisis utama. Semua hubungan bersifat asosiasi.

## Temuan

1. **Model pengukuran memadai.** Keempat konstruk strategi dan persepsi kinerja reliabel (Cronbach alpha 0,93-0,96, composite reliability 0,95-0,97), validitas konvergen terpenuhi (AVE 0,77-0,89; loading terendah 0,80), dan konstruk dapat dibedakan satu sama lain (HTMT tertinggi 0,54, batas atas interval bootstrap tertinggi 0,65 < 0,85).
2. **Melaporkan kenaikan penjualan.** Jalur terkuat berasal dari X3 Komunikasi pelanggan (beta = 0,34, p < 0,001, f2 = 0,12, kecil). Jalur yang intervalnya tidak mencakup nol: X1 Unggah produk dan X3 Komunikasi pelanggan. Urutan: X3 Komunikasi pelanggan > X1 Unggah produk > X2 Promosi > X4 Konsistensi toko. R2 = 0,26; AUC validasi silang 0,72 (SD 0,12).
3. **Besar kenaikan (y_obj).** Urutan jalur: X3 Komunikasi pelanggan > X1 Unggah produk > X2 Promosi > X4 Konsistensi toko; jalur yang intervalnya tidak mencakup nol: tidak ada; setelah koreksi Holm tidak ada yang bermakna (Holm p terkecil 0,307). R2 = 0,18, tetapi Q2_predict = 0,00: di luar sampel model hampir tidak lebih baik dari rata-rata, sejalan dengan R2 out-of-fold pada analisis utama.
4. **Persepsi kinerja (Y1-Y8).** Urutan jalur: X4 Konsistensi toko > X1 Unggah produk > X3 Komunikasi pelanggan > X2 Promosi (beta tertinggi 0,33); R2 = 0,37. Penilaian diri pelaku usaha paling dekat dengan X4 Konsistensi toko dan X1 Unggah produk, sedangkan laporan angka penjualan paling dekat dengan X3 Komunikasi pelanggan. Perbedaan ini sejalan dengan alasan persepsi tidak dipakai sebagai target utama.
5. **Konsisten dengan metode inti.** Urutan jalur PLS untuk naik_penjualan dibandingkan peringkat gabungan regresi logistik, Random Forest, dan SHAP: Spearman rho = 1,00. AUC validasi silang PLS 0,72, regresi logistik 0,72, Random Forest 0,73. X2 Promosi dan X4 Konsistensi toko belum meyakinkan berhubungan dengan pelaporan kenaikan, baik di PLS-SEM maupun di peringkat gabungan.

## Koefisien jalur strategi

| Strategi | Kinerja objektif (y_obj) | Melaporkan kenaikan (naik_penjualan) | Persepsi kinerja (Y1-Y8) |
|---|---|---|---|
| X1 Unggah produk | 0.15 | 0.27 | 0.30 |
| X2 Promosi | 0.07 | 0.10 | -0.02 |
| X3 Komunikasi pelanggan | 0.17 | 0.34 | 0.16 |
| X4 Konsistensi toko | 0.03 | -0.02 | 0.33 |


Tiap model juga mengendalikan profil usaha. Interval, p-value, dan ukuran efek ada di `sem_log.md` dan `tables/sem_jalur.csv`.

## Keterbatasan

- PLS-SEM di sini memakai data potong lintang yang sama dengan analisis utama, sehingga fungsinya sebagai pemeriksaan kekokohan, bukan bukti tambahan yang independen.
- naik_penjualan berupa 0/1; koefisien jalur PLS untuk target ini setara model peluang linear dan dibaca sebagai arah serta urutan, bukan besar peluang.
- Konstruk satu indikator (kinerja objektif dan profil usaha) dianggap terukur tanpa galat.
- rho_A sedikit di atas 1 pada X3 Komunikasi pelanggan dan X4 Konsistensi toko (maks 1,017). Ini muncul bila bobot indikator tidak seimbang relatif terhadap korelasi antarbutir; reliabilitas tetap dinilai dari alpha dan rho_C.
- Interval bootstrap loading lebar pada X2 Promosi, X3 Komunikasi pelanggan dan X4 Konsistensi toko (batas bawah terendah 0,38). Pada Mode A bobot butir mengikuti korelasinya dengan target; bila hubungan konstruk dengan target lemah, bobot di sampel ulang ikut tidak stabil. Estimasi titik tetap di atas ambang.
- Banyak butir didominasi jawaban netral dan ada responden dengan jawaban seragam; ini dapat menaikkan reliabilitas secara semu. CB-SEM tidak dipakai karena ukuran sampel kecil dan target utama hanya satu indikator.
