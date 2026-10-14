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
