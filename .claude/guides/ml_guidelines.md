# Pedoman Machine Learning

- n = 149: jangan pakai deep learning; hindari tuning besar-besaran.
- Validasi: RepeatedStratifiedKFold (5 lipat x 5 ulangan) untuk klasifikasi; RepeatedKFold untuk regresi.
- Semua praproses (scaling, encoding) di dalam sklearn Pipeline agar tidak terjadi data leakage.
- Baseline wajib: DummyClassifier/DummyRegressor dan Logistic/Linear Regression.
- Random Forest: n_estimators 300-500, max_depth 3-6, min_samples_leaf 3-5, random_state 42.
  XGBoost hanya sebagai pembanding, dengan kedalaman kecil dan regularisasi.
- Metrik klasifikasi: F1-macro, akurasi seimbang, confusion matrix. Regresi: MAE, RMSE, R2.
  Laporkan rata-rata dan simpangan baku antar lipatan.
- Interpretasi: permutation importance dihitung pada data uji tiap lipatan; SHAP (TreeExplainer)
  pada model akhir yang dilatih dengan seluruh data, dilaporkan sebagai ilustrasi (bukan bukti kausal).
- Imbalance: cek ukuran kelas; jika tidak seimbang, pakai class_weight="balanced" sebelum SMOTE.
- Tujuan model adalah menjelaskan, jadi jangan mengejar akurasi dengan fitur yang bocor dari Y.
- Simpan hasil CV per lipatan ke reports/tables untuk bukti.
