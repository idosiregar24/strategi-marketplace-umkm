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
