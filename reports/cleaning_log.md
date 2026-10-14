# Log Cleaning (Tahap 1)

Dibuat oleh `umkm.cleaning` pada 2026-10-14 14:15.

## Ringkasan

- Data mentah: 149 baris x 37 kolom.
- Data bersih: 149 baris x 64 kolom.
- Kolom `score` konstan, dibuang.
- `nama_usaha` hanya sebagai pengenal; laporan memakai `id_responden` (R001-R149).
- Nilai Likert di luar 1-5 atau kosong: 0.
- Missing setelah cleaning: `trx_sebelum`=4, `trx_sebelum_w`=4, `trx_sesudah`=4, `trx_sesudah_w`=4.

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

| id_responden | omzet_sebelum | omzet_sesudah | trx_sebelum | trx_sesudah | flag_trx_pecahan | flag_trx_tidak_wajar |
|---|---|---|---|---|---|---|
| R002 | 100,000,000 | 120,000,000 | 2.50 | 2.65 | 1 | 0 |
| R006 | 10,500,000 | 10,500,000 | 10,500,000 | 540 | 0 | 1 |
| R015 | 800,000,000 | 300,000,000 | 30,000,000 | 40,000,000 | 0 | 1 |
| R021 | 15,000,000 | 20,000,000 | 1,000,000 | 15,000,000 | 0 | 1 |


Transaksi sebelum dan sesudah 4 responden di atas DIKOSONGKAN (NaN), ditandai `flag_trx_dikosongkan`. Nilai asli tetap di `trx_*_raw`; omzet dan jawaban lain responden ini tetap dipakai. Inilah satu-satunya sumber missing di data bersih.


## 4. Platform

- Pengguna per platform: `mp_gofood` = 112, `mp_grabfood` = 80, `mp_shopee` = 100, `mp_maxim` = 8, `mp_tiktok` = 5.
- Sebaran `jumlah_platform`: 1 platform = 57, 2 platform = 33, 3 platform = 54, 4 platform = 5.
- Pilihan tak dikenal: tidak ada.

## 5. Winsorizing (D03, D16)

Persentil atas 99%; ekor bawah tidak dibatasi (D16). Batas dihitung dari gabungan nilai sebelum + sesudah per variabel (D15, DIUSULKAN) agar responden yang nilainya tidak berubah tetap tidak berubah. Kolom asli disimpan; kolom terwinsor berakhiran `_w`.

| Variabel | Batas bawah | Batas atas |
|---|---|---|
| omzet | - | 330,000,000 |
| trx | - | 10,220 |

- Sel yang berubah: `omzet_sebelum` = 1, `omzet_sesudah` = 1, `trx_sebelum` = 1, `trx_sesudah` = 2.
- Responden dengan `flag_outlier` = 1: 4.
- Nilai 0 yang terangkat oleh batas bawah: `omzet_sebelum` = 0, `omzet_sesudah` = 0, `trx_sebelum` = 0, `trx_sesudah` = 0.

| id_responden | omzet_sebelum | omzet_sebelum_w | omzet_sesudah | omzet_sesudah_w | trx_sebelum | trx_sebelum_w | trx_sesudah | trx_sesudah_w |
|---|---|---|---|---|---|---|---|---|
| R015 | 800,000,000 | 330,000,000 | 300,000,000 | 300,000,000 |  |  |  |  |
| R019 | 300,000,000 | 300,000,000 | 300,000,000 | 300,000,000 | 60,000 | 10,220 | 60,000 | 10,220 |
| R020 | 300,000,000 | 300,000,000 | 600,000,000 | 330,000,000 | 3,000 | 3,000 | 6,000 | 6,000 |
| R107 | 200,000,000 | 200,000,000 | 250,000,000 | 250,000,000 | 10,000 | 10,000 | 12,000 | 10,220 |


### Dampak winsorizing pada arah perubahan (naik/sama/turun)

_(tidak ada)_


## 6. Duplikat (hanya dilaporkan, tidak dibuang)

- Nama usaha sama: 0 kelompok.
- Pola jawaban identik (Likert + angka + lama usaha): 0 kelompok.
