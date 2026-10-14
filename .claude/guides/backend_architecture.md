# Arsitektur Pipeline dan Kesiapan Integrasi

## Paket Python: src/umkm/
| Modul | Tanggung jawab |
|---|---|
| config.py | Memuat config.yaml, path, parameter; base dir dari env `UMKM_BASE_DIR` atau folder proyek |
| schemas.py | Kontrak data (Pydantic): ProfilUMKM, SkorStrategi (1-5), HasilRekomendasi |
| io.py | Baca xlsx mentah, tulis csv/parquet, simpan artefak |
| cleaning.py | Rename kolom, parse Likert/omzet/lama usaha, pecah platform, winsorizing |
| features.py | Skor konstruk, alpha, d_omzet, d_trx, Y_obj, naik_penjualan, y_pelanggan_baru, tanpa_baseline, fitur profil |
| stats.py | Wilcoxon, Spearman, Kruskal, VIF, OLS robust, ordinal logit, bootstrap |
| models.py | Pipeline sklearn, CV, Random Forest/Logistic/XGBoost, permutation importance, SHAP |
| segmentation.py | K-Means, silhouette, stabilitas bootstrap, profil segmen |
| recommend.py | Benchmark, gap, skor prioritas, template rekomendasi; fungsi publik `recommend(profil) -> dict` |
| viz.py | Fungsi plot standar (heatmap, boxplot, bar SHAP) |
| pipeline.py | Menjalankan tahap 1-6 berurutan |

## Alur data
data/raw (xlsx) -> cleaning -> data_clean.csv -> features -> data_features.csv
-> models/stats -> reports/tables -> segmentation -> data_segmen.csv -> recommend -> rekomendasi.

## Eksekusi
- CLI: `python -m umkm.pipeline --stage N` (atau `--all`). Di Colab, awali dengan `!`.
- Makefile: `make clean-data`, `make features`, `make eda`, `make influence`, `make segment`, `make recommend`, `make all`, `make test`.
- Setiap tahap membaca keluaran tahap sebelumnya dari data/processed; tidak ada ketergantungan tersembunyi.
- Setiap tahap menulis log ringkas ke reports/logs/.

## Artefak model
- Simpan dengan joblib di models/, beserta `model_meta.json` (tanggal, seed, versi pustaka, fitur, metrik CV, hash data).
- Jangan menyimpan data mentah di dalam artefak.

## Kesiapan Integrasi (aplikasi/API TIDAK dibangun sekarang)

Tujuannya: nanti, sistem lain cukup memanggil kode yang sudah ada tanpa menulis ulang analisis.

1. **Logika di paket, notebook tipis.** Notebook hanya memanggil fungsi di `src/umkm/` dan menampilkan hasil.
2. **Kontrak data (`schemas.py`).** Model Pydantic mendefinisikan nama field, tipe, dan rentang masukan/keluaran.
   Kontrak yang sama dicatat di `reports/integration_contract.md`.
3. **Satu pintu masuk inferensi:** `recommend(profil: dict) -> dict`.
   - Tidak membaca xlsx mentah atau state notebook; hanya memuat artefak dari `models/v1/`.
   - Masukan dan keluaran JSON-serializable (dict/list/angka/teks).
4. **Artefak berversi** di `models/v1/`: `segmen.joblib` (scaler + K-Means), `model.joblib`,
   `benchmark_per_segmen.json`, `pengaruh_strategi.json`, `model_meta.json`
   (tanggal, seed, versi pustaka, daftar fitur, metrik CV, hash data). Perubahan model = folder `v2/`.
5. **Preprocessing yang sama untuk data baru.** Fungsi di cleaning/features menerima satu baris maupun banyak baris.
6. **Tanpa path absolut.** Semua path dari config + env `UMKM_BASE_DIR` agar sama di lokal, Colab, atau server.
7. **Dependensi inferensi minimal:** pandas, numpy, scikit-learn, joblib, pydantic, pyyaml.
   Paket analisis (statsmodels, shap, pingouin, dll.) hanya untuk tahap analisis (`pip install -e ".[analysis]"`).
8. **Bahasa keluaran:** teks rekomendasi disimpan sebagai template di `recommend.py`, bukan di notebook,
   agar mudah diubah/diterjemahkan oleh sistem tujuan.

### Contoh kontrak (sketsa)
Masukan:
{"skala_omzet": 18000000, "lama_usaha_pra_mp": 3, "lama_di_mp": 2, "platform": ["gofood", "shopee"],
 "x1_unggah": 2.0, "x2_promosi": 2.5, "x3_komunikasi": 4.2, "x4_konsistensi": 3.0}

Keluaran:
{"versi_model": "v1", "segmen": {"id": 2, "nama": "..."},
 "prioritas": [{"strategi": "x2_promosi", "skor": 2.5, "benchmark": 3.8, "prioritas": 0.31,
                "alasan": "...", "tindakan": "..."}],
 "catatan": "Berdasarkan pola asosiasi dari 149 UMKM, bukan jaminan hasil."}

### Jalur integrasi nanti (belum dikerjakan; hanya untuk gambaran)
- Sistem berbasis Python: `pip install` paket `umkm`, lalu panggil `recommend()` langsung.
- Sistem non-Python: bungkus `recommend()` dengan FastAPI (POST /recommend, GET /health) dan panggil via REST.
- Demo cepat: Streamlit memanggil `recommend()`.
Semua jalur ini memakai kontrak dan artefak yang sama.
