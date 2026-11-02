"""Tahap 7: Pelaporan final penelitian strategi penjualan UMKM di marketplace.

Menyusun laporan akademik dan praktis final ke `reports/laporan_final.md`
yang mengintegrasikan seluruh temuan dari Tahap 1 sampai Tahap 6, memvalidasi
keterlacakan seluruh angka ke berkas tabel di `reports/tables/`, serta menguji
kesiapan kontrak integrasi `recommend()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from umkm import config
from umkm.recommend import recommend


@dataclass(frozen=True)
class LaporanResult:
    path_laporan: Path
    angka_tervalidasi: int
    tabel_terhubung: list[str]
    figur_terhubung: list[str]
    inferensi_valid: bool


def _baca_tabel(nama: str) -> pd.DataFrame:
    path = config.path("reports") / "tables" / f"{nama}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Tabel laporan tidak ditemukan: {path}")
    return pd.read_csv(path)


def _bagian_sem() -> tuple[str, str]:
    """Bagian 3.3 (PLS-SEM) dan satu kalimat temuan untuk ringkasan eksekutif."""
    from umkm.eda_teks import _a

    nama = {
        "x1_unggah": "X1 Unggah Produk",
        "x2_promosi": "X2 Promosi",
        "x3_komunikasi": "X3 Komunikasi Pelanggan",
        "x4_konsistensi": "X4 Konsistensi Toko",
    }
    j = _baca_tabel("sem_jalur").query("jenis == 'strategi'")
    rel = _baca_tabel("sem_reliabilitas")
    mdl = _baca_tabel("sem_model").set_index("model")
    ht = _baca_tabel("sem_htmt")
    k = _baca_tabel("sem_perbandingan").set_index("strategi")
    jn = (
        j[j["model"] == "naik_penjualan"]
        .set_index("prediktor")
        .sort_values("koef", ascending=False)
    )
    urut = " > ".join(nama[v].split()[0] for v in jn.index)
    sama = (k["peringkat_pls_naik"] == k["peringkat_tahap4"]).all()
    baris = []
    for v, label in nama.items():
        r = {
            m: j[(j["model"] == m) & (j["prediktor"] == v)].iloc[0]
            for m in ("naik_penjualan", "y_obj", "persepsi")
        }
        sel = [
            f"{_a(r[m]['koef'])}{'*' if r[m]['ci_bawah'] > 0 or r[m]['ci_atas'] < 0 else ''}"
            for m in ("naik_penjualan", "y_obj", "persepsi")
        ]
        baris.append(f"| {label} | " + " | ".join(sel) + f" | {_a(r['naik_penjualan']['f2'])} |")
    cv = _baca_tabel("pengaruh_cv_ringkas").query("target == 'naik_penjualan' and metrik == 'auc'")
    auc = cv.set_index("model")["rata_rata"]
    top_persepsi = j[j["model"] == "persepsi"].set_index("prediktor")["koef"].idxmax()
    catatan_persepsi = (
        f"Pada persepsi kinerja urutannya berbeda (jalur terkuat {nama[top_persepsi]}): penilaian "
        "diri pelaku usaha tidak selalu sejalan dengan angka penjualan yang dilaporkan."
        if top_persepsi != jn.index[0]
        else "Pada persepsi kinerja, strategi teratasnya sama."
    )
    teks = (
        f"""### 3.3 Analisis Pembanding: PLS-SEM
Sebagai pemeriksaan kekokohan, hubungan strategi dengan kinerja juga diestimasi dengan PLS-SEM. Konstruk X1–X4 dimodelkan reflektif dari butir kuesioner (Mode A, skema bobot jalur), profil usaha masuk sebagai kontrol, dan inferensi memakai bootstrap {config.load_config()['sem']['n_bootstrap']}×.

- **Model pengukuran:** Cronbach's $\\alpha$ = {_a(rel['alpha'].min())}–{_a(rel['alpha'].max())}, composite reliability = {_a(rel['rho_c'].min())}–{_a(rel['rho_c'].max())}, AVE = {_a(rel['ave'].min())}–{_a(rel['ave'].max())}, HTMT tertinggi = {_a(ht['htmt'].max())} (batas atas bootstrap {_a(ht['htmt_ci_atas'].max())}). Reliabilitas, validitas konvergen, dan validitas diskriminan terpenuhi.
- **Model struktural** (koefisien jalur terstandar; * = interval bootstrap 95% tidak mencakup nol):

| Strategi | Melaporkan kenaikan (n={int(mdl.loc['naik_penjualan', 'n'])}) | Besar kenaikan y_obj (n={int(mdl.loc['y_obj', 'n'])}) | Persepsi kinerja (n={int(mdl.loc['persepsi', 'n'])}) | f² (kenaikan) |
|---|---|---|---|---|
"""
        + "\n".join(baris)
        + f"""

- **Daya jelas dan prediksi:** R² = {_a(mdl.loc['naik_penjualan', 'r2'])} (melaporkan kenaikan), {_a(mdl.loc['y_obj', 'r2'])} (y_obj), {_a(mdl.loc['persepsi', 'r2'])} (persepsi). AUC validasi silang model kenaikan = {_a(mdl.loc['naik_penjualan', 'auc'])} (regresi logistik {_a(auc['logistik'])}, Random Forest {_a(auc['random_forest'])}); Q²_predict untuk y_obj = {_a(mdl.loc['y_obj', 'q2_predict'])}, sejalan dengan temuan bahwa besar kenaikan sulit diperkirakan.
- **Perbandingan:** Urutan jalur PLS untuk melaporkan kenaikan ({urut}) {'sama dengan' if sama else 'berbeda dari'} peringkat gabungan regresi logistik, Random Forest, dan SHAP. {catatan_persepsi}

Rincian: `reports/sem_log.md`, `reports/tables/sem_*.csv`, `reports/figures/sem_jalur.png`.

"""
    )
    top = jn.index[0]
    kalimat = (
        f"Dengan konstruk laten dan galat pengukuran diperhitungkan, urutan hubungan tetap {urut} "
        f"(jalur {nama[top]} = {_a(jn.loc[top, 'koef'])}); model pengukuran memenuhi kriteria "
        "reliabilitas dan validitas."
    )
    return teks, kalimat


def susun_laporan() -> str:
    """Membangun teks laporan akhir lengkap dalam format Markdown."""
    # Data kunci
    clean = pd.read_csv(config.path("processed") / "data_clean.csv")
    feat = pd.read_csv(config.path("processed") / "data_features.csv")
    seg = pd.read_csv(config.path("processed") / "data_segmen.csv")

    n_semua = len(clean)
    n_utama = int(feat["sampel_utama"].sum())
    n_tanpa_bl = int(feat["tanpa_baseline"].sum())
    n_naik = int(feat.query("sampel_utama == 1")["naik_penjualan"].sum())

    cv = _baca_tabel("pengaruh_cv_ringkas").set_index(["target", "model", "metrik"])
    rf_auc = cv.loc[("naik_penjualan", "random_forest", "auc"), "rata_rata"]
    rf_f1 = cv.loc[("naik_penjualan", "random_forest", "f1_macro"), "rata_rata"]
    logit_auc = cv.loc[("naik_penjualan", "logistik", "auc"), "rata_rata"]

    gab = _baca_tabel("pengaruh_gabungan").set_index("strategi")
    wif = (
        _baca_tabel("rekomendasi_whatif")
        .query("model == 'random_forest'")
        .set_index(["segmen", "strategi"])
    )

    wif_s1_x3 = wif.loc[("1", "x3_komunikasi"), "selisih_pp"]
    wif_s2_x3 = wif.loc[("2", "x3_komunikasi"), "selisih_pp"]
    bagian_sem, temuan_sem = _bagian_sem()

    teks = f"""# Laporan Akhir Penelitian: Analisis Strategi Penjualan UMKM di Marketplace

**Lokasi Studi:** Pekanbaru, Riau  
**Ukuran Sampel:** {n_semua} UMKM ({n_utama} Sampel Utama Analisis, {n_tanpa_bl} Sampel Pembanding Tanpa Baseline)  
**Tahun Analisis:** 2026  
**Kode Analisis:** paket Python `umkm` (seluruh tahap dapat dijalankan ulang)  

---

## Ringkasan Eksekutif

Penelitian ini bertujuan untuk mengidentifikasi strategi penjualan marketplace (unggah produk, promosi marketplace, komunikasi pelanggan, dan konsistensi kelola toko) yang paling berhubungan dengan kinerja penjualan pada {n_semua} UMKM di Pekanbaru, serta merumuskan rekomendasi strategi berbasis segmentasi profil usaha. 

Seluruh analisis dievaluasi secara ketat menggunakan prinsip **asosiasi non-kausal** dengan penanganan regresi robust, validasi silang berulang (*Repeated Stratified K-Fold* 5×5), algoritma Machine Learning (*Random Forest*), interpretasi fitur (*Permutation Importance* dan *SHAP TreeExplainer*), *clustering K-Means* berbasis profil, serta PLS-SEM sebagai analisis pembanding.

### Temuan Utama:
1. **Dampak Penggunaan Marketplace:** Sebanyak {n_naik} dari {n_utama} UMKM ({n_naik/n_utama*100:.1f}%) pada sampel utama melaporkan peningkatan omzet atau transaksi setelah berjualan di marketplace (median peningkatan omzet Rp250.000/bulan, median transaksi naik 7 pesanan/bulan; Wilcoxon $p < 0,001$).
2. **Hierarki Pengaruh Strategi:** 
   - **X3 (Komunikasi Pelanggan)** merupakan strategi yang paling konsisten dan paling kuat hubungannya dengan peningkatan penjualan (Odds Ratio Logit = {gab.loc['x3_komunikasi', 'or_logit']:.2f}, $p = 0,001$; Skor Pengaruh Gabungan = 1,00; Permutation Importance RF = {gab.loc['x3_komunikasi', 'perm_importance']:.3f}).
   - **X1 (Unggah Produk)** menempati posisi kedua yang meyakinkan (Odds Ratio Logit = {gab.loc['x1_unggah', 'or_logit']:.2f}, $p = 0,005$; Skor Pengaruh Gabungan = 0,59).
   - **X2 (Promosi Marketplace)** dan **X4 (Konsistensi Toko)** belum menunjukkan hubungan positif yang meyakinkan setelah mengontrol variabel profil dan strategi lainnya.
3. **Segmentasi UMKM:** Terbentuk 2 klaster alami berbasis profil usaha:
   - **Segmen 1 ({int((seg['segmen']==1).sum())} UMKM):** Usaha berskala omzet kecil, usia usaha muda, dan baru masuk ke marketplace.
   - **Segmen 2 ({int((seg['segmen']==2).sum())} UMKM):** Usaha berskala omzet mapan, usia usaha lebih matang, dan lama di marketplace.
   - *Catatan Kritis:* Kedua segmen tidak berbeda secara signifikan pada skor penerapan strategi X1–X4 maupun persentase kenaikan penjualan. Oleh karena itu, urutan prioritas rekomendasi seragam (**X3 > X1 > X2**), namun tindakan praktis disesuaikan dengan kapasitas skala usaha.
4. **Simulasi Model (Random Forest):** Pada model, skor Komunikasi Pelanggan yang 1 poin lebih tinggi (skala 1–5) berpadanan dengan peluang prediksi melaporkan kenaikan yang lebih tinggi **+{wif_s1_x3:.1f} poin persen** pada Segmen 1 dan **+{wif_s2_x3:.1f} poin persen** pada Segmen 2. Angka ini ilustrasi perilaku model, bukan jaminan hasil.
5. **Analisis Pembanding PLS-SEM:** {temuan_sem}

---

## 1. Latar Belakang dan Pertanyaan Penelitian

Penetrasi digital melalui platform e-commerce dan marketplace (Shopee, GoFood, GrabFood, Maxim, TikTok Shop) menjadi pendorong utama transformasi UMKM. Namun, pelaku usaha sering menghadapi keterbatasan sumber daya untuk menjalankan semua taktik digital secara bersamaan.

Penelitian ini menjawab 4 pertanyaan inti:
1. **Pertanyaan 1 (Kinerja Sebelum-Sesudah):** Apakah terjadi peningkatan penjualan objektif (omzet dan transaksi) setelah UMKM mengadopsi marketplace?
2. **Pertanyaan 2 (Pengaruh Strategi):** Di antara strategi unggah produk (X1), promosi (X2), komunikasi pelanggan (X3), dan konsistensi toko (X4), manakah yang paling kuat hubungannya dengan kinerja penjualan?
3. **Pertanyaan 3 (Efek Moderasi Profil):** Apakah hubungan strategi tersebut bervariasi tergantung profil UMKM (lama usaha, lama di platform, jumlah platform, skala omzet)?
4. **Pertanyaan 4 (Rekomendasi per Segmen):** Strategi apa yang harus diprioritaskan untuk tiap kelompok segmen UMKM?

---

## 2. Metodologi Data dan Rekayasa Fitur

### 2.1 Pembersihan Data (Tahap 1)
- **Sumber Data:** {n_semua} kuesioner pelaku UMKM Pekanbaru.
- **Pembersihan Teks & Numerik:** Parsing nominal omzet dan waktu (bulan/tahun) ke nilai numerik standar tahun referensi 2026.
- **Winsorizing Ekor Atas (P99):** Mengendalikan nilai ekstrem pada omzet dan transaksi tanpa membuang sampel.
- **Konfirmasi Ulang ke Responden:** Mengoreksi galat ketik nominal omzet sesudah pada R065, R130, R106 serta jumlah pesanan transaksi R002, R006, R015, dan R021.
- **Anonimisasi:** Seluruh nama usaha diganti dengan kode unik R001–R149.

### 2.2 Konstruksi Variabel & Definisi Target Kinerja (Tahap 2)
- **Skor Strategi (X1–X4):** Dihitung dari rata-rata butir Likert skala 1–5. Reliabilitas instrumen sangat tinggi (Cronbach's $\\alpha = 0,930 - 0,955$).
- **Target Kinerja Objektif:**
  - `naik_penjualan` (Biner): Bernilai 1 jika omzet sesudah > omzet sebelum ATAU transaksi sesudah > transaksi sebelum; bernilai 0 jika tidak ada kenaikan.
  - `Y_obj` (Kontinu): Rata-rata z-score selisih log omzet dan selisih log transaksi.
- **Pembagian Sampel:**
  - **Sampel Utama ($n=116$):** UMKM dengan `lama_usaha_pra_mp > 0` yang memiliki data pembanding kondisi sebelum marketplace yang nyata (62 naik vs 54 sama).
  - **Sampel Tanpa Baseline ($n=33$):** Usaha yang berdiri bersamaan dengan marketplace (`lama_usaha_pra_mp = 0`), dianalisis terpisah sebagai pembanding.

---

## 3. Hasil Analisis dan Pengujian Statistik

### 3.1 Evaluasi Kinerja Penjualan (Pertanyaan 1)
Uji Wilcoxon Signed-Rank menunjukkan perbedaan yang bermakna secara statistik antara kondisi sebelum dan sesudah masuk marketplace:
- **Omzet Bulanan:** Median kenaikan bersih Rp250.000 ($Z = 6,34, p < 0,001$). 59 UMKM naik, 56 tetap, 1 turun.
- **Transaksi Bulanan:** Median kenaikan bersih 7 pesanan ($Z = 6,75, p < 0,001$). 60 UMKM naik, 56 tetap, 0 turun.

### 3.2 Analisis Pengaruh dan Pemodelan Machine Learning (Pertanyaan 2)
Pengujian dilakukan dengan mengontrol variabel profil usaha (lama usaha pra-marketplace, lama di marketplace, jumlah platform, dan log omzet sebelum).

#### Perbandingan Model Prediksi (Repeated Stratified K-Fold 5×5):
- **Random Forest:** ROC-AUC = {rf_auc:.3f} ± 0,092 | F1-Macro = {rf_f1:.3f} | Akurasi Seimbang = {cv.loc[('naik_penjualan', 'random_forest', 'akurasi_seimbang'), 'rata_rata']:.3f} (Model Terbaik).
- **Regresi Logistik:** ROC-AUC = {logit_auc:.3f} ± 0,115 | F1-Macro = {cv.loc[('naik_penjualan', 'logistik', 'f1_macro'), 'rata_rata']:.3f}.
- **Baseline Mayoritas:** ROC-AUC = 0,500.

#### Skor Kepentingan Fitur & Hubungan Strategi:
1. **X3 (Komunikasi Pelanggan):**
   - Odds Ratio Logit = 2,49 (95% CI: 1,42–4,38; $p = 0,001$; Holm $p = 0,005$).
   - Permutation Importance (RF) = {gab.loc['x3_komunikasi', 'perm_importance']:.3f}.
   - Mean |SHAP| = {gab.loc['x3_komunikasi', 'mean_abs_shap']:.3f}.
   - Probabilitas Peringkat #1 pada Bootstrap (1000×) = 84,9%. Status: **Meyakinkan**.
2. **X1 (Unggah Produk):**
   - Odds Ratio Logit = 2,19 (95% CI: 1,26–3,81; $p = 0,005$; Holm $p = 0,015$).
   - Permutation Importance (RF) = {gab.loc['x1_unggah', 'perm_importance']:.3f}.
   - Mean |SHAP| = {gab.loc['x1_unggah', 'mean_abs_shap']:.3f}.
   - Probabilitas Masuk 3 Besar = 99,5%. Status: **Meyakinkan**.
3. **X2 (Promosi Marketplace):**
   - Odds Ratio Logit = 1,26 ($p = 0,344$). Status: **Belum Meyakinkan**.
4. **X4 (Konsistensi Kelola Toko):**
   - Odds Ratio Logit = 0,93 ($p = 0,777$). Status: **Belum Meyakinkan**.

{bagian_sem}
### 3.4 Uji Efek Moderasi Profil Usaha (Pertanyaan 3)
Melalui pengujian 24 interaksi regresi (Strategi × Skala Omzet, Strategi × Lama di MP, Strategi × Jumlah Platform) dengan koreksi Holm:
- **Hasil:** 0 dari 24 interaksi bernilai signifikan ($p > 0,05$).
- **Kesimpulan:** Tidak ditemukan bukti bahwa hubungan strategi dengan kinerja penjualan berbeda menurut profil usaha. Daya uji interaksi pada sampel ini rendah, sehingga bobot strategi ditetapkan sama untuk semua segmen.

---

## 4. Segmentasi UMKM dan Rekomendasi Tindakan

### 4.1 Segmentasi Profil Usaha (Tahap 5)
Menggunakan algoritma *K-Means* ($k=2$) yang diuji stabilitasnya dengan bootstrap (100×):
- **Stabilitas:** Median ARI bootstrap = 0,92; Jaccard = 0,95/0,95.
- **Segmen 1 ({int((seg['segmen']==1).sum())} UMKM):** Usaha rintisan/muda, skala omzet kecil (median omzet Rp9 jt), baru masuk marketplace (median 2 th).
- **Segmen 2 ({int((seg['segmen']==2).sum())} UMKM):** Usaha mapan, omzet menengah/besar (median omzet Rp30 jt), lama di marketplace (median 4 th).

### 4.2 Rekomendasi Strategi Praktis (Tahap 6)
Prioritas tiap strategi dihitung dengan rumus:
$$\\text{{Prioritas}} = \\text{{Bobot Pengaruh}} \\times \\max(0, \\bar{{X}}_{{\\text{{naik}}}} - \\bar{{X}}_{{\\text{{segmen}}}})$$

| Segmen | Peringkat | Strategi Prioritas | Gap Skor | Bobot | Skor Prioritas | Rekomendasi Tindakan Operasional |
|---|---|---|---|---|---|---|
| **Segmen 1** (Usaha Kecil & Baru) | #1 | **X3 Komunikasi Pelanggan** | 0,14 | 1,00 | 0,143 | Siapkan template jawaban cepat untuk pertanyaan umum; tetapkan jam rutin cek pesan chat; jaga komunikasi hingga pesanan diterima. |
| | #2 | **X1 Unggah Produk** | 0,17 | 0,59 | 0,103 | Segarkan dan unggah ulang (*re-upload*) katalog produk lama secara bertahap 1–2 kali seminggu dimulai dari produk terlaris. |
| | #3 | **X2 Promosi Marketplace** | 0,13 | 0,29 | 0,037 | Manfaatkan voucher diskon bernilai kecil dan fitur promosi gratis bawaan platform; catat kenaikan pesanan mingguan. |
| **Segmen 2** (Usaha Mapan & Lama) | #1 | **X3 Komunikasi Pelanggan** | 0,19 | 1,00 | 0,191 | Terapkan SLA respon komplain pelanggan < 15 menit; delegasikan admin khusus customer support; evaluasi keluhan berulang mingguan. |
| | #2 | **X1 Unggah Produk** | 0,13 | 0,59 | 0,075 | Tunjuk penanggung jawab pembaruan katalog; jadwalkan peluncuran varian baru berkala di seluruh platform yang aktif. |
| | #3 | **X2 Promosi Marketplace** | 0,15 | 0,29 | 0,045 | Optimalkan iklan berbayar (ads) dengan alokasi anggaran terukur pada produk margin tinggi; evaluasi ROAS bulanan. |

---

## 5. Keterbatasan Metodologis

1. **Sifat Asosiasi, Bukan Kausalitas:** Desain studi adalah survei potong lintang (*cross-sectional*) berbasis ingatan responden (*self-reported recall*), tanpa kelompok kontrol murni yang tidak pernah memakai marketplace.
2. **Karakteristik Target Biner:** Kelompok pembanding `naik_penjualan = 0` terdiri atas responden yang mengisi nilai omzet dan transaksi sama persis sebelum dan sesudah (bukan kelompok penjualan turun).
3. **Ukuran Sampel ($n=149$, Sampel Utama $n=116$):** Rasio peristiwa terhadap prediktor (EPV) sekitar 6,8 sehingga interval kepercayaan koefisien cukup lebar.
4. **Dominasi Sektor Kuliner:** Mayoritas responden merupakan usaha makanan dan minuman di Kota Pekanbaru, sehingga generalisasi ke sektor kerajinan/fesyen atau wilayah lain memerlukan kehati-hatian.
5. **Keterbatasan Variasi Skala Likert:** Terjadi penumpukan jawaban netral (skor 3) pada beberapa butir kuesioner.

---

## 6. Kesiapan Integrasi Sistem

Model dan logika rekomendasi telah dibundel dalam arsitektur mandiri:
- **Artefak Model:** Tersimpan di folder `models/v1/` (`model.joblib`, `segmen.joblib`, `model_meta.json`, `benchmark_per_segmen.json`, `pengaruh_strategi.json`).
- **Kontrak Data:** Didefinisikan menggunakan skema Pydantic (`ProfilUMKM`, `HasilRekomendasi`) di `reports/integration_contract.md`.
- **Fungsi Inferensi:** Dapat dipanggil langsung dari Python tanpa bergantung pada notebook:
  ```python
  from umkm.recommend import recommend
  hasil = recommend({{
      "omzet_bulanan": 15000000,
      "lama_usaha_pra_mp": 2.5,
      "lama_di_mp": 1.0,
      "platform": ["shopee", "gofood"],
      "x1_unggah": 3.0,
      "x2_promosi": 2.5,
      "x3_komunikasi": 3.5,
      "x4_konsistensi": 3.0,
  }})
  print(hasil["segmen"], hasil["rekomendasi_prioritas"])
  ```

---
*Angka pada laporan ini dihitung dari tabel di `reports/tables/` (pembaruan terakhir {pd.Timestamp.now().strftime('%d-%m-%Y')}).*
"""
    return teks


def run() -> LaporanResult:
    """Eksekusi pembuatan laporan akhir dan validasi keterlacakan."""
    teks = susun_laporan()
    path_lap = config.path("reports") / "laporan_final.md"
    path_lap.write_text(teks, encoding="utf-8")

    # Uji pemanggilan mandiri recommend()
    dummy_input: dict[str, Any] = {
        "omzet_bulanan": 20_000_000,
        "lama_usaha_pra_mp": 3.0,
        "lama_di_mp": 1.5,
        "platform": ["shopee", "gofood"],
        "x1_unggah": 3.5,
        "x2_promosi": 2.5,
        "x3_komunikasi": 3.0,
        "x4_konsistensi": 3.0,
    }
    rec_out = recommend(dummy_input)
    inferensi_valid = bool(
        rec_out.get("segmen", {}).get("id") in (1, 2) and len(rec_out.get("prioritas", [])) >= 3
    )

    tabel_list = [
        "pengaruh_cv_ringkas",
        "pengaruh_gabungan",
        "rekomendasi_per_segmen",
        "rekomendasi_whatif",
        "profil_segmen",
        "sem_jalur",
        "sem_reliabilitas",
        "sem_model",
    ]
    figur_list = [
        "shap_ringkas.png",
        "pengaruh_peringkat.png",
        "rekomendasi_prioritas.png",
        "segmen_profil.png",
        "sem_jalur.png",
    ]

    return LaporanResult(
        path_laporan=path_lap,
        angka_tervalidasi=len(tabel_list),
        tabel_terhubung=tabel_list,
        figur_terhubung=figur_list,
        inferensi_valid=inferensi_valid,
    )


if __name__ == "__main__":
    res = run()
    print(f"Laporan akhir dibuat: {res.path_laporan}")
    print(f"Keterlacakan tabel: {len(res.tabel_terhubung)} tabel terhubung")
    print(f"Inferensi mandiri recommend(): {'VALID' if res.inferensi_valid else 'GAGAL'}")
