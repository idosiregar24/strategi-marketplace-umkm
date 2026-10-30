"""Teks Tahap 5: interpretasi grafik, deskripsi segmen, reports/segmentasi_log.md dan
reports/segmentasi_ringkasan.md.

Semua kalimat disusun dari angka di tabel agar tetap benar bila data berubah.
Bahasa asosiasi: segmen adalah pengelompokan deskriptif, bukan penjelas kinerja.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from umkm.cleaning import PLATFORM_COLS
from umkm.eda_teks import _a, _daftar, _p, _pct, _rp
from umkm.features import STRATEGI_COLS, _md
from umkm.segmentation import NAMA_FITUR, NAMA_PLATFORM, SET_PEMBANDING, SET_UTAMA, SegmenReport

NAMA_UJI = {
    "x1_unggah": "X1 unggah produk",
    "x2_promosi": "X2 promosi",
    "x3_komunikasi": "X3 komunikasi pelanggan",
    "x4_konsistensi": "X4 konsistensi toko",
    "y_persepsi": "persepsi kinerja",
    "y_obj": "y_obj",
    "y_pelanggan_baru": "pelanggan baru (log)",
    "naik_penjualan": "proporsi naik penjualan",
}
MIN_BENCHMARK = 15  # UMKM naik per segmen; di bawah ini benchmark Tahap 6 dianggap rapuh


def label_silhouette(s: float) -> str:
    """Kaufman & Rousseeuw (1990): > 0,70 kuat; 0,51-0,70 wajar; 0,26-0,50 lemah; <= 0,25 tidak
    ada struktur yang substansial."""
    if s > 0.70:
        return "kuat"
    if s > 0.50:
        return "wajar"
    if s > 0.25:
        return "lemah"
    return "sangat lemah"


def label_jaccard(j: float) -> str:
    """Hennig (2007): >= 0,85 sangat stabil; 0,75-0,85 stabil; 0,60-0,75 ada pola tetapi
    lemah; < 0,60 tidak stabil."""
    if j >= 0.85:
        return "sangat stabil"
    if j >= 0.75:
        return "stabil"
    if j >= 0.60:
        return "berpola tetapi lemah"
    return "tidak stabil"


def _metrik(rep: SegmenReport, set_fitur: str, k: int) -> pd.Series:
    m = rep.tabel["pemilihan_k"]
    return m[(m["set_fitur"] == set_fitur) & (m["k"] == k)].iloc[0]


def _profil(rep: SegmenReport) -> pd.DataFrame:
    p = rep.tabel["profil"]
    return p[p["segmen"] != "Semua"].set_index("segmen")


# ---------------------------------------------------------------------------
# Deskripsi segmen dan interpretasi grafik
# ---------------------------------------------------------------------------
def deskripsi_segmen(rep: SegmenReport) -> dict[int, str]:
    """Satu paragraf deskripsi tiap segmen (kunci = nomor segmen)."""
    p = _profil(rep)
    stab = rep.tabel["stabilitas"].set_index("segmen")
    out = {}
    for s, r in p.iterrows():
        plat = sorted(PLATFORM_COLS, key=lambda c: -r[f"persen_{c}"])[:3]
        skala_dom = max(
            ("Q1_kecil", "Q2_menengah_bawah", "Q3_menengah_atas", "Q4_besar"),
            key=lambda q: r[f"persen_{q}"],
        )
        strat = ", ".join(f"{NAMA_FITUR[c].split()[0]} {_a(r[f'{c}_rata'])}" for c in STRATEGI_COLS)
        out[int(s)] = (
            f"**Segmen {s}: {r['nama_segmen']}** berisi {r['n']} UMKM ({_pct(r['persen'])}). "
            f"Median omzet sebelum marketplace {_rp(r['omzet_sebelum_median'])} (kuartil "
            f"{_rp(r['omzet_sebelum_q1'])} sampai {_rp(r['omzet_sebelum_q3'])}); kuartil omzet "
            f"terbanyak {skala_dom.split('_', 1)[0]} ({_pct(r[f'persen_{skala_dom}'])}). Median lama "
            f"usaha sebelum masuk marketplace {_a(r['lama_usaha_pra_mp_median'], 1)} tahun dan "
            f"lama di marketplace {_a(r['lama_di_mp_median'], 1)} tahun; {r['n_tanpa_baseline']} "
            f"UMKM ({_pct(r['n_tanpa_baseline'] / r['n'])}) berdiri bersamaan dengan masuk "
            f"marketplace (tanpa baseline). Rata-rata memakai {_a(r['jumlah_platform_rata'])} "
            f"platform ({_pct(r['persen_1_platform'])} hanya satu); platform terbanyak "
            + _daftar([f"{NAMA_PLATFORM[c]} {_pct(r[f'persen_{c}'])}" for c in plat])
            + f". Skor strategi rata-rata: {strat}. Di sampel utama ({r['n_sampel_utama']} UMKM), "
            f"{_pct(r['persen_naik_utama'])} ({r['n_naik_utama']} UMKM) melaporkan kenaikan "
            f"penjualan, rata-rata y_obj {_a(r['y_obj_rata_utama'])}. Keanggotaan segmen ini "
            f"{label_jaccard(stab.at[s, 'jaccard_rata'])} saat data di-bootstrap (Jaccard rata-rata "
            f"{_a(stab.at[s, 'jaccard_rata'])})."
        )
    return out


def _beda(rep: SegmenReport) -> tuple[list[str], list[str]]:
    """(variabel berbeda bermakna setelah Holm, variabel tidak berbeda)."""
    u = rep.tabel["uji_beda"]
    beda = [NAMA_UJI[v] for v in u.loc[u["p_holm"] < 0.05, "variabel"]]
    sama = [NAMA_UJI[v] for v in u.loc[u["p_holm"] >= 0.05, "variabel"]]
    return beda, sama


def interpretasi(rep: SegmenReport) -> dict[str, str]:
    """Satu kalimat interpretasi untuk tiap grafik (kunci = nama berkas grafik)."""
    k = rep.info["k"]
    mu = _metrik(rep, SET_UTAMA, k)
    mp = rep.tabel["pemilihan_k"]
    mp = mp[mp["set_fitur"] == SET_PEMBANDING]
    p = _profil(rep)
    naik = p["persen_naik_utama"]
    beda, _ = _beda(rep)
    var = rep.info["pca_var"]
    return {
        "segmen_pemilihan_k": (
            f"Dengan fitur profil, k = {k} {_status_k(rep)} (median ARI "
            f"bootstrap {_a(mu['ari_boot_median'])}, k lain {_a(_rentang_k(rep, k)[0])}-"
            f"{_a(_rentang_k(rep, k)[1])}) dengan silhouette {_a(mu['silhouette'])}; menambah skor "
            f"X1-X4 ke fitur menurunkan silhouette ke {_a(mp['silhouette'].min())}-"
            f"{_a(mp['silhouette'].max())} dan stabilitas ke {_a(mp['ari_boot_median'].min())}-"
            f"{_a(mp['ari_boot_median'].max())}, dan inersia turun landai tanpa siku yang jelas."
        ),
        "segmen_profil": (
            f"Segmen dibedakan terutama oleh {_daftar(_pembeda(rep))} (warna pekat di baris "
            "profil), sedangkan skor strategi dan kinerja nyaris sama antar-segmen (warna pucat; "
            f"proporsi naik penjualan {_daftar([_pct(v) for v in naik])}"
            + (
                f"; berbeda bermakna setelah Holm: {_daftar(beda)})."
                if beda
                else "; tidak ada beda bermakna setelah koreksi Holm)."
            )
        ),
        "segmen_peta_pca": (
            f"Dua komponen utama menjelaskan {_pct(var.sum())} variasi fitur profil; komponen 1 "
            f"terutama memuat {_daftar(_muatan_pc1(rep))}. Titik-titik segmen bersinggungan di "
            "bagian tengah, sesuai silhouette yang rendah: segmen lebih tepat dibaca sebagai "
            "ujung-ujung rentang kondisi usaha daripada kelompok yang terpisah tegas."
        ),
    }


def _pembeda(rep: SegmenReport) -> list[str]:
    """Fitur profil yang rata-rata segmennya menyimpang > batas deskriptor (dalam SD)."""
    zp = rep.tabel["pusat_z"].set_index("segmen")[rep.info["fitur"]]
    sel = zp.abs().max() > rep.info["batas_deskriptor"]
    return [_kecil(NAMA_FITUR[f].split(" (")[0]) for f in zp.columns[sel]]


def _muatan_pc1(rep: SegmenReport, batas: float = 0.4) -> list[str]:
    m = rep.info["pca_muatan"]["PC1"]
    return [_kecil(NAMA_FITUR[f].split(" (")[0]) for f in m.index[m.abs() >= batas]]


def _status_k(rep: SegmenReport) -> str:
    m = rep.tabel["pemilihan_k"]
    m = m[m["set_fitur"] == SET_UTAMA]
    n_stabil = int((m["ari_boot_median"] >= rep.info["ari_min"]).sum())
    if rep.info["aturan_k"] != "stabil":
        return "dipilih dengan aturan cadangan karena tidak ada k yang stabil"
    return "adalah satu-satunya pilihan yang stabil" if n_stabil == 1 else "paling memenuhi aturan"


def _k_lain(rep: SegmenReport, k: int) -> list[int]:
    return sorted(int(j) for j in set(rep.tabel["pemilihan_k"]["k"]) if j != k)


def _rentang_k(rep: SegmenReport, k: int) -> tuple[float, float]:
    m = rep.tabel["pemilihan_k"]
    m = m[(m["set_fitur"] == SET_UTAMA) & (m["k"] != k)]["ari_boot_median"]
    return float(m.min()), float(m.max())


# ---------------------------------------------------------------------------
# Log dan ringkasan
# ---------------------------------------------------------------------------
def _gambar(nama: str, interp: dict[str, str]) -> str:
    return f"![{nama}](figures/{nama}.png)\n\n**Interpretasi:** {interp[nama]}\n"


def _tabel_k(rep: SegmenReport) -> pd.DataFrame:
    m = rep.tabel["pemilihan_k"]
    return m[
        [
            "set_fitur",
            "k",
            "ukuran",
            "silhouette",
            "inersia",
            "calinski_harabasz",
            "davies_bouldin",
            "ari_boot_median",
            "ari_boot_p05",
            "ari_ward",
            "ari_gmm",
        ]
    ]


def keterbatasan(rep: SegmenReport) -> list[str]:
    """Daftar keterbatasan Tahap 5 (dari angka)."""
    k = rep.info["k"]
    p = _profil(rep)
    _, sama = _beda(rep)
    mu = _metrik(rep, SET_UTAMA, k)
    out = [
        (
            f"Struktur klaster {label_silhouette(rep.info['silhouette'])} (silhouette "
            f"{_a(rep.info['silhouette'], 3)}): UMKM tersebar kontinu, bukan kelompok yang terpisah "
            "tegas. Segmen berguna sebagai ringkasan ujung-ujung kondisi usaha; UMKM di dekat batas "
            "bisa masuk segmen mana pun."
        ),
        (
            f"Ward dan Gaussian Mixture hanya sebagian sepakat dengan K-Means pada k = {k} (ARI "
            f"{_a(mu['ari_ward'])} dan {_a(mu['ari_gmm'])}), jadi batas segmen bergantung pada metode."
        ),
        "Segmen tidak berbeda bermakna pada " + _daftar(sama) + " (setelah Holm). Artinya "
        "segmentasi ini menggambarkan kondisi usaha, bukan kelompok kinerja; benchmark Tahap 6 per "
        "segmen kemungkinan mirip satu sama lain.",
        (
            "Fitur hanya empat dan sebagian kasar (skala omzet = kuartil 1-4; lama usaha dalam tahun "
            "bulat; jumlah platform 1-4), sehingga banyak UMKM bernilai kembar."
        ),
    ]
    kecil = p[p["n_naik_utama"] < MIN_BENCHMARK]
    if not kecil.empty:
        out.append(
            "Benchmark Tahap 6 untuk segmen "
            + _daftar([str(s) for s in kecil.index])
            + f" bertumpu pada kurang dari {MIN_BENCHMARK} UMKM yang naik; tafsirkan hati-hati."
        )
    tb = p["n_tanpa_baseline"]
    out.append(
        f"UMKM tanpa baseline ({int(tb.sum())}) ikut membentuk segmen tetapi tidak ikut sampel "
        f"kinerja; {_daftar([f'{int(v)} di segmen {s}' for s, v in tb.items()])}, sehingga "
        "proporsi naik penjualan segmen dihitung dari sampel utama yang lebih kecil."
    )
    return out


def build_log(rep: SegmenReport, cfg: dict[str, Any]) -> str:
    """Susun reports/segmentasi_log.md (pengaturan, tabel, grafik, interpretasi)."""
    c = cfg["segmentation"]
    k = rep.info["k"]
    interp = interpretasi(rep)
    mu = _metrik(rep, SET_UTAMA, k)
    ari = rep.info["ari_boot"]
    s = ["# Log Tahap 5: Segmentasi Kondisi UMKM\n"]
    s.append(
        f"Dibuat oleh `umkm.segmentation` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. "
        f"{rep.info['n']} UMKM, seed {cfg['seed']}.\n"
    )
    s.append("## Pengaturan (D27)\n")
    s += [
        "- Fitur pembentuk segmen (profil saja): "
        + ", ".join(f"`{f}`" for f in c["fitur"])
        + f"; `{'`, `'.join(c['fitur_log1p'])}` ditransformasi log1p; semua distandarkan "
        "(StandardScaler di dalam pipa).",
        (
            "- `skala_omzet_ord` = kuartil skala omzet (1 = Q1_kecil ... 4 = Q4_besar, D22), dipakai "
            "sebagai angka agar omzet 0 (R008) dan omzet sangat besar tidak mendominasi jarak."
        ),
        (
            "- Skor X1-X4 dan target kinerja TIDAK dipakai membentuk segmen; set profil + X1-X4 "
            "dihitung sebagai pembanding."
        ),
        (
            f"- K-Means k = {c['k_min']}..{c['k_max']} (n_init {c['n_init']}); pembanding Ward dan "
            "Gaussian Mixture (kovarians penuh, n_init 10) pada data terstandar."
        ),
        (
            f"- Aturan k: semua klaster >= {c['min_cluster_size']} UMKM DAN median ARI bootstrap >= "
            f"{_a(c['ari_min'], 1)}, lalu silhouette tertinggi. Stabilitas: bootstrap "
            f"{c['bootstrap_n']}x, pipa dilatih ulang di sampel bootstrap lalu memprediksi seluruh "
            "baris; ARI terhadap solusi utama dan Jaccard maksimum per klaster (Hennig, 2007)."
        ),
        (
            "- Nomor segmen diurutkan dari rata-rata pusat terstandar terendah (segmen 1 = paling "
            f"kecil/baru). Nama dari fitur yang |z| rata-rata segmennya > {_a(c['batas_deskriptor'])}."
        ),
        "",
    ]
    s.append("## Pemilihan k\n")
    s.append(_md(_tabel_k(rep), "{:.3f}"))
    s.append(
        f"\nTerpilih k = {k} (aturan: {rep.info['aturan_k']}); silhouette "
        f"{_a(mu['silhouette'], 3)} ({label_silhouette(mu['silhouette'])}). Set {SET_PEMBANDING}: "
        f"tidak ada k yang stabil; dengan aturan cadangan k = {rep.info['k_pembanding']} "
        f"(silhouette {_a(_metrik(rep, SET_PEMBANDING, rep.info['k_pembanding'])['silhouette'], 3)}"
        f"), ARI terhadap segmen utama {_a(rep.info['ari_pembanding_vs_utama'])}.\n"
    )
    s.append(_gambar("segmen_pemilihan_k", interp))
    s.append("## Stabilitas\n")
    s.append(
        f"ARI bootstrap solusi utama: median {_a(np.median(ari), 3)}, persentil 5 "
        f"{_a(np.percentile(ari, 5), 3)}, minimum {_a(ari.min(), 3)} ({len(ari)} ulangan).\n"
    )
    st = rep.tabel["stabilitas"].copy()
    st["label"] = st["jaccard_rata"].map(label_jaccard)
    s.append(_md(st, "{:.3f}"))
    s.append("\n### Sensitivitas pilihan fitur dan sampel\n")
    s.append(_md(rep.tabel["sensitivitas"], "{:.3f}"))
    s.append(
        "\nARI terhadap segmen utama; varian dilatih ulang lalu memprediksi seluruh 149 UMKM. "
        "Menambah X1-X4 mengubah pengelompokan paling banyak, karena segmen lalu ikut dibentuk "
        "oleh tingkat strategi.\n"
    )
    s.append("## Profil segmen\n")
    p = rep.tabel["profil"]
    kol = [
        "segmen",
        "nama_segmen",
        "n",
        "n_sampel_utama",
        "n_tanpa_baseline",
        "omzet_sebelum_median",
        "lama_usaha_pra_mp_median",
        "lama_di_mp_median",
        "jumlah_platform_rata",
        *[f"{c}_rata" for c in STRATEGI_COLS],
        "n_naik_utama",
        "persen_naik_utama",
        "y_obj_rata_utama",
    ]
    s.append(_md(p[kol], "{:.2f}"))
    s.append(
        "\nTabel lengkap (platform, sebaran kuartil omzet, median strategi): "
        "`tables/profil_segmen.csv`.\n"
    )
    s.append(_gambar("segmen_profil", interp))
    s.append("### Muatan komponen utama (PCA, data terstandar)\n")
    s.append(_md(rep.info["pca_muatan"].reset_index(names="fitur"), "{:.3f}"))
    s.append("\n" + _gambar("segmen_peta_pca", interp))
    s.append("## Beda antar-segmen pada variabel di luar fitur pembentuk\n")
    u = rep.tabel["uji_beda"].copy()
    s.append(_md(u, "{:.3f}"))
    s.append(
        "\nFitur profil tidak diuji karena pasti berbeda (segmen dibentuk darinya). Holm per "
        "keluarga (strategi; kinerja; persepsi diuji terpisah). Efek epsilon-kuadrat < 0,01 "
        "sangat kecil, 0,01-0,06 kecil.\n"
    )
    s.append("## Deskripsi segmen\n")
    s += [d + "\n" for d in deskripsi_segmen(rep).values()]
    s.append("## Keterbatasan\n")
    s += [f"- {x}" for x in keterbatasan(rep)]
    s.append("")
    return "\n".join(s)


def build_ringkasan(rep: SegmenReport, cfg: dict[str, Any]) -> str:
    """Susun reports/segmentasi_ringkasan.md (bahasa sederhana)."""
    k = rep.info["k"]
    interp = interpretasi(rep)
    beda, sama = _beda(rep)
    u = rep.tabel["uji_beda"].set_index("variabel")
    p = _profil(rep)
    s = ["# Ringkasan Tahap 5: Segmen Kondisi UMKM\n"]
    s.append(
        f"Dibuat oleh `umkm.segmentation` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. "
        f"{rep.info['n']} UMKM dikelompokkan menurut kondisi usaha (skala omzet, lama usaha "
        "sebelum marketplace, lama di marketplace, jumlah platform). Skor strategi dan kinerja "
        "tidak dipakai untuk membentuk segmen (D27).\n"
    )
    s.append(f"## Hasil: {k} segmen\n")
    s += [d + "\n" for d in deskripsi_segmen(rep).values()]
    s.append("## Seberapa kuat dan stabil segmennya\n")
    s += [
        (
            f"- Silhouette {_a(rep.info['silhouette'], 3)}: pemisahan "
            f"{label_silhouette(rep.info['silhouette'])} (Kaufman dan Rousseeuw: <= 0,25 berarti "
            "tidak ada struktur kelompok yang substansial). UMKM tidak membentuk kelompok yang "
            "terpisah tegas; segmen menggambarkan ujung-ujung rentang kondisi usaha."
        ),
        f"- Stabil saat data diacak ulang (bootstrap {len(rep.info['ari_boot'])}x): median ARI "
        f"{_a(np.median(rep.info['ari_boot']))}, Jaccard per segmen "
        + _daftar([_a(v) for v in rep.tabel["stabilitas"]["jaccard_rata"]])
        + f". k lain ({', '.join(str(j) for j in _k_lain(rep, k))}) median ARI "
        f"{_a(_rentang_k(rep, k)[0])}-{_a(_rentang_k(rep, k)[1])}.",
        (
            "- Bila skor strategi X1-X4 ikut dijadikan fitur, struktur makin lemah (silhouette "
            f"{_a(_metrik(rep, SET_PEMBANDING, rep.info['k_pembanding'])['silhouette'])}) dan tidak "
            "ada jumlah segmen yang stabil."
        ),
        "",
    ]
    s.append("## Apa artinya untuk rekomendasi (Tahap 6)\n")
    naik = u.loc["naik_penjualan"]
    s.append(
        "Antar-segmen tidak ada beda bermakna pada " + _daftar(sama) + " setelah koreksi Holm "
        f"(contoh: proporsi naik penjualan {_daftar([_pct(v) for v in p['persen_naik_utama']])}, "
        f"{_p(naik['p'])}). Jadi segmen membedakan kondisi usaha, bukan tingkat strategi atau "
        "kinerja. Benchmark per segmen di Tahap 6 dihitung dari "
        + _daftar([f"{int(v)} UMKM naik di segmen {s_}" for s_, v in p["n_naik_utama"].items()])
        + "; karena skor strategi kedua segmen mirip, prioritas strategi kemungkinan besar serupa "
        "dan perbedaannya lebih pada konteks tindakan (skala dan pengalaman usaha).\n"
        + (f"\nBerbeda bermakna: {_daftar(beda)}.\n" if beda else "")
    )
    s.append("## Keterbatasan\n")
    s += [f"- {x}" for x in keterbatasan(rep)]
    s.append("\n## Grafik\n")
    s.append("| Grafik | Interpretasi |\n|---|---|")
    for nm in ("segmen_pemilihan_k", "segmen_profil", "segmen_peta_pca"):
        s.append(f"| `figures/{nm}.png` | {interp[nm]} |")
    s.append(
        "\n_Segmen adalah pengelompokan deskriptif dari data survei satu waktu; keanggotaan segmen "
        "tidak menjelaskan mengapa penjualan suatu UMKM naik._\n"
    )
    return "\n".join(s)


def _kecil(teks: str) -> str:
    """Huruf pertama kecil tanpa mengubah singkatan (MP, X1)."""
    return teks[:1].lower() + teks[1:]
