# Setup Lingkungan Lokal (jalur utama)

## Prasyarat
- Python 3.10-3.12 (hindari versi yang terlalu baru: sebagian pustaka seperti shap/numba belum kompatibel).
- Git dan VS Code (disarankan) atau Jupyter.
- RAM 4 GB atau lebih; tidak butuh GPU.
- Jalankan Claude Code dari ROOT folder proyek agar CLAUDE.md dan .claude/ terbaca.

## Setup sekali di awal
```
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[analysis]"
pip install jupyter ipykernel pytest black ruff
python -m ipykernel install --user --name umkm
git init
```
Alternatif: `pip install -r requirements.txt` lalu `pip install -e .`

## Cara kerja sehari-hari
- Aktifkan venv di setiap terminal baru.
- Data mentah ada di `data/raw/` (tidak masuk Git). `base_dir` default adalah folder proyek,
  jadi `UMKM_BASE_DIR` tidak perlu diatur.
- Jalankan tahap: `python -m umkm.pipeline --stage N`. Jika `make` tidak tersedia (umumnya di Windows),
  pakai perintah python tersebut.
- Notebook: buka di VS Code atau Jupyter, pilih kernel `umkm`.
- Tes: `pytest`.
- Commit per tahap dengan pesan `tahap-N: ringkasan`.

## Pemecahan masalah
- Gagal memasang shap/pingouin/numba: pastikan Python 3.10-3.12 dan pip terbaru. Jika tetap gagal,
  jalankan tahap yang memerlukan pustaka itu di Google Colab (lihat colab_setup.md).
- Error path/file tidak ditemukan: jalankan perintah dari root folder proyek.
- PowerShell menolak mengaktifkan venv: jalankan `Set-ExecutionPolicy -Scope Process RemoteSigned` di sesi itu.
- Hasil berbeda antar mesin: pastikan seed 42 dan versi pustaka sama (`pip freeze`).
