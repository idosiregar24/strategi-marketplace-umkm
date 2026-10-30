"""Tahap 4: model machine learning untuk menjelaskan hubungan strategi dengan kinerja.

Validasi silang berulang, pembanding wajib (Dummy dan Logistic/Linear), Random Forest,
permutation importance pada data uji tiap lipatan, SHAP, dan bootstrap gabungan untuk
ketidakpastian peringkat. Semua praproses ada di dalam Pipeline (tanpa kebocoran data).
Fungsi tidak menulis berkas.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats as st
from sklearn.base import BaseEstimator, clone
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import confusion_matrix, mean_absolute_error, r2_score
from sklearn.model_selection import (
    KFold,
    RepeatedKFold,
    RepeatedStratifiedKFold,
    cross_val_predict,
    cross_validate,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SKOR_KLASIFIKASI = {
    "f1_macro": "f1_macro",
    "akurasi_seimbang": "balanced_accuracy",
    "auc": "roc_auc",
}
SKOR_REGRESI = {
    "mae": "neg_mean_absolute_error",
    "rmse": "neg_root_mean_squared_error",
    "r2": "r2",
}


# ---------------------------------------------------------------------------
# Model dan validasi silang
# ---------------------------------------------------------------------------
def rf_klasifikasi(params: dict[str, Any], seed: int = 42) -> RandomForestClassifier:
    """Random Forest klasifikasi dangkal (n kecil); n_jobs=1 agar paralel di tingkat CV."""
    return RandomForestClassifier(**params, random_state=seed, n_jobs=1)


def rf_regresi(params: dict[str, Any], seed: int = 42) -> RandomForestRegressor:
    """Random Forest regresi dengan parameter yang sama dengan versi klasifikasi."""
    return RandomForestRegressor(**params, random_state=seed, n_jobs=1)


def kandidat_klasifikasi(rf_params: dict[str, Any], seed: int = 42) -> dict[str, BaseEstimator]:
    """Pembanding mayoritas, regresi logistik, dan Random Forest."""
    return {
        "dummy_mayoritas": DummyClassifier(strategy="most_frequent"),
        "logistik": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "random_forest": rf_klasifikasi(rf_params, seed),
    }


def kandidat_regresi(rf_params: dict[str, Any], seed: int = 42) -> dict[str, BaseEstimator]:
    """Pembanding rata-rata, regresi linear, dan Random Forest."""
    return {
        "dummy_rata_rata": DummyRegressor(strategy="mean"),
        "linear": make_pipeline(StandardScaler(), LinearRegression()),
        "random_forest": rf_regresi(rf_params, seed),
    }


def skema_cv(klasifikasi: bool, n_splits: int, n_repeats: int, seed: int = 42):
    """RepeatedStratifiedKFold untuk klasifikasi, RepeatedKFold untuk regresi."""
    cls = RepeatedStratifiedKFold if klasifikasi else RepeatedKFold
    return cls(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)


def cv_metrik(
    models: dict[str, BaseEstimator], x: pd.DataFrame, y: pd.Series, cv, skor: dict[str, str]
) -> pd.DataFrame:
    """Metrik tiap lipatan untuk tiap model (bentuk panjang: model, lipatan, metrik, nilai).

    Skor 'neg_*' dibalik tandanya agar MAE/RMSE terbaca positif (lebih kecil lebih baik).
    """
    rows = []
    for nama, m in models.items():
        res = cross_validate(m, x, y, cv=cv, scoring=skor, n_jobs=-1)
        for metrik, scorer in skor.items():
            nilai = res[f"test_{metrik}"] * (-1 if scorer.startswith("neg_") else 1)
            rows += [
                {"model": nama, "lipatan": i, "metrik": metrik, "nilai": v}
                for i, v in enumerate(nilai)
            ]
    return pd.DataFrame(rows)


def ringkas_cv(per_lipatan: pd.DataFrame) -> pd.DataFrame:
    """Rata-rata dan simpangan baku antar lipatan per model x metrik."""
    return (
        per_lipatan.groupby(["model", "metrik"], sort=False)["nilai"]
        .agg(rata_rata="mean", sd="std", n_lipatan="count")
        .reset_index()
    )


def confusion_cv(model: BaseEstimator, x: pd.DataFrame, y: pd.Series, cv) -> dict[str, int]:
    """Confusion matrix (ambang 0,5) dijumlahkan atas semua lipatan uji."""
    tot = np.zeros((2, 2), dtype=int)
    for latih, uji in cv.split(x, y):
        m = clone(model).fit(x.iloc[latih], y.iloc[latih])
        tot += confusion_matrix(y.iloc[uji], m.predict(x.iloc[uji]), labels=[0, 1])
    return {"tn": tot[0, 0], "fp": tot[0, 1], "fn": tot[1, 0], "tp": tot[1, 1]}


def r2_oof(
    models_: dict[str, BaseEstimator],
    x: pd.DataFrame,
    y: pd.Series,
    n_splits: int,
    n_repeats: int,
    seed: int = 42,
) -> pd.DataFrame:
    """R2 dan MAE dari prediksi out-of-fold gabungan (seluruh baris sekaligus) per ulangan.

    Lebih stabil daripada rata-rata R2 per lipatan kecil yang bias negatif.
    """
    rows = []
    for nama, m in models_.items():
        for r in range(n_repeats):
            cv = KFold(n_splits=n_splits, shuffle=True, random_state=seed + r)
            pred = cross_val_predict(m, x, y, cv=cv, n_jobs=-1)
            rows.append(
                {
                    "model": nama,
                    "ulangan": r,
                    "r2_oof": r2_score(y, pred),
                    "mae_oof": mean_absolute_error(y, pred),
                }
            )
    return (
        pd.DataFrame(rows).groupby("model", sort=False)[["r2_oof", "mae_oof"]].mean().reset_index()
    )


# ---------------------------------------------------------------------------
# Interpretasi
# ---------------------------------------------------------------------------
def permutation_cv(
    model: BaseEstimator,
    x: pd.DataFrame,
    y: pd.Series,
    cv,
    skor: str,
    n_repeats: int,
    seed: int = 42,
) -> pd.DataFrame:
    """Permutation importance pada data uji tiap lipatan (model dilatih di data latih lipatan)."""

    def satu(i: int, latih: np.ndarray, uji: np.ndarray) -> list[dict[str, Any]]:
        m = clone(model).fit(x.iloc[latih], y.iloc[latih])
        r = permutation_importance(
            m, x.iloc[uji], y.iloc[uji], scoring=skor, n_repeats=n_repeats, random_state=seed
        )
        return [
            {"lipatan": i, "variabel": c, "importance": v}
            for c, v in zip(x.columns, r.importances_mean)
        ]

    hasil = Parallel(n_jobs=-1)(
        delayed(satu)(i, latih, uji) for i, (latih, uji) in enumerate(cv.split(x, y))
    )
    return pd.DataFrame([r for h in hasil for r in h])


def shap_kelas_positif(model: BaseEstimator, x: pd.DataFrame) -> np.ndarray:
    """Nilai SHAP (TreeExplainer) untuk kelas 1 (klasifikasi) atau keluaran (regresi), n x p."""
    import shap

    sv = shap.TreeExplainer(model).shap_values(x)
    if isinstance(sv, list):  # shap < 0.45: satu larik (n, p) per kelas
        sv = sv[-1]
    sv = np.asarray(sv)
    if sv.ndim == 3:  # (n, p, kelas)
        sv = sv[:, :, 1]
    return sv


def ringkas_shap(sv: np.ndarray, x: pd.DataFrame) -> pd.DataFrame:
    """mean|SHAP| per variabel dan arah hubungan (rho Spearman nilai variabel vs SHAP-nya)."""
    rows = []
    for j, c in enumerate(x.columns):
        rho = st.spearmanr(x[c], sv[:, j])[0] if x[c].nunique() > 1 else np.nan
        rows.append({"variabel": c, "mean_abs_shap": np.abs(sv[:, j]).mean(), "arah_rho": rho})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Skor pengaruh gabungan
# ---------------------------------------------------------------------------
def normalkan_positif(v: pd.Series) -> pd.Series:
    """Nilai negatif -> 0 (hubungan berlawanan tidak dijadikan bobot), lalu dibagi maksimum."""
    v = v.clip(lower=0)
    return v / v.max() if v.max() > 0 else v * 0.0


def skor_gabungan(
    koef_logit: pd.Series, perm: pd.Series, shap_abs: pd.Series, shap_arah: pd.Series
) -> pd.DataFrame:
    """Gabungkan tiga sumber (indeks = strategi) menjadi `pengaruh` 0-1.

    koef logit apa adanya (bertanda). Permutation importance negatif (mengacak variabel justru
    memperbaiki prediksi) dijadikan 0; permutation dan mean|SHAP| hanya dihitung bila arah SHAP
    positif. Tiap sumber dinormalkan (negatif -> 0, dibagi maksimum), lalu dirata-rata; skor ini
    relatif (strategi teratas selalu 1), bukan besaran efek.
    """
    positif = (shap_arah.fillna(0) >= 0).astype(float)
    out = pd.DataFrame(
        {
            "n_koef": normalkan_positif(koef_logit),
            "n_perm": normalkan_positif(perm.clip(lower=0) * positif),
            "n_shap": normalkan_positif(shap_abs * positif),
        }
    )
    out["pengaruh"] = out.mean(axis=1)
    return out


def _bootstrap_satu(
    x: pd.DataFrame,
    y: pd.Series,
    strategi: list[str],
    rf_params: dict[str, Any],
    skor: str,
    n_repeats: int,
    seed: int,
) -> dict[str, float] | None:
    from umkm.stats import logit_or

    warnings.simplefilter("ignore")  # peringatan konvergensi statsmodels di proses pekerja
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), len(x))
    oob = np.setdiff1d(np.arange(len(x)), idx)
    xb, yb = x.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)
    if yb.nunique() < 2 or y.iloc[oob].nunique() < 2:
        return None
    try:
        koef = logit_or(yb, xb)[0].set_index("variabel")["koef"]
    except ValueError:
        return None
    rf = rf_klasifikasi(rf_params, seed=int(seed % 2**31)).fit(xb, yb)
    sh = ringkas_shap(shap_kelas_positif(rf, x), x).set_index("variabel")
    pi = permutation_importance(
        rf, x.iloc[oob], y.iloc[oob], scoring=skor, n_repeats=n_repeats, random_state=42
    )
    perm = pd.Series(pi.importances_mean, index=x.columns)
    g = skor_gabungan(
        koef[strategi],
        perm[strategi],
        sh.loc[strategi, "mean_abs_shap"],
        sh.loc[strategi, "arah_rho"],
    )
    out = {f"koef_{s}": koef[s] for s in strategi}
    out |= {f"perm_{s}": perm[s] for s in strategi}
    out |= {f"shap_{s}": sh.at[s, "mean_abs_shap"] for s in strategi}
    out |= {f"pengaruh_{s}": g.at[s, "pengaruh"] for s in strategi}
    return out


def bootstrap_pengaruh(
    x: pd.DataFrame,
    y: pd.Series,
    strategi: list[str],
    rf_params: dict[str, Any],
    skor: str,
    n_repeats: int,
    n_boot: int,
    seed: int = 42,
) -> pd.DataFrame:
    """Bootstrap (resampling baris) koef logit, permutation importance OOB, mean|SHAP|, dan
    skor pengaruh gabungan; satu baris per iterasi yang berhasil (gagal = separasi/kelas tunggal).
    """
    seeds = np.random.SeedSequence(seed).generate_state(n_boot)
    hasil = Parallel(n_jobs=-1)(
        delayed(_bootstrap_satu)(x, y, strategi, rf_params, skor, n_repeats, int(s)) for s in seeds
    )
    return pd.DataFrame([h for h in hasil if h is not None])


def ringkas_bootstrap(boot: pd.DataFrame, strategi: list[str]) -> pd.DataFrame:
    """CI 95% persentil tiap ukuran, peringkat median, dan peluang menjadi peringkat 1."""
    peng = boot[[f"pengaruh_{s}" for s in strategi]].to_numpy()
    rank = (-peng).argsort(axis=1).argsort(axis=1) + 1
    rows = []
    for j, s in enumerate(strategi):
        r = {"strategi": s}
        for ukuran in ("koef", "perm", "shap", "pengaruh"):
            v = boot[f"{ukuran}_{s}"]
            r[f"{ukuran}_ci_bawah"], r[f"{ukuran}_ci_atas"] = v.quantile([0.025, 0.975])
        r["p_koef_positif"] = (boot[f"koef_{s}"] > 0).mean()
        r["peringkat_median"] = float(np.median(rank[:, j]))
        r["p_peringkat_1"] = float((rank[:, j] == 1).mean())
        r["p_tiga_besar"] = float((rank[:, j] <= 3).mean())
        rows.append(r)
    out = pd.DataFrame(rows)
    out.attrs["n_boot"] = len(boot)
    return out
