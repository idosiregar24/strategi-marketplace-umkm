# Pedoman Statistik

- Data Likert bersifat ordinal: utamakan uji nonparametrik (Spearman, Wilcoxon, Kruskal-Wallis).
  Skor rata-rata konstruk boleh diperlakukan sebagai pendekatan kontinu pada regresi, dengan pemeriksaan residual.
- Reliabilitas: Cronbach's alpha >= 0.70; korelasi item-total >= 0.30. Laporkan alpha-if-deleted.
- Regresi: standarkan prediktor agar koefisien sebanding; galat baku robust HC3; periksa VIF (waspada > 5).
- Ordinal logit: laporkan odds ratio dan interval kepercayaan 95%.
- Uji berganda: koreksi Holm pada perbandingan post-hoc.
- Laporkan ukuran efek (r untuk Wilcoxon, epsilon-kuadrat untuk Kruskal), bukan p-value saja.
- Ketidakpastian: bootstrap 1000x untuk peringkat dan importance.
- Bahasa: "berhubungan dengan", "terkait", "cenderung". Hindari "menyebabkan", "berdampak pasti".
- Selalu jalankan analisis sensitivitas yang tercantum di plan/04.
- Jika hasil tidak signifikan atau model tidak mengalahkan baseline, laporkan apa adanya.
