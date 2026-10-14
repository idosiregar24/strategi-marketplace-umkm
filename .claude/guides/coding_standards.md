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
