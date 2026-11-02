# Laporan Akhir Penelitian: Analisis Strategi Penjualan UMKM di Marketplace

**Lokasi Studi:** Pekanbaru, Riau  
**Ukuran Sampel:** 149 UMKM (116 Sampel Utama Analisis, 33 Sampel Pembanding Tanpa Baseline)  
**Tahun Analisis:** 2026  
**Kode Analisis:** paket Python `umkm` (seluruh tahap dapat dijalankan ulang)  

---

## Ringkasan Eksekutif

Penelitian ini bertujuan untuk mengidentifikasi strategi penjualan marketplace (unggah produk, promosi marketplace, komunikasi pelanggan, dan konsistensi kelola toko) yang paling berhubungan dengan kinerja penjualan pada 149 UMKM di Pekanbaru, serta merumuskan rekomendasi strategi berbasis segmentasi profil usaha. 

Seluruh analisis dievaluasi secara ketat menggunakan prinsip **asosiasi non-kausal** dengan penanganan regresi robust, validasi silang berulang (*Repeated Stratified K-Fold* 5×5), algoritma Machine Learning (*Random Forest*), interpretasi fitur (*Permutation Importance* dan *SHAP TreeExplainer*), *clustering K-Means* berbasis profil, serta PLS-SEM sebagai analisis pembanding.

### Temuan Utama:
1. **Dampak Penggunaan Marketplace:** Sebanyak 62 dari 116 UMKM (53.4%) pada sampel utama melaporkan peningkatan omzet atau transaksi setelah berjualan di marketplace (median peningkatan omzet Rp250.000/bulan, median transaksi naik 7 pesanan/bulan; Wilcoxon $p < 0,001$).
2. **Hierarki Pengaruh Strategi:** 
   - **X3 (Komunikasi Pelanggan)** merupakan strategi yang paling konsisten dan paling kuat hubungannya dengan peningkatan penjualan (Odds Ratio Logit = 2.49, $p = 0,001$; Skor Pengaruh Gabungan = 1,00; Permutation Importance RF = 0.115).
   - **X1 (Unggah Produk)** menempati posisi kedua yang meyakinkan (Odds Ratio Logit = 2.19, $p = 0,005$; Skor Pengaruh Gabungan = 0,59).
   - **X2 (Promosi Marketplace)** dan **X4 (Konsistensi Toko)** belum menunjukkan hubungan positif yang meyakinkan setelah mengontrol variabel profil dan strategi lainnya.
3. **Segmentasi UMKM:** Terbentuk 2 klaster alami berbasis profil usaha:
   - **Segmen 1 (74 UMKM):** Usaha berskala omzet kecil, usia usaha muda, dan baru masuk ke marketplace.
   - **Segmen 2 (75 UMKM):** Usaha berskala omzet mapan, usia usaha lebih matang, dan lama di marketplace.
   - *Catatan Kritis:* Kedua segmen tidak berbeda secara signifikan pada skor penerapan strategi X1–X4 maupun persentase kenaikan penjualan. Oleh karena itu, urutan prioritas rekomendasi seragam (**X3 > X1 > X2**), namun tindakan praktis disesuaikan dengan kapasitas skala usaha.
4. **Simulasi Model (Random Forest):** Pada model, skor Komunikasi Pelanggan yang 1 poin lebih tinggi (skala 1–5) berpadanan dengan peluang prediksi melaporkan kenaikan yang lebih tinggi **+14.4 poin persen** pada Segmen 1 dan **+17.5 poin persen** pada Segmen 2. Angka ini ilustrasi perilaku model, bukan jaminan hasil.
5. **Analisis Pembanding PLS-SEM:** Dengan konstruk laten dan galat pengukuran diperhitungkan, urutan hubungan tetap X3 > X1 > X2 > X4 (jalur X3 Komunikasi Pelanggan = 0,34); model pengukuran memenuhi kriteria reliabilitas dan validitas.

---

## 1. Latar Belakang dan Pertanyaan Penelitian

Penetrasi digital melalui platform e-commerce dan marketplace (Shopee, GoFood, GrabFood, Maxim, TikTok Shop) menjadi pendorong utama transformasi UMKM. Namun, pelaku usaha sering menghadapi keterbatasan sumber daya untuk menjalankan semua taktik digital secara bersamaan.

Penelitian ini menjawab 4 pertanyaan inti:
1. **Pertanyaan 1 (Kinerja Sebelum-Sesudah):** Apakah terjadi peningkatan penjualan objektif (omzet dan transaksi) setelah UMKM mengadopsi marketplace?
2. **Pertanyaan 2 (Pengaruh Strategi):** Di antara strategi unggah produk (X1), promosi (X2), komunikasi pelanggan (X3), dan konsistensi toko (X4), manakah yang paling kuat hubungannya dengan kinerja penjualan?
3. **Pertanyaan 3 (Efek Moderasi Profil):** Apakah hubungan strategi tersebut bervariasi tergantung profil UMKM (lama usaha, lama di platform, jumlah platform, skala omzet)?
4. **Pertanyaan 4 (Rekomendasi per Segmen):** Strategi apa yang harus diprioritaskan untuk tiap kelompok segmen UMKM?

---

## 2. Metodologi Data dan Rekayasa Fitur

### 2.1 Pembersihan Data (Tahap 1)
- **Sumber Data:** 149 kuesioner pelaku UMKM Pekanbaru.
- **Pembersihan Teks & Numerik:** Parsing nominal omzet dan waktu (bulan/tahun) ke nilai numerik standar tahun referensi 2026.
- **Winsorizing Ekor Atas (P99):** Mengendalikan nilai ekstrem pada omzet dan transaksi tanpa membuang sampel.
- **Konfirmasi Ulang ke Responden:** Mengoreksi galat ketik nominal omzet sesudah pada R065, R130, R106 serta jumlah pesanan transaksi R002, R006, R015, dan R021.
- **Anonimisasi:** Seluruh nama usaha diganti dengan kode unik R001–R149.

### 2.2 Konstruksi Variabel & Definisi Target Kinerja (Tahap 2)
- **Skor Strategi (X1–X4):** Dihitung dari rata-rata butir Likert skala 1–5. Reliabilitas instrumen sangat tinggi (Cronbach's $\alpha = 0,930 - 0,955$).
- **Target Kinerja Objektif:**
  - `naik_penjualan` (Biner): Bernilai 1 jika omzet sesudah > omzet sebelum ATAU transaksi sesudah > transaksi sebelum; bernilai 0 jika tidak ada kenaikan.
  - `Y_obj` (Kontinu): Rata-rata z-score selisih log omzet dan selisih log transaksi.
- **Pembagian Sampel:**
  - **Sampel Utama ($n=116$):** UMKM dengan `lama_usaha_pra_mp > 0` yang memiliki data pembanding kondisi sebelum marketplace yang nyata (62 naik vs 54 sama).
  - **Sampel Tanpa Baseline ($n=33$):** Usaha yang berdiri bersamaan dengan marketplace (`lama_usaha_pra_mp = 0`), dianalisis terpisah sebagai pembanding.

---

## 3. Hasil Analisis dan Pengujian Statistik

### 3.1 Evaluasi Kinerja Penjualan (Pertanyaan 1)
Uji Wilcoxon Signed-Rank menunjukkan perbedaan yang bermakna secara statistik antara kondisi sebelum dan sesudah masuk marketplace:
- **Omzet Bulanan:** Median kenaikan bersih Rp250.000 ($Z = 6,34, p < 0,001$). 59 UMKM naik, 56 tetap, 1 turun.
- **Transaksi Bulanan:** Median kenaikan bersih 7 pesanan ($Z = 6,75, p < 0,001$). 60 UMKM naik, 56 tetap, 0 turun.

### 3.2 Analisis Pengaruh dan Pemodelan Machine Learning (Pertanyaan 2)
Pengujian dilakukan dengan mengontrol variabel profil usaha (lama usaha pra-marketplace, lama di marketplace, jumlah platform, dan log omzet sebelum).

#### Perbandingan Model Prediksi (Repeated Stratified K-Fold 5×5):
- **Random Forest:** ROC-AUC = 0.735 ± 0,092 | F1-Macro = 0.699 | Akurasi Seimbang = 0.706 (Model Terbaik).
- **Regresi Logistik:** ROC-AUC = 0.717 ± 0,115 | F1-Macro = 0.618.
- **Baseline Mayoritas:** ROC-AUC = 0,500.

#### Skor Kepentingan Fitur & Hubungan Strategi:
1. **X3 (Komunikasi Pelanggan):**
   - Odds Ratio Logit = 2,49 (95% CI: 1,42–4,38; $p = 0,001$; Holm $p = 0,005$).
   - Permutation Importance (RF) = 0.115.
   - Mean |SHAP| = 0.091.
   - Probabilitas Peringkat #1 pada Bootstrap (1000×) = 84,9%. Status: **Meyakinkan**.
2. **X1 (Unggah Produk):**
   - Odds Ratio Logit = 2,19 (95% CI: 1,26–3,81; $p = 0,005$; Holm $p = 0,015$).
   - Permutation Importance (RF) = 0.033.
   - Mean |SHAP| = 0.057.
   - Probabilitas Masuk 3 Besar = 99,5%. Status: **Meyakinkan**.
3. **X2 (Promosi Marketplace):**
   - Odds Ratio Logit = 1,26 ($p = 0,344$). Status: **Belum Meyakinkan**.
4. **X4 (Konsistensi Kelola Toko):**
   - Odds Ratio Logit = 0,93 ($p = 0,777$). Status: **Belum Meyakinkan**.

### 3.3 Analisis Pembanding: PLS-SEM
Sebagai pemeriksaan kekokohan, hubungan strategi dengan kinerja juga diestimasi dengan PLS-SEM. Konstruk X1–X4 dimodelkan reflektif dari butir kuesioner (Mode A, skema bobot jalur), profil usaha masuk sebagai kontrol, dan inferensi memakai bootstrap 2000×.

- **Model pengukuran:** Cronbach's $\alpha$ = 0,93–0,96, composite reliability = 0,95–0,97, AVE = 0,77–0,89, HTMT tertinggi = 0,54 (batas atas bootstrap 0,65). Reliabilitas, validitas konvergen, dan validitas diskriminan terpenuhi.
- **Model struktural** (koefisien jalur terstandar; * = interval bootstrap 95% tidak mencakup nol):

| Strategi | Melaporkan kenaikan (n=116) | Besar kenaikan y_obj (n=116) | Persepsi kinerja (n=149) | f² (kenaikan) |
|---|---|---|---|---|
| X1 Unggah Produk | 0,27* | 0,15 | 0,30* | 0,08 |
| X2 Promosi | 0,10 | 0,07 | -0,02 | 0,01 |
| X3 Komunikasi Pelanggan | 0,34* | 0,17 | 0,16* | 0,12 |
| X4 Konsistensi Toko | -0,02 | 0,03 | 0,33* | 0,00 |

- **Daya jelas dan prediksi:** R² = 0,26 (melaporkan kenaikan), 0,18 (y_obj), 0,37 (persepsi). AUC validasi silang model kenaikan = 0,72 (regresi logistik 0,72, Random Forest 0,73); Q²_predict untuk y_obj = 0,00, sejalan dengan temuan bahwa besar kenaikan sulit diperkirakan.
- **Perbandingan:** Urutan jalur PLS untuk melaporkan kenaikan (X3 > X1 > X2 > X4) sama dengan peringkat gabungan regresi logistik, Random Forest, dan SHAP. Pada persepsi kinerja urutannya berbeda (jalur terkuat X4 Konsistensi Toko): penilaian diri pelaku usaha tidak selalu sejalan dengan angka penjualan yang dilaporkan.

Rincian: `reports/sem_log.md`, `reports/tables/sem_*.csv`, `reports/figures/sem_jalur.png`.


### 3.4 Uji Efek Moderasi Profil Usaha (Pertanyaan 3)
Melalui pengujian 24 interaksi regresi (Strategi × Skala Omzet, Strategi × Lama di MP, Strategi × Jumlah Platform) dengan koreksi Holm:
- **Hasil:** 0 dari 24 interaksi bernilai signifikan ($p > 0,05$).
- **Kesimpulan:** Tidak ditemukan bukti bahwa hubungan strategi dengan kinerja penjualan berbeda menurut profil usaha. Daya uji interaksi pada sampel ini rendah, sehingga bobot strategi ditetapkan sama untuk semua segmen.

---

## 4. Segmentasi UMKM dan Rekomendasi Tindakan

### 4.1 Segmentasi Profil Usaha (Tahap 5)
Menggunakan algoritma *K-Means* ($k=2$) yang diuji stabilitasnya dengan bootstrap (100×):
- **Stabilitas:** Median ARI bootstrap = 0,92; Jaccard = 0,95/0,95.
- **Segmen 1 (74 UMKM):** Usaha rintisan/muda, skala omzet kecil (median omzet Rp9 jt), baru masuk marketplace (median 2 th).
- **Segmen 2 (75 UMKM):** Usaha mapan, omzet menengah/besar (median omzet Rp30 jt), lama di marketplace (median 4 th).

### 4.2 Rekomendasi Strategi Praktis (Tahap 6)
Prioritas tiap strategi dihitung dengan rumus:
$$\text{Prioritas} = \text{Bobot Pengaruh} \times \max(0, \bar{X}_{\text{naik}} - \bar{X}_{\text{segmen}})$$

| Segmen | Peringkat | Strategi Prioritas | Gap Skor | Bobot | Skor Prioritas | Rekomendasi Tindakan Operasional |
|---|---|---|---|---|---|---|
| **Segmen 1** (Usaha Kecil & Baru) | #1 | **X3 Komunikasi Pelanggan** | 0,14 | 1,00 | 0,143 | Siapkan template jawaban cepat untuk pertanyaan umum; tetapkan jam rutin cek pesan chat; jaga komunikasi hingga pesanan diterima. |
| | #2 | **X1 Unggah Produk** | 0,17 | 0,59 | 0,103 | Segarkan dan unggah ulang (*re-upload*) katalog produk lama secara bertahap 1–2 kali seminggu dimulai dari produk terlaris. |
| | #3 | **X2 Promosi Marketplace** | 0,13 | 0,29 | 0,037 | Manfaatkan voucher diskon bernilai kecil dan fitur promosi gratis bawaan platform; catat kenaikan pesanan mingguan. |
| **Segmen 2** (Usaha Mapan & Lama) | #1 | **X3 Komunikasi Pelanggan** | 0,19 | 1,00 | 0,191 | Terapkan SLA respon komplain pelanggan < 15 menit; delegasikan admin khusus customer support; evaluasi keluhan berulang mingguan. |
| | #2 | **X1 Unggah Produk** | 0,13 | 0,59 | 0,075 | Tunjuk penanggung jawab pembaruan katalog; jadwalkan peluncuran varian baru berkala di seluruh platform yang aktif. |
| | #3 | **X2 Promosi Marketplace** | 0,15 | 0,29 | 0,045 | Optimalkan iklan berbayar (ads) dengan alokasi anggaran terukur pada produk margin tinggi; evaluasi ROAS bulanan. |

---

## 5. Keterbatasan Metodologis

1. **Sifat Asosiasi, Bukan Kausalitas:** Desain studi adalah survei potong lintang (*cross-sectional*) berbasis ingatan responden (*self-reported recall*), tanpa kelompok kontrol murni yang tidak pernah memakai marketplace.
2. **Karakteristik Target Biner:** Kelompok pembanding `naik_penjualan = 0` terdiri atas responden yang mengisi nilai omzet dan transaksi sama persis sebelum dan sesudah (bukan kelompok penjualan turun).
3. **Ukuran Sampel ($n=149$, Sampel Utama $n=116$):** Rasio peristiwa terhadap prediktor (EPV) sekitar 6,8 sehingga interval kepercayaan koefisien cukup lebar.
4. **Dominasi Sektor Kuliner:** Mayoritas responden merupakan usaha makanan dan minuman di Kota Pekanbaru, sehingga generalisasi ke sektor kerajinan/fesyen atau wilayah lain memerlukan kehati-hatian.
5. **Keterbatasan Variasi Skala Likert:** Terjadi penumpukan jawaban netral (skor 3) pada beberapa butir kuesioner.

---

## 6. Kesiapan Integrasi Sistem

Model dan logika rekomendasi telah dibundel dalam arsitektur mandiri:
- **Artefak Model:** Tersimpan di folder `models/v1/` (`model.joblib`, `segmen.joblib`, `model_meta.json`, `benchmark_per_segmen.json`, `pengaruh_strategi.json`).
- **Kontrak Data:** Didefinisikan menggunakan skema Pydantic (`ProfilUMKM`, `HasilRekomendasi`) di `reports/integration_contract.md`.
- **Fungsi Inferensi:** Dapat dipanggil langsung dari Python tanpa bergantung pada notebook:
  ```python
  from umkm.recommend import recommend
  hasil = recommend({
      "omzet_bulanan": 15000000,
      "lama_usaha_pra_mp": 2.5,
      "lama_di_mp": 1.0,
      "platform": ["shopee", "gofood"],
      "x1_unggah": 3.0,
      "x2_promosi": 2.5,
      "x3_komunikasi": 3.5,
      "x4_konsistensi": 3.0,
  })
  print(hasil["segmen"], hasil["rekomendasi_prioritas"])
  ```

---
*Angka pada laporan ini dihitung dari tabel di `reports/tables/` (pembaruan terakhir 02-11-2026).*
