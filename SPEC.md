# Spesifikasi Proyek + Bootstrap `.claude/`: Analisis Strategi Penjualan UMKM di Marketplace

> File ini punya dua fungsi:
> 1. **Spesifikasi proyek** yang dibaca manusia (tujuan, keputusan, rencana).
> 2. **Instruksi bootstrap untuk AI agent** (Claude Code atau sejenisnya): saat file ini dibaca, agent membuat folder `.claude/` berisi rencana kerja dan panduan teknis, lalu **berhenti**.

---

## 0. Cara Memakai (untuk Manusia)

1. Buat folder proyek kosong, lalu letakkan:
   - file ini di root, misalnya sebagai `SPEC.md`
   - data di `data/raw/Kuesioner_Penelitian__Responses_.xlsx`
2. Buka Claude Code di folder tersebut dan ketik:
   > Baca `SPEC.md`, lalu jalankan **Bagian A (Bootstrap)** saja. Jangan mulai analisis.
3. Setelah `.claude/` terbentuk, periksa isinya. Pengerjaan analisis dimulai dengan perintah `/next-stage`.
4. **Lingkup saat ini: analisis dan laporan saja** (tanpa aplikasi). Kode tetap ditulis siap-integrasi agar
   mudah dihubungkan ke sistem nanti (lihat `guides/backend_architecture.md`).
5. **Lingkungan kerja: LOKAL.** Claude Code, kode, dan notebook berjalan di komputer Anda dalam satu folder proyek
   (lihat `guides/local_setup.md`). Google Colab hanya opsional/cadangan (`guides/colab_setup.md`).

---

# BAGIAN A: INSTRUKSI UNTUK AI AGENT (Bootstrap)

## A.1 Peran dan batasan

Anda adalah agent yang menyiapkan lingkungan kerja proyek analisis data. Pada tahap ini:

- **Lakukan:** membuat folder dan file dokumentasi sesuai Bagian B, membuat kerangka folder proyek, `requirements.txt`, `.gitignore`.
- **Jangan lakukan:** membaca atau mengubah isi data, menulis kode analisis, menjalankan model, atau memulai Tahap 1. Semua itu baru dikerjakan setelah pengguna menjalankan `/next-stage`.
- **Jangan menulis ulang isi** file di Bagian B dengan parafrase. Salin sesuai spesifikasi; boleh merapikan format saja.
- Jika ada file yang sudah ada, **jangan timpa**. Tanyakan dulu kepada pengguna.
- Bahasa dokumen: **Bahasa Indonesia**. Nama variabel/fungsi dalam kode: `snake_case` mengikuti kamus data.

## A.2 Langkah bootstrap

1. Buat struktur folder (A.3).
2. Buat setiap file `.claude/*` dengan isi persis seperti yang dispesifikasikan di Bagian B.
3. Buat `CLAUDE.md` di root proyek (B.1).
4. Buat kerangka proyek: folder kosong dengan `.gitkeep`, `requirements.txt`, `pyproject.toml`, `.gitignore`, `config.yaml` (B.10).
5. Jalankan checklist verifikasi (A.4).
6. Laporkan ke pengguna: daftar file yang dibuat, lalu **tunggu instruksi**.

## A.3 Struktur target

```
.
├── CLAUDE.md
├── SPEC.md                          # file ini
├── config.yaml
├── requirements.txt
├── pyproject.toml                   # paket `umkm` bisa di-pip install (Colab/sistem lain)
├── .gitignore
├── .claude/
│   ├── README.md                    # indeks panduan
│   ├── decisions.md                 # keputusan yang sudah/ belum disepakati
│   ├── progress.md                  # status tiap tahap
│   ├── settings.json                # izin dan larangan akses
│   ├── plan/
│   │   ├── 00_overview.md
│   │   ├── 01_cleaning.md
│   │   ├── 02_konstruksi_variabel.md
│   │   ├── 03_eda.md
│   │   ├── 04_analisis_pengaruh.md
│   │   ├── 05_segmentasi.md
│   │   ├── 06_rekomendasi.md
│   │   └── 07_pelaporan.md
│   ├── guides/
│   │   ├── data_dictionary.md
│   │   ├── coding_standards.md
│   │   ├── backend_architecture.md   # pipeline + kesiapan integrasi
│   │   ├── local_setup.md
│   │   ├── colab_setup.md            # opsional
│   │   ├── statistical_guidelines.md
│   │   ├── ml_guidelines.md
│   │   └── recommendation_logic.md
│   ├── commands/
│   │   ├── next-stage.md
│   │   ├── run-stage.md
│   │   ├── log-decision.md
│   │   └── check-quality.md
│   └── agents/
│       └── stats-reviewer.md
├── data/
│   ├── raw/                         # data asli (read-only)
│   └── processed/
├── src/umkm/                        # paket Python (kerangka kosong)
├── notebooks/
├── tests/
├── reports/
│   ├── figures/
│   └── tables/
├── models/
└── app/                             # DITUNDA: jangan dibuat sekarang
```

## A.4 Checklist verifikasi bootstrap

- [ ] Semua file pada A.3 ada dan tidak kosong (kecuali `.gitkeep`).
- [ ] `CLAUDE.md` merujuk ke `.claude/README.md`.
- [ ] `.claude/settings.json` adalah JSON valid.
- [ ] `data/raw/` tidak diubah isinya.
- [ ] Tidak ada kode analisis yang ditulis atau dijalankan.

---

# BAGIAN B: ISI FILE YANG HARUS DIBUAT

Setiap sub-bagian berisi **path file** dan **isi lengkapnya** di dalam blok kode.

## B.1 `CLAUDE.md` (root)

````markdown
# Proyek: Analisis Strategi Penjualan UMKM di Marketplace

Baca `.claude/README.md` sebelum mengerjakan apa pun.

## Tujuan singkat
Mengidentifikasi strategi marketplace (unggah produk, promosi, komunikasi pelanggan,
konsistensi kelola toko) yang paling berhubungan dengan kinerja penjualan 149 UMKM,
lalu menyusun rekomendasi strategi per segmen UMKM.

## Aturan wajib
1. Jangan pernah mengubah file di `data/raw/`.
2. Kerjakan SATU tahap per sesi; ikuti `.claude/plan/` sesuai urutan.
3. Setiap keputusan analitis dicatat di `.claude/decisions.md`.
4. Setelah selesai tahap, perbarui `.claude/progress.md`.
5. Random seed selalu 42.
6. Hasil bersifat asosiasi, bukan kausalitas. Jangan pakai bahasa sebab-akibat.
7. Jika ada keputusan berstatus "BELUM DISEPAKATI", tanyakan ke pengguna sebelum lanjut.
8. Tampilkan hasil tiap tahap ke pengguna sebelum lanjut ke tahap berikutnya.
9. Lingkup saat ini adalah analisis dan laporan. JANGAN membangun API/aplikasi kecuali pengguna meminta.
10. Logika ada di `src/umkm/`; notebook hanya memanggil fungsi. Lingkungan utama: LOKAL (venv + Jupyter/VS Code,
    lihat `.claude/guides/local_setup.md`). Kode tetap harus portabel ke Google Colab
    (tanpa path absolut; gunakan config dan env `UMKM_BASE_DIR`).
11. Rancang untuk integrasi ke sistem nanti: ikuti bagian "Kesiapan Integrasi" di
    `.claude/guides/backend_architecture.md`.

## Perintah
- `/next-stage`  : kerjakan tahap berikutnya yang belum selesai
- `/run-stage N` : jalankan ulang tahap N
- `/log-decision`: catat keputusan baru
- `/check-quality`: audit cepat kualitas data/hasil
````

## B.2 `.claude/README.md`

````markdown
# Indeks Panduan

| Kebutuhan | Buka |
|---|---|
| Ringkasan proyek dan tahapan | `plan/00_overview.md` |
| Kerjakan tahap tertentu | `plan/01_...` s.d. `plan/07_...` |
| Arti tiap kolom data | `guides/data_dictionary.md` |
| Gaya kode dan struktur modul | `guides/coding_standards.md`, `guides/backend_architecture.md` |
| Kesiapan integrasi ke sistem lain | `guides/backend_architecture.md` (bagian Kesiapan Integrasi) |
| Setup lingkungan lokal (utama) | `guides/local_setup.md` |
| Menjalankan di Google Colab (opsional) | `guides/colab_setup.md` |
| Aturan statistik | `guides/statistical_guidelines.md` |
| Aturan machine learning | `guides/ml_guidelines.md` |
| Logika rekomendasi | `guides/recommendation_logic.md` |
| Keputusan yang sudah dibuat | `decisions.md` |
| Status pengerjaan | `progress.md` |

## Alur kerja agent
1. Baca `progress.md` untuk tahu tahap berikutnya.
2. Baca file `plan/` tahap tersebut dan panduan yang dirujuknya.
3. Kerjakan, simpan keluaran ke lokasi yang ditentukan.
4. Ringkas hasil ke pengguna dan tunggu persetujuan.
5. Perbarui `progress.md` dan `decisions.md`.
````

## B.3 `.claude/decisions.md`

````markdown
# Log Keputusan

Status: DISEPAKATI / DIUSULKAN (default sementara, konfirmasi dulu) / BELUM DISEPAKATI

| ID | Topik | Keputusan | Status | Tanggal |
|---|---|---|---|---|
| D01 | Tujuan penelitian | Opsi (a): mengidentifikasi strategi yang berpengaruh terhadap kinerja penjualan; rekomendasi diturunkan dari temuan | DISEPAKATI | 2026-10-13 |
| D02 | Definisi kinerja (target) | Kinerja diukur HANYA dari 5 isian objektif: omzet sebelum/sesudah, transaksi sebelum/sesudah, dan pelanggan baru per bulan. 8 item Likert Y (Y1-Y8) BUKAN target; hanya variabel pendukung/validasi | DISEPAKATI | 2026-10-14 |
| D03 | Outlier omzet dan transaksi | Winsorizing pada persentil 1 dan 99 (tidak dibuang). Wajib ada analisis sensitivitas tanpa baris yang terkena winsorizing | DISEPAKATI | 2026-10-13 |
| D04 | Omzet sebelum = 0 | Pakai selisih log1p (log(1+sesudah) - log(1+sebelum)) agar tetap terdefinisi | DIUSULKAN | 2026-10-13 |
| D05 | Responden dengan omzet dan transaksi tidak berubah (sekitar 80 dari 149) | Tetap disertakan di analisis utama; sensitivitas tanpa kelompok `tanpa_baseline` (lihat D14) | DIUSULKAN | 2026-10-14 |
| D06 | Kolom "pelanggan baru per bulan" (ambigu: sebelum atau setelah) | Target TAMBAHAN terpisah (bukan bagian Y_obj): `y_pelanggan_baru = log1p(pelanggan_baru)`; tidak dipakai sebagai fitur | DIUSULKAN | 2026-10-14 |
| D07 | Metode inti | Regresi (OLS robust + ordinal logit) + Random Forest/SHAP sebagai penguat | DISEPAKATI | 2026-10-13 |
| D08 | SEM / PLS-SEM | Opsional; hanya jika pengguna meminta | BELUM DISEPAKATI | |
| D09 | Aplikasi (Streamlit/FastAPI) | DITUNDA. Lingkup sekarang hanya analisis dan laporan | DISEPAKATI | 2026-10-13 |
| D10 | Penanganan lama usaha berupa tahun kalender (mis. 2018, 2023) | Tandai di kolom flag; konversi dengan tahun referensi 2026; minta konfirmasi pengguna untuk kasus ambigu | DIUSULKAN | 2026-10-13 |
| D11 | Kesiapan integrasi | Kode dirancang siap-integrasi: logika di paket `umkm`, kontrak data (Pydantic), satu fungsi `recommend(profil) -> dict`, artefak model berversi, tanpa path absolut | DISEPAKATI | 2026-10-13 |
| D12 | Lingkungan kerja | LOKAL sebagai utama (venv Python 3.10-3.12, Jupyter/VS Code, Claude Code dijalankan dari root folder proyek). Google Colab hanya opsional/cadangan | DISEPAKATI | 2026-10-13 |
| D13 | Bentuk target | (a) `naik_penjualan` biner (1 jika omzet ATAU transaksi naik) = target utama klasifikasi; (b) `Y_obj` = rata-rata z(d_omzet) dan z(d_trx) = target utama regresi; (c) `y_pelanggan_baru` = target tambahan. Alasan: sekitar 80 responden tidak berubah, "turun" hanya sekitar 3, sehingga tertil penuh nilai kembar | DIUSULKAN | 2026-10-14 |
| D14 | Responden tanpa baseline | Responden dengan lama_usaha_pra_mp = 0 (usaha berdiri bersama marketplace, "sebelum" tidak bermakna): beri flag `tanpa_baseline`; analisis dijalankan dengan dan tanpa mereka; pengguna memutuskan mana yang jadi analisis utama | BELUM DISEPAKATI | 2026-10-14 |
````

## B.4 `.claude/progress.md`

````markdown
# Progres

| Tahap | Nama | Status | Keluaran utama | Selesai pada |
|---|---|---|---|---|
| 1 | Cleaning | BELUM | data/processed/data_clean.csv, reports/cleaning_log.md | |
| 2 | Konstruksi variabel | BELUM | data/processed/data_features.csv | |
| 3 | EDA | BELUM | reports/figures/eda_*, reports/tables/eda_*.csv | |
| 4 | Analisis pengaruh | BELUM | reports/tables/pengaruh_*.csv | |
| 5 | Segmentasi | BELUM | data/processed/data_segmen.csv | |
| 6 | Rekomendasi | BELUM | reports/tables/rekomendasi_per_segmen.csv, models/v1/, reports/integration_contract.md | |
| 7 | Pelaporan | BELUM | reports/laporan_final.md | |

Status: BELUM / BERJALAN / MENUNGGU PERSETUJUAN / SELESAI

## Catatan sesi
(Agent menambahkan ringkasan singkat tiap selesai tahap: apa dikerjakan, temuan penting, masalah terbuka.)
````

## B.5 `.claude/settings.json`

````json
{
  "permissions": {
    "allow": [
      "Bash(python:*)",
      "Bash(pip install:*)",
      "Bash(pytest:*)",
      "Bash(jupyter nbconvert:*)",
      "Bash(make:*)",
      "Bash(git status)",
      "Bash(git diff:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Edit(./data/raw/**)",
      "Write(./data/raw/**)"
    ]
  }
}
````

## B.6 Rencana kerja: `.claude/plan/*.md`

### `.claude/plan/00_overview.md`

````markdown
# Gambaran Umum

## Tujuan
Mengetahui strategi marketplace mana yang paling berhubungan dengan kinerja penjualan UMKM,
lalu menyusun rekomendasi strategi per segmen UMKM.

## Pertanyaan penelitian
1. Apakah omzet, transaksi, dan pelanggan baru meningkat setelah memakai marketplace?
2. Dari X1-X4, strategi mana yang paling kuat hubungannya dengan kinerja?
3. Apakah pengaruhnya berbeda menurut kondisi UMKM (skala, lama usaha, jumlah platform)?
4. Strategi apa yang diprioritaskan untuk tiap segmen?

## Kerangka
Strategi (X1-X4) + profil UMKM  ->  kinerja objektif (omzet, transaksi, pelanggan baru)  ->  pengaruh tiap strategi
->  segmentasi UMKM  ->  rekomendasi prioritas per segmen.

## Variabel
- X1_unggah (4 item), X2_promosi (4), X3_komunikasi (5), X4_konsistensi (5): skor rata-rata Likert 1-5.
- Target kinerja (HANYA 5 isian objektif): `naik_penjualan` (biner), `Y_obj` (kontinu), `y_pelanggan_baru` (tambahan). Lihat Tahap 2 dan decisions.md (D02, D13).
- Y_persepsi (8 item Likert): BUKAN target; hanya variabel pendukung/validasi.
- Profil: lama_usaha_pra_mp, lama_di_mp, jumlah_platform, platform biner, skala_omzet.

## Urutan tahap
1 Cleaning -> 2 Konstruksi variabel -> 3 EDA -> 4 Analisis pengaruh
-> 5 Segmentasi -> 6 Rekomendasi -> 7 Pelaporan.
Tampilkan hasil ke pengguna dan minta persetujuan di akhir tiap tahap.

## Prinsip
- Interpretabilitas di atas akurasi. Model sederhana dulu.
- Sampel kecil (n=149): CV berulang, laporkan ketidakpastian.
- Hanya klaim asosiasi.
- Semua keputusan dicatat.
````

### `.claude/plan/01_cleaning.md`

````markdown
# Tahap 1: Cleaning

Rujukan: guides/data_dictionary.md, guides/backend_architecture.md
Modul: src/umkm/cleaning.py
Masukan: data/raw/Kuesioner_Penelitian__Responses_.xlsx
Keluaran: data/processed/data_clean.csv, reports/cleaning_log.md

## Langkah
1. Muat data; rename kolom sesuai kamus data (kolom 0-36 -> nama pendek).
2. Buang kolom `score` (konstan 0). Pertahankan `nama_usaha` hanya sebagai ID; jangan dipakai sebagai fitur.
3. Likert: ambil angka di depan label dengan regex `^\s*(\d)`. Tangani variasi "1.Tidak" dan "1. Tidak".
4. AUDIT label vs angka: periksa apakah teks label sesuai angkanya. Contoh yang sudah terlihat:
   baris dengan "2. Sangat Tidak Konsisten" (angka 2 tetapi label "sangat tidak"). Catat semua
   ketidaksesuaian di cleaning_log.md. Default: pakai angka. Tanyakan pengguna jika jumlahnya besar.
5. Omzet: hapus titik pemisah ribuan dan non-digit, ubah ke numerik. Periksa nilai 0 dan nilai tak terbaca.
6. Lama usaha (`lama_usaha_pra_mp`, `lama_di_mp`):
   - "N bulan" -> N/12 tahun
   - nilai >= 1900 (tahun kalender, mis. 2018/2023) -> 2026 - nilai, beri `flag_lama_tahun_kalender = 1`
   - sisanya numerik tahun
   Daftar baris ber-flag dilaporkan ke pengguna untuk dikonfirmasi.
7. Platform: pecah teks multi-pilihan (pisah koma) jadi kolom biner `mp_gofood`, `mp_grabfood`,
   `mp_shopee`, `mp_maxim`, `mp_tiktok`; hitung `jumlah_platform`.
8. Transaksi: cek nilai tidak wajar (mis. jutaan transaksi/bulan untuk UMKM) dan nilai pecahan (mis. 2.65).
9. Outlier: winsorizing persentil 1 dan 99 pada omzet dan transaksi (decisions D03).
   Simpan kolom asli (`*_raw`) dan kolom terwinsor (`*_w`); tambah `flag_outlier`.
10. Duplikat: cek duplikat pada nama_usaha dan pola jawaban identik; laporkan, jangan buang otomatis.
11. Simpan data_clean.csv dan tulis cleaning_log.md: jumlah baris/kolom, jumlah nilai diubah per aturan,
    daftar flag, keputusan yang butuh konfirmasi.

## Kriteria selesai
- 149 baris tetap utuh (kecuali pengguna menyetujui pembuangan).
- Tidak ada missing tak terjelaskan; semua Likert bernilai 1-5; omzet/transaksi numerik.
- cleaning_log.md ada dan lengkap; tes unit untuk fungsi parsing lulus.
````

### `.claude/plan/02_konstruksi_variabel.md`

````markdown
# Tahap 2: Konstruksi Variabel

Rujukan: guides/statistical_guidelines.md, decisions.md (D02, D06, D13, D14)
Modul: src/umkm/features.py
Masukan: data/processed/data_clean.csv
Keluaran: data/processed/data_features.csv, reports/tables/reliabilitas.csv

## Langkah
1. Validitas dan reliabilitas konstruk X1-X4 (dan Y_persepsi sebagai variabel pendukung):
   Cronbach's alpha (target >= 0.70), korelasi item-total (target >= 0.30), alpha-if-item-deleted.
   Jika rendah: laporkan, jangan otomatis membuang item; tanyakan pengguna.
2. Skor konstruk = rata-rata item: X1_unggah, X2_promosi, X3_komunikasi, X4_konsistensi.
   Hitung juga Y_persepsi (hanya pendukung, BUKAN target).
3. Komponen kinerja objektif (nilai terwinsor):
   - d_omzet = log1p(omzet_sesudah_w) - log1p(omzet_sebelum_w)
   - d_trx   = log1p(trx_sesudah_w) - log1p(trx_sebelum_w)
   Simpan juga pertumbuhan persen untuk pelaporan (kosongkan jika sebelum = 0).
4. Target:
   - `naik_penjualan` (biner, target utama klasifikasi): 1 jika d_omzet > 0 ATAU d_trx > 0, selain itu 0.
     Data awal menunjukkan sekitar 66 naik vs 83 tidak naik (cukup seimbang); kategori "turun" hanya sekitar 3
     responden sehingga digabung ke "tidak naik".
   - `Y_obj` (kontinu, target utama regresi): rata-rata z(d_omzet) dan z(d_trx).
     Catatan: distribusinya menumpuk di nol (sekitar 80 responden tidak berubah di keduanya), jadi pakai galat baku
     robust dan jadikan regresi logistik pada `naik_penjualan` sebagai pembanding utama.
   - `y_pelanggan_baru` = log1p(pelanggan_baru): target tambahan terpisah (waktu pengukuran ambigu, D06).
5. Penanda baseline: `tanpa_baseline` = 1 jika lama_usaha_pra_mp = 0 (D14). Laporkan jumlahnya total dan per
   nilai `naik_penjualan`.
6. Fitur profil: lama_usaha_pra_mp, lama_di_mp, jumlah_platform, mp_* biner,
   skala_omzet (kategori berdasarkan kuartil omzet_sebelum_w), plus flag dari Tahap 1.
   `pelanggan_baru` BUKAN fitur (ia target tambahan).
7. Simpan data_features.csv dan tabel reliabilitas.

## Kriteria selesai
- Reliabilitas tiap konstruk X terdokumentasi.
- Sebaran naik/sama/turun untuk omzet dan transaksi, serta ukuran kelas `naik_penjualan`, dilaporkan.
- Jumlah `tanpa_baseline` dilaporkan dan ditanyakan ke pengguna (D14).
- Tidak ada kebocoran (leakage): fitur X dan profil tidak dihitung dari target.
````

### `.claude/plan/03_eda.md`

````markdown
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
````

### `.claude/plan/04_analisis_pengaruh.md`

````markdown
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
   (c) tanpa responden `tanpa_baseline`, (d) target alternatif: hanya d_omzet, hanya d_trx, dan y_pelanggan_baru. Laporkan apakah peringkat berubah.

## Kriteria selesai
- Peringkat pengaruh X1-X4 dengan interval ketidakpastian (bootstrap 1000x).
- Metrik CV dibandingkan dengan baseline; jika model tidak mengalahkan baseline, katakan terus terang.
- Kalimat temuan memakai bahasa asosiasi.
````

### `.claude/plan/05_segmentasi.md`

````markdown
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
````

### `.claude/plan/06_rekomendasi.md`

````markdown
# Tahap 6: Rekomendasi Strategi

Rujukan: guides/recommendation_logic.md
Modul: src/umkm/recommend.py
Keluaran: reports/tables/rekomendasi_per_segmen.csv, reports/rekomendasi_ringkas.md

## Langkah
1. Hitung benchmark per segmen: median skor X1-X4 pada UMKM dengan naik_penjualan = 1 di segmen itu.
   Jika kelompok itu di suatu segmen < 5 orang, pakai benchmark seluruh responden dengan naik_penjualan = 1.
2. Hitung gap dan skor prioritas (rumus di recommendation_logic.md).
3. Peringkat strategi per segmen -> ambil 3 teratas.
4. (Opsional) Simulasi what-if: naikkan satu strategi +1 poin pada model terbaik; catat perubahan prediksi.
5. Susun tabel: segmen | strategi prioritas 1-3 | alasan (angka) | tindakan konkret.
6. Validasi kewajaran dengan pengguna/pembimbing sebelum finalisasi.
7. Simpan artefak inferensi ke `models/v1/`: scaler + K-Means segmen, model terbaik, `benchmark_per_segmen.json`,
   `pengaruh_strategi.json`, `model_meta.json` (lihat backend_architecture.md).
8. Implementasikan `recommend(profil: dict) -> dict` (keluaran JSON-serializable) dan uji dengan 3 contoh masukan.
9. Tulis `reports/integration_contract.md`: skema masukan/keluaran, rentang nilai, contoh JSON, versi artefak,
   cara memuat artefak, dan dependensi minimal.

## Kriteria selesai
Tiap segmen punya 3 rekomendasi dengan alasan berbasis angka dan tindakan yang dapat dikerjakan UMKM.
Bahasa tidak kausal.
`recommend()` dapat dipanggil dari skrip terpisah (tanpa notebook) dan hasilnya cocok dengan tabel di laporan.
````

### `.claude/plan/07_pelaporan.md`

````markdown
# Tahap 7: Pelaporan

Keluaran: reports/laporan_final.md, notebook final, README proyek

## Langkah
1. Susun laporan: latar belakang, data dan cleaning, metode, hasil per pertanyaan penelitian,
   segmentasi, rekomendasi, keterbatasan.
2. Pastikan semua angka di laporan dapat ditelusuri ke file di reports/tables.
3. Tulis bagian keterbatasan: sampel kecil, self-report, survei satu waktu, dominasi kuliner,
   variasi Y rendah, keputusan outlier.
4. Jalankan ulang pipeline dari awal (`make all`) untuk membuktikan reproduksibilitas.
5. Pastikan `reports/integration_contract.md` lengkap dan `recommend()` dapat dipanggil mandiri.
   Aplikasi/API TIDAK dibangun kecuali pengguna meminta.
````

## B.7 Panduan teknis: `.claude/guides/*.md`

### `.claude/guides/data_dictionary.md`

````markdown
# Kamus Data

Sumber: Kuesioner_Penelitian__Responses_.xlsx, sheet "Form Responses 1", 149 baris x 37 kolom.
Pemetaan berdasarkan urutan kolom (indeks mulai 0).

| Idx | Nama baru | Isi | Tipe |
|---|---|---|---|
| 0 | timestamp | Waktu pengisian | datetime |
| 1 | score | Konstan 0 -> DIBUANG | - |
| 2 | nama_usaha | ID usaha (bukan fitur) | teks |
| 3 | lama_usaha_pra_mp | Lama usaha berjalan sebelum memakai marketplace (tahun) | numerik (data kotor) |
| 4 | lama_di_mp | Lama usaha berjalan setelah memakai marketplace (tahun) | numerik (data kotor) |
| 5 | platform_raw | Marketplace yang dipakai (multi-pilihan, dipisah koma) | teks |
| 6-9 | x1_unggah_1..4 | Pengunggahan produk (rutin mingguan, produk baru, unggah ulang, pemantauan) | Likert 1-5 |
| 10-13 | x2_promosi_1..4 | Promosi (voucher/diskon, iklan berbayar, fitur promosi, evaluasi promosi) | Likert 1-5 |
| 14-18 | x3_komunikasi_1..5 | Komunikasi pelanggan (respon cepat, jelas dan sopan, balas hari yang sama, komplain, jaga komunikasi) | Likert 1-5 |
| 19-23 | x4_konsistensi_1..5 | Konsistensi toko (toko aktif, stok, foto/deskripsi, harga akurat, tetap kelola saat sibuk) | Likert 1-5 |
| 24-31 | y_persepsi_1..8 | [PENDUKUNG, bukan target] Persepsi kinerja (omzet naik, penjualan tumbuh, pesanan naik, transaksi sering, pelanggan baru, jangkauan luar daerah, usaha berkembang, kontribusi marketplace) | Likert 1-5 |
| 32 | omzet_sebelum_raw | [TARGET] Rata-rata omzet sebelum marketplace | teks -> numerik (Rp) |
| 33 | omzet_sesudah_raw | [TARGET] Rata-rata omzet sesudah marketplace | teks -> numerik (Rp) |
| 34 | trx_sebelum_raw | [TARGET] Jumlah transaksi sebelum marketplace | numerik |
| 35 | trx_sesudah_raw | [TARGET] Jumlah transaksi sesudah marketplace | numerik |
| 36 | pelanggan_baru | [TARGET tambahan] Pelanggan baru per bulan (ambigu: sebelum atau setelah) | numerik |

## Skala Likert
Label berbeda antar blok, tetapi semuanya 1-5 dengan angka di depan label:
- X1: 1 Tidak Pernah ... 5 Sangat Sering
- X2: 1 Tidak Pernah Memanfaatkan ... 5 Sangat Sering Memanfaatkan
- X3: 1 Sangat Tidak Sesuai ... 5 Sangat Sesuai
- X4: 1 Sangat Tidak Konsisten ... 5 Sangat Konsisten
- Y: 1 Sangat Tidak Setuju ... 5 Sangat Setuju

## Masalah data yang sudah diketahui
- Omzet teks dengan format campuran ("3.500.000" vs "60000000").
- Lama usaha campur: tahun biasa, tahun kalender (2018, 2023), dan bulan ("3 bulan").
- Omzet sebelum = sesudah pada sekitar 57% responden; naik sekitar 40%; turun sekitar 3%.
- Outlier ekstrem pada omzet (sampai Rp800 juta) dan transaksi (sampai puluhan juta).
- Omzet sebelum bernilai 0 pada sebagian responden.
- Format label tidak seragam ("1.Tidak" vs "1. Tidak"); ditemukan pula label yang tidak sesuai
  dengan angkanya pada blok X4 (contoh: angka 2 dengan label "Sangat Tidak Konsisten").
- Item omzet naik didominasi "Netral" (110 dari 149).
- Platform terbanyak: GoFood+GrabFood+Shopee (53), GoFood saja (25), Shopee saja (22).
- Catatan instrumen ("Item Pertanyaan Penelitian 2026") menyebut 5 item untuk X1 dan X2, tetapi Excel hanya memuat
  4 item masing-masing: X1.2 ("sering memperbarui katalog produk") dan X2.1 ("memanfaatkan fitur promo yang ada")
  tidak ada di Excel. Analisis memakai item yang ada di Excel; konfirmasi ke pengguna.
- Omzet dan transaksi bergerak searah: dari 149 responden, 80 tidak berubah di keduanya, 58 naik di keduanya,
  11 campuran. Sekitar 29 dari 80 responden yang tidak berubah punya lama_usaha_pra_mp = 0 (usaha berdiri bersama
  marketplace), sehingga "sebelum" kemungkinan tidak bermakna (D14).
- Pelanggan baru per bulan: rentang 0-1500, median 80, tanpa missing; waktu pengukuran ambigu (D06).
````

### `.claude/guides/coding_standards.md`

````markdown
# Standar Kode

- Python 3.10+, ketik tipe (type hints) pada fungsi publik, docstring singkat Bahasa Indonesia.
- Format: black + ruff. Panjang baris 100.
- Satu fungsi satu tugas; fungsi murni (tanpa efek samping) untuk transformasi data.
- Semua path dan parameter (seed, persentil winsorizing, k klaster, lipatan CV) ada di config.yaml,
  bukan hard-coded.
- Seed global 42 untuk NumPy, scikit-learn, XGBoost.
- Notebook hanya untuk eksplorasi dan menampilkan hasil; logika dipindah ke src/umkm/.
- Setiap fungsi parsing/cleaning punya tes di tests/ (pytest) dengan kasus tepi
  ("3.500.000", "60000000", "2018", "3 bulan", "1.Tidak Pernah").
- Jangan mencetak data pribadi (nama usaha) ke laporan publik; gunakan ID.
- Commit kecil dan sering; pesan commit: `tahap-N: ringkasan`.
- Setiap keluaran (tabel/gambar) disimpan ke reports/ dengan nama deskriptif dan dapat dibuat ulang oleh skrip.
````

### `.claude/guides/backend_architecture.md`

````markdown
# Arsitektur Pipeline dan Kesiapan Integrasi

## Paket Python: src/umkm/
| Modul | Tanggung jawab |
|---|---|
| config.py | Memuat config.yaml, path, parameter; base dir dari env `UMKM_BASE_DIR` atau folder proyek |
| schemas.py | Kontrak data (Pydantic): ProfilUMKM, SkorStrategi (1-5), HasilRekomendasi |
| io.py | Baca xlsx mentah, tulis csv/parquet, simpan artefak |
| cleaning.py | Rename kolom, parse Likert/omzet/lama usaha, pecah platform, winsorizing |
| features.py | Skor konstruk, alpha, d_omzet, d_trx, Y_obj, naik_penjualan, y_pelanggan_baru, tanpa_baseline, fitur profil |
| stats.py | Wilcoxon, Spearman, Kruskal, VIF, OLS robust, ordinal logit, bootstrap |
| models.py | Pipeline sklearn, CV, Random Forest/Logistic/XGBoost, permutation importance, SHAP |
| segmentation.py | K-Means, silhouette, stabilitas bootstrap, profil segmen |
| recommend.py | Benchmark, gap, skor prioritas, template rekomendasi; fungsi publik `recommend(profil) -> dict` |
| viz.py | Fungsi plot standar (heatmap, boxplot, bar SHAP) |
| pipeline.py | Menjalankan tahap 1-6 berurutan |

## Alur data
data/raw (xlsx) -> cleaning -> data_clean.csv -> features -> data_features.csv
-> models/stats -> reports/tables -> segmentation -> data_segmen.csv -> recommend -> rekomendasi.

## Eksekusi
- CLI: `python -m umkm.pipeline --stage N` (atau `--all`). Di Colab, awali dengan `!`.
- Makefile: `make clean-data`, `make features`, `make eda`, `make influence`, `make segment`, `make recommend`, `make all`, `make test`.
- Setiap tahap membaca keluaran tahap sebelumnya dari data/processed; tidak ada ketergantungan tersembunyi.
- Setiap tahap menulis log ringkas ke reports/logs/.

## Artefak model
- Simpan dengan joblib di models/, beserta `model_meta.json` (tanggal, seed, versi pustaka, fitur, metrik CV, hash data).
- Jangan menyimpan data mentah di dalam artefak.

## Kesiapan Integrasi (aplikasi/API TIDAK dibangun sekarang)

Tujuannya: nanti, sistem lain cukup memanggil kode yang sudah ada tanpa menulis ulang analisis.

1. **Logika di paket, notebook tipis.** Notebook hanya memanggil fungsi di `src/umkm/` dan menampilkan hasil.
2. **Kontrak data (`schemas.py`).** Model Pydantic mendefinisikan nama field, tipe, dan rentang masukan/keluaran.
   Kontrak yang sama dicatat di `reports/integration_contract.md`.
3. **Satu pintu masuk inferensi:** `recommend(profil: dict) -> dict`.
   - Tidak membaca xlsx mentah atau state notebook; hanya memuat artefak dari `models/v1/`.
   - Masukan dan keluaran JSON-serializable (dict/list/angka/teks).
4. **Artefak berversi** di `models/v1/`: `segmen.joblib` (scaler + K-Means), `model.joblib`,
   `benchmark_per_segmen.json`, `pengaruh_strategi.json`, `model_meta.json`
   (tanggal, seed, versi pustaka, daftar fitur, metrik CV, hash data). Perubahan model = folder `v2/`.
5. **Preprocessing yang sama untuk data baru.** Fungsi di cleaning/features menerima satu baris maupun banyak baris.
6. **Tanpa path absolut.** Semua path dari config + env `UMKM_BASE_DIR` agar sama di lokal, Colab, atau server.
7. **Dependensi inferensi minimal:** pandas, numpy, scikit-learn, joblib, pydantic, pyyaml.
   Paket analisis (statsmodels, shap, pingouin, dll.) hanya untuk tahap analisis (`pip install -e ".[analysis]"`).
8. **Bahasa keluaran:** teks rekomendasi disimpan sebagai template di `recommend.py`, bukan di notebook,
   agar mudah diubah/diterjemahkan oleh sistem tujuan.

### Contoh kontrak (sketsa)
Masukan:
{"skala_omzet": 18000000, "lama_usaha_pra_mp": 3, "lama_di_mp": 2, "platform": ["gofood", "shopee"],
 "x1_unggah": 2.0, "x2_promosi": 2.5, "x3_komunikasi": 4.2, "x4_konsistensi": 3.0}

Keluaran:
{"versi_model": "v1", "segmen": {"id": 2, "nama": "..."},
 "prioritas": [{"strategi": "x2_promosi", "skor": 2.5, "benchmark": 3.8, "prioritas": 0.31,
                "alasan": "...", "tindakan": "..."}],
 "catatan": "Berdasarkan pola asosiasi dari 149 UMKM, bukan jaminan hasil."}

### Jalur integrasi nanti (belum dikerjakan; hanya untuk gambaran)
- Sistem berbasis Python: `pip install` paket `umkm`, lalu panggil `recommend()` langsung.
- Sistem non-Python: bungkus `recommend()` dengan FastAPI (POST /recommend, GET /health) dan panggil via REST.
- Demo cepat: Streamlit memanggil `recommend()`.
Semua jalur ini memakai kontrak dan artefak yang sama.
````

### `.claude/guides/local_setup.md`

````markdown
# Setup Lingkungan Lokal (jalur utama)

## Prasyarat
- Python 3.10-3.12 (hindari versi yang terlalu baru: sebagian pustaka seperti shap/numba belum kompatibel).
- Git dan VS Code (disarankan) atau Jupyter.
- RAM 4 GB atau lebih; tidak butuh GPU.
- Jalankan Claude Code dari ROOT folder proyek agar CLAUDE.md dan .claude/ terbaca.

## Setup sekali di awal
```
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[analysis]"
pip install jupyter ipykernel pytest black ruff
python -m ipykernel install --user --name umkm
git init
```
Alternatif: `pip install -r requirements.txt` lalu `pip install -e .`

## Cara kerja sehari-hari
- Aktifkan venv di setiap terminal baru.
- Data mentah ada di `data/raw/` (tidak masuk Git). `base_dir` default adalah folder proyek,
  jadi `UMKM_BASE_DIR` tidak perlu diatur.
- Jalankan tahap: `python -m umkm.pipeline --stage N`. Jika `make` tidak tersedia (umumnya di Windows),
  pakai perintah python tersebut.
- Notebook: buka di VS Code atau Jupyter, pilih kernel `umkm`.
- Tes: `pytest`.
- Commit per tahap dengan pesan `tahap-N: ringkasan`.

## Pemecahan masalah
- Gagal memasang shap/pingouin/numba: pastikan Python 3.10-3.12 dan pip terbaru. Jika tetap gagal,
  jalankan tahap yang memerlukan pustaka itu di Google Colab (lihat colab_setup.md).
- Error path/file tidak ditemukan: jalankan perintah dari root folder proyek.
- PowerShell menolak mengaktifkan venv: jalankan `Set-ExecutionPolicy -Scope Process RemoteSigned` di sesi itu.
- Hasil berbeda antar mesin: pastikan seed 42 dan versi pustaka sama (`pip freeze`).
````

### `.claude/guides/colab_setup.md`

````markdown
# Menjalankan di Google Colab (OPSIONAL / cadangan)

Jalur utama proyek adalah lokal (lihat `local_setup.md`). Pakai Colab hanya jika instalasi lokal bermasalah
atau untuk berbagi notebook dengan orang lain.

## Prinsip
- Runtime Colab bersifat sementara: file di `/content` hilang saat sesi berakhir.
- Kode disimpan di **GitHub**; data dan keluaran disimpan di **Google Drive**.
- Data kuesioner memuat nama usaha: jangan unggah `data/raw/*.xlsx` ke repo publik (sudah ada di .gitignore).
- Tidak butuh GPU; runtime CPU standar cukup untuk 149 baris.

## Struktur di Drive
MyDrive/umkm_proyek/data/raw/Kuesioner_Penelitian__Responses_.xlsx
MyDrive/umkm_proyek/data/processed/, reports/, models/ (dibuat otomatis oleh pipeline)

## Sel pertama di setiap notebook (`notebooks/00_setup_colab.ipynb`, dibuat saat Tahap 1)
```python
from google.colab import drive
drive.mount('/content/drive')

import os
os.environ["UMKM_BASE_DIR"] = "/content/drive/MyDrive/umkm_proyek"

!git clone https://github.com/<user>/<repo>.git /content/proyek 2>/dev/null || git -C /content/proyek pull
%cd /content/proyek
!pip install -q -e ".[analysis]"
```
Jalankan tahap lewat `!python -m umkm.pipeline --stage 1`, atau impor fungsinya langsung di notebook.

## Kebiasaan yang perlu dijaga
- Jalankan ulang sel setup setiap sesi baru. Jika Colab meminta restart setelah pip, restart lalu jalankan dari sel setup.
- Semua path lewat config/`UMKM_BASE_DIR`, bukan `/content/...` yang di-hardcode di modul.
- Simpan semua keluaran ke Drive, commit kode ke GitHub secara berkala.
- Di akhir proyek, jalankan `pip freeze` dan catat versi di `requirements.txt` agar hasil dapat direproduksi.
- Claude Code berjalan di terminal/VS Code lokal, bukan di dalam Colab. Alur yang disarankan: edit kode di lokal
  bersama agent, push ke GitHub, lalu jalankan di Colab. Jika tidak memakai agent, rencana di `plan/` tetap bisa diikuti manual.
````

### `.claude/guides/statistical_guidelines.md`

````markdown
# Pedoman Statistik

- Data Likert bersifat ordinal: utamakan uji nonparametrik (Spearman, Wilcoxon, Kruskal-Wallis).
  Skor rata-rata konstruk boleh diperlakukan sebagai pendekatan kontinu pada regresi, dengan pemeriksaan residual.
- Reliabilitas: Cronbach's alpha >= 0.70; korelasi item-total >= 0.30. Laporkan alpha-if-deleted.
- Regresi: standarkan prediktor agar koefisien sebanding; galat baku robust HC3; periksa VIF (waspada > 5).
- Ordinal logit: laporkan odds ratio dan interval kepercayaan 95%.
- Uji berganda: koreksi Holm pada perbandingan post-hoc.
- Laporkan ukuran efek (r untuk Wilcoxon, epsilon-kuadrat untuk Kruskal), bukan p-value saja.
- Ketidakpastian: bootstrap 1000x untuk peringkat dan importance.
- Bahasa: "berhubungan dengan", "terkait", "cenderung". Hindari "menyebabkan", "berdampak pasti".
- Selalu jalankan analisis sensitivitas yang tercantum di plan/04.
- Jika hasil tidak signifikan atau model tidak mengalahkan baseline, laporkan apa adanya.
````

### `.claude/guides/ml_guidelines.md`

````markdown
# Pedoman Machine Learning

- n = 149: jangan pakai deep learning; hindari tuning besar-besaran.
- Validasi: RepeatedStratifiedKFold (5 lipat x 5 ulangan) untuk klasifikasi; RepeatedKFold untuk regresi.
- Semua praproses (scaling, encoding) di dalam sklearn Pipeline agar tidak terjadi data leakage.
- Baseline wajib: DummyClassifier/DummyRegressor dan Logistic/Linear Regression.
- Random Forest: n_estimators 300-500, max_depth 3-6, min_samples_leaf 3-5, random_state 42.
  XGBoost hanya sebagai pembanding, dengan kedalaman kecil dan regularisasi.
- Metrik klasifikasi: F1-macro, akurasi seimbang, confusion matrix. Regresi: MAE, RMSE, R2.
  Laporkan rata-rata dan simpangan baku antar lipatan.
- Interpretasi: permutation importance dihitung pada data uji tiap lipatan; SHAP (TreeExplainer)
  pada model akhir yang dilatih dengan seluruh data, dilaporkan sebagai ilustrasi (bukan bukti kausal).
- Imbalance: cek ukuran kelas; jika tidak seimbang, pakai class_weight="balanced" sebelum SMOTE.
- Tujuan model adalah menjelaskan, jadi jangan mengejar akurasi dengan fitur yang bocor dari Y.
- Simpan hasil CV per lipatan ke reports/tables untuk bukti.
````

### `.claude/guides/recommendation_logic.md`

````markdown
# Logika Rekomendasi

Strategi s dalam {X1_unggah, X2_promosi, X3_komunikasi, X4_konsistensi}.

1. pengaruh_s: pengaruh strategi s yang sudah dinormalkan ke 0-1, diambil dari rata-rata
   peringkat/skor ternormalisasi |koefisien terstandar|, permutation importance, dan mean|SHAP| (Tahap 4).
2. benchmark_s(segmen): median skor strategi s pada UMKM dengan naik_penjualan = 1 di segmen tersebut.
3. skor_s(UMKM atau segmen): skor strategi s yang dinilai (rata-rata segmen untuk rekomendasi per segmen).
4. gap_s = max(0, benchmark_s - skor_s).
5. prioritas_s = pengaruh_s x gap_s.
6. Urutkan prioritas_s menurun; ambil 3 teratas (hanya yang prioritas_s > 0).

## Template kalimat
"Untuk segmen [nama], strategi [s] menjadi prioritas karena skor rata-rata [x.x]
berada [gap] poin di bawah UMKM yang penjualannya naik pada segmen yang sama, dan strategi ini
termasuk yang paling berhubungan dengan kinerja penjualan."

## Tindakan konkret (contoh dasar, sesuaikan dengan item kuesioner)
- X1_unggah: jadwalkan unggah ulang mingguan, tambah produk baru berkala, pantau produk yang sepi.
- X2_promosi: gunakan voucher/diskon terukur, coba fitur iklan, evaluasi hasil promosi bulanan.
- X3_komunikasi: balas chat di hari yang sama, tanggapi komplain segera, jawaban jelas dan sopan.
- X4_konsistensi: perbarui stok, harga, foto dan deskripsi; jaga toko tetap aktif saat sibuk.

## Catatan
- Rekomendasi adalah prioritas berbasis pola asosiasi, bukan jaminan hasil.
- Jika pengaruh suatu strategi tidak berbeda dari nol secara meyakinkan, nyatakan ketidakpastiannya dan
  turunkan bobot rekomendasinya.
````

## B.8 Perintah kustom: `.claude/commands/*.md`

### `.claude/commands/next-stage.md`

````markdown
---
description: Kerjakan tahap berikutnya yang belum selesai
---
1. Baca `.claude/progress.md` dan tentukan tahap pertama berstatus BELUM atau BERJALAN.
2. Baca file plan tahap itu dan panduan yang dirujuknya.
3. Periksa `.claude/decisions.md`: jika ada keputusan BELUM DISEPAKATI/DIUSULKAN yang relevan, tanyakan ke pengguna dulu.
4. Kerjakan tahap tersebut sampai kriteria selesai terpenuhi.
5. Ringkas hasil (angka kunci, temuan, masalah terbuka), perbarui progress.md, set status MENUNGGU PERSETUJUAN, lalu berhenti.
````

### `.claude/commands/run-stage.md`

````markdown
---
description: Jalankan ulang tahap tertentu (contoh: /run-stage 3)
argument-hint: nomor tahap 1-7
---
Jalankan ulang tahap nomor $ARGUMENTS sesuai `.claude/plan/`. Pertahankan hasil lama dengan memberi akhiran
tanggal pada berkas keluaran sebelumnya, catat alasan pengulangan di decisions.md, lalu perbarui progress.md.
````

### `.claude/commands/log-decision.md`

````markdown
---
description: Catat keputusan baru ke decisions.md
argument-hint: ringkasan keputusan
---
Tambahkan baris baru ke `.claude/decisions.md` dengan ID berikutnya, topik, keputusan "$ARGUMENTS",
status DISEPAKATI, dan tanggal hari ini. Jika keputusan mengubah rencana, perbarui file plan terkait.
````

### `.claude/commands/check-quality.md`

````markdown
---
description: Audit cepat kualitas data atau hasil terakhir
---
Periksa keluaran terbaru: (1) jumlah baris/kolom sesuai harapan, (2) tidak ada NaN tak terjelaskan,
(3) rentang nilai wajar (Likert 1-5, omzet >= 0), (4) tidak ada kebocoran Y ke fitur,
(5) angka di laporan cocok dengan tabel di reports/tables, (6) tidak ada bahasa kausal.
Laporkan temuan sebagai daftar singkat berisi masalah dan saran perbaikan.
````

## B.9 Sub-agent: `.claude/agents/stats-reviewer.md`

````markdown
---
name: stats-reviewer
description: Meninjau kebenaran metodologi statistik dan bahasa klaim pada hasil analisis. Gunakan setelah Tahap 4 dan sebelum pelaporan.
tools: Read, Grep, Glob
---
Anda adalah peninjau statistik. Baca `.claude/guides/statistical_guidelines.md` dan `.claude/guides/ml_guidelines.md`,
lalu periksa hasil di `reports/`:
- Apakah uji sesuai tipe data (ordinal vs kontinu)?
- Apakah ada data leakage, multikolinearitas yang diabaikan, atau koreksi uji berganda yang terlewat?
- Apakah klaim melebihi bukti (bahasa kausal, generalisasi berlebihan dari 149 responden)?
- Apakah analisis sensitivitas dilakukan dan konsisten?
Keluarkan daftar masalah berurutan menurut tingkat keparahan, tanpa mengubah file apa pun.
````

## B.10 Kerangka proyek (dibuat kosong, tanpa implementasi)

**`config.yaml`**
````yaml
seed: 42
base_dir: null   # diisi config.py dari env UMKM_BASE_DIR, jika kosong pakai folder proyek
paths:
  raw: data/raw/Kuesioner_Penelitian__Responses_.xlsx
  processed: data/processed
  reports: reports
  models: models
cleaning:
  winsor_lower: 0.01
  winsor_upper: 0.99
  tahun_referensi: 2026
cv:
  n_splits: 5
  n_repeats: 5
segmentation:
  k_min: 2
  k_max: 6
  min_cluster_size: 15
  bootstrap_n: 100
bootstrap_n: 1000
````

**`requirements.txt`**
````
pandas
numpy
openpyxl
scipy
statsmodels
scikit-learn
xgboost
shap
pingouin
matplotlib
seaborn
plotly
pyyaml
joblib
pytest
black
ruff
jupyter
pydantic
# opsional (nanti, saat integrasi/aplikasi):
# fastapi
# uvicorn
# streamlit
````

**`pyproject.toml`**
````toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "umkm"
version = "0.1.0"
requires-python = ">=3.10"
# dependensi minimal untuk inferensi/integrasi
dependencies = ["pandas", "numpy", "scikit-learn", "joblib", "pydantic", "pyyaml", "openpyxl"]

[project.optional-dependencies]
# hanya untuk tahap analisis
analysis = ["scipy", "statsmodels", "xgboost", "shap", "pingouin", "matplotlib", "seaborn", "plotly"]

[tool.setuptools.packages.find]
where = ["src"]
````

**`.gitignore`**
````
__pycache__/
.ipynb_checkpoints/
.venv/
.env
models/**/*.joblib
data/raw/*.xlsx
data/processed/
````

Buat juga `src/umkm/__init__.py` kosong, serta `.gitkeep` di `data/raw`, `data/processed`, `notebooks`, `tests`, `reports/figures`, `reports/tables`, `models`.

---

# BAGIAN C: Ringkasan Konteks (untuk Manusia)

**Data:** 149 responden UMKM (mayoritas kuliner) di GoFood, GrabFood, Shopee, MaximFood, TikTok Shop.

**Keputusan yang sudah disepakati:**
- Tujuan: memahami strategi yang berpengaruh terhadap kinerja penjualan (opsi a).
- Kinerja diukur dari 5 isian objektif: omzet, transaksi (sebelum/sesudah), dan pelanggan baru. Persepsi Likert (Y1-Y8) bukan target.
- Outlier dibatasi (winsorizing P1-P99), tidak dibuang, disertai analisis sensitivitas.
- Lingkup sekarang: analisis dan laporan. Aplikasi/sistem ditunda, tetapi kode dirancang siap-integrasi (D11).
- Lingkungan kerja: lokal (D12, disepakati); Google Colab hanya opsional.

**Masih perlu dikonfirmasi saat pengerjaan** (ditandai DIUSULKAN/BELUM DISEPAKATI di `.claude/decisions.md`): penanganan omzet sebelum = 0, bentuk target (D13), perlakuan responden tanpa baseline (D14), responden dengan omzet tidak berubah, tafsir kolom pelanggan baru, lama usaha berupa tahun kalender, dan SEM.

**Peringatan metodologis:** hasil adalah hubungan (asosiasi) dari survei satu waktu dengan sampel kecil dan data self-report; bukan bukti sebab-akibat.
