"""Tahap 4: analisis pengaruh strategi terhadap kinerja penjualan (asosiasi, bukan kausal).

Membaca data_features.csv; menulis reports/tables/pengaruh_*.csv, reports/figures/pengaruh_*.png
dan shap_*.png, serta reports/pengaruh_log.md dan pengaruh_ringkasan.md.

Target utama klasifikasi `naik_penjualan` (logit + Random Forest) menjadi dasar bobot
rekomendasi; `y_obj` dilaporkan lewat OLS HC3 dan CV regresi (D26). Di sampel utama,
naik_penjualan = 0 berarti responden menulis omzet DAN transaksi sebelum = sesudah, jadi
kontrasnya "melaporkan kenaikan" vs "melaporkan angka sama".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as st

from umkm import models, stats, viz
from umkm.eda import NAMA_KONSTRUK

ALPHA = 0.05
NAMA_VARIABEL = {
    **{k: v for k, v in NAMA_KONSTRUK.items() if k.startswith("x")},
    "lama_usaha_pra_mp": "Lama usaha sebelum MP",
    "lama_di_mp": "Lama di marketplace",
    "jumlah_platform": "Jumlah platform",
    "log_omzet_sebelum": "Omzet sebelum (log)",
}
NAMA_TARGET = {
    "naik_penjualan": "naik_penjualan (logit)",
    "y_obj": "y_obj (OLS)",
    "d_omzet": "d_omzet (OLS)",
    "d_trx": "d_trx (OLS)",
    "y_pelanggan_baru": "y_pelanggan_baru (OLS)",
}


def _nama(cols) -> list[str]:
    return [NAMA_VARIABEL.get(c, c) for c in cols]


# ---------------------------------------------------------------------------
# Regresi utama, moderasi, sensitivitas
# ---------------------------------------------------------------------------
def regresi_utama(
    df: pd.DataFrame, strategi: list[str], kontrol: list[str]
) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    """Logit naik_penjualan dan OLS y_obj dengan prediktor strategi + kontrol (terstandar)."""
    x = df[strategi + kontrol]
    lg, info_lg = stats.logit_or(df["naik_penjualan"], x)
    ols, info_ols = stats.ols_hc3(df["y_obj"], x)
    lg["sd_poin"] = lg["variabel"].map(x.std(ddof=1))
    lg["peluang_minus_1sd"] = [stats.peluang_logit(info_lg["const"], k, -1) for k in lg["koef"]]
    lg["peluang_plus_1sd"] = [stats.peluang_logit(info_lg["const"], k, 1) for k in lg["koef"]]
    lg.insert(0, "model", "logit_naik_penjualan")
    ols.insert(0, "model", "ols_y_obj")
    out = pd.concat([lg, ols], ignore_index=True)
    out["jenis"] = np.where(out["variabel"].isin(strategi), "strategi", "kontrol")
    strat = out["jenis"] == "strategi"  # Holm per model untuk 4 uji strategi (D23)
    out.loc[strat, "p_holm"] = out[strat].groupby("model")["p"].transform(stats.holm)
    info = {"logit_naik_penjualan": info_lg, "ols_y_obj": info_ols}
    info["lr_blok_strategi"] = stats.logit_lr_blok(df["naik_penjualan"], x, strategi)
    diag = stats.ols_diagnostik(df["y_obj"], x)
    diag["id_cook_maks"] = df.loc[diag.pop("baris_cook_maks"), "id_responden"]
    info["ols_diagnostik"] = diag
    info["vif_maks"] = float(stats.vif(df, strategi + kontrol)["vif"].max())
    return out, info


def pola_isian(df: pd.DataFrame) -> pd.DataFrame:
    """Bandingkan kelompok naik_penjualan 1 vs 0 pada penanda gaya mengisi kuesioner.

    Kelompok 0 di sampel utama = menulis angka omzet dan transaksi yang sama persis; tabel ini
    memeriksa apakah mereka juga berbeda dalam pola isian lain (bukan hanya kinerja).
    """
    omzet = np.expm1(df["log_omzet_sebelum"]).round()
    indikator = {
        "jawaban seragam (D20)": df["flag_jawaban_seragam"] == 1,
        "omzet sebelum kelipatan Rp1 jt": (omzet % 1_000_000) == 0,
        "memakai 1 platform saja": df["jumlah_platform"] == 1,
    }
    numerik = {
        "lama di marketplace (tahun)": df["lama_di_mp"],
        "lama usaha sebelum MP (tahun)": df["lama_usaha_pra_mp"],
        "omzet sebelum (Rp jt)": omzet / 1e6,
        "skor persepsi kinerja (1-5)": df["y_persepsi"],
    }
    g1, g0 = df["naik_penjualan"] == 1, df["naik_penjualan"] == 0
    rows = []
    for nama, v in indikator.items():
        tab = [[(v & g1).sum(), (~v & g1).sum()], [(v & g0).sum(), (~v & g0).sum()]]
        rows.append(
            {
                "penanda": nama,
                "jenis": "proporsi",
                "naik_1": v[g1].mean(),
                "naik_0": v[g0].mean(),
                "p": st.fisher_exact(tab)[1],
                "uji": "Fisher",
            }
        )
    for nama, v in numerik.items():
        mw = stats.mann_whitney(v[g1], v[g0])
        rows.append(
            {
                "penanda": nama,
                "jenis": "median",
                "naik_1": mw["median_1"],
                "naik_0": mw["median_0"],
                "p": mw["p"],
                "uji": "Mann-Whitney",
            }
        )
    out = pd.DataFrame(rows)
    out["p_holm"] = stats.holm(out["p"])
    return out


def moderasi(
    df: pd.DataFrame, strategi: list[str], kontrol: list[str], moderator: list[str]
) -> pd.DataFrame:
    """Uji interaksi strategi x moderator satu per satu (model utama + satu suku interaksi).

    Suku interaksi = z(strategi) * z(moderator); Holm per model (keluarga = semua pasangan).
    """
    rows = []
    for model, target in (("logit_naik_penjualan", "naik_penjualan"), ("ols_y_obj", "y_obj")):
        fungsi = stats.logit_or if model.startswith("logit") else stats.ols_hc3
        z = stats.standarkan(df[strategi + kontrol])
        for s in strategi:
            for m in moderator:
                x = z.copy()
                x["interaksi"] = z[s] * z[m]
                try:
                    tab, _ = fungsi(df[target], x)
                except ValueError:
                    continue
                r = tab.set_index("variabel").loc["interaksi"]
                rows.append(
                    {
                        "model": model,
                        "strategi": s,
                        "moderator": m,
                        "koef": r["koef"],
                        "ci_bawah": r["ci_bawah"],
                        "ci_atas": r["ci_atas"],
                        "p": r["p"],
                    }
                )
    out = pd.DataFrame(rows)
    out["p_holm"] = out.groupby("model")["p"].transform(lambda p: stats.holm(p))
    return out


def daftar_varian(
    utama: pd.DataFrame, semua: pd.DataFrame, kontrol: list[str], tanpa_id: list[str]
) -> list[dict[str, Any]]:
    """Varian sensitivitas (plan/04 langkah 7): data, kontrol, dan target per varian."""
    tanpa_log = [k for k in kontrol if k != "log_omzet_sebelum"]
    base = ["naik_penjualan", "y_obj"]
    return [
        {
            "varian": "utama",
            "ket": "sampel utama (n=116)",
            "data": utama,
            "kontrol": kontrol,
            "target": base,
        },
        {
            "varian": "a_tanpa_winsor",
            "ket": "tanpa baris terwinsor",
            "data": utama[utama["flag_outlier"] == 0],
            "kontrol": kontrol,
            "target": base,
        },
        {
            "varian": "b_tanpa_omzet_tetap",
            "ket": "tanpa omzet sebelum = sesudah",
            "data": utama[utama["arah_omzet"] != "sama"],
            "kontrol": kontrol,
            "target": base,
        },
        {
            "varian": "c_semua_149",
            "ket": "semua 149 responden",
            "data": semua,
            "kontrol": kontrol,
            "target": base,
        },
        {
            "varian": "d_target_d_omzet",
            "ket": "target hanya d_omzet",
            "data": utama,
            "kontrol": kontrol,
            "target": ["d_omzet"],
        },
        {
            "varian": "d_target_d_trx",
            "ket": "target hanya d_trx",
            "data": utama,
            "kontrol": kontrol,
            "target": ["d_trx"],
        },
        {
            "varian": "d_target_pelanggan_baru",
            "ket": "target y_pelanggan_baru",
            "data": utama,
            "kontrol": kontrol,
            "target": ["y_pelanggan_baru"],
        },
        {
            "varian": "e_tanpa_seragam",
            "ket": "tanpa jawaban seragam (D20)",
            "data": utama[utama["flag_jawaban_seragam"] == 0],
            "kontrol": kontrol,
            "target": base,
        },
        {
            "varian": "f_tanpa_" + "_".join(tanpa_id),
            "ket": f"tanpa {', '.join(tanpa_id)} (D25)",
            "data": utama[~utama["id_responden"].isin(tanpa_id)],
            "kontrol": kontrol,
            "target": base,
        },
        {
            "varian": "g_tanpa_log_omzet",
            "ket": "tanpa kontrol log_omzet_sebelum",
            "data": utama,
            "kontrol": tanpa_log,
            "target": base,
        },
    ]


def sensitivitas(varian: list[dict[str, Any]], strategi: list[str], min_kelas: int) -> pd.DataFrame:
    """Koefisien strategi tiap varian x target, beserta peringkat dan status."""
    rows = []
    for v in varian:
        d = v["data"]
        for target in v["target"]:
            logit = target == "naik_penjualan"
            base = {"varian": v["varian"], "keterangan": v["ket"], "target": NAMA_TARGET[target]}
            n0, n1 = int((d[target] == 0).sum()), int((d[target] == 1).sum())
            if logit and min(n0, n1) < min_kelas:
                rows.append(
                    {
                        **base,
                        "n": len(d),
                        "status": f"tidak dihitung: kelas terlalu kecil ({n1} vs {n0})",
                    }
                )
                continue
            fungsi = stats.logit_or if logit else stats.ols_hc3
            try:
                tab, info = fungsi(d[target], d[strategi + v["kontrol"]])
            except ValueError as e:
                rows.append({**base, "n": len(d), "status": str(e)})
                continue
            tab = tab[tab["variabel"].isin(strategi)].copy()
            tab["peringkat"] = tab["koef"].rank(ascending=False, method="min").astype(int)
            for _, r in tab.iterrows():
                rows.append(
                    {
                        **base,
                        "n": info["n"],
                        "variabel": r["variabel"],
                        "koef": r["koef"],
                        "p": r["p"],
                        "peringkat": r["peringkat"],
                        "status": "ok",
                    }
                )
    return pd.DataFrame(rows)


def ringkas_sensitivitas(sens: pd.DataFrame) -> pd.DataFrame:
    """Per varian x target: strategi teratas, strategi bermakna positif dan negatif (p < 0,05,
    tanpa koreksi), serta rho peringkat vs varian utama target yang sama dan vs logit utama."""
    ok = sens[sens["status"] == "ok"]
    ref_logit = ok[(ok["varian"] == "utama") & (ok["target"] == NAMA_TARGET["naik_penjualan"])]
    ref_logit = ref_logit.set_index("variabel")
    rows = []
    for (var, tgt), g in sens.groupby(["varian", "target"], sort=False):
        if (g["status"] != "ok").all():
            rows.append(
                {"varian": var, "target": tgt, "n": g["n"].iloc[0], "status": g["status"].iloc[0]}
            )
            continue
        g = g.set_index("variabel")
        ref = ok[(ok["varian"] == "utama") & (ok["target"] == tgt)].set_index("variabel")
        if ref.empty:  # target alternatif: dibandingkan dengan OLS y_obj utama
            ref = ok[(ok["varian"] == "utama") & (ok["target"] == NAMA_TARGET["y_obj"])]
            ref = ref.set_index("variabel")
        rho = st.spearmanr(g.loc[ref.index, "koef"], ref["koef"])[0]
        rho_logit = st.spearmanr(g.loc[ref_logit.index, "koef"], ref_logit["koef"])[0]
        sig = g["p"] < ALPHA
        neg = g["koef"] < 0
        rows.append(
            {
                "varian": var,
                "target": tgt,
                "n": int(g["n"].iloc[0]),
                "teratas": g["koef"].idxmax(),
                "bermakna_positif": ", ".join(g.index[sig & ~neg]) or "-",
                "bermakna_negatif": ", ".join(g.index[sig & neg]) or "-",
                "p_min_negatif": g.loc[neg, "p"].min() if neg.any() else np.nan,
                "rho_peringkat_vs_utama": rho,
                "rho_vs_logit_utama": rho_logit,
                "status": "ok",
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Peringkat gabungan
# ---------------------------------------------------------------------------
def peringkat_gabungan(
    reg: pd.DataFrame,
    perm: pd.DataFrame,
    shap_tab: pd.DataFrame,
    boot_ringkas: pd.DataFrame,
    strategi: list[str],
) -> pd.DataFrame:
    """Tabel pengaruh per strategi: tiga sumber (mentah + ternormalisasi), skor gabungan,
    interval bootstrap, peluang peringkat, dan penanda `meyakinkan` (CI koef logit > 0)."""
    koef = reg[reg["model"] == "logit_naik_penjualan"].set_index("variabel").loc[strategi]
    pm = perm.groupby("variabel")["importance"].mean().loc[strategi]
    sh = shap_tab.set_index("variabel").loc[strategi]
    g = models.skor_gabungan(koef["koef"], pm, sh["mean_abs_shap"], sh["arah_rho"])
    out = pd.DataFrame(
        {
            "strategi": strategi,
            "nama": _nama(strategi),
            "koef_logit": koef["koef"].to_numpy(),
            "or_logit": koef["or"].to_numpy(),
            "p_logit": koef["p"].to_numpy(),
            "perm_importance": pm.to_numpy(),
            "mean_abs_shap": sh["mean_abs_shap"].to_numpy(),
            "arah_shap": sh["arah_rho"].to_numpy(),
        }
    )
    out = pd.concat([out, g.reset_index(drop=True)], axis=1)
    out = out.merge(boot_ringkas, on="strategi", how="left")
    out["peringkat"] = out["pengaruh"].rank(ascending=False, method="min").astype(int)
    out["meyakinkan"] = out["koef_ci_bawah"] > 0
    return out.sort_values("peringkat").reset_index(drop=True)


def bobot_rekomendasi(gab: pd.DataFrame, minimum: float) -> pd.Series:
    """Bobot `pengaruh_s` untuk Tahap 6 (D26): skor gabungan x peluang bootstrap koef logit > 0,
    dengan batas bawah `minimum` agar strategi lemah masih bisa muncul bila gap-nya besar."""
    return (gab["pengaruh"] * gab["p_koef_positif"]).clip(lower=minimum)


def gabungan_titik(
    d: pd.DataFrame, strategi: list[str], kontrol: list[str], c: dict[str, Any], cv, seed: int
) -> pd.DataFrame:
    """Skor pengaruh gabungan (tanpa bootstrap) untuk satu data: logit + permutation CV + SHAP."""
    x = d[strategi + kontrol].reset_index(drop=True)
    y = d["naik_penjualan"].reset_index(drop=True)
    koef = stats.logit_or(y, x)[0].set_index("variabel")["koef"]
    rf = models.rf_klasifikasi(c["rf"], seed)
    pm = models.permutation_cv(rf, x, y, cv, c["skor_importance"], c["permutation_repeats"], seed)
    pm = pm.groupby("variabel")["importance"].mean()
    sh = models.ringkas_shap(models.shap_kelas_positif(rf.fit(x, y), x), x).set_index("variabel")
    g = models.skor_gabungan(
        koef[strategi],
        pm[strategi],
        sh.loc[strategi, "mean_abs_shap"],
        sh.loc[strategi, "arah_rho"],
    )
    g["peringkat"] = g["pengaruh"].rank(ascending=False, method="min").astype(int)
    return g.rename_axis("strategi").reset_index()


def konsistensi_sumber(gab: pd.DataFrame) -> pd.DataFrame:
    """Korelasi peringkat (Spearman) antar tiga sumber pengaruh pada 4 strategi."""
    sumber = {"koef_logit": "koef_logit", "permutation": "perm_importance", "shap": "n_shap"}
    nama = list(sumber)
    rows = []
    for i, a in enumerate(nama):
        for b in nama[i + 1 :]:
            rho = st.spearmanr(gab[sumber[a]], gab[sumber[b]])[0]
            rows.append({"sumber_a": a, "sumber_b": b, "rho_peringkat": rho})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------
@dataclass
class PengaruhReport:
    """Tabel, info model, dan path grafik Tahap 4."""

    tabel: dict[str, pd.DataFrame] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    grafik: dict[str, Any] = field(default_factory=dict)


def analisis(df_semua: pd.DataFrame, cfg: dict[str, Any]) -> PengaruhReport:
    """Jalankan seluruh analisis Tahap 4 dan kembalikan tabel (tanpa menulis berkas)."""
    c = cfg["influence"]
    seed = cfg["seed"]
    strategi, kontrol = c["strategi"], c["kontrol"]
    utama = df_semua[df_semua["sampel_utama"] == 1].reset_index(drop=True)
    x, y = utama[strategi + kontrol], utama["naik_penjualan"]
    rep = PengaruhReport()
    t = rep.tabel

    t["regresi"], rep.info["regresi"] = regresi_utama(utama, strategi, kontrol)

    cv_k = models.skema_cv(True, cfg["cv"]["n_splits"], cfg["cv"]["n_repeats"], seed)
    cv_r = models.skema_cv(False, cfg["cv"]["n_splits"], cfg["cv"]["n_repeats"], seed)
    lip_k = models.cv_metrik(
        models.kandidat_klasifikasi(c["rf"], seed), x, y, cv_k, models.SKOR_KLASIFIKASI
    )
    lip_r = models.cv_metrik(
        models.kandidat_regresi(c["rf"], seed), x, utama["y_obj"], cv_r, models.SKOR_REGRESI
    )
    tanpa_id = c["sensitivitas_tanpa_id"]
    u2 = utama[~utama["id_responden"].isin(tanpa_id)].reset_index(drop=True)
    x2 = u2[strategi + kontrol]
    lip_r2 = models.cv_metrik(
        models.kandidat_regresi(c["rf"], seed), x2, u2["y_obj"], cv_r, models.SKOR_REGRESI
    )
    nama_y2 = "y_obj_tanpa_" + "_".join(tanpa_id)
    lip_k.insert(0, "target", "naik_penjualan")
    lip_r.insert(0, "target", "y_obj")
    lip_r2.insert(0, "target", nama_y2)
    t["cv_per_lipatan"] = pd.concat([lip_k, lip_r, lip_r2], ignore_index=True)
    t["cv_ringkas"] = pd.concat(
        [
            models.ringkas_cv(lip_k).assign(target="naik_penjualan"),
            models.ringkas_cv(lip_r).assign(target="y_obj"),
            models.ringkas_cv(lip_r2).assign(target=nama_y2),
        ],
        ignore_index=True,
    )[["target", "model", "metrik", "rata_rata", "sd", "n_lipatan"]]
    n_sp, n_rep = cfg["cv"]["n_splits"], cfg["cv"]["n_repeats"]
    kand_r = models.kandidat_regresi(c["rf"], seed)
    t["r2_oof"] = pd.concat(
        [
            models.r2_oof(kand_r, x, utama["y_obj"], n_sp, n_rep, seed).assign(target="y_obj"),
            models.r2_oof(kand_r, x2, u2["y_obj"], n_sp, n_rep, seed).assign(target=nama_y2),
        ],
        ignore_index=True,
    )
    t["confusion"] = pd.DataFrame(
        [
            {"model": nm, **models.confusion_cv(m, x, y, cv_k)}
            for nm, m in models.kandidat_klasifikasi(c["rf"], seed).items()
            if nm != "dummy_mayoritas"
        ]
    )
    t["pola_isian"] = pola_isian(utama)

    rf = models.rf_klasifikasi(c["rf"], seed)
    t["permutation"] = models.permutation_cv(
        rf, x, y, cv_k, c["skor_importance"], c["permutation_repeats"], seed
    )
    rf_akhir = models.rf_klasifikasi(c["rf"], seed).fit(x, y)
    sv = models.shap_kelas_positif(rf_akhir, x)
    t["shap"] = models.ringkas_shap(sv, x)
    t["shap"]["mean_shap_naik_1"] = sv[y.to_numpy() == 1].mean(axis=0)
    t["shap"]["mean_shap_naik_0"] = sv[y.to_numpy() == 0].mean(axis=0)
    rep.info["shap_values"] = sv
    rep.info["x"] = x

    boot = models.bootstrap_pengaruh(
        x,
        y,
        strategi,
        c["rf"],
        c["skor_importance"],
        c["permutation_repeats"],
        cfg["bootstrap_n"],
        seed,
    )
    t["bootstrap"] = boot
    boot_r = models.ringkas_bootstrap(boot, strategi)
    rep.info["n_boot"] = len(boot)
    t["gabungan"] = peringkat_gabungan(t["regresi"], t["permutation"], t["shap"], boot_r, strategi)
    t["gabungan"]["bobot_rekomendasi"] = bobot_rekomendasi(t["gabungan"], c["bobot_minimum"])
    t["konsistensi"] = konsistensi_sumber(t["gabungan"])
    var_gab = {
        "utama": utama,
        "c_semua_149": df_semua,
        "e_tanpa_seragam": utama[utama["flag_jawaban_seragam"] == 0],
    }
    t["gabungan_sensitivitas"] = pd.concat(
        [
            gabungan_titik(d, strategi, kontrol, c, cv_k, seed).assign(varian=v)
            for v, d in var_gab.items()
        ],
        ignore_index=True,
    )

    t["moderasi"] = moderasi(utama, strategi, kontrol, c["moderator"])
    varian = daftar_varian(utama, df_semua, kontrol, c["sensitivitas_tanpa_id"])
    t["sensitivitas"] = sensitivitas(varian, strategi, c["min_kelas_logit"])
    t["sensitivitas_ringkas"] = ringkas_sensitivitas(t["sensitivitas"])
    rep.info["n_utama"] = len(utama)
    rep.info["n_naik"] = int(y.sum())
    sama = (utama["arah_omzet"] == "sama") & (utama["arah_trx"] == "sama")
    rep.info["n_0_angka_sama"] = int((sama & (y == 0)).sum())
    rep.info["id_omzet_turun_naik"] = utama.loc[
        (utama["arah_omzet"] == "turun") & (y == 1), "id_responden"
    ].tolist()
    seragam = utama["flag_jawaban_seragam"] == 1
    rep.info["n_seragam"] = int(seragam.sum())
    rep.info["n_seragam_naik"] = int((seragam & (y == 1)).sum())
    rep.info["tanpa_id"] = tanpa_id
    return rep


def buat_grafik(rep: PengaruhReport, strategi: list[str]) -> dict[str, Any]:
    """Grafik Tahap 4 (Figure, belum disimpan)."""
    t = rep.tabel
    figs = {}
    g = t["gabungan"]
    figs["pengaruh_peringkat"] = viz.dot_ci(
        g.set_index("nama")["pengaruh"],
        g["pengaruh_ci_bawah"],
        g["pengaruh_ci_atas"],
        "Skor pengaruh gabungan tiap strategi",
        "Skor pengaruh (0-1; 1 = paling berhubungan dengan naik_penjualan)",
        subjudul=f"Titik = estimasi; garis = interval bootstrap 95% ({rep.info['n_boot']}x). "
        "Teks = peluang menjadi peringkat 1.",
        teks_tambahan=[f"P(#1) {p:.0%}" for p in g["p_peringkat_1"]],
    )
    figs["pengaruh_peringkat"].axes[0].set_xticks([0, 0.25, 0.5, 0.75, 1])
    lg = t["regresi"][t["regresi"]["model"] == "logit_naik_penjualan"].sort_values(
        "or", ascending=False
    )
    figs["pengaruh_odds_ratio"] = viz.dot_ci(
        lg.set_index(pd.Index(_nama(lg["variabel"])))["or"],
        lg["or_ci_bawah"],
        lg["or_ci_atas"],
        "Odds melaporkan penjualan naik, per 1 SD skor lebih tinggi",
        "Odds ratio (skala log; 1 = tidak berhubungan)",
        subjudul="Regresi logistik naik_penjualan, sampel utama; biru = strategi, abu-abu = kontrol",
        sorot=lg["jenis"].eq("strategi").tolist(),
        referensi=1.0,
        skala_log=True,
        teks_tambahan=[f"p = {p:.3f}" for p in lg["p"]],
    )
    figs["pengaruh_odds_ratio"].axes[0].set_xticks([0.25, 0.5, 1, 2, 4])
    sh = t["shap"].sort_values("mean_abs_shap", ascending=False)
    figs["shap_ringkas"] = viz.bar_horizontal(
        sh.set_index(pd.Index(_nama(sh["variabel"])))["mean_abs_shap"],
        "Kontribusi rata-rata tiap variabel pada model Random Forest",
        "mean |SHAP| (peluang naik_penjualan)",
        subjudul="Model akhir dilatih dengan seluruh sampel utama; ilustrasi, bukan bukti kausal",
        label_fmt="{:.3f}",
        teks_tambahan=[("arah +" if r > 0 else "arah -") for r in sh["arah_rho"]],
    )
    xs = rep.info["x"]
    j = [list(xs.columns).index(s) for s in strategi]
    figs["shap_arah"] = viz.scatter_panel(
        xs[strategi],
        rep.info["shap_values"][:, j],
        _nama(strategi),
        "Arah hubungan skor strategi dengan prediksi model",
        "Skor strategi (1-5)",
        "Nilai SHAP",
        subjudul="Tiap titik = satu UMKM; di atas garis = skor itu menaikkan prediksi peluang naik",
        teks_panel=[
            f"rho = {r:.2f}" for r in t["shap"].set_index("variabel").loc[strategi, "arah_rho"]
        ],
    )
    for target, nm, judul in (
        (NAMA_TARGET["naik_penjualan"], "pengaruh_sensitivitas_logit", "logit naik_penjualan"),
        (NAMA_TARGET["y_obj"], "pengaruh_sensitivitas_ols", "OLS y_obj"),
    ):
        s = t["sensitivitas"]
        s = s[(s["target"] == target) & (s["status"] == "ok")]
        piv = s.pivot(index="varian", columns="variabel", values="koef")[strategi]
        piv = piv.loc[[v for v in s["varian"].unique()]]
        pv = s.pivot(index="varian", columns="variabel", values="p")[strategi].loc[piv.index]
        anot = piv.map(lambda v: f"{v:.2f}") + pv.map(lambda p: "*" if p < ALPHA else "")
        piv.columns = _nama(strategi)
        anot.columns = piv.columns
        ket = s.drop_duplicates("varian").set_index("varian")["keterangan"]
        piv.index = anot.index = [ket[v] for v in piv.index]
        figs[nm] = viz.heatmap(
            piv,
            f"Koefisien strategi pada tiap skenario sensitivitas ({judul})",
            "Strategi",
            "Skenario",
            subjudul="Koefisien terstandar; * = p < 0,05 (tanpa koreksi uji berganda)",
            anotasi=anot,
            label_skala="koefisien terstandar",
        )
    return figs


def run(cfg: dict[str, Any] | None = None) -> PengaruhReport:
    """Baca data_features, jalankan Tahap 4, tulis tabel, grafik, log, dan ringkasan."""
    from umkm import config, io
    from umkm.pengaruh_teks import build_log, build_ringkasan

    cfg = cfg or config.load_config()
    reports = config.path("reports")
    df = pd.read_csv(config.path("processed") / "data_features.csv")
    rep = analisis(df, cfg)
    for nm, tab in rep.tabel.items():
        io.write_csv(tab, reports / "tables" / f"pengaruh_{nm}.csv")
    for nm, fig in buat_grafik(rep, cfg["influence"]["strategi"]).items():
        rep.grafik[nm] = viz.simpan(fig, reports / "figures" / f"{nm}.png")
    io.write_text(build_log(rep, cfg), reports / "pengaruh_log.md")
    io.write_text(build_ringkasan(rep, cfg), reports / "pengaruh_ringkasan.md")
    return rep
