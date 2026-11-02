"""Analisis pembanding Tahap 4: PLS-SEM (asosiasi, bukan kausal).

Model jalur PLS (Lohmöller/Wold): konstruk strategi X1-X4 reflektif (Mode A, skema bobot
jalur), variabel profil sebagai konstruk satu indikator. Tiga model:
- `y_obj`          : kinerja objektif (indikator tunggal), sampel utama (model utama PLS);
- `naik_penjualan` : pelaporan kenaikan (indikator tunggal, 0/1), sampel utama, padanan logit/RF;
- `persepsi`       : persepsi kinerja Y1-Y8 (reflektif), 149 responden, pembanding.

Membaca data_features.csv (+ butir Y dari data_clean.csv); menulis reports/tables/sem_*.csv,
reports/figures/sem_*.png, reports/sem_log.md dan sem_ringkasan.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats as st
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold

from umkm import stats

STRATEGI = ["x1_unggah", "x2_promosi", "x3_komunikasi", "x4_konsistensi"]
BUTIR = {
    "x1_unggah": [f"x1_unggah_{i}" for i in range(1, 5)],
    "x2_promosi": [f"x2_promosi_{i}" for i in range(1, 5)],
    "x3_komunikasi": [f"x3_komunikasi_{i}" for i in range(1, 6)],
    "x4_konsistensi": [f"x4_konsistensi_{i}" for i in range(1, 6)],
}
BUTIR_Y = [f"y_persepsi_{i}" for i in range(1, 9)]
NAMA_MODEL = {
    "y_obj": "Kinerja objektif (y_obj)",
    "naik_penjualan": "Melaporkan kenaikan (naik_penjualan)",
    "persepsi": "Persepsi kinerja (Y1-Y8)",
}


# ---------------------------------------------------------------------------
# Spesifikasi dan estimasi PLS
# ---------------------------------------------------------------------------
@dataclass
class ModelPLS:
    """`blok`: konstruk -> indikator; `jalur`: konstruk endogen -> konstruk prediktor."""

    blok: dict[str, list[str]]
    jalur: dict[str, list[str]]

    @property
    def indikator(self) -> list[str]:
        return [i for v in self.blok.values() for i in v]


def spesifikasi(target: str, kontrol: list[str]) -> ModelPLS:
    """Model X1-X4 + kontrol -> target. `persepsi` = konstruk reflektif Y1-Y8."""
    blok = {k: BUTIR[k] for k in STRATEGI} | {k: [k] for k in kontrol}
    blok[target] = BUTIR_Y if target == "persepsi" else [target]
    return ModelPLS(blok, {target: STRATEGI + kontrol})


def _z(a: np.ndarray) -> np.ndarray:
    sd = a.std(axis=0)
    if np.any(sd == 0):
        raise ValueError("indikator konstan")
    return (a - a.mean(axis=0)) / sd


def _ols(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(x, y, rcond=None)[0]


def estimasi(
    data: pd.DataFrame, m: ModelPLS, maks_iter: int = 300, toleransi: float = 1e-7
) -> dict[str, Any]:
    """Algoritma PLS: bobot luar, skor konstruk (terstandar), loading, koefisien jalur, R2.

    Arah konstruk ditetapkan agar jumlah loading positif (indeterminasi tanda).
    """
    xs = {k: _z(data[v].to_numpy(float)) for k, v in m.blok.items()}
    n = len(data)
    nama = list(m.blok)
    w = {k: np.ones(len(m.blok[k])) for k in nama}
    for it in range(maks_iter):
        skor = {k: _z(xs[k] @ w[k]) for k in nama}
        proksi = {k: np.zeros(n) for k in nama}
        for endo, pred in m.jalur.items():  # skema bobot jalur
            b = _ols(skor[endo], np.column_stack([skor[p] for p in pred]))
            for p, bp in zip(pred, b):
                proksi[endo] += bp * skor[p]
                proksi[p] += np.corrcoef(skor[p], skor[endo])[0, 1] * skor[endo]
        baru = {}
        for k in nama:
            if len(m.blok[k]) == 1:
                baru[k] = np.ones(1)
            else:
                v = xs[k].T @ _z(proksi[k]) / n  # Mode A
                baru[k] = v / (xs[k] @ v).std()
        beda = max(np.abs(baru[k] - w[k]).max() for k in nama)
        w = baru
        if beda < toleransi:
            break
    skor = {k: xs[k] @ w[k] for k in nama}
    loading = {}
    for k in nama:
        lam = np.array([np.corrcoef(xs[k][:, j], skor[k])[0, 1] for j in range(xs[k].shape[1])])
        if lam.sum() < 0:
            w[k], skor[k], lam = -w[k], -skor[k], -lam
        loading[k] = lam
    jalur, r2 = {}, {}
    for endo, pred in m.jalur.items():
        x = np.column_stack([skor[p] for p in pred])
        b = _ols(skor[endo], x)
        jalur |= {(p, endo): bp for p, bp in zip(pred, b)}
        r2[endo] = 1 - np.sum((skor[endo] - x @ b) ** 2) / np.sum(skor[endo] ** 2)
    return {
        "bobot": w,
        "loading": loading,
        "skor": pd.DataFrame(skor, index=data.index),
        "jalur": jalur,
        "r2": r2,
        "iterasi": it + 1,
        "konvergen": beda < toleransi,
    }


# ---------------------------------------------------------------------------
# Model pengukuran
# ---------------------------------------------------------------------------
def htmt(data: pd.DataFrame, blok: dict[str, list[str]]) -> pd.DataFrame:
    """Heterotrait-monotrait ratio antar konstruk multi-indikator (korelasi absolut)."""
    multi = [k for k, v in blok.items() if len(v) > 1]
    r = data[[i for k in multi for i in blok[k]]].corr().abs()

    def mono(k: str) -> float:
        sub = r.loc[blok[k], blok[k]].to_numpy()
        return sub[np.triu_indices_from(sub, 1)].mean()

    out = pd.DataFrame(np.nan, index=multi, columns=multi)
    for i, a in enumerate(multi):
        for b in multi[i + 1 :]:
            out.loc[b, a] = r.loc[blok[a], blok[b]].to_numpy().mean() / np.sqrt(mono(a) * mono(b))
    return out


def reliabilitas(data: pd.DataFrame, m: ModelPLS, fit: dict[str, Any]) -> pd.DataFrame:
    """Cronbach alpha, rho_A (Dijkstra-Henseler), rho_C (composite reliability), AVE."""
    rows = []
    for k, ind in m.blok.items():
        if len(ind) == 1:
            continue
        x = data[ind].to_numpy(float)
        s = np.corrcoef(x, rowvar=False)
        lam, w = fit["loading"][k], fit["bobot"][k]
        kk = len(ind)
        alpha = kk / (kk - 1) * (1 - kk / s.sum())
        ww = np.outer(w, w)
        rho_a = (
            (w @ w) ** 2
            * (w @ (s - np.diag(np.diag(s))) @ w)
            / (w @ (ww - np.diag(np.diag(ww))) @ w)
        )
        rho_c = lam.sum() ** 2 / (lam.sum() ** 2 + np.sum(1 - lam**2))
        rows.append(
            {
                "konstruk": k,
                "n_indikator": kk,
                "alpha": alpha,
                "rho_a": rho_a,
                "rho_c": rho_c,
                "ave": float(np.mean(lam**2)),
                "loading_min": float(lam.min()),
            }
        )
    return pd.DataFrame(rows)


def fornell_larcker(m: ModelPLS, fit: dict[str, Any], rel: pd.DataFrame) -> pd.DataFrame:
    """Diagonal = akar AVE; di bawah diagonal = korelasi antar skor konstruk."""
    multi = rel["konstruk"].tolist()
    out = fit["skor"][multi].corr()
    for k, ave in zip(multi, rel["ave"]):
        out.loc[k, k] = np.sqrt(ave)
    return out.where(np.tril(np.ones(out.shape, bool)))


# ---------------------------------------------------------------------------
# Model struktural: bootstrap, f2, VIF, daya prediksi
# ---------------------------------------------------------------------------
def bootstrap(
    data: pd.DataFrame, m: ModelPLS, n_boot: int, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
    """Sampel bootstrap (paralel, satu seed turunan per sampel): koefisien jalur, loading, HTMT.
    Mengembalikan juga jumlah sampel gagal (indikator konstan di sampel ulang)."""

    def satu(s: int) -> tuple[dict, dict, dict] | None:
        rng = np.random.default_rng(s)
        d = data.iloc[rng.integers(0, len(data), len(data))].reset_index(drop=True)
        try:
            f = estimasi(d, m)
        except (ValueError, np.linalg.LinAlgError):
            return None
        h = htmt(d, m.blok).stack().dropna()
        return (
            {f"{p}->{e}": v for (p, e), v in f["jalur"].items()},
            {i: lam for k in m.blok for i, lam in zip(m.blok[k], f["loading"][k])},
            {f"{a}|{b}": v for (a, b), v in h.items()},
        )

    seeds = np.random.SeedSequence(seed).generate_state(n_boot)
    hasil = Parallel(n_jobs=-1)(delayed(satu)(int(s)) for s in seeds)
    ok = [h for h in hasil if h is not None]
    jalur, loading, ht = (pd.DataFrame([h[i] for h in ok]) for i in range(3))
    return jalur, loading, ht, n_boot - len(ok)


def _uji(est: float, boot: pd.Series, n: int) -> dict[str, float]:
    sd = boot.std(ddof=1)
    t = est / sd
    return {
        "se_boot": sd,
        "t": t,
        "p": 2 * st.t.sf(abs(t), df=n - 1),
        "ci_bawah": boot.quantile(0.025),
        "ci_atas": boot.quantile(0.975),
    }


def f2_vif(m: ModelPLS, fit: dict[str, Any]) -> pd.DataFrame:
    """Effect size f2 dan VIF inner per jalur (dari skor konstruk)."""
    rows = []
    for endo, pred in m.jalur.items():
        y = fit["skor"][endo].to_numpy()

        def r2(cols: list[str], yy: np.ndarray) -> float:
            x = fit["skor"][cols].to_numpy()
            return 1 - np.sum((yy - x @ _ols(yy, x)) ** 2) / np.sum((yy - yy.mean()) ** 2)

        r2_penuh = fit["r2"][endo]
        for p in pred:
            lain = [q for q in pred if q != p]
            rows.append(
                {
                    "prediktor": p,
                    "endogen": endo,
                    "f2": (r2_penuh - r2(lain, y)) / (1 - r2_penuh),
                    "vif_inner": 1 / (1 - r2(lain, fit["skor"][p].to_numpy())),
                }
            )
    return pd.DataFrame(rows)


def _prediksi(train: pd.DataFrame, test: pd.DataFrame, m: ModelPLS, target: str) -> np.ndarray:
    """Prediksi indikator target (skala asli) di data uji dari bobot dan jalur data latih."""
    f = estimasi(train, m)
    pred = m.jalur[target]
    yhat = np.zeros(len(test))
    for p in pred:
        x = test[m.blok[p]].to_numpy(float)
        mu, sd = train[m.blok[p]].mean().to_numpy(), train[m.blok[p]].std(ddof=0).to_numpy()
        yhat += f["jalur"][(p, target)] * (((x - mu) / sd) @ f["bobot"][p])
    return train[target].mean() + yhat * train[target].std(ddof=0)


def daya_prediksi(
    data: pd.DataFrame, m: ModelPLS, target: str, seed: int, k: int = 5, ulang: int = 5
) -> dict[str, float]:
    """Validasi silang k x ulang (skema sama dengan Tahap 4): Q2_predict (vs rata-rata data latih),
    RMSE PLS vs benchmark regresi linear pada indikator; untuk target biner juga AUC."""
    biner = set(data[target].unique()) <= {0, 1}
    cv = (RepeatedStratifiedKFold if biner else RepeatedKFold)(
        n_splits=k, n_repeats=ulang, random_state=seed
    )
    x_lm = [i for p in m.jalur[target] for i in m.blok[p]]
    sse = {"pls": 0.0, "lm": 0.0, "naif": 0.0}
    auc = []
    for tr, te in cv.split(data, data[target] if biner else None):
        a, b = data.iloc[tr], data.iloc[te]
        y = b[target].to_numpy(float)
        p_pls = _prediksi(a, b, m, target)
        xa = np.column_stack([np.ones(len(a)), a[x_lm].to_numpy(float)])
        xb = np.column_stack([np.ones(len(b)), b[x_lm].to_numpy(float)])
        p_lm = xb @ _ols(a[target].to_numpy(float), xa)
        sse["pls"] += np.sum((y - p_pls) ** 2)
        sse["lm"] += np.sum((y - p_lm) ** 2)
        sse["naif"] += np.sum((y - a[target].mean()) ** 2)
        if biner:
            auc.append(roc_auc_score(y, p_pls))
    n_tot = len(data) * ulang
    out = {
        "q2_predict": 1 - sse["pls"] / sse["naif"],
        "rmse_pls": np.sqrt(sse["pls"] / n_tot),
        "rmse_lm": np.sqrt(sse["lm"] / n_tot),
    }
    if biner:
        out |= {"auc": float(np.mean(auc)), "auc_sd": float(np.std(auc, ddof=1))}
    return out


# ---------------------------------------------------------------------------
# Satu model lengkap
# ---------------------------------------------------------------------------
@dataclass
class HasilModel:
    target: str
    n: int
    fit: dict[str, Any]
    tabel: dict[str, pd.DataFrame] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)


def analisis_model(data: pd.DataFrame, target: str, cfg: dict[str, Any]) -> HasilModel:
    """Estimasi, pengukuran, bootstrap, f2/VIF, dan (untuk target satu indikator) daya prediksi."""
    sc, seed = cfg["sem"], cfg["seed"]
    m = spesifikasi(target, cfg["influence"]["kontrol"])
    data = data[m.indikator].dropna().reset_index(drop=True)
    fit = estimasi(data, m)
    n = len(data)
    bj, bl, bh, gagal = bootstrap(data, m, sc["n_bootstrap"], seed)
    fv = f2_vif(m, fit).set_index("prediktor")
    rows = []
    for (p, e), v in fit["jalur"].items():
        rows.append(
            {
                "model": target,
                "prediktor": p,
                "jenis": "strategi" if p in STRATEGI else "kontrol",
                "koef": v,
                **_uji(v, bj[f"{p}->{e}"], n),
                "p_koef_positif": float((bj[f"{p}->{e}"] > 0).mean()),
                "f2": fv.loc[p, "f2"],
                "vif_inner": fv.loc[p, "vif_inner"],
            }
        )
    jalur = pd.DataFrame(rows)
    s = jalur["jenis"] == "strategi"
    jalur.loc[s, "p_holm"] = stats.holm(jalur.loc[s, "p"])
    loading = pd.DataFrame(
        [
            {
                "model": target,
                "konstruk": k,
                "indikator": i,
                "loading": lam,
                "bobot": w,
                **_uji(lam, bl[i], n),
            }
            for k in m.blok
            if len(m.blok[k]) > 1
            for i, lam, w in zip(m.blok[k], fit["loading"][k], fit["bobot"][k])
        ]
    )
    rel = reliabilitas(data, m, fit)
    rel.insert(0, "model", target)
    h = htmt(data, m.blok).stack().dropna().rename("htmt").reset_index()
    h.columns = ["konstruk_a", "konstruk_b", "htmt"]
    h["htmt_ci_atas"] = [bh[f"{a}|{b}"].quantile(0.95) for a, b in zip(h.konstruk_a, h.konstruk_b)]
    h.insert(0, "model", target)
    fl = fornell_larcker(m, fit, rel.drop(columns="model"))
    hasil = HasilModel(target, n, fit)
    hasil.tabel = {"jalur": jalur, "loading": loading, "reliabilitas": rel, "htmt": h, "fl": fl}
    hasil.info = {
        "r2": fit["r2"][target],
        "r2_adj": 1 - (1 - fit["r2"][target]) * (n - 1) / (n - len(m.jalur[target]) - 1),
        "iterasi": fit["iterasi"],
        "konvergen": fit["konvergen"],
        "boot_gagal": gagal,
    }
    if len(m.blok[target]) == 1:
        hasil.info |= daya_prediksi(data, m, target, seed, sc["cv_lipatan"], sc["cv_ulang"])
    return hasil


# ---------------------------------------------------------------------------
# Perbandingan dengan metode inti Tahap 4
# ---------------------------------------------------------------------------
def perbandingan(
    hasil: dict[str, HasilModel], reg: pd.DataFrame, gab: pd.DataFrame
) -> pd.DataFrame:
    """Satu baris per strategi: jalur PLS tiap model, OLS/logit terstandar, RF, peringkat gabungan."""
    out = gab.set_index("strategi")[["nama", "perm_importance", "peringkat"]].rename(
        columns={"perm_importance": "rf_perm_importance", "peringkat": "peringkat_tahap4"}
    )
    for model, kol in (("ols_y_obj", "ols_y_obj"), ("logit_naik_penjualan", "logit_naik")):
        r = reg[reg["model"] == model].set_index("variabel")
        out[f"{kol}_koef"] = r["koef"]
        out[f"{kol}_p"] = r["p"]
    for t, h in hasil.items():
        j = h.tabel["jalur"].set_index("prediktor")
        out[f"pls_{t}_koef"] = j["koef"]
        out[f"pls_{t}_p_holm"] = j["p_holm"]
        out[f"pls_{t}_f2"] = j["f2"]
    out["peringkat_pls_naik"] = out["pls_naik_penjualan_koef"].rank(ascending=False).astype(int)
    out["peringkat_pls_y_obj"] = out["pls_y_obj_koef"].rank(ascending=False).astype(int)
    return out.reindex(STRATEGI).reset_index().rename(columns={"index": "strategi"})


@dataclass
class SemReport:
    hasil: dict[str, HasilModel]
    tabel: dict[str, pd.DataFrame] = field(default_factory=dict)
    grafik: dict[str, Any] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)


def siapkan_data(feat: pd.DataFrame, clean: pd.DataFrame) -> pd.DataFrame:
    """data_features + butir Y1-Y8 dari data_clean (digabung lewat id_responden)."""
    return feat.merge(clean[["id_responden", *BUTIR_Y]], on="id_responden", how="left")


def analisis(
    data: pd.DataFrame,
    reg: pd.DataFrame,
    gab: pd.DataFrame,
    cv: pd.DataFrame,
    cfg: dict[str, Any],
) -> SemReport:
    """Tiga model PLS-SEM + perbandingan dengan regresi dan Random Forest (tabel Tahap 4)."""
    utama = data[data["sampel_utama"] == 1]
    hasil = {
        "y_obj": analisis_model(utama, "y_obj", cfg),
        "naik_penjualan": analisis_model(utama, "naik_penjualan", cfg),
        "persepsi": analisis_model(data, "persepsi", cfg),
    }
    rep = SemReport(hasil)
    for nm in ("jalur", "loading", "reliabilitas", "htmt"):
        rep.tabel[nm] = pd.concat([h.tabel[nm] for h in hasil.values()], ignore_index=True)
    rep.tabel["fornell_larcker"] = hasil["y_obj"].tabel["fl"].reset_index(names="konstruk")
    rep.tabel["model"] = pd.DataFrame(
        [{"model": t, "nama": NAMA_MODEL[t], "n": h.n, **h.info} for t, h in hasil.items()]
    )
    rep.tabel["perbandingan"] = perbandingan(hasil, reg, gab)
    k = rep.tabel["perbandingan"]
    auc = cv[(cv["target"] == "naik_penjualan") & (cv["metrik"] == "auc")].set_index("model")
    rep.info = {
        "n_boot": cfg["sem"]["n_bootstrap"],
        "rho_peringkat": float(st.spearmanr(k["peringkat_pls_naik"], k["peringkat_tahap4"])[0]),
        "auc_logistik": float(auc.loc["logistik", "rata_rata"]),
        "auc_rf": float(auc.loc["random_forest", "rata_rata"]),
    }
    return rep


def buat_grafik(rep: SemReport) -> dict[str, Any]:
    from umkm import viz
    from umkm.pengaruh import NAMA_VARIABEL

    j = rep.tabel["jalur"]
    j = j[j["jenis"] == "strategi"].copy()
    pendek = {"y_obj": "y_obj", "naik_penjualan": "naik", "persepsi": "persepsi"}
    j["label"] = [f"{NAMA_VARIABEL[p]} -> {pendek[m]}" for p, m in zip(j.prediktor, j.model)]
    j = j.set_index("label")
    fig_jalur = viz.dot_ci(
        j["koef"],
        j["ci_bawah"],
        j["ci_atas"],
        "Koefisien jalur PLS-SEM: strategi terhadap tiga ukuran kinerja",
        "Koefisien jalur terstandar (interval bootstrap 95%)",
        subjudul=f"Bootstrap {rep.info['n_boot']}x; biru = interval tidak mencakup nol",
        sorot=((j["ci_bawah"] > 0) | (j["ci_atas"] < 0)).tolist(),
        referensi=0,
        teks_tambahan=[f"f2 {v:.2f}" for v in j["f2"]],
    )
    ld = rep.tabel["loading"]
    ld = ld[ld["model"].isin(["y_obj", "persepsi"]) & ~ld.duplicated("indikator")].set_index(
        "indikator"
    )
    fig_loading = viz.dot_ci(
        ld["loading"],
        ld["ci_bawah"],
        ld["ci_atas"],
        "Loading luar indikator (model pengukuran PLS-SEM)",
        "Loading (interval bootstrap 95%); garis = ambang 0,708",
        subjudul="X1-X4 dari model y_obj (n=116), Y1-Y8 dari model persepsi (n=149)",
        sorot=(ld["ci_bawah"] >= 0.708).tolist(),
        referensi=0.708,
    )
    return {"sem_jalur": fig_jalur, "sem_loading": fig_loading}


def run(cfg: dict[str, Any] | None = None) -> SemReport:
    """Baca data, jalankan PLS-SEM, tulis tabel, grafik, log, ringkasan."""
    from umkm import config, io, viz
    from umkm.sem_teks import build_log, build_ringkasan

    cfg = cfg or config.load_config()
    reports = config.path("reports")
    feat = pd.read_csv(config.path("processed") / "data_features.csv")
    clean = pd.read_csv(config.path("processed") / "data_clean.csv")
    reg = pd.read_csv(reports / "tables" / "pengaruh_regresi.csv")
    gab = pd.read_csv(reports / "tables" / "pengaruh_gabungan.csv")
    cv = pd.read_csv(reports / "tables" / "pengaruh_cv_ringkas.csv")
    rep = analisis(siapkan_data(feat, clean), reg, gab, cv, cfg)
    for nm, tab in rep.tabel.items():
        io.write_csv(tab, reports / "tables" / f"sem_{nm}.csv")
    for nm, fig in buat_grafik(rep).items():
        rep.grafik[nm] = viz.simpan(fig, reports / "figures" / f"{nm}.png")
    io.write_text(build_log(rep, cfg), reports / "sem_log.md")
    io.write_text(build_ringkasan(rep, cfg), reports / "sem_ringkasan.md")
    return rep
