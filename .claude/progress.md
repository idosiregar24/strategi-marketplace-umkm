# Progres

| Tahap | Nama | Status | Keluaran utama | Selesai pada |
|---|---|---|---|---|
| 1 | Cleaning | SELESAI | data/processed/data_clean.csv, reports/cleaning_log.md, notebooks/00_setup_colab.ipynb | 2026-10-14 |
| 2 | Konstruksi variabel | SELESAI | data/processed/data_features.csv, reports/features_log.md, reports/tables/reliabilitas*.csv | 2026-10-14 |
| 3 | EDA | MENUNGGU PERSETUJUAN | reports/figures/eda_*, reports/tables/eda_*.csv, reports/eda_log.md, reports/eda_ringkasan.md | |
| 4 | Analisis pengaruh | BELUM | reports/tables/pengaruh_*.csv | |
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
