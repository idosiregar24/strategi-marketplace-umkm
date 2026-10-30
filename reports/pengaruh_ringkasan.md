# Ringkasan Tahap 4: Strategi yang Berhubungan dengan Kinerja Penjualan

Dibuat oleh `umkm.pengaruh` pada 2026-10-30 11:03. Sampel utama 116 UMKM.

## Apa yang dibandingkan

Dari 116 UMKM sampel utama, 62 melaporkan omzet atau transaksi naik (`naik_penjualan` = 1). 54 dari 54 UMKM sisanya menulis omzet DAN transaksi yang sama persis sebelum dan sesudah; tidak ada yang melaporkan keduanya turun. Jadi yang dibandingkan di sini adalah UMKM yang **melaporkan kenaikan** dengan UMKM yang **melaporkan angka sama**, bukan UMKM yang naik dengan yang turun. R015 dihitung naik karena transaksinya naik walau omzetnya turun (definisi D13).

## Temuan

1. **Strategi yang paling berhubungan dengan melaporkan kenaikan.** Setelah profil usaha (lama usaha, jumlah platform, omzet awal) dikendalikan:
   - X3 Komunikasi pelanggan: UMKM yang skornya 1 SD (sekitar 0,6 poin) lebih tinggi memiliki odds melaporkan kenaikan 2,49 kali lebih besar (p = 0,001; Holm 0,005); perkiraan peluangnya 34% pada skor 1 SD di bawah rata-rata vs 76% pada 1 SD di atas rata-rata (variabel lain di rata-rata).
   - X1 Unggah produk: UMKM yang skornya 1 SD (sekitar 0,6 poin) lebih tinggi memiliki odds melaporkan kenaikan 2,19 kali lebih besar (p = 0,005; Holm 0,015); perkiraan peluangnya 37% pada skor 1 SD di bawah rata-rata vs 73% pada 1 SD di atas rata-rata (variabel lain di rata-rata).
   - X2 Promosi dan X4 Konsistensi toko belum meyakinkan.
2. **Peringkat gabungan** (regresi logistik + permutation importance + SHAP): 1. X3 Komunikasi pelanggan (1,00), 2. X1 Unggah produk (0,59), 3. X2 Promosi (0,36), 4. X4 Konsistensi toko (0,00). X3 Komunikasi pelanggan menjadi peringkat 1 pada 85% dari 1000 sampel bootstrap; X1 Unggah produk dan X2 Promosi kadang bertukar tempat. Skor ini relatif (teratas selalu 1), bukan besaran efek.
3. **Promosi (X2)** yang di EDA berkorelasi dengan kinerja tidak lagi bermakna bila keempat strategi dan profil usaha dimasukkan bersama (OR 1,26, p = 0,344). Perbandingan ini tidak sepenuhnya setara (EDA memakai korelasi dengan y_obj, Tahap 4 memakai naik/tidak naik), jadi promosi dibaca sebagai belum meyakinkan, bukan tidak berhubungan.
4. **Strategi menambah daya jelaskan.** Model dengan keempat strategi jauh lebih cocok daripada model berisi profil usaha saja (uji likelihood-ratio p < 0,001).
5. **Kemampuan model.** Untuk membedakan UMKM yang melaporkan kenaikan dari yang menulis angka sama, Random Forest (AUC 0,73) dan regresi logistik (AUC 0,72) lebih baik dari tebakan mayoritas (AUC 0,50), walau masih jauh dari sempurna. Besar kenaikan (`y_obj`) hampir tidak dapat diperkirakan (R2 out-of-fold -0,03 dengan semua responden; 0,10 tanpa R021), sehingga bobot rekomendasi diambil dari model naik/tidak naik.
6. **Cukup stabil.** X3 Komunikasi pelanggan tetap teratas di 5 dari 5 skenario lain untuk target naik/tidak naik, termasuk dua skenario yang paling mengubah data (semua 149 responden dan tanpa jawaban seragam), dan skor gabungannya tetap teratas di kedua skenario itu. Untuk target lain urutannya berbeda (lihat butir berikut).
7. **Hasil yang berlawanan.** X3 Komunikasi pelanggan berhubungan negatif dengan y_pelanggan_baru (koef -0,53, p < 0,001). Angka pelanggan baru tidak jelas diukur sebelum atau sesudah marketplace (D06), jadi hasil ini belum dapat ditafsirkan, tetapi perlu dicatat.
8. **Omzet awal.** UMKM beromzet awal lebih besar cenderung lebih jarang melaporkan kenaikan (OR 0,61). Ini mungkin mencerminkan regresi ke rata-rata atau kebiasaan usaha besar menulis angka yang sama; karena itu omzet awal dijadikan kontrol.
9. **Kelompok angka sama.** Kelompok yang menulis angka sama tidak berbeda bermakna dari kelompok yang naik dalam pembulatan omzet, jumlah platform, lama usaha, lama di marketplace, maupun besar omzet (Holm p >= 0,05); jawaban seragam justru lebih sering di kelompok naik (13% vs 2%). Penanda ini tidak menunjukkan bahwa kelompok angka sama sekadar asal mengisi, tetapi penanda tersebut kasar sehingga kemungkinan itu belum dapat disingkirkan.
10. **Moderasi.** Tidak ditemukan bukti bahwa hubungan strategi berbeda menurut omzet awal, jumlah platform, atau lama di marketplace (0 dari 24 interaksi bermakna setelah koreksi). Daya uji untuk ini rendah, jadi Tahap 6 memakai bobot yang sama untuk semua segmen dan perbedaan antar-segmen datang dari selisih skor.

## Bobot untuk rekomendasi (Tahap 6)

| Strategi | Skor pengaruh | CI bawah | CI atas | Keyakinan arah positif | Meyakinkan | Bobot dipakai |
|---|---|---|---|---|---|---|
| X3 Komunikasi pelanggan | 1.00 | 0.62 | 1.00 | 1.00 | ya | 1.00 |
| X1 Unggah produk | 0.59 | 0.24 | 0.98 | 1.00 | ya | 0.59 |
| X2 Promosi | 0.36 | 0.08 | 0.81 | 0.83 | TIDAK | 0.29 |
| X4 Konsistensi toko | 0.00 | 0.00 | 0.30 | 0.37 | TIDAK | 0.10 |


Bobot dipakai = skor pengaruh x keyakinan arah positif (bagian sampel bootstrap dengan koefisien logit > 0), minimal 0,1 (D26). Di Tahap 6 bobot ini dikalikan dengan selisih skor tiap segmen terhadap UMKM yang melaporkan kenaikan; strategi yang belum meyakinkan tetap bisa muncul bila selisihnya besar, dengan catatan ketidakpastian.

## Keterbatasan

- **Arti target.** "Tidak naik" berarti menulis omzet dan transaksi yang sama persis, bukan turun; kemungkinan sebagian angka sama itu salin-tempel tidak dapat disingkirkan.
- **Data satu waktu dan ingatan responden.** Angka sebelum dan sesudah diisi sekaligus dari ingatan, tanpa kelompok pembanding yang tidak memakai marketplace. Hasil adalah keterkaitan, bukan bukti bahwa strategi menyebabkan penjualan naik.
- **Sumber yang sama.** Skor strategi dan angka kinerja sama-sama diisi sendiri oleh responden; UMKM yang menilai dirinya aktif mungkin juga cenderung melaporkan kenaikan (bias metode bersama).
- **Jawaban seragam.** 9 responden sampel utama menjawab semua butir strategi dengan angka sama (8 di antaranya naik). Tanpa mereka odds ratio X3 Komunikasi pelanggan 2,49 -> 2,69 dan X1 Unggah produk 2,19 -> 1,86.
- **Sampel kecil.** n = 116 dengan 8 prediktor (sekitar 6,8 kejadian per prediktor); interval kepercayaan lebar dan daya uji interaksi rendah.
- **Instrumen.** Unggah produk (X1) dan promosi (X2) hanya diukur dengan 4 butir (D19), dan sebagian besar butir didominasi jawaban netral.
- **Cakupan.** UMKM kuliner di Pekanbaru yang memakai marketplace; tidak otomatis berlaku untuk jenis usaha atau kota lain.

## Grafik

| Grafik | Interpretasi |
|---|---|
| `figures/pengaruh_peringkat.png` | X3 Komunikasi pelanggan memiliki skor pengaruh tertinggi (peringkat 1 pada 85% sampel bootstrap), disusul X1 Unggah produk (0,59); X2 Promosi dan X4 Konsistensi toko belum meyakinkan (interval koefisien logit bootstrap mencakup nol). Skor ini relatif: strategi teratas selalu bernilai 1. |
| `figures/pengaruh_odds_ratio.png` | Dengan profil usaha dikendalikan, UMKM dengan skor X3 Komunikasi pelanggan (OR 2,49) dan X1 Unggah produk (OR 2,19) yang 1 SD lebih tinggi memiliki odds melaporkan kenaikan lebih besar; omzet awal yang lebih besar berhubungan dengan odds yang lebih kecil (OR 0,61). |
| `figures/shap_ringkas.png` | Pada Random Forest, kontribusi rata-rata terbesar berasal dari X3 Komunikasi pelanggan (mean |SHAP| 0,091), lalu X2 Promosi dan X1 Unggah produk; di antara variabel profil, Omzet sebelum (log) paling besar (0,039). |
| `figures/shap_arah.png` | Untuk X3 Komunikasi pelanggan, X1 Unggah produk dan X2 Promosi, skor yang lebih tinggi cenderung menaikkan prediksi peluang melaporkan kenaikan; X4 Konsistensi toko hampir tidak mengubah prediksi (rho -0,09). |
| `figures/pengaruh_sensitivitas_logit.png` | X3 Komunikasi pelanggan tetap teratas di 5 dari 5 skenario selain utama; strategi yang bermakna (p < 0,05, tanpa koreksi): X1 Unggah produk (6 dari 6) dan X3 Komunikasi pelanggan (6 dari 6). Skenario yang paling mengubah data adalah semua 149 responden dan tanpa jawaban seragam; skenario lain hanya membuang sedikit baris atau satu kontrol. |
| `figures/pengaruh_sensitivitas_ols.png` | Pada OLS y_obj koefisien strategi kecil; strategi bermakna hanya muncul di 2 dari 7 skenario, dan hasilnya peka terhadap satu responden (R021, Cook's distance 0,71). |

_Semua hasil adalah pola keterkaitan dari data survei satu waktu, bukan bukti bahwa strategi tertentu menyebabkan penjualan naik._
