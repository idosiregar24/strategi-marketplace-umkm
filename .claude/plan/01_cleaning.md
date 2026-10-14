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
