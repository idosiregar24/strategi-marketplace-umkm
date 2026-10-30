# Log Cleaning (Tahap 1)

Dibuat oleh `umkm.cleaning` pada 2026-10-30 09:52.

## Ringkasan

- Data mentah: 149 baris x 37 kolom.
- Data bersih: 149 baris x 65 kolom.
- Kolom `score` konstan, dibuang.
- `nama_usaha` hanya sebagai pengenal; laporan memakai `id_responden` (R001-R149).
- Nilai Likert di luar 1-5 atau kosong: 0.
- Missing setelah cleaning: tidak ada.

## Koreksi hasil konfirmasi responden (D25)

Nilai diganti sesuai jawaban konfirmasi ulang (diatur di `config.yaml`, `cleaning.koreksi`); isian asli tetap di kolom `*_raw`, baris ditandai `flag_dikoreksi`. Koreksi diterapkan sebelum penandaan transaksi janggal dan winsorizing.

| id_responden | kolom | nilai_lama | nilai_baru | keterangan |
|---|---|---|---|---|
| R065 | omzet_sesudah | 9,000,000 | 90,000,000 | terisi 9 jt; dikonfirmasi 90 jt (omzet tetap) |
| R130 | omzet_sesudah | 32,000,000 | 320,000,000 | terisi 32 jt; dikonfirmasi 320 jt (omzet tetap) |
| R106 | omzet_sesudah | 1,500,000 | 15,000,000 | terisi 1,5 jt; dikonfirmasi 15 jt (kurang satu nol) |
| R006 | trx_sebelum | 10,500,000 | 300 | terisi 10,5 jt (= omzet); dikonfirmasi 300 pesanan/bulan |
| R006 | trx_sesudah | 540 | 300 | terisi 540; dikonfirmasi 300 pesanan/bulan |
| R015 | trx_sebelum | 30,000,000 | 300 | terisi 30 jt; dikonfirmasi 300 pesanan/bulan |
| R015 | trx_sesudah | 40,000,000 | 400 | terisi 40 jt; dikonfirmasi 400 pesanan/bulan |
| R021 | trx_sebelum | 1,000,000 | 100 | terisi 1 jt; dikonfirmasi 100 pesanan/bulan |
| R021 | trx_sesudah | 15,000,000 | 15,000 | terisi 15 jt; dikonfirmasi 15.000 pesanan/bulan (naik 150x, masih diragukan) |
| R002 | trx_sebelum | 2.50 | 2,500 | terisi 2,5; dikonfirmasi 2.500 pesanan/bulan (dalam ribuan) |
| R002 | trx_sesudah | 2.65 | 2,650 | terisi 2,65; dikonfirmasi 2.650 pesanan/bulan (dalam ribuan) |
| R019 | lama_usaha_pra_mp | 8 | 5 | isian 2018 = tahun berdiri; marketplace sejak 2023 -> 2023 - 2018 = 5 th |

## 1. Likert: audit label vs angka

Ditemukan 5 sel dengan label yang tidak cocok dengan angkanya (5 responden). Sesuai rencana, yang dipakai adalah ANGKA.

| kolom | nilai_asli | angka_dipakai | label_harapan | jumlah |
|---|---|---|---|---|
| x4_konsistensi_1 | 2. Sangat Tidak Konsisten | 2 | tidak konsisten | 5 |


Responden terdampak: R002, R003, R051, R103, R106


Variasi format seperti "1.Tidak Pernah" (tanpa spasi) ditangani regex dan tidak dihitung sebagai ketidaksesuaian.

## 2. Lama usaha

- Isian "N bulan" diubah ke N/12 tahun: `lama_usaha_pra_mp` = 4, `lama_di_mp` = 4.
- Isian tahun kalender (>= 1900) diubah ke 2026 - tahun (D10, DISEPAKATI), ditandai `flag_lama_tahun_kalender`:

| id_responden | kolom | nilai_asli | hasil_tahun |
|---|---|---|---|
| R019 | lama_usaha_pra_mp | 2018 | 8 |
| R019 | lama_di_mp | 2023 | 3 |

- `lama_usaha_pra_mp`: min 0.00, median 3.00, maks 22.00; bernilai 0 = 33.
- `lama_di_mp`: min 0.08, median 3.00, maks 13.00; bernilai 0 = 0.

## 3. Omzet, transaksi, pelanggan baru

- Teks dengan titik pemisah ribuan yang diubah ke angka: `omzet_sebelum` = 2, `omzet_sesudah` = 2, `trx_sebelum` = 0, `trx_sesudah` = 0.
- Nilai tak terbaca: tidak ada.
- Jumlah nilai 0: `omzet_sebelum` = 1, `omzet_sesudah` = 0, `trx_sebelum` = 1, `trx_sesudah` = 0, `pelanggan_baru` = 1.

### Transaksi tidak wajar (D17)

Kriteria `flag_trx_tidak_wajar`: transaksi > 100,000 atau sama persis dengan omzet di baris yang sama. `flag_trx_pecahan`: transaksi bukan bilangan bulat.

_(tidak ada)_


Transaksi di atas hanya ditandai, tidak diubah.


## 4. Platform

- Pengguna per platform: `mp_gofood` = 112, `mp_grabfood` = 80, `mp_shopee` = 100, `mp_maxim` = 8, `mp_tiktok` = 5.
- Sebaran `jumlah_platform`: 1 platform = 57, 2 platform = 33, 3 platform = 54, 4 platform = 5.
- Pilihan tak dikenal: tidak ada.

## 5. Winsorizing (D03, D16)

Persentil atas 99%; ekor bawah tidak dibatasi (D16). Batas dihitung dari gabungan nilai sebelum + sesudah per variabel (D15, DIUSULKAN) agar responden yang nilainya tidak berubah tetap tidak berubah. Kolom asli disimpan; kolom terwinsor berakhiran `_w`.

| Variabel | Batas bawah | Batas atas |
|---|---|---|
| omzet | - | 330,000,000 |
| trx | - | 12,090 |

- Sel yang berubah: `omzet_sebelum` = 1, `omzet_sesudah` = 1, `trx_sebelum` = 1, `trx_sesudah` = 2.
- Responden dengan `flag_outlier` = 1: 4.
- Nilai 0 yang terangkat oleh batas bawah: `omzet_sebelum` = 0, `omzet_sesudah` = 0, `trx_sebelum` = 0, `trx_sesudah` = 0.

| id_responden | omzet_sebelum | omzet_sebelum_w | omzet_sesudah | omzet_sesudah_w | trx_sebelum | trx_sebelum_w | trx_sesudah | trx_sesudah_w |
|---|---|---|---|---|---|---|---|---|
| R015 | 800,000,000 | 330,000,000 | 300,000,000 | 300,000,000 | 300 | 300 | 400 | 400 |
| R019 | 300,000,000 | 300,000,000 | 300,000,000 | 300,000,000 | 60,000 | 12,090 | 60,000 | 12,090 |
| R020 | 300,000,000 | 300,000,000 | 600,000,000 | 330,000,000 | 3,000 | 3,000 | 6,000 | 6,000 |
| R021 | 15,000,000 | 15,000,000 | 20,000,000 | 20,000,000 | 100 | 100 | 15,000 | 12,090 |


### Dampak winsorizing pada arah perubahan (naik/sama/turun)

_(tidak ada)_


## 6. Duplikat (hanya dilaporkan, tidak dibuang)

- Nama usaha sama: 0 kelompok.
- Pola jawaban identik (Likert + angka + lama usaha): 0 kelompok.
