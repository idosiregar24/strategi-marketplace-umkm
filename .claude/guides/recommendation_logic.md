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
