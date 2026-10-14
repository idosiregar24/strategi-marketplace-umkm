"""Uji statistik dan ukuran efek (nonparametrik, VIF).

Semua fungsi murni: menerima Series/DataFrame dan mengembalikan dict/DataFrame tanpa menulis berkas.
Dipakai mulai Tahap 3 (EDA); Tahap 4 menambah regresi dan bootstrap di modul ini.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
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
