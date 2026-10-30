"""Uji statistik dan ukuran efek (nonparametrik, VIF).

Semua fungsi murni: menerima Series/DataFrame dan mengembalikan dict/DataFrame tanpa menulis berkas.
Dipakai mulai Tahap 3 (EDA); Tahap 4 menambah regresi OLS robust (HC3) dan logit.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

LIKERT_MIN = 1
LIKERT_MAX = 5
BATAS_CEILING_FLOOR = 0.15  # > 15% responden di skor minimum/maksimum (Terwee dkk., 2007)
BATAS_DOMINASI = 0.50  # > 50% jawaban pada satu nilai


def label_efek(r: float) -> str:
    """Label ukuran efek |r| menurut Cohen: < 0,1 sangat kecil; 0,1 kecil; 0,3 sedang; 0,5 besar."""
    if r is None or np.isnan(r):
        return ""
    a = abs(r)
    if a < 0.1:
        return "sangat kecil"
    if a < 0.3:
        return "kecil"
    if a < 0.5:
        return "sedang"
    return "besar"


# ---------------------------------------------------------------------------
# Distribusi skor Likert
# ---------------------------------------------------------------------------
def ringkas_skor(x: pd.Series) -> dict[str, Any]:
    """Statistik skor skala 1-5: pusat, sebaran, kemencengan, floor/ceiling, nilai dominan."""
    x = x.dropna()
    modus = x.mode().iloc[0]
    return {
        "n": len(x),
        "rata_rata": x.mean(),
        "sd": x.std(ddof=1),
        "median": x.median(),
        "q1": x.quantile(0.25),
        "q3": x.quantile(0.75),
        "min": x.min(),
        "max": x.max(),
        "skewness": st.skew(x, bias=False),
        "pct_floor": (x == LIKERT_MIN).mean(),
        "pct_ceiling": (x == LIKERT_MAX).mean(),
        "nilai_dominan": modus,
        "pct_nilai_dominan": (x == modus).mean(),
        "pct_tepat_3": (x == 3).mean(),
    }


def sebaran_butir(items: pd.DataFrame) -> pd.DataFrame:
    """Proporsi jawaban 1-5 per butir Likert, plus penanda dominasi satu kategori."""
    rows = []
    for col in items.columns:
        vc = items[col].dropna().astype(int).value_counts(normalize=True)
        prop = {f"pct_{k}": float(vc.get(k, 0.0)) for k in range(LIKERT_MIN, LIKERT_MAX + 1)}
        top = max(prop, key=prop.get)
        rows.append(
            {
                "butir": col,
                **prop,
                "kategori_dominan": int(top.split("_")[1]),
                "pct_dominan": prop[top],
                "dominasi_netral": prop["pct_3"] > BATAS_DOMINASI,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Uji berpasangan dan dua kelompok
# ---------------------------------------------------------------------------
def wilcoxon_berpasangan(sebelum: pd.Series, sesudah: pd.Series) -> dict[str, Any]:
    """Wilcoxon signed-rank (sesudah - sebelum), pasangan tanpa beda dibuang (zero_method='wilcox').

    Ukuran efek: r = Z / sqrt(n_berbeda), r_semua_pasangan = Z / sqrt(n_pasangan) (lebih konservatif
    bila banyak pasangan tanpa beda), dan korelasi rank-biserial berpasangan (W+ - W-) / (W+ + W-);
    semuanya positif jika nilai sesudah cenderung lebih tinggi.
    """
    pair = pd.concat([sebelum, sesudah], axis=1).dropna()
    d = pair.iloc[:, 1] - pair.iloc[:, 0]
    nz = d[d != 0]
    out: dict[str, Any] = {
        "n_pasangan": len(d),
        "n_naik": int((d > 0).sum()),
        "n_sama": int((d == 0).sum()),
        "n_turun": int((d < 0).sum()),
        "median_sebelum": pair.iloc[:, 0].median(),
        "median_sesudah": pair.iloc[:, 1].median(),
        "median_selisih": d.median(),
    }
    if len(nz) == 0:
        kosong = ("W", "z", "p", "r", "r_semua_pasangan", "r_rank_biserial")
        return {**out, **dict.fromkeys(kosong, np.nan)}
    ranks = st.rankdata(nz.abs())
    w_plus, w_minus = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    res = st.wilcoxon(nz, zero_method="wilcox", correction=False, method="approx")
    z = abs(float(res.zstatistic)) * np.sign(w_plus - w_minus)
    return {
        **out,
        "W": float(res.statistic),
        "z": z,
        "p": float(res.pvalue),
        "r": z / np.sqrt(len(nz)),
        "r_semua_pasangan": z / np.sqrt(len(d)),
        "r_rank_biserial": (w_plus - w_minus) / (w_plus + w_minus),
    }


def mann_whitney(x1: pd.Series, x0: pd.Series) -> dict[str, Any]:
    """Mann-Whitney U dua sisi (kelompok 1 vs kelompok 0), pendekatan normal dengan koreksi ties.

    Ukuran efek: rank-biserial = 2*U1/(n1*n0) - 1 (positif jika kelompok 1 cenderung lebih tinggi)
    dan r = Z / sqrt(N).
    """
    x1, x0 = x1.dropna(), x0.dropna()
    n1, n0 = len(x1), len(x0)
    res = st.mannwhitneyu(x1, x0, alternative="two-sided", method="asymptotic")
    rb = 2 * float(res.statistic) / (n1 * n0) - 1
    z = float(st.norm.isf(res.pvalue / 2)) * np.sign(rb)
    return {
        "n_1": n1,
        "n_0": n0,
        "median_1": x1.median(),
        "median_0": x0.median(),
        "rata_1": x1.mean(),
        "rata_0": x0.mean(),
        "U": float(res.statistic),
        "z": z,
        "p": float(res.pvalue),
        "r": z / np.sqrt(n1 + n0),
        "r_rank_biserial": rb,
    }


def kruskal_eps(kelompok: list[pd.Series]) -> dict[str, Any]:
    """Kruskal-Wallis antar-kelompok dengan efek epsilon-kuadrat = H / (n - 1)."""
    kel = [pd.Series(g).dropna() for g in kelompok]
    n = sum(len(g) for g in kel)
    res = st.kruskal(*kel)
    return {
        "n": n,
        "H": float(res.statistic),
        "p": float(res.pvalue),
        "efek": res.statistic / (n - 1),
    }


def chi2_cramer(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    """Uji keterkaitan dua variabel kategorik: Fisher (tabel 2x2) atau chi-kuadrat, + Cramer's V."""
    tab = pd.crosstab(x, y)
    chi2, p, _, _ = st.chi2_contingency(tab, correction=False)
    n = int(tab.to_numpy().sum())
    uji = "chi-kuadrat"
    if tab.shape == (2, 2):
        p, uji = float(st.fisher_exact(tab)[1]), "Fisher"
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    return {"n": n, "statistik": float(chi2), "p": float(p), "efek": float(v), "uji": uji}


def holm(p: pd.Series) -> pd.Series:
    """p-value terkoreksi Holm; nilai kosong dibiarkan kosong."""
    out = pd.Series(np.nan, index=p.index)
    ok = p.notna()
    if ok.any():
        out[ok] = multipletests(p[ok], method="holm")[1]
    return out


# ---------------------------------------------------------------------------
# Korelasi dan multikolinearitas
# ---------------------------------------------------------------------------
def spearman_ci(rho: float, n: int, level: float = 0.95) -> tuple[float, float]:
    """Interval kepercayaan rho Spearman via transformasi Fisher, SE Bonett-Wright (2000)."""
    if n <= 3 or np.isnan(rho) or abs(rho) >= 1:
        return (np.nan, np.nan)
    se = np.sqrt((1 + rho**2 / 2) / (n - 3))
    zc = st.norm.ppf(0.5 + level / 2)
    zr = np.arctanh(rho)
    return (float(np.tanh(zr - zc * se)), float(np.tanh(zr + zc * se)))


def spearman_tabel(df: pd.DataFrame, xs: list[str], ys: list[str]) -> pd.DataFrame:
    """Rho Spearman tiap pasangan x-y (pairwise complete), CI 95%, p, dan p Holm di seluruh tabel."""
    rows = []
    for x in xs:
        for y in ys:
            pair = df[[x, y]].dropna()
            rho, p = st.spearmanr(pair[x], pair[y])
            lo, hi = spearman_ci(float(rho), len(pair))
            rows.append(
                {"x": x, "y": y, "n": len(pair), "rho": rho, "ci_bawah": lo, "ci_atas": hi, "p": p}
            )
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["p"])
    return out


def vif(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Variance Inflation Factor tiap kolom (dengan konstanta); baris dengan nilai kosong dibuang."""
    x = add_constant(df[cols].dropna().astype(float), has_constant="add")
    rows = [
        {"variabel": c, "vif": variance_inflation_factor(x.values, i)}
        for i, c in enumerate(x.columns)
        if c != "const"
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Regresi (Tahap 4)
# ---------------------------------------------------------------------------
def standarkan(x: pd.DataFrame) -> pd.DataFrame:
    """z-score per kolom (SD sampel, ddof=1)."""
    return (x - x.mean()) / x.std(ddof=1)


def _tabel_koef(fit: Any, cols: list[str]) -> pd.DataFrame:
    ci = fit.conf_int()
    return pd.DataFrame(
        {
            "variabel": cols,
            "koef": fit.params[cols].to_numpy(),
            "se": fit.bse[cols].to_numpy(),
            "ci_bawah": ci.loc[cols, 0].to_numpy(),
            "ci_atas": ci.loc[cols, 1].to_numpy(),
            "p": fit.pvalues[cols].to_numpy(),
        }
    )


def ols_hc3(y: pd.Series, x: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """OLS dengan prediktor terstandar dan galat baku robust HC3; baris kosong dibuang.

    Koefisien = perubahan y untuk kenaikan 1 SD prediktor, dengan prediktor lain tetap.
    """
    data = pd.concat([y, x], axis=1).dropna()
    cols = list(x.columns)
    fit = sm.OLS(data[y.name], add_constant(standarkan(data[cols]))).fit(cov_type="HC3")
    info = {"n": int(fit.nobs), "r2": fit.rsquared, "r2_adj": fit.rsquared_adj}
    return _tabel_koef(fit, cols), info


def logit_or(y: pd.Series, x: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Regresi logistik (y biner) dengan prediktor terstandar; baris kosong dibuang.

    Koefisien dalam log-odds per 1 SD prediktor; odds ratio (OR) dan CI 95% = exp(koef/CI).
    Melempar ValueError bila model tidak konvergen atau terjadi separasi sempurna.
    """
    data = pd.concat([y, x], axis=1).dropna()
    cols = list(x.columns)
    try:
        fit = sm.Logit(data[y.name], add_constant(standarkan(data[cols]))).fit(disp=0, maxiter=200)
    except Exception as e:  # PerfectSeparationError / LinAlgError
        raise ValueError(f"logit gagal: {e}") from e
    if not fit.mle_retvals.get("converged", True):
        raise ValueError("logit tidak konvergen")
    out = _tabel_koef(fit, cols)
    for c in ("koef", "ci_bawah", "ci_atas"):
        out[c.replace("koef", "or") if c == "koef" else f"or_{c}"] = np.exp(out[c])
    info = {
        "n": int(fit.nobs),
        "n_1": int(data[y.name].sum()),
        "pseudo_r2": fit.prsquared,
        "const": float(fit.params["const"]),
        "llf": float(fit.llf),
    }
    return out, info


def peluang_logit(const: float, koef: float, z: float) -> float:
    """Peluang prediksi logit bila satu prediktor terstandar = z dan prediktor lain di rata-rata."""
    return float(1 / (1 + np.exp(-(const + koef * z))))


def logit_lr_blok(y: pd.Series, x: pd.DataFrame, blok: list[str]) -> dict[str, float]:
    """Uji likelihood-ratio: apakah blok prediktor menambah kecocokan logit di atas sisanya."""
    data = pd.concat([y, x], axis=1).dropna()
    _, penuh = logit_or(data[y.name], data[list(x.columns)])
    _, kecil = logit_or(data[y.name], data[[c for c in x.columns if c not in blok]])
    lr = 2 * (penuh["llf"] - kecil["llf"])
    return {
        "lr": lr,
        "df": len(blok),
        "p": float(st.chi2.sf(lr, len(blok))),
        "pseudo_r2_penuh": penuh["pseudo_r2"],
        "pseudo_r2_tanpa_blok": kecil["pseudo_r2"],
    }


def ols_diagnostik(y: pd.Series, x: pd.DataFrame) -> dict[str, float]:
    """Pemeriksaan residual OLS: kemencengan, kurtosis, Jarque-Bera, dan Cook's distance maks."""
    data = pd.concat([y, x], axis=1).dropna()
    fit = sm.OLS(data[y.name], add_constant(standarkan(data[list(x.columns)]))).fit()
    res = fit.resid
    cook = fit.get_influence().cooks_distance[0]
    return {
        "skew_residual": float(st.skew(res)),
        "kurtosis_residual": float(st.kurtosis(res)),
        "p_jarque_bera": float(st.jarque_bera(res).pvalue),
        "cook_maks": float(cook.max()),
        "baris_cook_maks": int(data.index[int(cook.argmax())]),
        "n_cook_di_atas_4_per_n": int((cook > 4 / len(data)).sum()),
    }
