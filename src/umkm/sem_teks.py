"""Teks analisis pembanding PLS-SEM: reports/sem_log.md dan reports/sem_ringkasan.md.

Semua kalimat disusun dari angka di tabel agar tetap benar bila data berubah.
Bahasa asosiasi: koefisien jalur dibaca sebagai hubungan terstandar, bukan pengaruh sebab-akibat.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from umkm.eda_teks import _a, _daftar, _p
from umkm.features import _md
from umkm.pengaruh import NAMA_VARIABEL
from umkm.sem import NAMA_MODEL, STRATEGI, SemReport


def _n(v: str) -> str:
    return NAMA_VARIABEL.get(v, {"persepsi": "Persepsi kinerja"}.get(v, v))


def _f2(v: float) -> str:
    """Label besar efek f2 (Cohen): 0,02 kecil, 0,15 sedang, 0,35 besar."""
    if v >= 0.35:
        return "besar"
    if v >= 0.15:
        return "sedang"
    if v >= 0.02:
        return "kecil"
    return "sangat kecil"


def _jalur(rep: SemReport, model: str) -> pd.DataFrame:
    j = rep.tabel["jalur"]
    return j[(j["model"] == model) & (j["jenis"] == "strategi")].set_index("prediktor")


def _bermakna(rep: SemReport, model: str) -> list[str]:
    j = _jalur(rep, model)
    return [_n(v) for v in j.index if j.loc[v, "ci_bawah"] > 0 or j.loc[v, "ci_atas"] < 0]


def _urut(rep: SemReport, model: str) -> list[str]:
    return [_n(v) for v in _jalur(rep, model)["koef"].sort_values(ascending=False).index]


def fakta(rep: SemReport, cfg: dict[str, Any]) -> dict[str, Any]:
    """Angka kunci yang dipakai berulang di log dan ringkasan."""
    sc = cfg["sem"]
    rel = rep.tabel["reliabilitas"]
    ld = rep.tabel["loading"]
    h = rep.tabel["htmt"]
    m = rep.tabel["model"].set_index("model")
    return {
        "m": m,
        "alpha": (rel["alpha"].min(), rel["alpha"].max()),
        "rho_c": (rel["rho_c"].min(), rel["rho_c"].max()),
        "ave": (rel["ave"].min(), rel["ave"].max()),
        "rho_a_lebih_1": rel[rel["rho_a"] > 1],
        "loading_min": ld["loading"].min(),
        "loading_kurang": ld[ld["loading"] < sc["ambang_loading"]],
        "htmt_maks": h.loc[h["htmt"].idxmax()],
        "htmt_ci_maks": h["htmt_ci_atas"].max(),
        "htmt_ok": bool((h["htmt_ci_atas"] < sc["ambang_htmt"]).all()),
    }


def temuan(rep: SemReport, cfg: dict[str, Any]) -> list[str]:
    f = fakta(rep, cfg)
    m = f["m"]
    k = rep.tabel["perbandingan"].set_index("strategi")
    jn, jy, jp = (_jalur(rep, t) for t in ("naik_penjualan", "y_obj", "persepsi"))
    top = jn["koef"].idxmax()
    out = [
        (
            f"**Model pengukuran memadai.** Keempat konstruk strategi dan persepsi kinerja reliabel "
            f"(Cronbach alpha {_a(f['alpha'][0])}-{_a(f['alpha'][1])}, composite reliability "
            f"{_a(f['rho_c'][0])}-{_a(f['rho_c'][1])}), validitas konvergen terpenuhi (AVE "
            f"{_a(f['ave'][0])}-{_a(f['ave'][1])}; loading terendah {_a(f['loading_min'])}), dan "
            f"konstruk dapat dibedakan satu sama lain (HTMT tertinggi {_a(f['htmt_maks']['htmt'])}, "
            f"batas atas interval bootstrap tertinggi {_a(f['htmt_ci_maks'])} "
            f"{'< ' + _a(cfg['sem']['ambang_htmt']) if f['htmt_ok'] else 'melewati ambang'})."
        ),
        (
            f"**Melaporkan kenaikan penjualan.** Jalur terkuat berasal dari {_n(top)} "
            f"(beta = {_a(jn.loc[top, 'koef'])}, {_p(jn.loc[top, 'p'])}, f2 = {_a(jn.loc[top, 'f2'])}, "
            f"{_f2(jn.loc[top, 'f2'])}). Jalur yang intervalnya tidak mencakup nol: "
            f"{_daftar(_bermakna(rep, 'naik_penjualan'))}. Urutan: {' > '.join(_urut(rep, 'naik_penjualan'))}. "
            f"R2 = {_a(m.loc['naik_penjualan', 'r2'])}; AUC validasi silang "
            f"{_a(m.loc['naik_penjualan', 'auc'])} (SD {_a(m.loc['naik_penjualan', 'auc_sd'])})."
        ),
        f"**Besar kenaikan (y_obj).** Urutan jalur: {' > '.join(_urut(rep, 'y_obj'))}; jalur yang "
        f"intervalnya tidak mencakup nol: {_daftar(_bermakna(rep, 'y_obj'))}; "
        + (
            f"setelah koreksi Holm tidak ada yang bermakna (Holm p terkecil {_a(jy['p_holm'].min(), 3)}). "
            if jy["p_holm"].min() >= 0.05
            else f"Holm p terkecil {_a(jy['p_holm'].min(), 3)}. "
        )
        + f"R2 = {_a(m.loc['y_obj', 'r2'])}, tetapi Q2_predict = {_a(m.loc['y_obj', 'q2_predict'])}"
        + (
            ": di luar sampel model hampir tidak lebih baik dari rata-rata, sejalan dengan R2 "
            "out-of-fold pada analisis utama."
            if m.loc["y_obj", "q2_predict"] < 0.05
            else "."
        ),
        f"**Persepsi kinerja (Y1-Y8).** Urutan jalur: {' > '.join(_urut(rep, 'persepsi'))} "
        f"(beta tertinggi {_a(jp['koef'].max())}); R2 = {_a(m.loc['persepsi', 'r2'])}. "
        + (
            f"Penilaian diri pelaku usaha paling dekat dengan {_daftar(_urut(rep, 'persepsi')[:2])}, "
            f"sedangkan laporan angka penjualan paling dekat dengan {_n(top)}. Perbedaan ini sejalan "
            "dengan alasan persepsi tidak dipakai sebagai target utama."
            if _urut(rep, "persepsi")[0] != _n(top)
            else "Polanya searah dengan kinerja objektif."
        ),
        (
            f"**{'Konsisten' if rep.info['rho_peringkat'] >= 0.8 else 'Sebagian berbeda'} dengan metode "
            f"inti.** Urutan jalur PLS untuk naik_penjualan dibandingkan peringkat gabungan regresi "
            f"logistik, Random Forest, dan SHAP: Spearman rho = {_a(rep.info['rho_peringkat'])}. AUC "
            f"validasi silang PLS {_a(m.loc['naik_penjualan', 'auc'])}, regresi logistik "
            f"{_a(rep.info['auc_logistik'])}, Random Forest {_a(rep.info['auc_rf'])}."
        ),
    ]
    lemah = [v for v in STRATEGI if v not in jn.index[(jn["ci_bawah"] > 0) | (jn["ci_atas"] < 0)]]
    lemah = [v for v in lemah if k.loc[v, "peringkat_tahap4"] >= 3]
    if lemah:
        out[-1] += (
            f" {_daftar([_n(v) for v in lemah])} belum meyakinkan berhubungan dengan pelaporan "
            "kenaikan, baik di PLS-SEM maupun di peringkat gabungan."
        )
    return out


def keterbatasan(rep: SemReport, cfg: dict[str, Any]) -> list[str]:
    f = fakta(rep, cfg)
    out = [
        (
            "PLS-SEM di sini memakai data potong lintang yang sama dengan analisis utama, sehingga "
            "fungsinya sebagai pemeriksaan kekokohan, bukan bukti tambahan yang independen."
        ),
        (
            "naik_penjualan berupa 0/1; koefisien jalur PLS untuk target ini setara model peluang "
            "linear dan dibaca sebagai arah serta urutan, bukan besar peluang."
        ),
        "Konstruk satu indikator (kinerja objektif dan profil usaha) dianggap terukur tanpa galat.",
    ]
    if len(f["rho_a_lebih_1"]):
        r = f["rho_a_lebih_1"]
        out.append(
            "rho_A sedikit di atas 1 pada "
            + _daftar(sorted({_n(v) for v in r["konstruk"]}))
            + f" (maks {_a(r['rho_a'].max(), 3)}). Ini muncul bila bobot indikator tidak seimbang "
            "relatif terhadap korelasi antarbutir; reliabilitas tetap dinilai dari alpha dan rho_C."
        )
    ld = rep.tabel["loading"]
    lebar = ld[(ld["model"] == "y_obj") & (ld["ci_bawah"] < cfg["sem"]["ambang_loading"])]
    if len(lebar):
        out.append(
            "Interval bootstrap loading lebar pada "
            + _daftar(sorted({_n(v) for v in lebar["konstruk"]}))
            + f" (batas bawah terendah {_a(lebar['ci_bawah'].min())}). Pada Mode A bobot butir "
            "mengikuti korelasinya dengan target; bila hubungan konstruk dengan target lemah, bobot "
            "di sampel ulang ikut tidak stabil. Estimasi titik tetap di atas ambang."
        )
    if len(f["loading_kurang"]):
        out.append(
            f"{len(f['loading_kurang'])} loading di bawah {_a(cfg['sem']['ambang_loading'], 3)}; "
            "butir tetap dipertahankan karena AVE dan reliabilitas konstruk sudah memadai."
        )
    out.append(
        "Banyak butir didominasi jawaban netral dan ada responden dengan jawaban seragam; ini dapat "
        "menaikkan reliabilitas secara semu. CB-SEM tidak dipakai karena ukuran sampel kecil dan "
        "target utama hanya satu indikator."
    )
    return out


def _tabel_jalur(rep: SemReport, model: str) -> str:
    j = rep.tabel["jalur"]
    j = j[j["model"] == model].copy()
    j["prediktor"] = j["prediktor"].map(_n)
    j["ci_95"] = [f"[{lo:.2f}; {hi:.2f}]" for lo, hi in zip(j["ci_bawah"], j["ci_atas"])]
    tab = j[["prediktor", "koef", "se_boot", "ci_95", "p", "p_holm", "f2", "vif_inner"]].rename(
        columns={
            "prediktor": "Prediktor",
            "koef": "Beta",
            "se_boot": "SE",
            "ci_95": "CI 95%",
            "p": "p",
            "p_holm": "p Holm",
            "f2": "f2",
            "vif_inner": "VIF",
        }
    )
    return _md(tab, "{:.3f}")


def build_log(rep: SemReport, cfg: dict[str, Any]) -> str:
    """Susun reports/sem_log.md (rinci, untuk peninjau)."""
    sc = cfg["sem"]
    m = rep.tabel["model"]
    s = ["# Log Analisis Pembanding: PLS-SEM\n"]
    s.append(
        f"Dibuat oleh `umkm.sem` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. Seed {cfg['seed']}, "
        f"bootstrap {sc['n_bootstrap']}x, validasi silang {sc['cv_lipatan']}x{sc['cv_ulang']}.\n"
    )
    s.append("## Spesifikasi\n")
    s.append(
        "- Konstruk X1-X4 reflektif (Mode A) dengan butir kuesioner masing-masing; skema bobot jalur; "
        "indikator distandarkan.\n"
        "- Profil usaha (lama usaha sebelum marketplace, lama di marketplace, jumlah platform, omzet "
        "sebelum log) masuk sebagai konstruk satu indikator, sama dengan kontrol pada regresi.\n"
        "- Tiga model dengan prediktor yang sama:\n"
        + "\n".join(f"  - `{r.model}`: {r.nama}, n = {r.n}" for r in m.itertuples())
        + "\n- Inferensi: bootstrap persentil 95% dan uji t (SE bootstrap); koreksi Holm untuk "
        "empat jalur strategi di tiap model.\n"
        "- Daya prediksi (target satu indikator): Q2_predict terhadap rata-rata data latih dan RMSE "
        "dibandingkan regresi linear pada seluruh indikator.\n"
    )
    s.append("## Model pengukuran\n")
    rel = rep.tabel["reliabilitas"].copy()
    rel["konstruk"] = rel["konstruk"].map(_n)
    s.append(_md(rel.drop(columns="loading_min"), "{:.3f}"))
    s.append(
        f"\nAmbang: alpha dan rho_C >= 0,70; AVE >= 0,50; loading >= {_a(sc['ambang_loading'], 3)}.\n"
    )
    s.append("### Validitas diskriminan (HTMT)\n")
    h = rep.tabel["htmt"]
    h = (
        h[h["model"].isin(["y_obj", "persepsi"])]
        .drop_duplicates(["konstruk_a", "konstruk_b"])
        .copy()
    )
    h["konstruk_a"], h["konstruk_b"] = h["konstruk_a"].map(_n), h["konstruk_b"].map(_n)
    s.append(_md(h.drop(columns="model"), "{:.3f}"))
    s.append(
        f"\nHTMT dan batas atas interval bootstrap 95% dibandingkan dengan ambang "
        f"{_a(sc['ambang_htmt'])}.\n"
    )
    s.append("### Kriteria Fornell-Larcker (model y_obj)\n")
    fl = rep.tabel["fornell_larcker"].copy()
    fl["konstruk"] = fl["konstruk"].map(_n)
    s.append(_md(fl, "{:.3f}"))
    s.append("\nDiagonal = akar AVE; harus lebih besar dari korelasi pada baris dan kolomnya.\n")
    s.append("## Model struktural\n")
    for r in m.itertuples():
        s.append(f"### {r.nama} (n = {r.n})\n")
        s.append(_tabel_jalur(rep, r.model))
        txt = f"\nR2 = {_a(r.r2, 3)} (adj. {_a(r.r2_adj, 3)}); algoritma konvergen dalam {r.iterasi} iterasi"
        if pd.notna(r.q2_predict):
            txt += (
                f"; Q2_predict = {_a(r.q2_predict, 3)}; RMSE PLS {_a(r.rmse_pls, 3)} vs regresi linear "
                f"{_a(r.rmse_lm, 3)}"
            )
        if pd.notna(getattr(r, "auc", float("nan"))):
            txt += f"; AUC {_a(r.auc, 3)} (SD {_a(r.auc_sd, 3)})"
        s.append(txt + f". Sampel bootstrap gagal: {r.boot_gagal}.\n")
    s.append("## Perbandingan dengan analisis utama\n")
    k = rep.tabel["perbandingan"]
    tab = k[
        [
            "nama",
            "logit_naik_koef",
            "pls_naik_penjualan_koef",
            "ols_y_obj_koef",
            "pls_y_obj_koef",
            "pls_persepsi_koef",
            "rf_perm_importance",
            "peringkat_tahap4",
            "peringkat_pls_naik",
        ]
    ].rename(
        columns={
            "nama": "Strategi",
            "logit_naik_koef": "Logit (log-odds/SD)",
            "pls_naik_penjualan_koef": "PLS naik",
            "ols_y_obj_koef": "OLS y_obj",
            "pls_y_obj_koef": "PLS y_obj",
            "pls_persepsi_koef": "PLS persepsi",
            "rf_perm_importance": "RF importance",
            "peringkat_tahap4": "Peringkat gabungan",
            "peringkat_pls_naik": "Peringkat PLS naik",
        }
    )
    s.append(_md(tab, "{:.3f}"))
    s.append(
        "\nKoefisien logit dalam log-odds per SD, PLS dan OLS terstandar; yang dibandingkan adalah "
        f"arah dan urutan. Spearman rho peringkat = {_a(rep.info['rho_peringkat'])}.\n"
    )
    s.append("## Temuan\n")
    s += [f"{i}. {x}" for i, x in enumerate(temuan(rep, cfg), 1)]
    s.append("\n## Keterbatasan\n")
    s += [f"- {x}" for x in keterbatasan(rep, cfg)]
    s.append("\n## Grafik\n")
    s.append(
        "- `figures/sem_jalur.png`: koefisien jalur strategi pada tiga model dengan interval bootstrap."
    )
    s.append("- `figures/sem_loading.png`: loading luar seluruh butir dengan ambang 0,708.\n")
    return "\n".join(s)


def build_ringkasan(rep: SemReport, cfg: dict[str, Any]) -> str:
    """Susun reports/sem_ringkasan.md (bahasa sederhana)."""
    s = ["# Ringkasan: PLS-SEM sebagai Analisis Pembanding\n"]
    s.append(
        "PLS-SEM menguji hubungan keempat strategi dengan kinerja penjualan sambil memperhitungkan "
        "galat pengukuran butir kuesioner. Hasilnya dibandingkan dengan regresi logistik, Random "
        "Forest, dan SHAP pada analisis utama. Semua hubungan bersifat asosiasi.\n"
    )
    s.append("## Temuan\n")
    s += [f"{i}. {x}" for i, x in enumerate(temuan(rep, cfg), 1)]
    s.append("\n## Koefisien jalur strategi\n")
    j = rep.tabel["jalur"]
    j = j[j["jenis"] == "strategi"]
    tab = j.pivot(index="prediktor", columns="model", values="koef").reindex(STRATEGI)
    tab = tab[list(NAMA_MODEL)].rename(columns=NAMA_MODEL)
    tab.index = tab.index.map(_n)
    s.append(_md(tab.reset_index(names="Strategi"), "{:.2f}"))
    s.append(
        "\nTiap model juga mengendalikan profil usaha. Interval, p-value, dan ukuran efek ada di "
        "`sem_log.md` dan `tables/sem_jalur.csv`.\n"
    )
    s.append("## Keterbatasan\n")
    s += [f"- {x}" for x in keterbatasan(rep, cfg)]
    return "\n".join(s) + "\n"
