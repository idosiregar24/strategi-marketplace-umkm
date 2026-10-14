# Menjalankan di Google Colab (OPSIONAL / cadangan)

Jalur utama proyek adalah lokal (lihat `local_setup.md`). Pakai Colab hanya jika instalasi lokal bermasalah
atau untuk berbagi notebook dengan orang lain.

## Prinsip
- Runtime Colab bersifat sementara: file di `/content` hilang saat sesi berakhir.
- Kode disimpan di **GitHub**; data dan keluaran disimpan di **Google Drive**.
- Data kuesioner memuat nama usaha: jangan unggah `data/raw/*.xlsx` ke repo publik (sudah ada di .gitignore).
- Tidak butuh GPU; runtime CPU standar cukup untuk 149 baris.

## Jalur tanpa GitHub (dipakai saat ini)
Proyek belum memakai Git, jadi jalur termudah adalah lewat zip:
1. Di lokal, buat `umkm_proyek.zip` (isi: src, tests, notebooks, data/raw, config.yaml, pyproject.toml,
   requirements.txt, CLAUDE.md, SPEC.md; tanpa .venv). Buat ulang zip setiap kali kode berubah.
2. Unggah zip ke `MyDrive/`, buka `notebooks/00_setup_colab.ipynb` di Colab, jalankan dari atas.
   Sel setup mengekstrak zip ke `MyDrive/umkm_proyek/` (hanya jika folder itu belum ada; hapus foldernya
   untuk memakai zip baru), mengatur `UMKM_BASE_DIR`, dan menambahkan `src/` ke `sys.path`
   (tanpa `pip install -e`, jadi tidak perlu restart runtime).
3. Kompatibilitas sudah diuji: Tahap 1 menghasilkan data_clean.csv identik di pandas 2.2 (Colab) dan pandas 3 (lokal).

## Struktur di Drive
MyDrive/umkm_proyek/data/raw/Kuesioner_Penelitian__Responses_.xlsx
MyDrive/umkm_proyek/data/processed/, reports/, models/ (dibuat otomatis oleh pipeline)

## Sel pertama di setiap notebook (`notebooks/00_setup_colab.ipynb`, dibuat saat Tahap 1)
```python
from google.colab import drive
drive.mount('/content/drive')

import os
os.environ["UMKM_BASE_DIR"] = "/content/drive/MyDrive/umkm_proyek"

!git clone https://github.com/<user>/<repo>.git /content/proyek 2>/dev/null || git -C /content/proyek pull
%cd /content/proyek
!pip install -q -e ".[analysis]"
```
Jalankan tahap lewat `!python -m umkm.pipeline --stage 1`, atau impor fungsinya langsung di notebook.

## Kebiasaan yang perlu dijaga
- Jalankan ulang sel setup setiap sesi baru. Jika Colab meminta restart setelah pip, restart lalu jalankan dari sel setup.
- Semua path lewat config/`UMKM_BASE_DIR`, bukan `/content/...` yang di-hardcode di modul.
- Simpan semua keluaran ke Drive, commit kode ke GitHub secara berkala.
- Di akhir proyek, jalankan `pip freeze` dan catat versi di `requirements.txt` agar hasil dapat direproduksi.
- Claude Code berjalan di terminal/VS Code lokal, bukan di dalam Colab. Alur yang disarankan: edit kode di lokal
  bersama agent, push ke GitHub, lalu jalankan di Colab. Jika tidak memakai agent, rencana di `plan/` tetap bisa diikuti manual.
