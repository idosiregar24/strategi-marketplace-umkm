# Tahap 6: Rekomendasi Strategi

Rujukan: guides/recommendation_logic.md
Modul: src/umkm/recommend.py
Keluaran: reports/tables/rekomendasi_per_segmen.csv, reports/rekomendasi_ringkas.md

## Langkah
1. Hitung benchmark per segmen: median skor X1-X4 pada UMKM dengan naik_penjualan = 1 di segmen itu.
   Jika kelompok itu di suatu segmen < 5 orang, pakai benchmark seluruh responden dengan naik_penjualan = 1.
   DIUBAH (D28, 2026-10-30): benchmark = RATA-RATA (bukan median) skor UMKM naik, agar sebanding dengan
   rata-rata skor segmen; median dihitung sebagai sensitivitas.
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
