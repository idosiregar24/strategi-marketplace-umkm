# Ringkasan Tahap 5: Segmen Kondisi UMKM

Dibuat oleh `umkm.segmentation` pada 2026-10-30 11:56. 149 UMKM dikelompokkan menurut kondisi usaha (skala omzet, lama usaha sebelum marketplace, lama di marketplace, jumlah platform). Skor strategi dan kinerja tidak dipakai untuk membentuk segmen (D27).

## Hasil: 2 segmen

**Segmen 1: Omzet kecil, usaha muda, baru di marketplace** berisi 74 UMKM (50%). Median omzet sebelum marketplace Rp9,0 jt (kuartil Rp5,2 jt sampai Rp15,0 jt); kuartil omzet terbanyak Q1 (53%). Median lama usaha sebelum masuk marketplace 1,0 tahun dan lama di marketplace 2,0 tahun; 27 UMKM (36%) berdiri bersamaan dengan masuk marketplace (tanpa baseline). Rata-rata memakai 2,22 platform (30% hanya satu); platform terbanyak Shopee 77%, GoFood 74% dan GrabFood 59%. Skor strategi rata-rata: X1 2,33, X2 2,39, X3 3,46, X4 3,11. Di sampel utama (47 UMKM), 57% (27 UMKM) melaporkan kenaikan penjualan, rata-rata y_obj 0,14. Keanggotaan segmen ini sangat stabil saat data di-bootstrap (Jaccard rata-rata 0,94).

**Segmen 2: Omzet besar, usaha mapan, lama di marketplace** berisi 75 UMKM (50%). Median omzet sebelum marketplace Rp30,0 jt (kuartil Rp20,5 jt sampai Rp60,0 jt); kuartil omzet terbanyak Q4 (45%). Median lama usaha sebelum masuk marketplace 5,0 tahun dan lama di marketplace 4,0 tahun; 6 UMKM (8%) berdiri bersamaan dengan masuk marketplace (tanpa baseline). Rata-rata memakai 1,88 platform (47% hanya satu); platform terbanyak GoFood 76%, Shopee 57% dan GrabFood 48%. Skor strategi rata-rata: X1 2,39, X2 2,36, X3 3,56, X4 3,27. Di sampel utama (69 UMKM), 51% (35 UMKM) melaporkan kenaikan penjualan, rata-rata y_obj -0,09. Keanggotaan segmen ini sangat stabil saat data di-bootstrap (Jaccard rata-rata 0,95).

## Seberapa kuat dan stabil segmennya

- Silhouette 0,247: pemisahan sangat lemah (Kaufman dan Rousseeuw: <= 0,25 berarti tidak ada struktur kelompok yang substansial). UMKM tidak membentuk kelompok yang terpisah tegas; segmen menggambarkan ujung-ujung rentang kondisi usaha.
- Stabil saat data diacak ulang (bootstrap 100x): median ARI 0,92, Jaccard per segmen 0,94 dan 0,95. k lain (3, 4, 5, 6) median ARI 0,47-0,59.
- Bila skor strategi X1-X4 ikut dijadikan fitur, struktur makin lemah (silhouette 0,13) dan tidak ada jumlah segmen yang stabil.

## Apa artinya untuk rekomendasi (Tahap 6)

Antar-segmen tidak ada beda bermakna pada X1 unggah produk, X2 promosi, X3 komunikasi pelanggan, X4 konsistensi toko, persepsi kinerja, y_obj, pelanggan baru (log) dan proporsi naik penjualan setelah koreksi Holm (contoh: proporsi naik penjualan 57% dan 51%, p = 0,570). Jadi segmen membedakan kondisi usaha, bukan tingkat strategi atau kinerja. Benchmark per segmen di Tahap 6 dihitung dari 27 UMKM naik di segmen 1 dan 35 UMKM naik di segmen 2; karena skor strategi kedua segmen mirip, prioritas strategi kemungkinan besar serupa dan perbedaannya lebih pada konteks tindakan (skala dan pengalaman usaha).

## Keterbatasan

- Struktur klaster sangat lemah (silhouette 0,247): UMKM tersebar kontinu, bukan kelompok yang terpisah tegas. Segmen berguna sebagai ringkasan ujung-ujung kondisi usaha; UMKM di dekat batas bisa masuk segmen mana pun.
- Ward dan Gaussian Mixture hanya sebagian sepakat dengan K-Means pada k = 2 (ARI 0,51 dan 0,42), jadi batas segmen bergantung pada metode.
- Segmen tidak berbeda bermakna pada X1 unggah produk, X2 promosi, X3 komunikasi pelanggan, X4 konsistensi toko, persepsi kinerja, y_obj, pelanggan baru (log) dan proporsi naik penjualan (setelah Holm). Artinya segmentasi ini menggambarkan kondisi usaha, bukan kelompok kinerja; benchmark Tahap 6 per segmen kemungkinan mirip satu sama lain.
- Fitur hanya empat dan sebagian kasar (skala omzet = kuartil 1-4; lama usaha dalam tahun bulat; jumlah platform 1-4), sehingga banyak UMKM bernilai kembar.
- UMKM tanpa baseline (33) ikut membentuk segmen tetapi tidak ikut sampel kinerja; 27 di segmen 1 dan 6 di segmen 2, sehingga proporsi naik penjualan segmen dihitung dari sampel utama yang lebih kecil.

## Grafik

| Grafik | Interpretasi |
|---|---|
| `figures/segmen_pemilihan_k.png` | Dengan fitur profil, k = 2 adalah satu-satunya pilihan yang stabil (median ARI bootstrap 0,92, k lain 0,47-0,59) dengan silhouette 0,25; menambah skor X1-X4 ke fitur menurunkan silhouette ke 0,13-0,14 dan stabilitas ke 0,36-0,44, dan inersia turun landai tanpa siku yang jelas. |
| `figures/segmen_profil.png` | Segmen dibedakan terutama oleh skala omzet, lama usaha sebelum MP dan lama di marketplace (warna pekat di baris profil), sedangkan skor strategi dan kinerja nyaris sama antar-segmen (warna pucat; proporsi naik penjualan 57% dan 51%; tidak ada beda bermakna setelah koreksi Holm). |
| `figures/segmen_peta_pca.png` | Dua komponen utama menjelaskan 65% variasi fitur profil; komponen 1 terutama memuat skala omzet, lama usaha sebelum MP dan lama di marketplace. Titik-titik segmen bersinggungan di bagian tengah, sesuai silhouette yang rendah: segmen lebih tepat dibaca sebagai ujung-ujung rentang kondisi usaha daripada kelompok yang terpisah tegas. |

_Segmen adalah pengelompokan deskriptif dari data survei satu waktu; keanggotaan segmen tidak menjelaskan mengapa penjualan suatu UMKM naik._
