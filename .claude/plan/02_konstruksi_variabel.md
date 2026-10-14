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
