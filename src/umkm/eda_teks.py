"""Teks Tahap 3: kalimat interpretasi per grafik, log teknis, dan ringkasan awam.

Semua angka diambil dari tabel hasil `eda.build_tables`, sehingga teks ikut berubah bila data atau
keputusan berubah. Bahasa: asosiasi ("berhubungan", "cenderung"), bukan sebab-akibat.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from umkm import stats
from umkm.features import STRATEGI_COLS, _md

if TYPE_CHECKING:
    from umkm.eda import EdaReport

ALPHA = 0.05
NAMA = {
    "x1_unggah": "unggah produk (X1)",
    "x2_promosi": "promosi (X2)",
    "x3_komunikasi": "komunikasi pelanggan (X3)",
    "x4_konsistensi": "konsistensi kelola toko (X4)",
    "y_persepsi": "persepsi kinerja",
}


def _a(x: float, d: int = 2) -> str:
    """Angka format Indonesia (koma desimal)."""
    return f"{x:.{d}f}".replace(".", ",")


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _rp(x: float) -> str:
    if abs(x) < 1e6:
        return f"Rp{x / 1e3:,.0f} ribu".replace(",", ".")
    return f"Rp{x / 1e6:,.1f} jt".replace(",", "#").replace(".", ",").replace("#", ".")


def _kapital(teks: str) -> str:
    """Huruf pertama kapital tanpa mengubah huruf lain (beda dengan str.capitalize)."""
    return teks[:1].upper() + teks[1:]


def _p(p: float) -> str:
    return "p < 0,001" if p < 0.001 else f"p = {_a(p, 3)}"


def _daftar(items: list[str]) -> str:
    if not items:
        return "tidak ada"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " dan " + items[-1]


def _rentang(v: pd.Series) -> str:
    if v.min() == v.max():
        return _a(v.min())
    sep = " sampai " if v.min() < 0 else "-"
    return f"{_a(v.min())}{sep}{_a(v.max())}"


# ---------------------------------------------------------------------------
# Interpretasi satu kalimat per grafik
# ---------------------------------------------------------------------------
def interpretasi(t: dict[str, pd.DataFrame], df: pd.DataFrame) -> dict[str, str]:
    """Satu kalimat interpretasi untuk tiap grafik (kunci = nama berkas grafik)."""
    out: dict[str, str] = {}
    n_all = len(df)

    plat = t["profil_platform"]
    combo = t["profil_kombinasi_platform"].iloc[0]
    kecil = plat[plat["n_semua_149"] < 10]
    out["eda_profil_platform"] = (
        f"{plat.iloc[0]['platform']} ({_pct(plat.iloc[0]['pct_semua_149'])}) dan "
        f"{plat.iloc[1]['platform']} ({_pct(plat.iloc[1]['pct_semua_149'])}) paling banyak dipakai "
        f"dan kombinasi terbanyak adalah {combo['kombinasi']} ({combo['n']} UMKM); "
        + (
            f"{_daftar(list(kecil['platform']))} hanya dipakai "
            f"{_daftar([str(n) for n in kecil['n_semua_149']])} UMKM sehingga terlalu sedikit "
            "untuk dianalisis sebagai kelompok tersendiri."
            if len(kecil)
            else "semua platform dipakai cukup banyak UMKM."
        )
    )

    num = t["profil_numerik"].query("sampel == 'semua_149'").set_index("variabel")
    n_tb = int(df["tanpa_baseline"].sum())
    out["eda_profil_lama_usaha"] = (
        f"Median lama usaha sebelum marketplace {_a(num.loc['lama_usaha_pra_mp', '50%'], 0)} tahun "
        f"dan median lama berjualan di marketplace {_a(num.loc['lama_di_mp', '50%'], 0)} tahun; "
        f"{n_tb} UMKM ({_pct(n_tb / n_all)}) berdiri bersamaan dengan masuk marketplace sehingga "
        "tidak punya kondisi 'sebelum' yang bermakna dan dikeluarkan dari analisis utama (D14)."
    )

    sk = t["profil_skala_omzet"]
    out["eda_profil_skala_omzet"] = (
        f"Keempat kelompok skala usaha berukuran mirip ({sk['n_semua_149'].min()}-"
        f"{sk['n_semua_149'].max()} UMKM) karena dibentuk dari kuartil; separuh UMKM beromzet "
        f"sebelum marketplace paling banyak {_rp(num.loc['omzet_sebelum_juta', '50%'] * 1e6)} "
        "per bulan."
    )

    dk = t["distribusi_konstruk"].query("sampel == 'semua_149'").set_index("konstruk")
    strat = dk.loc[STRATEGI_COLS].sort_values("median")
    rendah = [
        f"{NAMA[k]} (median {_a(r['median'])})" for k, r in strat.iterrows() if r["median"] < 3
    ]
    tengah = [
        f"{NAMA[k]} (median {_a(r['median'])})" for k, r in strat.iterrows() if r["median"] >= 3
    ]
    ada_cf = bool((dk["efek_floor"] | dk["efek_ceiling"]).any())
    tumpuk = dk.sort_values("pct_nilai_dominan", ascending=False).iloc[0]
    out["eda_distribusi_konstruk"] = (
        f"Skor {_daftar(rendah)} tergolong rendah, sedangkan {_daftar(tengah)} berada di sekitar "
        f"titik tengah; {'ada' if ada_cf else 'tidak ada'} efek lantai/atap (> 15% responden di "
        f"skor 1 atau 5), tetapi skor menumpuk di satu nilai, paling ekstrem pada "
        f"{NAMA[tumpuk.name]} ({_pct(tumpuk['pct_nilai_dominan'])} responden tepat "
        f"{_a(tumpuk['nilai_dominan'], 0)})."
    )

    sb = t["sebaran_butir"]
    dom = sb[sb["dominasi_netral"]]
    y_dom = dom["butir"].str.startswith("y_persepsi").sum()
    x12 = sb[sb["butir"].str.startswith(("x1_", "x2_"))]
    out["eda_butir_likert"] = (
        f"Jawaban netral (3) dipilih lebih dari separuh responden pada {len(dom)} dari {len(sb)} "
        f"butir, termasuk {y_dom} dari 8 butir persepsi kinerja "
        f"({_pct(sb.loc[sb['butir'].str.startswith('y_'), 'pct_3'].min())}-"
        f"{_pct(sb.loc[sb['butir'].str.startswith('y_'), 'pct_3'].max())}); sebaliknya butir unggah "
        f"dan promosi didominasi skor 1-2 ({_pct((x12['pct_1'] + x12['pct_2']).min())}-"
        f"{_pct((x12['pct_1'] + x12['pct_2']).max())} responden), terutama iklan berbayar."
    )

    ss = t["sebelum_sesudah"].set_index(["sampel", "variabel"])
    om, tr = ss.loc[("utama", "omzet (Rp)")], ss.loc[("utama", "transaksi")]
    out["eda_arah_perubahan"] = (
        f"Di sampel utama, {_pct(om['pct_naik'])} UMKM mencatat omzet naik dan "
        f"{_pct(tr['pct_naik'])} transaksi naik, hampir separuh tidak berubah, dan penurunan jarang "
        f"(omzet {om['n_turun']} UMKM, transaksi {tr['n_turun']}); bila {n_tb} UMKM tanpa baseline "
        "ikut dihitung, porsi 'sama' membesar karena mereka umumnya mengisi angka sebelum = sesudah."
    )
    out["eda_sebelum_sesudah"] = (
        f"Hampir semua titik berada pada atau sedikit di atas garis diagonal: perubahan umumnya kecil "
        f"(median selisih omzet {_rp(om['median_selisih'])}, transaksi "
        f"{_a(tr['median_selisih'], 1)}), tetapi di antara UMKM yang berubah, arahnya hampir "
        f"selalu naik (Wilcoxon: omzet r = {_a(om['r'])}, transaksi r = {_a(tr['r'])}, keduanya "
        f"{_p(max(om['p'], tr['p']))}); "
        f"titik merah di bawah garis adalah {om['n_turun']} UMKM yang omzetnya turun."
    )

    kor = t["spearman_kinerja"].query("sampel == 'utama'")
    yo = kor[kor["y"] == "y_obj"].sort_values("rho", ascending=False)
    sig = yo[yo["p_holm"] < ALPHA]
    tdk = yo[yo["p_holm"] >= ALPHA]
    pb = kor[kor["y"] == "y_pelanggan_baru"]
    pb_pos = pb[(pb["rho"] > 0) & (pb["p_holm"] < ALPHA)]
    out["eda_spearman_heatmap"] = (
        f"{_kapital(_daftar([NAMA[x] for x in sig['x']]))} berkorelasi positif lemah-sedang "
        f"dengan kinerja gabungan Y_obj (rho {_rentang(sig['rho'])}, Holm p < 0,05), sedangkan "
        f"{_daftar([NAMA[x] for x in tdk['x']])} paling lemah (rho {_rentang(tdk['rho'])}, tidak "
        "bermakna); "
        + (
            "tidak satu pun strategi berkorelasi positif bermakna dengan jumlah pelanggan baru."
            if pb_pos.empty
            else f"{_daftar([NAMA[x] for x in pb_pos['x']])} juga berkorelasi dengan pelanggan baru."
        )
    )

    mw = t["mw_naik_penjualan"].query("varian == 'utama' and variabel in @STRATEGI_COLS")
    beda = mw[mw["p_holm"] < ALPHA].sort_values("r_rank_biserial", ascending=False)
    sama = mw[mw["p_holm"] >= ALPHA]
    out["eda_boxplot_naik_penjualan"] = (
        f"UMKM yang penjualannya naik cenderung memiliki skor {_daftar([NAMA[x] for x in beda['variabel']])} "
        f"lebih tinggi (rank-biserial {_rentang(beda['r_rank_biserial'])}, efek kecil-sedang, "
        f"Holm p < 0,05), sedangkan skor {_daftar([NAMA[x] for x in sama['variabel']])} tidak "
        "berbeda nyata antara kedua kelompok."
    )

    tb = t["mw_tanpa_baseline"].query("varian == 'strategi'")
    out["eda_boxplot_tanpa_baseline"] = "Skor keempat strategi UMKM tanpa baseline " + (
        f"tidak berbeda nyata dari UMKM lainnya (semua Holm p > 0,05, rank-biserial "
        f"{_rentang(tb['r_rank_biserial'])}), sehingga mengeluarkan mereka dari analisis "
        "utama kecil kemungkinannya menggeser gambaran strategi sampel."
        if (tb["p_holm"] >= ALPHA).all()
        else "berbeda pada sebagian strategi; lihat tabel untuk rinciannya."
    )
    return out


# ---------------------------------------------------------------------------
# Log teknis
# ---------------------------------------------------------------------------
def _gambar(nama: str, interp: dict[str, str]) -> str:
    return f"\n![{nama}](figures/{nama}.png)\n\n**Interpretasi:** {interp[nama]}\n"


def _kolom(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df[[c for c in cols if c in df.columns]]


def build_log(rep: EdaReport, df: pd.DataFrame, interp: dict[str, str]) -> str:
    """Susun reports/eda_log.md (tabel ringkas + grafik + interpretasi)."""
    t = rep.tabel
    n_utama = int(df["sampel_utama"].sum())
    s = ["# Log EDA (Tahap 3)\n"]
    s.append(f"Dibuat oleh `umkm.eda` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}.\n")
    s.append(
        f"- Analisis yang menyangkut kinerja memakai **sampel utama** (n = {n_utama}, D14); "
        f"semua {len(df)} responden dilaporkan sebagai pembanding. Profil dan skor strategi memakai "
        f"{len(df)} responden.\n"
        "- Uji nonparametrik: Wilcoxon signed-rank (pasangan tanpa beda dibuang), Mann-Whitney U "
        "(pendekatan normal dengan koreksi ties), Spearman (CI 95% Fisher-z, SE Bonett-Wright). "
        "Koreksi Holm per keluarga uji. Ukuran efek: r = Z/sqrt(N) dan rank-biserial; label Cohen "
        "(0,1 kecil; 0,3 sedang; 0,5 besar).\n"
        "- Semua hasil adalah **asosiasi**, bukan sebab-akibat.\n"
        "- Tabel lengkap: `reports/tables/eda_*.csv`.\n"
    )

    s.append("## 1. Profil responden\n")
    s.append(_md(t["profil_platform"]))
    s.append("\nKombinasi platform (5 teratas):\n")
    s.append(_md(t["profil_kombinasi_platform"].head(5)))
    s.append(_gambar("eda_profil_platform", interp))
    s.append("\n" + _md(t["profil_numerik"]))
    s.append(_gambar("eda_profil_lama_usaha", interp))
    s.append("\n" + _md(t["profil_skala_omzet"]))
    s.append(_gambar("eda_profil_skala_omzet", interp))

    s.append("\n## 2. Distribusi skor konstruk\n")
    s.append(
        f"Efek lantai/atap: > {stats.BATAS_CEILING_FLOOR:.0%} responden di skor 1 atau 5. "
        f"Dominasi: > {stats.BATAS_DOMINASI:.0%} responden pada satu nilai skor.\n\n"
    )
    s.append(
        _md(
            _kolom(
                t["distribusi_konstruk"],
                [
                    "sampel",
                    "konstruk",
                    "n",
                    "rata_rata",
                    "sd",
                    "median",
                    "skewness",
                    "pct_floor",
                    "pct_ceiling",
                    "nilai_dominan",
                    "pct_nilai_dominan",
                    "efek_floor",
                    "efek_ceiling",
                    "dominasi_satu_nilai",
                ],
            )
        )
    )
    s.append(_gambar("eda_distribusi_konstruk", interp))
    s.append(
        "\n"
        + _md(
            _kolom(
                t["sebaran_butir"],
                ["label", "pct_1", "pct_2", "pct_3", "pct_4", "pct_5", "dominasi_netral"],
            )
        )
    )
    s.append(_gambar("eda_butir_likert", interp))

    s.append("\n## 3. Sebelum vs sesudah (nilai terwinsor)\n")
    s.append(
        _md(
            _kolom(
                t["sebelum_sesudah"],
                [
                    "sampel",
                    "variabel",
                    "n_pasangan",
                    "n_naik",
                    "n_sama",
                    "n_turun",
                    "median_sebelum",
                    "median_sesudah",
                    "median_selisih",
                    "z",
                    "p",
                    "r",
                    "r_semua_pasangan",
                    "r_rank_biserial",
                    "efek",
                ],
            ),
            "{:,.3g}",
        )
    )
    s.append(
        "\nCatatan: Wilcoxon membuang pasangan tanpa beda, sehingga r dihitung dari UMKM yang "
        "berubah saja; `r_semua_pasangan` (pembagi = semua pasangan) lebih konservatif. Transaksi "
        "tidak punya satu pun penurunan, jadi rank-biserial = 1. Perbandingan sebelum-sesudah ini "
        "tidak punya kelompok pembanding, sehingga tidak dapat dipakai untuk menyimpulkan bahwa "
        "kenaikan disebabkan oleh marketplace.\n"
    )
    s.append(_gambar("eda_arah_perubahan", interp))
    s.append(_gambar("eda_sebelum_sesudah", interp))

    s.append("\n## 4. Korelasi Spearman strategi vs kinerja\n")
    s.append(_md(t["spearman_kinerja"], "{:.3f}"))
    s.append(_gambar("eda_spearman_heatmap", interp))
    s.append("\n### Persepsi sebagai pembanding\n")
    s.append(_md(t["spearman_persepsi"], "{:.3f}"))
    s.append(
        "\n`persepsi_vs_angka`: apakah persepsi selaras dengan angka nyata; `butir_vs_padanan`: butir "
        "persepsi vs ukuran objektif padanannya; `persepsi_vs_strategi`: persepsi vs skor strategi.\n"
    )

    s.append("\n## 5. Perbandingan kelompok (Mann-Whitney U)\n")
    s.append("### naik_penjualan = 1 vs 0\n")
    s.append(
        "Holm dihitung per varian atas 4 strategi; baris y_persepsi diuji terpisah (pembanding). "
        "`utama_tanpa_seragam` = sampel utama tanpa `flag_jawaban_seragam` (D20).\n\n"
    )
    cols_mw = [
        "varian",
        "variabel",
        "n_1",
        "n_0",
        "median_1",
        "median_0",
        "z",
        "p",
        "p_holm",
        "r",
        "r_rank_biserial",
        "efek",
    ]
    s.append(_md(_kolom(t["mw_naik_penjualan"], cols_mw), "{:.3f}"))
    s.append(_gambar("eda_boxplot_naik_penjualan", interp))
    s.append("\n### tanpa_baseline (1) vs punya baseline (0), 149 responden\n")
    s.append(_md(_kolom(t["mw_tanpa_baseline"], cols_mw), "{:.3f}"))
    s.append(_gambar("eda_boxplot_tanpa_baseline", interp))

    s.append("\n## 6. VIF\n")
    v = t["vif"]
    s.append(
        f"Batas waspada VIF > {_a(5.0, 0)}. VIF maksimum: "
        + "; ".join(
            f"{k[0]} / {k[1]} = {_a(g['vif'].max())}" for k, g in v.groupby(["sampel", "set"])
        )
        + ". `jumlah_platform` dan dummy platform tidak dimasukkan bersamaan (kolinear sempurna).\n\n"
    )
    s.append(_md(v.query("sampel == 'utama'"), "{:.2f}"))
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Ringkasan awam
# ---------------------------------------------------------------------------
def temuan(t: dict[str, pd.DataFrame], df: pd.DataFrame) -> list[str]:
    """5-8 temuan awal dalam bahasa awam."""
    n_utama = int(df["sampel_utama"].sum())
    out = []

    plat = t["profil_platform"]
    num = t["profil_numerik"].query("sampel == 'semua_149'").set_index("variabel")
    out.append(
        f"**Profil.** Sebagian besar UMKM berjualan lewat {plat.iloc[0]['platform']} "
        f"({_pct(plat.iloc[0]['pct_semua_149'])}), {plat.iloc[1]['platform']} "
        f"({_pct(plat.iloc[1]['pct_semua_149'])}), dan {plat.iloc[2]['platform']} "
        f"({_pct(plat.iloc[2]['pct_semua_149'])}); rata-rata memakai "
        f"{_a(num.loc['jumlah_platform', 'mean'], 1)} platform. Omzet bulanan sebelum marketplace "
        f"bermedian {_rp(num.loc['omzet_sebelum_juta', '50%'] * 1e6)}, dan median lama berjualan di "
        f"marketplace {_a(num.loc['lama_di_mp', '50%'], 0)} tahun."
    )

    ss = t["sebelum_sesudah"].set_index(["sampel", "variabel"])
    om = ss.loc[("utama", "omzet (Rp)")]
    n_naik = int(df.loc[df["sampel_utama"] == 1, "naik_penjualan"].sum())
    out.append(
        f"**Kinerja.** Dari {n_utama} UMKM di sampel utama, {n_naik} ({_pct(n_naik / n_utama)}) "
        f"mencatat omzet atau transaksi naik sesudah memakai marketplace, hampir separuh tidak "
        f"berubah, dan yang turun hanya {om['n_turun']} UMKM (omzet). Kenaikannya umumnya kecil "
        f"(median selisih omzet {_rp(om['median_selisih'])}). Karena tidak ada kelompok pembanding "
        "yang tidak memakai marketplace, angka ini menggambarkan perubahan, bukan bukti bahwa "
        "marketplace penyebabnya."
    )

    dk = t["distribusi_konstruk"].query("sampel == 'semua_149'").set_index("konstruk")
    out.append(
        f"**Praktik strategi.** UMKM umumnya jarang mengunggah produk (rata-rata "
        f"{_a(dk.loc['x1_unggah', 'rata_rata'])} dari 5) dan jarang berpromosi "
        f"({_a(dk.loc['x2_promosi', 'rata_rata'])}), terutama iklan berbayar; komunikasi dengan "
        f"pelanggan ({_a(dk.loc['x3_komunikasi', 'rata_rata'])}) dan konsistensi kelola toko "
        f"({_a(dk.loc['x4_konsistensi', 'rata_rata'])}) dinilai lebih baik."
    )

    sb = t["sebaran_butir"]
    out.append(
        f"**Banyak jawaban netral.** Pada {int(sb['dominasi_netral'].sum())} dari {len(sb)} butir, "
        f"lebih dari separuh responden memilih jawaban tengah (3). Paling mencolok pada persepsi "
        f"kinerja: {_pct(dk.loc['y_persepsi', 'pct_tepat_3'])} responden skornya tepat 3. Variasi "
        "jawaban yang sempit membuat perbedaan antar-UMKM lebih sulit terdeteksi."
    )

    kor = t["spearman_kinerja"].query("sampel == 'utama' and y == 'y_obj'")
    kor = kor.sort_values("rho", ascending=False)
    sig = kor[kor["p_holm"] < ALPHA]
    lemah = kor[kor["p_holm"] >= ALPHA]
    out.append(
        f"**Strategi yang berhubungan dengan kenaikan penjualan.** "
        f"{_kapital(_daftar([NAMA[x] for x in sig['x']]))} berhubungan positif dengan kenaikan "
        f"omzet/transaksi (korelasi lemah-sedang, rho {_rentang(sig['rho'])}). UMKM yang "
        "penjualannya naik cenderung punya skor strategi tersebut lebih tinggi. "
        f"{_kapital(_daftar([NAMA[x] for x in lemah['x']]))} hubungannya paling lemah dan belum "
        "bermakna. Ini pola keterkaitan, bukan bukti sebab-akibat; Tahap 4 akan mengujinya dengan "
        "mengontrol profil usaha."
    )

    pb = t["spearman_kinerja"].query("sampel == 'utama' and y == 'y_pelanggan_baru'")
    pers = t["spearman_persepsi"].query("sampel == 'utama'")
    pva = pers[pers["jenis"] == "persepsi_vs_angka"]
    pvs = pers[pers["jenis"] == "persepsi_vs_strategi"]
    neg = pb.sort_values("rho").iloc[0]
    out.append(
        f"**Pelanggan baru dan persepsi.** Jumlah pelanggan baru tidak berhubungan bermakna dengan "
        f"strategi mana pun setelah koreksi uji berganda (rho {_rentang(pb['rho'])}; "
        f"{NAMA[neg['x']]} bahkan sedikit negatif), mungkin karena waktu pengukurannya ambigu (D06). "
        f"Persepsi kinerja hanya lemah selaras dengan angka nyata (rho maks "
        f"{_a(pva['rho'].max())}) dan lebih dekat dengan skor strategi (rho maks "
        f"{_a(pvs['rho'].max())}); ini mendukung keputusan memakai angka objektif sebagai ukuran "
        "kinerja (D02)."
    )

    mw = (
        t["mw_naik_penjualan"].query("variabel in @STRATEGI_COLS").set_index(["varian", "variabel"])
    )
    n_sg = int(df.loc[df["sampel_utama"] == 1, "flag_jawaban_seragam"].sum())
    n_sg_naik = int(
        df.loc[
            (df["sampel_utama"] == 1) & (df["flag_jawaban_seragam"] == 1), "naik_penjualan"
        ].sum()
    )
    berubah = [
        f"{NAMA[x]} (Holm p {_a(mw.loc[('utama', x), 'p_holm'], 3)} -> "
        f"{_a(mw.loc[('utama_tanpa_seragam', x), 'p_holm'], 3)})"
        for x in STRATEGI_COLS
        if (mw.loc[("utama", x), "p_holm"] < ALPHA)
        != (mw.loc[("utama_tanpa_seragam", x), "p_holm"] < ALPHA)
    ]
    vmax = t["vif"]["vif"].max()
    out.append(
        f"**Kepekaan dan kesiapan Tahap 4.** {n_sg} responden sampel utama menjawab semua butir "
        f"strategi dengan angka yang sama ({n_sg_naik} di antaranya naik). Tanpa mereka, "
        + (
            f"kesimpulan berubah untuk {_daftar(berubah)}, jadi hasil itu perlu dibaca hati-hati. "
            if berubah
            else "kesimpulan perbandingan kelompok tidak berubah. "
        )
        + f"Antar-variabel tidak ada tumpang-tindih berlebihan (VIF maks {_a(vmax)}, jauh di "
        "bawah 5), sehingga keempat strategi aman dimasukkan bersama ke model regresi."
    )
    return out


def build_ringkasan(rep: EdaReport, df: pd.DataFrame, interp: dict[str, str]) -> str:
    """Susun reports/eda_ringkasan.md (temuan awal + daftar grafik)."""
    s = ["# Ringkasan EDA: Temuan Awal\n"]
    s.append(
        f"Dibuat oleh `umkm.eda` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. Data: {len(df)} UMKM; "
        f"analisis kinerja memakai {int(df['sampel_utama'].sum())} UMKM yang punya kondisi "
        "'sebelum marketplace'. Semua temuan menggambarkan **keterkaitan**, bukan sebab-akibat. "
        "Rincian teknis ada di `eda_log.md`.\n"
    )
    s.append("## Temuan\n")
    s.extend(f"{i}. {x}" for i, x in enumerate(temuan(rep.tabel, df), 1))
    s.append("\n## Daftar grafik\n")
    s.append("| Grafik | Interpretasi |\n|---|---|")
    s.extend(f"| `figures/{k}.png` | {v} |" for k, v in interp.items())
    return "\n".join(s) + "\n"
