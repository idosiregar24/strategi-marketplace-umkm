# Progres

| Tahap | Nama | Status | Keluaran utama | Selesai pada |
|---|---|---|---|---|
| 1 | Cleaning | SELESAI | data/processed/data_clean.csv, reports/cleaning_log.md, notebooks/00_setup_colab.ipynb | 2026-10-14 |
| 2 | Konstruksi variabel | SELESAI | data/processed/data_features.csv, reports/features_log.md, reports/tables/reliabilitas*.csv | 2026-10-14 |
| 3 | EDA | SELESAI | reports/figures/eda_*, reports/tables/eda_*.csv, reports/eda_log.md, reports/eda_ringkasan.md | 2026-10-30 |
| 4 | Analisis pengaruh | SELESAI | reports/tables/pengaruh_*.csv, reports/figures/pengaruh_*.png, shap_*.png, reports/pengaruh_log.md, reports/pengaruh_ringkasan.md | 2026-10-30 |
| 5 | Segmentasi | BELUM | data/processed/data_segmen.csv | |
| 6 | Rekomendasi | BELUM | reports/tables/rekomendasi_per_segmen.csv, models/v1/, reports/integration_contract.md | |
| 7 | Pelaporan | BELUM | reports/laporan_final.md | |

Status: BELUM / BERJALAN / MENUNGGU PERSETUJUAN / SELESAI

## Catatan sesi
(Agent menambahkan ringkasan singkat tiap selesai tahap: apa dikerjakan, temuan penting, masalah terbuka.)

### 2026-10-14 - Tahap 1 (Cleaning)
- Dikerjakan: venv `.venv` (Python 3.11.9) + `pip install -e ".[analysis]"`; modul `config.py`, `io.py`,
  `cleaning.py`, `pipeline.py`; 31 tes di `tests/test_cleaning.py` lulus; ruff + black bersih.
  Jalankan ulang: `.venv/Scripts/python.exe -m umkm.pipeline --stage 1`.
- Hasil: 149 baris x 63 kolom, tanpa missing, semua Likert 1-5, omzet/transaksi numerik. D10 disepakati
  (R019: 2018 -> 8 th, 2023 -> 3 th).
- Temuan: 5 label Likert tidak cocok (D18); 4 responden transaksi janggal (D17); winsor P1 mengangkat nilai 0
  dan menghapus 3 perubahan naik (D16); 33 responden lama_usaha_pra_mp = 0 (untuk D14, Tahap 2); tanpa duplikat.
- D16 disepakati (winsor hanya P99) dan Tahap 1 dijalankan ulang: 3 responden terkena winsor; hanya R015
  (trx) yang arah perubahannya bergeser (naik -> sama), terkait D17.
- D17 disepakati: transaksi R002/R006/R015/R021 dikosongkan; dijalankan ulang (149 x 64). Winsor P99 kini
  mengenai 4 responden (R015 omzet; R019, R020, R107); tidak ada arah perubahan yang bergeser.
  Omzet: naik 60 / sama 85 / turun 4. Transaksi: naik 61 / sama 84 / turun 0 / kosong 4.
- Kesiapan Colab: `parse_timestamp` diperbaiki (pandas 2.2 membaca tanggal Excel sebagai datetime -> overflow);
  33 tes lolos dan data_clean.csv identik di pandas 2.2 dan 3. Dibuat `notebooks/00_setup_colab.ipynb` dan
  `umkm_proyek.zip` (jalur Drive, tanpa GitHub); alur notebook disimulasikan pada zip dan berhasil.
- D15 dan D18 disepakati. Tahap 1 disetujui pengguna: SELESAI.

### 2026-10-14 - Tahap 2 (Konstruksi variabel)
- Keputusan sebelum mulai: D04, D05, D06, D13 disepakati; D14 = analisis utama TANPA 33 responden
  `tanpa_baseline` (n=116); D19 = pakai 4 butir X1/X2 yang ada.
- Dikerjakan: `src/umkm/features.py`, pipeline `--stage 2`, 9 tes baru (total 41 lolos), sel Tahap 2 di
  notebook Colab, zip diperbarui.
- Hasil: data_features.csv 149 x 58. Alpha X1-X4 = 0,955 / 0,930 / 0,947 / 0,952 (semua butir-total >= 0,74).
  Korelasi antar strategi rendah-sedang (maks 0,39). naik_penjualan sampel utama: 61 naik vs 55 tidak.
  Missing hanya d_trx (4, D17) dan pct_* (sebelum = 0).
- Temuan: 10 responden straightlining (D20); omzet turun tepat 10x pada R065 dan R130 (D21).
- Terbuka: D20, D21, D22 (DIUSULKAN). Rencana Tahap 4 diperbarui (sensitivitas c, e, f, g).
- Catatan: file xlsx asli juga masih ada di root proyek (salinan identik dengan data/raw/).
- Tahap 2 disetujui pengguna (2026-10-14): SELESAI. D20, D21, D22 DISEPAKATI sesuai usulan.

### 2026-10-14 - Tahap 3 (EDA)
- Dikerjakan: modul `stats.py` (Wilcoxon, Mann-Whitney, Spearman+CI, Holm, VIF, ringkas skor), `viz.py`
  (gaya + palet tervalidasi CVD), `eda.py` (tabel + grafik), `eda_teks.py` (interpretasi/log/ringkasan dari angka);
  pipeline `--stage 3`; 17 tes baru (total 58 lolos); ruff + black bersih; `notebooks/03_eda.ipynb`; sel Tahap 3 di
  notebook Colab; zip diperbarui dan alur Colab disimulasikan dari zip (tahap 1-3, hasil identik).
- Hasil: 12 tabel `eda_*.csv`, 10 grafik `eda_*.png` (semua berjudul, sumbu berlabel, satu kalimat interpretasi di
  `eda_log.md` dan `eda_ringkasan.md`).
- Temuan kunci (sampel utama n=116): 53% naik (omzet atau transaksi), kenaikan kecil (median selisih omzet Rp50 rb).
  Spearman dengan Y_obj: X2 0,33, X3 0,30, X1 0,27 (Holm p < 0,05), X4 0,14 (tidak bermakna). Mann-Whitney naik vs
  tidak: X2/X3/X1 r_rb 0,28-0,33 (Holm p < 0,05), X4 tidak. Pelanggan baru tidak berkorelasi bermakna dengan strategi
  (X3 -0,20, Holm p = 0,24). Persepsi lemah selaras dengan angka (rho maks 0,27). VIF maks 1,57.
- Temuan kualitas: 18 dari 26 butir didominasi jawaban netral; y_persepsi 67% tepat 3. Tanpa 9 responden
  straightlining (8 naik), X1 tidak lagi bermakna (Holm 0,014 -> 0,108), X3 menguat (r_rb 0,39). Tanpa baseline vs
  lainnya: skor strategi tidak berbeda.
- Terbuka: D23 (DIUSULKAN). Untuk Tahap 4: perhatikan kepekaan X1 terhadap D20; korelasi negatif X3-pelanggan baru.
- Catatan Colab: jika folder `MyDrive/umkm_proyek/` sudah ada, hapus/ganti dengan isi zip baru agar modul Tahap 3 ikut.

### 2026-10-15 - Di luar tahap: dokumentasi dan dashboard
- `reports/hasil_utama.md` (ringkasan hasil manual), README.md, `.gitignore` diperketat (*.xlsx, cache).
- Dashboard lokal (D24): `src/umkm/dashboard.py` + `src/umkm/static/dashboard.html`; `python -m umkm.dashboard`
  -> http://localhost:8000. 9 tes baru (total 67 lolos). Tahap 3 masih MENUNGGU PERSETUJUAN.

### 2026-10-27 - Koreksi hasil konfirmasi responden (D25), tahap 1-3 dijalankan ulang
- Dikerjakan: `cleaning.apply_koreksi` + `config.yaml` `cleaning.koreksi` (5 sel: R065, R130, R106 omzet_sesudah;
  R006 trx_sesudah; R019 lama_usaha_pra_mp); kolom baru `flag_dikoreksi` (data_clean 149 x 65, data_features
  149 x 59); 4 tes baru; teks D21 di features_log, eda_teks, dashboard, hasil_utama.md disesuaikan;
  `python -m umkm.pipeline --all` dan ekspor xlsx dijalankan ulang.
- Dampak: omzet sampel utama naik 58 -> 59, turun 4 -> 1; median selisih omzet Rp50 rb -> Rp250 rb;
  naik_penjualan dan sampel_utama tidak berubah sehingga tabel Mann-Whitney identik. Spearman y_obj (utama):
  X2 0,33 -> 0,35, X3 0,30 -> 0,29 (tetap bermakna), X1 0,27 -> 0,23 (Holm 0,040 -> 0,124, tidak lagi bermakna),
  X4 0,14. flag_omzet_turun_tajam kini 0.
- Terbuka: D25 (DIUSULKAN), terutama keputusan tetap mengosongkan transaksi R002/R006/R015/R021.
  Tahap 3 tetap MENUNGGU PERSETUJUAN.
- data_umkm.xlsx ditambah sheet "Data terkoreksi" (nilai final tanpa kolom teknis, sel yang berubah diberi warna
  kuning) dan "Catatan koreksi" (12 sel: isian asli, nilai dipakai, alasan). 82 tes lolos.

### 2026-10-30 - Konfirmasi kedua: transaksi R002/R006/R015/R021 (D25), tahap 1-3 dijalankan ulang
- 8 entri koreksi transaksi di `config.yaml` (jumlah pesanan per bulan); tidak ada lagi transaksi dikosongkan, data
  bersih tanpa missing. Teks D17 di features_log, ekspor, dashboard, hasil_utama.md, rencana Tahap 4 disesuaikan.
  82 tes lolos; data_umkm.xlsx diperbarui.
- Dampak (sampel utama): naik_penjualan 61 -> 62 (R015 naik karena transaksi naik); winsor P99 trx 12.090 mengenai
  R015 dan R021. R021 (100 -> 15.000) jadi y_obj tertinggi (4,76) -> sensitivitas (f) Tahap 4 tanpa R021.
  Spearman y_obj: X2 0,32, X3 0,28 bermakna; X1 0,26 (Holm 0,060), X4 0,14 tidak. Mann-Whitney: X1/X2/X3 bermakna;
  tanpa responden seragam X1 dan X2 tidak lagi bermakna (Holm 0,091), X3 menguat.
- D25 DISEPAKATI pengguna (2026-10-30). Terbuka: D23 (DIUSULKAN). Tahap 3 MENUNGGU PERSETUJUAN.
- 2026-10-30: D23 DISEPAKATI; Tahap 3 disetujui pengguna: SELESAI. Lanjut Tahap 4.

### 2026-10-30 - Tahap 4 (Analisis pengaruh)
- Dikerjakan: `stats.py` (+standarkan, ols_hc3, logit_or), `models.py` (CV 5x5, kandidat + baseline, RF, permutation
  per lipatan, SHAP, bootstrap paralel, skor gabungan), `pengaruh.py` (regresi, moderasi, sensitivitas a-g, peringkat,
  grafik), `pengaruh_teks.py` (log + ringkasan dari angka), `viz.dot_ci` dan `viz.scatter_panel`; pipeline `--stage 4`
  (sekitar 6 menit); config `influence`; 8 tes baru (total 90 lolos); ruff + black bersih; `notebooks/04_pengaruh.ipynb`;
  sel Tahap 4 di notebook Colab (memasang shap); `umkm_proyek.zip` dibuat ulang (34 berkas, termasuk koreksi D25).
- Hasil (n=116, 62 naik): logit OR per SD X3 2,49 (p 0,001), X1 2,19 (p 0,005), X2 1,26 (p 0,34), X4 0,93 (p 0,78);
  log_omzet_sebelum OR 0,61 (p 0,04). CV naik_penjualan: RF AUC 0,735 / F1 0,70, logistik 0,72 / 0,62, baseline
  0,50 / 0,35. CV y_obj: semua model R2 sekitar -0,11 sampai -0,12 (tidak mengalahkan baseline) -> bobot dari naik_penjualan (D26).
- Peringkat gabungan (bootstrap 1000x): X3 1,00 (P#1 85%), X1 0,59 (P#2 65%), X2 0,36, X4 0,00. Sumber sepakat
  (rho 0,8-1,0). X1 dan X3 "meyakinkan" (CI koef > 0), X2 dan X4 tidak. X3 teratas di 6/6 skenario logit; X1 dan X3
  bermakna di semua skenario. Moderasi: 0/24 interaksi bermakna setelah Holm.
- Tinjauan stats-reviewer (2026-10-30): 2 KRITIS, 6 PENTING, 8 MINOR. Diterapkan: (1) kontras target ditulis
  terang (54/54 naik=0 = angka sama) + tabel `pengaruh_pola_isian` (tidak ada beda bermakna); (2) hubungan negatif
  dilaporkan (X3 vs y_pelanggan_baru koef -0,53, p < 0,001); (3) bug tanda permutation di `skor_gabungan` diperbaiki
  + tes; (4) OR ditulis sebagai odds + peluang prediksi -1/+1 SD (X3 34% -> 76%, X1 37% -> 73%) + SD poin; (5) bobot
  rekomendasi = pengaruh x p_koef_positif, minimal 0,1 (pilihan pengguna); (6) CV y_obj tanpa R021 + R2 out-of-fold;
  (7) bagian Keterbatasan, penjelasan spekulatif diperlunak; (8) skor gabungan untuk skenario c dan e (X3 tetap #1).
  Tambahan: Holm 4 strategi, uji LR blok strategi (p < 0,001), diagnostik residual OLS (R021 Cook 0,71), confusion
  matrix, SHAP per kelas, penanganan format SHAP lama. 96 tes lolos. D26 DISEPAKATI. `recommendation_logic.md`
  langkah 1 diperbarui. Belum: logit Firth (EPV 6,8; dicatat sebagai keterbatasan sampel kecil).

- 2026-10-30: Tahap 4 disetujui pengguna: SELESAI. Berikutnya Tahap 5 (segmentasi) di sesi baru.
