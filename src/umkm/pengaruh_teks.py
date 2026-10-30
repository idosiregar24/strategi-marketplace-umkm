"""Teks Tahap 4: interpretasi grafik, reports/pengaruh_log.md, dan reports/pengaruh_ringkasan.md.

Semua kalimat disusun dari angka di tabel agar tetap benar bila data berubah.
Bahasa asosiasi: "berhubungan dengan", "cenderung", bukan sebab-akibat. Odds ratio ditulis
sebagai odds (bukan peluang) dan dibandingkan antar-UMKM (bukan "kenaikan" di satu UMKM).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from umkm.eda_teks import _a, _daftar, _kapital, _p, _pct
from umkm.features import _md
from umkm.pengaruh import ALPHA, NAMA_TARGET, NAMA_VARIABEL, PengaruhReport

SKENARIO_KETAT = ["c_semua_149", "e_tanpa_seragam"]  # mengubah data cukup banyak


def _n(v: str) -> str:
    return NAMA_VARIABEL.get(v, v)


def _cv(t: dict[str, pd.DataFrame], target: str, model: str, metrik: str) -> float:
    r = t["cv_ringkas"]
    sel = r[(r["target"] == target) & (r["model"] == model) & (r["metrik"] == metrik)]
    return float(sel["rata_rata"].iloc[0])


def _oof(t: dict[str, pd.DataFrame], target: str, model: str, kolom: str) -> float:
    r = t["r2_oof"]
    return float(r[(r["target"] == target) & (r["model"] == model)][kolom].iloc[0])


def fakta(rep: PengaruhReport) -> dict[str, Any]:
    """Angka kunci yang dipakai berulang di log dan ringkasan."""
    t, info = rep.tabel, rep.info
    g = t["gabungan"]
    lg = t["regresi"][t["regresi"]["model"] == "logit_naik_penjualan"].set_index("variabel")
    ols = t["regresi"][t["regresi"]["model"] == "ols_y_obj"].set_index("variabel")
    sens = t["sensitivitas"]
    ok = sens[sens["status"] == "ok"]
    sl = ok[ok["target"] == NAMA_TARGET["naik_penjualan"]]
    sl_lain = sl[sl["varian"] != "utama"]
    so = ok[ok["target"] == NAMA_TARGET["y_obj"]]
    top = g["strategi"].iloc[0]
    y2 = "y_obj_tanpa_" + "_".join(info["tanpa_id"])
    r2 = {
        tg: {m: _oof(t, tg, m, "r2_oof") for m in ("dummy_rata_rata", "linear", "random_forest")}
        for tg in ("y_obj", y2)
    }
    mae = {
        tg: {m: _oof(t, tg, m, "mae_oof") for m in ("dummy_rata_rata", "linear", "random_forest")}
        for tg in ("y_obj", y2)
    }
    negatif = sens[(sens["status"] == "ok") & (sens["p"] < ALPHA) & (sens["koef"] < 0)]
    e = sl[sl["varian"] == "e_tanpa_seragam"].set_index("variabel")
    return {
        "g": g,
        "lg": lg,
        "ols": ols,
        "top": top,
        "sl_lain": sl_lain,
        "n_var_logit_lain": sl_lain["varian"].nunique(),
        "teratas_logit_lain": sl_lain[sl_lain["peringkat"] == 1]
        .groupby("variabel")["varian"]
        .nunique(),
        "bermakna_logit": sl[(sl["p"] < ALPHA) & (sl["koef"] > 0)]
        .groupby("variabel")["varian"]
        .nunique(),
        "n_var_logit": sl["varian"].nunique(),
        "so": so,
        "auc": {
            m: _cv(t, "naik_penjualan", m, "auc")
            for m in ("dummy_mayoritas", "logistik", "random_forest")
        },
        "f1": {
            m: _cv(t, "naik_penjualan", m, "f1_macro")
            for m in ("dummy_mayoritas", "logistik", "random_forest")
        },
        "y2": y2,
        "r2": r2,
        "mae": mae,
        "negatif": negatif,
        "or_tanpa_seragam": {v: float(np.exp(e.at[v, "koef"])) for v in e.index},
        "mod_sig": t["moderasi"][t["moderasi"]["p_holm"] < ALPHA],
        "lr": info["regresi"]["lr_blok_strategi"],
        "diag": info["regresi"]["ols_diagnostik"],
    }


# ---------------------------------------------------------------------------
# Kalimat yang dipakai ulang
# ---------------------------------------------------------------------------
def _kalimat_or(lg: pd.DataFrame, v: str) -> str:
    """Satu strategi: odds ratio per 1 SD plus peluang prediksi di -1 SD dan +1 SD."""
    return (
        f"{_n(v)}: UMKM yang skornya 1 SD (sekitar {_a(lg.at[v, 'sd_poin'], 1)} poin) lebih "
        f"tinggi memiliki odds melaporkan kenaikan {_a(lg.at[v, 'or'])} kali lebih besar "
        f"({_p(lg.at[v, 'p'])}; Holm {_a(lg.at[v, 'p_holm'], 3)}); perkiraan peluangnya "
        f"{_pct(lg.at[v, 'peluang_minus_1sd'])} pada skor 1 SD di bawah rata-rata vs "
        f"{_pct(lg.at[v, 'peluang_plus_1sd'])} pada 1 SD di atas rata-rata (variabel lain di "
        "rata-rata)"
    )


def _kontras(rep: PengaruhReport) -> str:
    i = rep.info
    n0 = i["n_utama"] - i["n_naik"]
    teks = (
        f"Dari {i['n_utama']} UMKM sampel utama, {i['n_naik']} melaporkan omzet atau transaksi "
        f"naik (`naik_penjualan` = 1). {i['n_0_angka_sama']} dari {n0} UMKM sisanya menulis "
        "omzet DAN transaksi yang sama persis sebelum dan sesudah; tidak ada yang melaporkan "
        "keduanya turun. Jadi yang dibandingkan di sini adalah UMKM yang **melaporkan kenaikan** "
        "dengan UMKM yang **melaporkan angka sama**, bukan UMKM yang naik dengan yang turun."
    )
    if i["id_omzet_turun_naik"]:
        teks += (
            f" {', '.join(i['id_omzet_turun_naik'])} dihitung naik karena transaksinya naik "
            "walau omzetnya turun (definisi D13)."
        )
    return teks


def _keterangan_pola(t: dict[str, pd.DataFrame]) -> str:
    p = t["pola_isian"]
    beda = p[p["p_holm"] < ALPHA]
    teks = (
        "Kelompok yang menulis angka sama tidak berbeda bermakna dari kelompok yang naik dalam "
        "pembulatan omzet, jumlah platform, lama usaha, lama di marketplace, maupun besar omzet "
        "(Holm p >= 0,05)"
        if beda.empty
        else f"Kelompok angka sama berbeda pada {_daftar(beda['penanda'].tolist())}"
    )
    seragam = p.set_index("penanda").loc["jawaban seragam (D20)"]
    return teks + (
        f"; jawaban seragam justru lebih sering di kelompok naik ({_pct(seragam['naik_1'])} vs "
        f"{_pct(seragam['naik_0'])}). Penanda ini tidak menunjukkan bahwa kelompok angka sama "
        "sekadar asal mengisi, tetapi penanda tersebut kasar sehingga kemungkinan itu belum "
        "dapat disingkirkan."
    )


def keterbatasan(rep: PengaruhReport) -> list[str]:
    """Daftar keterbatasan yang wajib dibaca bersama hasil Tahap 4."""
    f = fakta(rep)
    i = rep.info
    n_pred = len(f["lg"])
    epv = min(i["n_naik"], i["n_utama"] - i["n_naik"]) / n_pred
    out = [
        (
            '**Arti target.** "Tidak naik" berarti menulis omzet dan transaksi yang sama persis, '
            "bukan turun; kemungkinan sebagian angka sama itu salin-tempel tidak dapat "
            "disingkirkan."
        ),
        (
            "**Data satu waktu dan ingatan responden.** Angka sebelum dan sesudah diisi sekaligus dari "
            "ingatan, tanpa kelompok pembanding yang tidak memakai marketplace. Hasil adalah "
            "keterkaitan, bukan bukti bahwa strategi menyebabkan penjualan naik."
        ),
        (
            "**Sumber yang sama.** Skor strategi dan angka kinerja sama-sama diisi sendiri oleh "
            "responden; UMKM yang menilai dirinya aktif mungkin juga cenderung melaporkan kenaikan "
            "(bias metode bersama)."
        ),
        f"**Jawaban seragam.** {i['n_seragam']} responden sampel utama menjawab semua butir "
        f"strategi dengan angka sama ({i['n_seragam_naik']} di antaranya naik). Tanpa mereka "
        "odds ratio "
        + _daftar(
            [
                f"{_n(v)} {_a(f['lg'].at[v, 'or'])} -> {_a(f['or_tanpa_seragam'][v])}"
                for v in f["g"]["strategi"][:2]
            ]
        )
        + ".",
        (
            f"**Sampel kecil.** n = {i['n_utama']} dengan {n_pred} prediktor (sekitar "
            f"{_a(epv, 1)} kejadian per prediktor); interval kepercayaan lebar dan daya uji "
            "interaksi rendah."
        ),
        (
            "**Instrumen.** Unggah produk (X1) dan promosi (X2) hanya diukur dengan 4 butir (D19), "
            "dan sebagian besar butir didominasi jawaban netral."
        ),
        (
            "**Cakupan.** UMKM kuliner di Pekanbaru yang memakai marketplace; tidak otomatis berlaku "
            "untuk jenis usaha atau kota lain."
        ),
    ]
    return out


# ---------------------------------------------------------------------------
# Interpretasi grafik
# ---------------------------------------------------------------------------
def interpretasi(rep: PengaruhReport) -> dict[str, str]:
    """Satu kalimat interpretasi per grafik."""
    f = fakta(rep)
    g, lg = f["g"], f["lg"]
    s1, s2 = g.iloc[0], g.iloc[1]
    lemah = g[~g["meyakinkan"]]["strategi"].tolist()
    out = {}
    out["pengaruh_peringkat"] = (
        f"{_kapital(_n(s1['strategi']))} memiliki skor pengaruh tertinggi (peringkat 1 pada "
        f"{_pct(s1['p_peringkat_1'])} sampel bootstrap), disusul {_n(s2['strategi'])} "
        f"({_a(s2['pengaruh'])}); {_daftar([_n(s) for s in lemah]) or 'tidak ada'} belum "
        "meyakinkan (interval koefisien logit bootstrap mencakup nol). Skor ini relatif: "
        "strategi teratas selalu bernilai 1."
    )
    strat_sig = [v for v in g["strategi"] if lg.at[v, "p_holm"] < ALPHA]
    out["pengaruh_odds_ratio"] = (
        "Dengan profil usaha dikendalikan, UMKM dengan skor "
        + _daftar([f"{_n(v)} (OR {_a(lg.at[v, 'or'])})" for v in strat_sig])
        + " yang 1 SD lebih tinggi memiliki odds melaporkan kenaikan lebih besar; omzet awal "
        f"yang lebih besar berhubungan dengan odds yang lebih kecil "
        f"(OR {_a(lg.at['log_omzet_sebelum', 'or'])})."
    )
    sh = rep.tabel["shap"].sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    profil = sh[~sh["variabel"].str.startswith("x")].iloc[0]
    out["shap_ringkas"] = (
        f"Pada Random Forest, kontribusi rata-rata terbesar berasal dari {_n(sh['variabel'][0])} "
        f"(mean |SHAP| {_a(sh['mean_abs_shap'][0], 3)}), lalu "
        f"{_daftar([_n(v) for v in sh['variabel'][1:3]])}; di antara variabel profil, "
        f"{_n(profil['variabel'])} paling besar ({_a(profil['mean_abs_shap'], 3)})."
    )
    arah = rep.tabel["shap"].set_index("variabel")
    naik = [s for s in g["strategi"] if arah.at[s, "arah_rho"] >= 0.3]
    datar = [s for s in g["strategi"] if abs(arah.at[s, "arah_rho"]) < 0.3]
    turun = [s for s in g["strategi"] if arah.at[s, "arah_rho"] <= -0.3]
    bag = []
    if naik:
        bag.append(
            f"untuk {_daftar([_n(s) for s in naik])}, skor yang lebih tinggi cenderung "
            "menaikkan prediksi peluang melaporkan kenaikan"
        )
    if datar:
        bag.append(
            f"{_daftar([_n(s) for s in datar])} hampir tidak mengubah prediksi (rho "
            f"{_daftar([_a(arah.at[s, 'arah_rho']) for s in datar])})"
        )
    if turun:
        bag.append(f"{_daftar([_n(s) for s in turun])} berarah negatif")
    out["shap_arah"] = _kapital("; ".join(bag)) + "."
    tl = f["teratas_logit_lain"]
    out["pengaruh_sensitivitas_logit"] = (
        f"{_kapital(_n(f['top']))} tetap teratas di {tl.get(f['top'], 0)} dari "
        f"{f['n_var_logit_lain']} skenario selain utama; strategi yang bermakna (p < 0,05, tanpa "
        "koreksi): "
        + _daftar(
            [f"{_n(v)} ({k} dari {f['n_var_logit']})" for v, k in f["bermakna_logit"].items()]
        )
        + ". Skenario yang paling mengubah data adalah semua 149 responden dan tanpa jawaban "
        "seragam; skenario lain hanya membuang sedikit baris atau satu kontrol."
    )
    so = f["so"]
    out["pengaruh_sensitivitas_ols"] = (
        "Pada OLS y_obj koefisien strategi kecil; strategi bermakna hanya muncul di "
        f"{so[so['p'] < ALPHA]['varian'].nunique()} dari {so['varian'].nunique()} skenario, "
        f"dan hasilnya peka terhadap satu responden ({f['diag']['id_cook_maks']}, Cook's distance "
        f"{_a(f['diag']['cook_maks'])})."
    )
    return out


def _gambar(nama: str, interp: dict[str, str]) -> str:
    return f"![{nama}](figures/{nama}.png)\n\n{interp[nama]}\n"


# ---------------------------------------------------------------------------
# Log teknis
# ---------------------------------------------------------------------------
def build_log(rep: PengaruhReport, cfg: dict[str, Any]) -> str:
    """Susun reports/pengaruh_log.md (rincian teknis)."""
    t, info = rep.tabel, rep.info
    f = fakta(rep)
    interp = interpretasi(rep)
    c = cfg["influence"]
    s = ["# Log Analisis Pengaruh (Tahap 4)\n"]
    s.append(f"Dibuat oleh `umkm.pengaruh` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}.\n")
    s.append("## Rancangan\n")
    s.append(
        f"- Sampel utama n = {info['n_utama']} ({info['n_naik']} naik_penjualan = 1). "
        f"Prediktor: 4 skor strategi + kontrol {', '.join(f'`{k}`' for k in c['kontrol'])}, "
        "semua distandarkan (koefisien per 1 SD)."
    )
    s.append(f"- {_kontras(rep)}")
    s.append(
        "- Target `naik_penjualan` (logit + Random Forest) menjadi dasar bobot rekomendasi; "
        "`y_obj` dilaporkan lewat OLS HC3 dan CV regresi (D26)."
    )
    s.append(
        f"- CV: {cfg['cv']['n_splits']} lipatan x {cfg['cv']['n_repeats']} ulangan, seed "
        f"{cfg['seed']}; Random Forest {c['rf']}. Bootstrap {info['n_boot']} iterasi berhasil "
        f"dari {cfg['bootstrap_n']}. VIF maksimum model {_a(info['regresi']['vif_maks'])}.\n"
    )

    s.append("## 1. Regresi logistik `naik_penjualan` (target utama)\n")
    il = info["regresi"]["logit_naik_penjualan"]
    lr = f["lr"]
    s.append(
        f"n = {il['n']}, pseudo R2 McFadden = {_a(il['pseudo_r2'], 3)}. Uji likelihood-ratio "
        f"blok 4 strategi di atas kontrol: LR = {_a(lr['lr'])}, df = {lr['df']}, {_p(lr['p'])} "
        f"(pseudo R2 {_a(lr['pseudo_r2_tanpa_blok'], 3)} -> {_a(lr['pseudo_r2_penuh'], 3)}). "
        "`p_holm` = koreksi Holm atas 4 strategi. `peluang_*` = peluang prediksi pada skor "
        "1 SD di bawah/di atas rata-rata, variabel lain di rata-rata.\n"
    )
    kol = [
        "variabel",
        "koef",
        "or",
        "or_ci_bawah",
        "or_ci_atas",
        "p",
        "p_holm",
        "sd_poin",
        "peluang_minus_1sd",
        "peluang_plus_1sd",
    ]
    s.append(_md(f["lg"].reset_index()[kol], "{:.3f}"))
    s.append("\n" + _gambar("pengaruh_odds_ratio", interp))

    s.append("## 2. OLS `y_obj` (galat baku HC3)\n")
    io_, d = info["regresi"]["ols_y_obj"], f["diag"]
    s.append(
        f"n = {io_['n']}, R2 = {_a(io_['r2'], 3)}, R2 adj = {_a(io_['r2_adj'], 3)} (in-sample). "
        f"Residual sangat menceng (skew {_a(d['skew_residual'])}, kurtosis "
        f"{_a(d['kurtosis_residual'])}, Jarque-Bera {_p(d['p_jarque_bera'])}); Cook's distance "
        f"terbesar {_a(d['cook_maks'])} pada {d['id_cook_maks']}, {d['n_cook_di_atas_4_per_n']} "
        "baris di atas 4/n. Inferensi OLS y_obj karena itu dibaca hati-hati.\n"
    )
    s.append(
        _md(
            f["ols"].reset_index()[["variabel", "koef", "ci_bawah", "ci_atas", "p", "p_holm"]],
            "{:.3f}",
        )
    )
    sig_lg = [_n(v) for v in f["g"]["strategi"] if f["lg"].at[v, "p_holm"] < ALPHA]
    s.append(
        "\nPerbandingan logit vs OLS: arah koefisien strategi "
        + (
            "sama"
            if all(
                np.sign(f["lg"].loc[f["g"]["strategi"], "koef"])
                == np.sign(f["ols"].loc[f["g"]["strategi"], "koef"])
            )
            else "tidak selalu sama"
        )
        + f"; di logit {_daftar(sig_lg)} bermakna setelah Holm, di OLS tidak ada yang bermakna "
        "(semua p_holm >= 0,05).\n"
        if (f["ols"].loc[f["g"]["strategi"], "p_holm"] >= ALPHA).all()
        else "\n"
    )

    s.append("## 3. Validasi silang (data uji tiap lipatan)\n")
    s.append(_md(t["cv_ringkas"], "{:.3f}"))
    a, f1 = f["auc"], f["f1"]
    s.append(
        f"\n- `naik_penjualan`: Random Forest AUC {_a(a['random_forest'], 3)} dan F1-macro "
        f"{_a(f1['random_forest'], 3)}, logistik AUC {_a(a['logistik'], 3)}, baseline mayoritas "
        f"AUC {_a(a['dummy_mayoritas'], 3)} / F1 {_a(f1['dummy_mayoritas'], 3)}: kedua model "
        "lebih baik dari baseline, tetapi jauh dari sempurna."
    )
    s.append("\nConfusion matrix (ambang 0,5), dijumlahkan atas 25 lipatan uji:\n")
    s.append(_md(t["confusion"]))
    r2, mae, y2 = f["r2"], f["mae"], f["y2"]
    s.append("\nR2 dan MAE dari prediksi out-of-fold gabungan (rata-rata 5 ulangan):\n")
    s.append(_md(t["r2_oof"], "{:.3f}"))
    s.append(
        f"\n- `y_obj`: dengan semua responden, model tidak lebih baik secara berarti dari "
        f"rata-rata (R2 OOF linear {_a(r2['y_obj']['linear'], 3)}, RF "
        f"{_a(r2['y_obj']['random_forest'], 3)}, baseline {_a(r2['y_obj']['dummy_rata_rata'], 3)};"
        f" MAE {_a(mae['y_obj']['linear'], 3)} vs {_a(mae['y_obj']['dummy_rata_rata'], 3)}). "
        f"Tanpa {', '.join(info['tanpa_id'])} model sedikit lebih baik (R2 OOF linear "
        f"{_a(r2[y2]['linear'], 3)}, RF {_a(r2[y2]['random_forest'], 3)}), tetapi tetap lemah dan "
        "bergantung pada satu responden. Karena itu bobot rekomendasi diambil dari "
        "`naik_penjualan` (D26).\n"
    )

    s.append("## 4. Pemeriksaan kelompok yang menulis angka sama\n")
    s.append(_md(t["pola_isian"], "{:.3f}"))
    s.append(f"\n{_keterangan_pola(t)}\n")

    s.append("## 5. Permutation importance (Random Forest, data uji tiap lipatan)\n")
    pm = (
        t["permutation"]
        .groupby("variabel")["importance"]
        .agg(rata_rata="mean", sd="std", pct_lipatan_positif=lambda v: (v > 0).mean())
        .sort_values("rata_rata", ascending=False)
        .reset_index()
    )
    s.append(f"Skor: penurunan {c['skor_importance']} saat variabel diacak.\n")
    s.append(_md(pm, "{:.3f}"))

    s.append("\n## 6. SHAP (Random Forest akhir, seluruh sampel utama)\n")
    s.append(
        "`mean_shap_naik_1/0` = rata-rata SHAP pada UMKM yang naik / angka sama (SHAP per kelas). "
        "SHAP dihitung in-sample dan dibaca sebagai ilustrasi.\n"
    )
    s.append(_md(t["shap"].sort_values("mean_abs_shap", ascending=False), "{:.3f}"))
    s.append("\n" + _gambar("shap_ringkas", interp))
    s.append(_gambar("shap_arah", interp))

    s.append("## 7. Peringkat gabungan, ketidakpastian, dan bobot rekomendasi\n")
    s.append(
        "Tiap sumber dinormalkan ke 0-1 (koef logit bertanda; permutation negatif -> 0; "
        "permutation dan SHAP hanya bila arah SHAP positif; dibagi maksimum), lalu `pengaruh` = "
        "rata-ratanya. Skor ini relatif (teratas selalu 1), bukan besaran efek. Bootstrap "
        "mengulang logit, RF, SHAP, dan permutation (baris out-of-bag). `meyakinkan` = batas "
        "bawah CI 95% koef logit bootstrap > 0. `bobot_rekomendasi` = pengaruh x "
        f"p_koef_positif, minimal {_a(c['bobot_minimum'], 1)} (D26).\n"
    )
    kol = [
        "strategi",
        "koef_logit",
        "perm_importance",
        "mean_abs_shap",
        "n_koef",
        "n_perm",
        "n_shap",
        "pengaruh",
        "pengaruh_ci_bawah",
        "pengaruh_ci_atas",
        "p_peringkat_1",
        "p_koef_positif",
        "meyakinkan",
        "bobot_rekomendasi",
    ]
    s.append(_md(f["g"][kol], "{:.3f}"))
    s.append(
        "\nKorelasi peringkat antar-sumber (rho Spearman atas 4 strategi; permutation dan SHAP "
        "berasal dari Random Forest yang sama, jadi tidak sepenuhnya independen):\n"
    )
    s.append(_md(t["konsistensi"], "{:.2f}"))
    s.append("\nSkor gabungan (tanpa bootstrap) pada skenario yang paling mengubah data:\n")
    gs = t["gabungan_sensitivitas"].pivot(index="strategi", columns="varian", values="pengaruh")
    s.append(_md(gs.reset_index(), "{:.3f}"))
    s.append("\n" + _gambar("pengaruh_peringkat", interp))

    s.append("## 8. Moderasi (interaksi strategi x profil)\n")
    mod = t["moderasi"]
    s.append(
        f"{len(mod)} interaksi diuji (Holm per model). Bermakna setelah Holm: "
        f"{len(f['mod_sig'])}. Lima p terkecil:\n"
    )
    s.append(_md(mod.sort_values("p").head(5), "{:.3f}"))
    s.append(
        "\nTidak ditemukan bukti interaksi; dengan n = 116 daya uji interaksi rendah, jadi ini "
        "bukan bukti bahwa hubungannya sama di semua kelompok. Moderator skala usaha memakai "
        "`log_omzet_sebelum` (kontinu), bukan kuartil `skala_omzet`.\n"
        if f["mod_sig"].empty
        else "\n"
    )

    s.append("## 9. Sensitivitas\n")
    s.append(_md(t["sensitivitas_ringkas"], "{:.3f}"))
    s.append(
        "\n`bermakna_*` memakai p < 0,05 tanpa koreksi. `rho_peringkat_vs_utama` = korelasi "
        "peringkat koefisien 4 strategi dengan varian utama target yang sama (target alternatif "
        "dibandingkan dengan OLS y_obj utama); `rho_vs_logit_utama` = dibandingkan dengan logit "
        "utama. Dengan 4 strategi, satu pertukaran urutan sudah membuat rho = 0,8.\n"
    )
    if not f["negatif"].empty:
        s.append(
            "Hubungan negatif yang bermakna: "
            + "; ".join(
                f"{_n(r['variabel'])} pada {r['target']} ({r['keterangan']}): koef "
                f"{_a(r['koef'])}, {_p(r['p'])}"
                for _, r in f["negatif"].iterrows()
            )
            + ". Variabel pelanggan baru berupa satu angka dengan waktu pengukuran ambigu (D06), "
            "sehingga hasil ini sulit ditafsirkan.\n"
        )
    s.append(_gambar("pengaruh_sensitivitas_logit", interp))
    s.append(_gambar("pengaruh_sensitivitas_ols", interp))

    s.append("## 10. Keterbatasan\n")
    s += [f"- {k}" for k in keterbatasan(rep)]
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------------------
# Ringkasan bahasa sederhana
# ---------------------------------------------------------------------------
def temuan(rep: PengaruhReport) -> list[str]:
    """Temuan utama berbahasa sederhana."""
    f = fakta(rep)
    g, lg = f["g"], f["lg"]
    t = rep.tabel
    a, r2, y2 = f["auc"], f["r2"], f["y2"]
    kuat = [v for v in g["strategi"] if g.set_index("strategi").at[v, "meyakinkan"]]
    lemah = [v for v in g["strategi"] if v not in kuat]
    items = [
        "**Strategi yang paling berhubungan dengan melaporkan kenaikan.** Setelah profil usaha "
        "(lama usaha, jumlah platform, omzet awal) dikendalikan:\n"
        + "\n".join(f"   - {_kalimat_or(lg, v)}." for v in kuat)
        + f"\n   - {_kapital(_daftar([_n(v) for v in lemah]))} belum meyakinkan.",
        "**Peringkat gabungan** (regresi logistik + permutation importance + SHAP): "
        + ", ".join(
            f"{i + 1}. {_n(s)} ({_a(v)})"
            for i, (s, v) in enumerate(zip(g["strategi"], g["pengaruh"]))
        )
        + f". {_kapital(_n(g['strategi'].iloc[0]))} menjadi peringkat 1 pada "
        f"{_pct(g['p_peringkat_1'].iloc[0])} dari {rep.info['n_boot']} sampel bootstrap; "
        f"{_n(g['strategi'].iloc[1])} dan {_n(g['strategi'].iloc[2])} kadang bertukar tempat. "
        "Skor ini relatif (teratas selalu 1), bukan besaran efek.",
        (
            f"**Promosi (X2)** yang di EDA berkorelasi dengan kinerja tidak lagi bermakna bila "
            f"keempat strategi dan profil usaha dimasukkan bersama (OR {_a(lg.at['x2_promosi', 'or'])},"
            f" {_p(lg.at['x2_promosi', 'p'])}). Perbandingan ini tidak sepenuhnya setara (EDA memakai "
            "korelasi dengan y_obj, Tahap 4 memakai naik/tidak naik), jadi promosi dibaca sebagai "
            "belum meyakinkan, bukan tidak berhubungan."
        ),
        (
            f"**Strategi menambah daya jelaskan.** Model dengan keempat strategi jauh lebih cocok "
            f"daripada model berisi profil usaha saja (uji likelihood-ratio {_p(f['lr']['p'])})."
        ),
        (
            f"**Kemampuan model.** Untuk membedakan UMKM yang melaporkan kenaikan dari yang menulis "
            f"angka sama, Random Forest (AUC {_a(a['random_forest'])}) dan regresi logistik (AUC "
            f"{_a(a['logistik'])}) lebih baik dari tebakan mayoritas (AUC "
            f"{_a(a['dummy_mayoritas'])}), walau masih jauh dari sempurna. Besar kenaikan "
            f"(`y_obj`) hampir tidak dapat diperkirakan (R2 out-of-fold "
            f"{_a(max(r2['y_obj']['linear'], r2['y_obj']['random_forest']))} dengan semua responden; "
            f"{_a(max(r2[y2]['linear'], r2[y2]['random_forest']))} tanpa "
            f"{', '.join(rep.info['tanpa_id'])}), sehingga bobot rekomendasi diambil dari model "
            "naik/tidak naik."
        ),
        (
            f"**Cukup stabil.** {_kapital(_n(f['top']))} tetap teratas di "
            f"{f['teratas_logit_lain'].get(f['top'], 0)} dari {f['n_var_logit_lain']} skenario lain "
            "untuk target naik/tidak naik, termasuk dua skenario yang paling mengubah data (semua "
            "149 responden dan tanpa jawaban seragam), dan skor gabungannya tetap teratas di kedua "
            "skenario itu. Untuk target lain urutannya berbeda (lihat butir berikut)."
        ),
    ]
    if not f["negatif"].empty:
        items.append(
            "**Hasil yang berlawanan.** "
            + "; ".join(
                f"{_n(r['variabel'])} berhubungan negatif dengan {r['target'].split(' ')[0]} "
                f"(koef {_a(r['koef'])}, {_p(r['p'])})"
                for _, r in f["negatif"].iterrows()
            )
            + ". Angka pelanggan baru tidak jelas diukur sebelum atau sesudah marketplace (D06), "
            "jadi hasil ini belum dapat ditafsirkan, tetapi perlu dicatat."
        )
    items.append(
        f"**Omzet awal.** UMKM beromzet awal lebih besar cenderung lebih jarang melaporkan "
        f"kenaikan (OR {_a(lg.at['log_omzet_sebelum', 'or'])}). Ini mungkin mencerminkan "
        "regresi ke rata-rata atau kebiasaan usaha besar menulis angka yang sama; karena itu "
        "omzet awal dijadikan kontrol."
    )
    items.append(f"**Kelompok angka sama.** {_keterangan_pola(t)}")
    items.append(
        f"**Moderasi.** Tidak ditemukan bukti bahwa hubungan strategi berbeda menurut omzet "
        f"awal, jumlah platform, atau lama di marketplace ({len(f['mod_sig'])} dari "
        f"{len(t['moderasi'])} interaksi bermakna setelah koreksi). Daya uji untuk ini rendah, "
        "jadi Tahap 6 memakai bobot yang sama untuk semua segmen dan perbedaan antar-segmen "
        "datang dari selisih skor."
        if f["mod_sig"].empty
        else f"**Moderasi.** {len(f['mod_sig'])} interaksi bermakna setelah koreksi (lihat log)."
    )
    return items


def build_ringkasan(rep: PengaruhReport, cfg: dict[str, Any]) -> str:
    """Susun reports/pengaruh_ringkasan.md (bahasa sederhana)."""
    f = fakta(rep)
    g = f["g"]
    interp = interpretasi(rep)
    s = ["# Ringkasan Tahap 4: Strategi yang Berhubungan dengan Kinerja Penjualan\n"]
    s.append(
        f"Dibuat oleh `umkm.pengaruh` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. "
        f"Sampel utama {rep.info['n_utama']} UMKM.\n"
    )
    s.append("## Apa yang dibandingkan\n")
    s.append(_kontras(rep) + "\n")
    s.append("## Temuan\n")
    s += [f"{i}. {x}" for i, x in enumerate(temuan(rep), 1)]
    s.append("\n## Bobot untuk rekomendasi (Tahap 6)\n")
    tab = g[
        [
            "nama",
            "pengaruh",
            "pengaruh_ci_bawah",
            "pengaruh_ci_atas",
            "p_koef_positif",
            "meyakinkan",
            "bobot_rekomendasi",
        ]
    ].rename(
        columns={
            "nama": "Strategi",
            "pengaruh": "Skor pengaruh",
            "pengaruh_ci_bawah": "CI bawah",
            "pengaruh_ci_atas": "CI atas",
            "p_koef_positif": "Keyakinan arah positif",
            "meyakinkan": "Meyakinkan",
            "bobot_rekomendasi": "Bobot dipakai",
        }
    )
    s.append(_md(tab, "{:.2f}"))
    s.append(
        f"\nBobot dipakai = skor pengaruh x keyakinan arah positif (bagian sampel bootstrap "
        f"dengan koefisien logit > 0), minimal {_a(cfg['influence']['bobot_minimum'], 1)} (D26). Di "
        "Tahap 6 bobot ini dikalikan dengan selisih skor tiap segmen terhadap UMKM yang "
        "melaporkan kenaikan; strategi yang belum meyakinkan tetap bisa muncul bila selisihnya "
        "besar, dengan catatan ketidakpastian.\n"
    )
    s.append("## Keterbatasan\n")
    s += [f"- {k}" for k in keterbatasan(rep)]
    s.append("\n## Grafik\n")
    s.append("| Grafik | Interpretasi |\n|---|---|")
    for nm in (
        "pengaruh_peringkat",
        "pengaruh_odds_ratio",
        "shap_ringkas",
        "shap_arah",
        "pengaruh_sensitivitas_logit",
        "pengaruh_sensitivitas_ols",
    ):
        s.append(f"| `figures/{nm}.png` | {interp[nm]} |")
    s.append(
        "\n_Semua hasil adalah pola keterkaitan dari data survei satu waktu, bukan bukti bahwa "
        "strategi tertentu menyebabkan penjualan naik._\n"
    )
    return "\n".join(s)
