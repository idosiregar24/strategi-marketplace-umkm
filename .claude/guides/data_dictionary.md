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
