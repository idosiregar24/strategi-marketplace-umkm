# Kontrak Integrasi: `recommend(profil) -> dict`

Dibuat ulang oleh Tahap 6 (`python -m umkm.pipeline --stage 6`) pada 2026-10-30T15:54:36. Versi artefak: **v1**. Aplikasi/API belum dibangun (D09); dokumen ini menjelaskan cara sistem lain memanggil kode yang sudah ada.

## Ringkas

- Pintu masuk tunggal: `umkm.recommend.recommend(profil: dict, dir_model=None) -> dict`.
- Hanya memuat artefak di `models/v1/` (lewat config + env `UMKM_BASE_DIR`); tidak membaca data survei, xlsx, atau state notebook.
- Masukan divalidasi `umkm.schemas.ProfilUMKM`; keluaran mengikuti `umkm.schemas.HasilRekomendasi` (dict/list/angka/teks, siap `json.dumps`).
- Dependensi minimal: pandas, numpy, scikit-learn, joblib, pydantic, pyyaml (`pip install -e .`, tanpa `[analysis]`).

## Cara memakai

```python
from umkm.recommend import recommend

hasil = recommend({
    "id_umkm": "contoh_C_sketsa_kontrak",
    "omzet_bulanan": 18000000,
    "lama_usaha_pra_mp": 3,
    "lama_di_mp": 2,
    "platform": ["gofood", "shopee"],
    "x1_unggah": 2.0,
    "x2_promosi": 2.5,
    "x3_komunikasi": 4.2,
    "x4_konsistensi": 3.0,
})
print(hasil["prioritas"][0]["strategi"])
```

Dari terminal (skrip terpisah, tanpa notebook): `python -m umkm.recommend profil.json` atau `cat profil.json | python -m umkm.recommend -`. Folder artefak lain: `--dir-model path/ke/models/v1`.

## Skema masukan (`ProfilUMKM`)

| field | tipe | wajib | rentang | keterangan |
|---|---|---|---|---|
| id_umkm | string / null | tidak | - | Penanda opsional; dikembalikan apa adanya |
| omzet_bulanan | number | ya | >= 0 | Omzet per bulan (Rp). Di data latih: omzet sebelum masuk marketplace |
| lama_usaha_pra_mp | number | ya | >= 0, <= 100 | Lama usaha sebelum masuk marketplace (tahun) |
| lama_di_mp | number | ya | >= 0, <= 100 | Lama berjualan di marketplace (tahun) |
| platform | list[gofood / grabfood / shopee / maxim / tiktok] | ya | min item 1 | Platform yang dipakai (huruf kecil, tanpa duplikat) |
| x1_unggah | number | ya | >= 1, <= 5 | Rata-rata 4 butir X1 unggah produk |
| x2_promosi | number | ya | >= 1, <= 5 | Rata-rata 4 butir X2 promosi |
| x3_komunikasi | number | ya | >= 1, <= 5 | Rata-rata 5 butir X3 komunikasi pelanggan |
| x4_konsistensi | number | ya | >= 1, <= 5 | Rata-rata 5 butir X4 konsistensi toko |


Field lain ditolak (`extra = forbid`) agar salah ketik nama field langsung ketahuan. `platform` dinormalkan (huruf kecil, tanpa spasi, tanpa duplikat); platform di luar lima nilai itu ditolak. `jumlah_platform` dihitung dari panjang `platform`.

### Rentang data latih

| field | min | maks |
|---|---|---|
| omzet_bulanan | 0 | 330.000.000 |
| lama_usaha_pra_mp | 0 | 22 |
| lama_di_mp | 0 | 13 |
| jumlah_platform | 1 | 4 |


Nilai di luar rentang tetap diproses, tetapi keluaran memberi `peringatan`. Batas kuartil omzet (skala omzet untuk segmen): Rp9.000.000, Rp18.000.000, Rp30.000.000. Di data latih, omzet = omzet per bulan SEBELUM masuk marketplace; untuk UMKM baru pakai omzet per bulan saat ini.

## Skema keluaran (`HasilRekomendasi`)

| field | tipe | wajib | rentang | keterangan |
|---|---|---|---|---|
| versi_model | string | ya | - | - |
| id_umkm | string / null | tidak | - | - |
| segmen | Segmen | ya | - | - |
| skor | list[SkorStrategi] | ya | - | - |
| prioritas | list[Prioritas] | ya | - | - |
| peringatan | list[string] | ya | - | - |
| catatan | string | ya | - | - |


Tiap elemen `skor` (`SkorStrategi`) dan `prioritas` (`Prioritas`):

| field | tipe | wajib | rentang | keterangan |
|---|---|---|---|---|
| strategi | string | ya | - | - |
| nama | string | ya | - | - |
| skor | number | ya | >= 1, <= 5 | - |
| benchmark | number | ya | >= 1, <= 5 | - |
| gap | number | ya | >= 0 | - |
| bobot | number | ya | >= 0, <= 1 | - |
| prioritas | number | ya | >= 0 | - |
| peringkat | integer | ya | >= 1 | - |
| hubungan_meyakinkan | boolean | ya | - | - |
| selisih_prediksi_plus1 | number / null | tidak | - | Ilustrasi model: selisih peluang prediksi (poin persen) bila skor +1 |
| fokus_butir | list[string] | ya | - | - |
| alasan | string | ya | - | - |
| tindakan | string | ya | - | - |


- `skor` selalu berisi 4 strategi; `prioritas` berisi 0-3 strategi dengan prioritas > 0, urut `peringkat`. Daftar kosong = semua skor sudah setara atau di atas benchmark (ada kalimat di `peringatan`).
- `gap` = max(0, benchmark - skor); `prioritas` = `bobot` x `gap`. `benchmark` = rata-rata skor UMKM yang melaporkan kenaikan penjualan di segmen yang sama (D28).
- `selisih_prediksi_plus1` = ilustrasi model: selisih peluang prediksi naik penjualan (poin persen) bila skor strategi itu +1 (maks 5). Bukan perkiraan dampak.
- `fokus_butir` = kode butir kuesioner (lihat data_dictionary.md) dengan gap terbesar di segmen itu; `tindakan` menerjemahkannya ke langkah konkret.
- Teks (`alasan`, `tindakan`, `catatan`) berasal dari templat di `umkm/recommend.py` dan boleh diganti/diterjemahkan oleh sistem tujuan.

## Galat

- Masukan tidak sah -> `pydantic.ValidationError` (turunan `ValueError`); pesannya menyebut field dan aturan yang dilanggar. Bungkus API sebaiknya mengembalikan HTTP 422.
- Artefak tidak ada -> `FileNotFoundError` dengan petunjuk menjalankan Tahap 6.
- Versi scikit-learn berbeda dari saat artefak dibuat -> tetap jalan, ada `peringatan`.

## Artefak `models/v1/`

| Berkas | Isi |
|---|---|
| `segmen.joblib` | dict: `pipa` (StandardScaler + K-Means), `urutan` (label -> nomor segmen), `fitur`, `fitur_log1p` |
| `model.joblib` | dict: `model` (random_forest, target naik_penjualan), `fitur`, `nama`, `target` |
| `benchmark_per_segmen.json` | batas kuartil omzet, n prioritas, per segmen: nama, konteks, n, benchmark, skor rata-rata, median, butir fokus |
| `pengaruh_strategi.json` | bobot, skor pengaruh, P(koef > 0), meyakinkan, OR, p (Tahap 4) |
| `model_meta.json` | tanggal, seed, versi pustaka, fitur, metrik CV, rentang latih, hash data |

Memuat: `umkm.recommend.muat_artefak(str(path))` (di-cache per folder). Berkas `.joblib` adalah pickle: hanya muat artefak yang dibuat pipeline proyek ini sendiri. Perubahan model atau data = folder versi baru (`v2/`), ubah `recommendation.versi_model` di config.yaml. `*.joblib` tidak masuk git (`.gitignore`); buat ulang dengan Tahap 6.

### Versi pustaka saat artefak dibuat

python 3.11.9 | pandas 3.0.6 | numpy 2.4.6 | scikit-learn 1.9.1 | joblib 1.6.0 | pydantic 2.14.1

### Metrik CV model (naik_penjualan, RepeatedStratifiedKFold 5x5)

| model | f1_macro | akurasi_seimbang | auc |
|---|---|---|---|
| dummy_mayoritas | 0.348 | 0.500 | 0.500 |
| logistik | 0.618 | 0.622 | 0.717 |
| random_forest | 0.699 | 0.706 | 0.735 |


### Hash data latih (SHA-256)

- `data_features.csv`: `fb7fde3f26e436f0a9aa86d74637ed9b2a16d6b3bc15223993354adc9d294631`
- `data_segmen.csv`: `fccdf57c6d4cb475d084a92cf58e80c5a575c1dcc35ca6a1cf6722da7c6c66cb`

## Contoh

### `contoh_A_kecil_baru`

Masukan:

```json
{
  "id_umkm": "contoh_A_kecil_baru",
  "omzet_bulanan": 6000000,
  "lama_usaha_pra_mp": 1,
  "lama_di_mp": 1,
  "platform": [
    "gofood"
  ],
  "x1_unggah": 2.0,
  "x2_promosi": 2.25,
  "x3_komunikasi": 3.0,
  "x4_konsistensi": 3.0
}
```

Keluaran:

```json
{
  "versi_model": "v1",
  "id_umkm": "contoh_A_kecil_baru",
  "segmen": {
    "id": 1,
    "nama": "Omzet kecil, usaha muda, baru di marketplace"
  },
  "skor": [
    {
      "strategi": "x1_unggah",
      "nama": "X1 Unggah produk",
      "skor": 2.0,
      "benchmark": 2.5093,
      "gap": 0.5093,
      "bobot": 0.5898,
      "prioritas": 0.3004
    },
    {
      "strategi": "x2_promosi",
      "nama": "X2 Promosi",
      "skor": 2.25,
      "benchmark": 2.5185,
      "gap": 0.2685,
      "bobot": 0.2947,
      "prioritas": 0.0791
    },
    {
      "strategi": "x3_komunikasi",
      "nama": "X3 Komunikasi pelanggan",
      "skor": 3.0,
      "benchmark": 3.6074,
      "gap": 0.6074,
      "bobot": 1.0,
      "prioritas": 0.6074
    },
    {
      "strategi": "x4_konsistensi",
      "nama": "X4 Konsistensi toko",
      "skor": 3.0,
      "benchmark": 3.237,
      "gap": 0.237,
      "bobot": 0.1,
      "prioritas": 0.0237
    }
  ],
  "prioritas": [
    {
      "strategi": "x3_komunikasi",
      "nama": "X3 Komunikasi pelanggan",
      "skor": 3.0,
      "benchmark": 3.6074,
      "gap": 0.6074,
      "bobot": 1.0,
      "prioritas": 0.6074,
      "peringkat": 1,
      "hubungan_meyakinkan": true,
      "selisih_prediksi_plus1": 16.53,
      "fokus_butir": [
        "x3_komunikasi_5",
        "x3_komunikasi_1"
      ],
      "alasan": "Skor X3 Komunikasi pelanggan UMKM ini 3,00 berada 0,61 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 1: 3,61); strategi ini termasuk yang paling berhubungan dengan laporan kenaikan penjualan (bobot 1,00).",
      "tindakan": "Utamakan menjaga komunikasi sampai pesanan diterima pelanggan dan membalas chat pelanggan dengan cepat. Siapkan template jawaban untuk pertanyaan yang sering muncul dan tetapkan jam cek chat beberapa kali sehari."
    },
    {
      "strategi": "x1_unggah",
      "nama": "X1 Unggah produk",
      "skor": 2.0,
      "benchmark": 2.5093,
      "gap": 0.5093,
      "bobot": 0.5898,
      "prioritas": 0.3004,
      "peringkat": 2,
      "hubungan_meyakinkan": true,
      "selisih_prediksi_plus1": 13.77,
      "fokus_butir": [
        "x1_unggah_3",
        "x1_unggah_4"
      ],
      "alasan": "Skor X1 Unggah produk UMKM ini 2,00 berada 0,51 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 1: 2,51); strategi ini termasuk yang paling berhubungan dengan laporan kenaikan penjualan (bobot 0,59).",
      "tindakan": "Utamakan mengunggah ulang produk lama agar tetap terlihat pembeli dan memantau produk yang sepi dan perlu diunggah ulang. Mulai dari jadwal tetap 1-2 kali seminggu dan lengkapi katalog secara bertahap, dimulai dari produk terlaris."
    },
    {
      "strategi": "x2_promosi",
      "nama": "X2 Promosi",
      "skor": 2.25,
      "benchmark": 2.5185,
      "gap": 0.2685,
      "bobot": 0.2947,
      "prioritas": 0.0791,
      "peringkat": 3,
      "hubungan_meyakinkan": false,
      "selisih_prediksi_plus1": 11.25,
      "fokus_butir": [
        "x2_promosi_4",
        "x2_promosi_3"
      ],
      "alasan": "Skor X2 Promosi UMKM ini 2,25 berada 0,27 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 1: 2,52); hubungannya dengan laporan kenaikan penjualan belum meyakinkan, sehingga bobotnya diturunkan menjadi 0,29.",
      "tindakan": "Utamakan mengevaluasi hasil tiap promosi (pesanan sebelum vs selama promo) dan memanfaatkan fitur promosi bawaan marketplace. Mulai dari fitur promosi gratis dari platform dan voucher bernilai kecil; catat jumlah pesanan selama promo untuk dibandingkan dengan minggu biasa."
    }
  ],
  "peringatan": [],
  "catatan": "Prioritas disusun dari pola asosiasi pada 149 UMKM responden survei satu waktu, bukan jaminan hasil. Benchmark = rata-rata skor UMKM yang melaporkan kenaikan penjualan di segmen yang sama."
}
```

### `contoh_B_besar_mapan`

Masukan:

```json
{
  "id_umkm": "contoh_B_besar_mapan",
  "omzet_bulanan": 50000000,
  "lama_usaha_pra_mp": 8,
  "lama_di_mp": 5,
  "platform": [
    "gofood",
    "grabfood",
    "shopee"
  ],
  "x1_unggah": 3.0,
  "x2_promosi": 2.0,
  "x3_komunikasi": 3.4,
  "x4_konsistensi": 3.6
}
```

Keluaran:

```json
{
  "versi_model": "v1",
  "id_umkm": "contoh_B_besar_mapan",
  "segmen": {
    "id": 2,
    "nama": "Omzet besar, usaha mapan, lama di marketplace"
  },
  "skor": [
    {
      "strategi": "x1_unggah",
      "nama": "X1 Unggah produk",
      "skor": 3.0,
      "benchmark": 2.5143,
      "gap": 0.0,
      "bobot": 0.5898,
      "prioritas": 0.0
    },
    {
      "strategi": "x2_promosi",
      "nama": "X2 Promosi",
      "skor": 2.0,
      "benchmark": 2.5143,
      "gap": 0.5143,
      "bobot": 0.2947,
      "prioritas": 0.1516
    },
    {
      "strategi": "x3_komunikasi",
      "nama": "X3 Komunikasi pelanggan",
      "skor": 3.4,
      "benchmark": 3.7486,
      "gap": 0.3486,
      "bobot": 1.0,
      "prioritas": 0.3486
    },
    {
      "strategi": "x4_konsistensi",
      "nama": "X4 Konsistensi toko",
      "skor": 3.6,
      "benchmark": 3.4,
      "gap": 0.0,
      "bobot": 0.1,
      "prioritas": 0.0
    }
  ],
  "prioritas": [
    {
      "strategi": "x3_komunikasi",
      "nama": "X3 Komunikasi pelanggan",
      "skor": 3.4,
      "benchmark": 3.7486,
      "gap": 0.3486,
      "bobot": 1.0,
      "prioritas": 0.3486,
      "peringkat": 1,
      "hubungan_meyakinkan": true,
      "selisih_prediksi_plus1": 29.6,
      "fokus_butir": [
        "x3_komunikasi_4",
        "x3_komunikasi_1"
      ],
      "alasan": "Skor X3 Komunikasi pelanggan UMKM ini 3,40 berada 0,35 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 2: 3,75); strategi ini termasuk yang paling berhubungan dengan laporan kenaikan penjualan (bobot 1,00).",
      "tindakan": "Utamakan menanggapi keluhan atau komplain pelanggan segera dan membalas chat pelanggan dengan cepat. Bagi tugas membalas chat dan komplain (per platform atau per shift) dengan batas waktu respons; tinjau komplain yang berulang setiap minggu."
    },
    {
      "strategi": "x2_promosi",
      "nama": "X2 Promosi",
      "skor": 2.0,
      "benchmark": 2.5143,
      "gap": 0.5143,
      "bobot": 0.2947,
      "prioritas": 0.1516,
      "peringkat": 2,
      "hubungan_meyakinkan": false,
      "selisih_prediksi_plus1": 14.12,
      "fokus_butir": [
        "x2_promosi_3",
        "x2_promosi_4"
      ],
      "alasan": "Skor X2 Promosi UMKM ini 2,00 berada 0,51 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 2: 2,51); hubungannya dengan laporan kenaikan penjualan belum meyakinkan, sehingga bobotnya diturunkan menjadi 0,29.",
      "tindakan": "Utamakan memanfaatkan fitur promosi bawaan marketplace dan mengevaluasi hasil tiap promosi (pesanan sebelum vs selama promo). Uji iklan berbayar dengan anggaran terbatas pada produk andalan; bandingkan hasil antar-platform setiap bulan dan hentikan promosi yang tidak menambah pesanan."
    }
  ],
  "peringatan": [],
  "catatan": "Prioritas disusun dari pola asosiasi pada 149 UMKM responden survei satu waktu, bukan jaminan hasil. Benchmark = rata-rata skor UMKM yang melaporkan kenaikan penjualan di segmen yang sama."
}
```

### `contoh_C_sketsa_kontrak`

Masukan:

```json
{
  "id_umkm": "contoh_C_sketsa_kontrak",
  "omzet_bulanan": 18000000,
  "lama_usaha_pra_mp": 3,
  "lama_di_mp": 2,
  "platform": [
    "gofood",
    "shopee"
  ],
  "x1_unggah": 2.0,
  "x2_promosi": 2.5,
  "x3_komunikasi": 4.2,
  "x4_konsistensi": 3.0
}
```

Keluaran:

```json
{
  "versi_model": "v1",
  "id_umkm": "contoh_C_sketsa_kontrak",
  "segmen": {
    "id": 2,
    "nama": "Omzet besar, usaha mapan, lama di marketplace"
  },
  "skor": [
    {
      "strategi": "x1_unggah",
      "nama": "X1 Unggah produk",
      "skor": 2.0,
      "benchmark": 2.5143,
      "gap": 0.5143,
      "bobot": 0.5898,
      "prioritas": 0.3033
    },
    {
      "strategi": "x2_promosi",
      "nama": "X2 Promosi",
      "skor": 2.5,
      "benchmark": 2.5143,
      "gap": 0.0143,
      "bobot": 0.2947,
      "prioritas": 0.0042
    },
    {
      "strategi": "x3_komunikasi",
      "nama": "X3 Komunikasi pelanggan",
      "skor": 4.2,
      "benchmark": 3.7486,
      "gap": 0.0,
      "bobot": 1.0,
      "prioritas": 0.0
    },
    {
      "strategi": "x4_konsistensi",
      "nama": "X4 Konsistensi toko",
      "skor": 3.0,
      "benchmark": 3.4,
      "gap": 0.4,
      "bobot": 0.1,
      "prioritas": 0.04
    }
  ],
  "prioritas": [
    {
      "strategi": "x1_unggah",
      "nama": "X1 Unggah produk",
      "skor": 2.0,
      "benchmark": 2.5143,
      "gap": 0.5143,
      "bobot": 0.5898,
      "prioritas": 0.3033,
      "peringkat": 1,
      "hubungan_meyakinkan": true,
      "selisih_prediksi_plus1": 10.57,
      "fokus_butir": [
        "x1_unggah_3",
        "x1_unggah_1"
      ],
      "alasan": "Skor X1 Unggah produk UMKM ini 2,00 berada 0,51 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 2: 2,51); strategi ini termasuk yang paling berhubungan dengan laporan kenaikan penjualan (bobot 0,59).",
      "tindakan": "Utamakan mengunggah ulang produk lama agar tetap terlihat pembeli dan menjadwalkan unggah produk rutin setiap minggu. Tunjuk penanggung jawab katalog; segarkan produk lama secara bergilir di setiap platform yang dipakai dan pantau produk yang sepi tiap minggu."
    },
    {
      "strategi": "x4_konsistensi",
      "nama": "X4 Konsistensi toko",
      "skor": 3.0,
      "benchmark": 3.4,
      "gap": 0.4,
      "bobot": 0.1,
      "prioritas": 0.04,
      "peringkat": 2,
      "hubungan_meyakinkan": false,
      "selisih_prediksi_plus1": -2.02,
      "fokus_butir": [
        "x4_konsistensi_2",
        "x4_konsistensi_5"
      ],
      "alasan": "Skor X4 Konsistensi toko UMKM ini 3,00 berada 0,40 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 2: 3,40); hubungannya dengan laporan kenaikan penjualan belum meyakinkan, sehingga bobotnya diturunkan menjadi 0,10.",
      "tindakan": "Utamakan memperbarui stok produk secara rutin dan tetap mengelola toko saat sedang sibuk. Samakan stok, harga, dan foto di semua platform dengan daftar periksa harian; tunjuk pengganti agar toko tetap dikelola saat sibuk."
    },
    {
      "strategi": "x2_promosi",
      "nama": "X2 Promosi",
      "skor": 2.5,
      "benchmark": 2.5143,
      "gap": 0.0143,
      "bobot": 0.2947,
      "prioritas": 0.0042,
      "peringkat": 3,
      "hubungan_meyakinkan": false,
      "selisih_prediksi_plus1": 7.4,
      "fokus_butir": [
        "x2_promosi_3",
        "x2_promosi_4"
      ],
      "alasan": "Skor X2 Promosi UMKM ini 2,50 berada 0,01 poin di bawah rata-rata UMKM yang penjualannya naik pada segmen yang sama (segmen 2: 2,51); hubungannya dengan laporan kenaikan penjualan belum meyakinkan, sehingga bobotnya diturunkan menjadi 0,29.",
      "tindakan": "Utamakan memanfaatkan fitur promosi bawaan marketplace dan mengevaluasi hasil tiap promosi (pesanan sebelum vs selama promo). Uji iklan berbayar dengan anggaran terbatas pada produk andalan; bandingkan hasil antar-platform setiap bulan dan hentikan promosi yang tidak menambah pesanan."
    }
  ],
  "peringatan": [],
  "catatan": "Prioritas disusun dari pola asosiasi pada 149 UMKM responden survei satu waktu, bukan jaminan hasil. Benchmark = rata-rata skor UMKM yang melaporkan kenaikan penjualan di segmen yang sama."
}
```

## Jalur integrasi nanti (belum dikerjakan)

- Sistem Python: `pip install` paket `umkm` lalu panggil `recommend()` langsung.
- Sistem non-Python: bungkus dengan FastAPI (`POST /recommend` -> `recommend(body)`, `GET /health` -> versi artefak dari `model_meta.json`).
- Semua jalur memakai kontrak dan artefak yang sama.
