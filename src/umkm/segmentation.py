"""Tahap 5: segmentasi kondisi UMKM dengan K-Means (pembanding Ward dan Gaussian Mixture).

Membaca data_features.csv; menulis data/processed/data_segmen.csv, reports/tables/profil_segmen.csv
dan segmen_*.csv, reports/figures/segmen_*.png, serta reports/segmentasi_log.md dan
segmentasi_ringkasan.md.

Segmen dibentuk HANYA dari profil UMKM (skala omzet, lama usaha sebelum MP, lama di MP, jumlah
platform; D27). Skor strategi X1-X4 dan target kinerja tidak dipakai untuk membentuk segmen, agar
benchmark Tahap 6 (skor UMKM yang naik di segmen yang sama) tidak melingkar. Set profil + X1-X4
dihitung sebagai pembanding.

Fungsi inti (`siapkan_fitur`, `pipa_kmeans`, `tetapkan_segmen`) hanya butuh pandas/numpy/sklearn
agar bisa dipakai `recommend()` untuk satu UMKM baru.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from umkm.cleaning import PLATFORM_COLS
from umkm.features import SKALA_LABELS, STRATEGI_COLS

NAMA_FITUR = {
    "skala_omzet_ord": "Skala omzet (kuartil 1-4)",
    "lama_usaha_pra_mp": "Lama usaha sebelum MP (th)",
    "lama_di_mp": "Lama di marketplace (th)",
    "jumlah_platform": "Jumlah platform",
    "x1_unggah": "X1 Unggah produk",
    "x2_promosi": "X2 Promosi",
    "x3_komunikasi": "X3 Komunikasi pelanggan",
    "x4_konsistensi": "X4 Konsistensi toko",
}
NAMA_PLATFORM = {
    "mp_gofood": "GoFood",
    "mp_grabfood": "GrabFood",
    "mp_shopee": "Shopee",
    "mp_maxim": "Maxim",
    "mp_tiktok": "TikTok",
}
# Deskriptor nama segmen: (rendah, sedang, tinggi); sedang kosong = tidak disebut di nama
DESKRIPTOR = {
    "skala_omzet_ord": ("omzet kecil", "omzet menengah", "omzet besar"),
    "lama_usaha_pra_mp": ("usaha muda", "", "usaha mapan"),
    "lama_di_mp": ("baru di marketplace", "", "lama di marketplace"),
    "jumlah_platform": ("sedikit platform", "", "banyak platform"),
}
SET_UTAMA = "profil"
SET_PEMBANDING = "profil + strategi"


# ---------------------------------------------------------------------------
# Fitur dan model (dipakai juga untuk UMKM baru)
# ---------------------------------------------------------------------------
def skala_ordinal(skala: pd.Series) -> pd.Series:
    """Label kuartil skala_omzet (Q1_kecil..Q4_besar) -> angka 1-4."""
    peta = {lab: i for i, lab in enumerate(SKALA_LABELS, 1)}
    out = skala.map(peta)
    if out.isna().any():
        raise ValueError(f"skala_omzet tidak dikenal: {sorted(set(skala[out.isna()]))}")
    return out.astype(float)


def siapkan_fitur(df: pd.DataFrame, fitur: list[str], log1p: list[str]) -> pd.DataFrame:
    """Matriks fitur klaster (belum distandarkan); berlaku untuk satu maupun banyak baris."""
    x = df.copy()
    if "skala_omzet_ord" in fitur and "skala_omzet_ord" not in x:
        x["skala_omzet_ord"] = skala_ordinal(x["skala_omzet"])
    x = x[fitur].astype(float)
    for c in log1p:
        if c in x:
            x[c] = np.log1p(x[c])
    return x


def pipa_kmeans(k: int, seed: int = 42, n_init: int = 50) -> Pipeline:
    """StandardScaler + K-Means; skala dihitung di dalam pipa (ikut tersimpan untuk data baru)."""
    return Pipeline(
        [("skala", StandardScaler()), ("kmeans", KMeans(k, n_init=n_init, random_state=seed))]
    )


def urutan_segmen(pipa: Pipeline) -> dict[int, int]:
    """Label K-Means -> nomor segmen 1..k, urut dari rata-rata pusat terstandar terendah.

    Semua fitur profil berarah sama (lebih besar/lama/banyak), jadi segmen 1 = paling kecil/baru.
    """
    pusat = pipa.named_steps["kmeans"].cluster_centers_.mean(axis=1)
    return {int(lab): i for i, lab in enumerate(np.argsort(pusat), 1)}


def tetapkan_segmen(pipa: Pipeline, x: pd.DataFrame, urutan: dict[int, int]) -> pd.Series:
    """Nomor segmen (1..k) untuk tiap baris x memakai pipa yang sudah dilatih."""
    return pd.Series(pipa.predict(x), index=x.index).map(urutan).astype(int)


# ---------------------------------------------------------------------------
# Pemilihan k dan stabilitas
# ---------------------------------------------------------------------------
def _jaccard(a: np.ndarray, b: np.ndarray) -> float:
    return float((a & b).sum() / max((a | b).sum(), 1))


def stabilitas_bootstrap(
    x: pd.DataFrame, k: int, label: np.ndarray, n_boot: int, seed: int = 42, n_init: int = 10
) -> tuple[np.ndarray, np.ndarray]:
    """ARI tiap bootstrap terhadap solusi utama, dan Jaccard maksimum tiap klaster (n_boot x k).

    Tiap ulangan: pipa (scaler + K-Means) dilatih pada sampel bootstrap lalu memprediksi seluruh
    baris; Jaccard klaster c = kecocokan terbaik dengan salah satu klaster bootstrap (Hennig, 2007).
    """
    rng = np.random.default_rng(seed)
    kel = np.unique(label)
    ari = np.empty(n_boot)
    jac = np.empty((n_boot, len(kel)))
    for b in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        pb = pipa_kmeans(k, seed + b, n_init).fit(x.iloc[i])
        lb = pb.predict(x)
        ari[b] = adjusted_rand_score(label, lb)
        for j, c in enumerate(kel):
            jac[b, j] = max(_jaccard(label == c, lb == d) for d in np.unique(lb))
    return ari, jac


def metrik_k(
    x: pd.DataFrame, ks: range, seed: int, n_init: int, n_boot: int, n_init_boot: int
) -> pd.DataFrame:
    """Metrik tiap k: silhouette, inersia (elbow), CH, DB, ukuran klaster, ARI bootstrap,
    dan kesesuaian Ward/GMM dengan K-Means."""
    z = StandardScaler().fit_transform(x)
    rows = []
    for k in ks:
        pipa = pipa_kmeans(k, seed, n_init).fit(x)
        lab = pipa.named_steps["kmeans"].labels_
        ari, _ = stabilitas_bootstrap(x, k, lab, n_boot, seed, n_init_boot)
        ward = AgglomerativeClustering(k, linkage="ward").fit_predict(z)
        gmm = GaussianMixture(k, n_init=10, random_state=seed).fit(z).predict(z)
        ukuran = np.bincount(lab, minlength=k)
        rows.append(
            {
                "k": k,
                "silhouette": silhouette_score(z, lab),
                "inersia": pipa.named_steps["kmeans"].inertia_,
                "calinski_harabasz": calinski_harabasz_score(z, lab),
                "davies_bouldin": davies_bouldin_score(z, lab),
                "ukuran_min": int(ukuran.min()),
                "ukuran": "/".join(map(str, sorted(ukuran, reverse=True))),
                "ari_boot_median": float(np.median(ari)),
                "ari_boot_p05": float(np.percentile(ari, 5)),
                "ari_boot_rata": float(ari.mean()),
                "silhouette_ward": silhouette_score(z, ward),
                "ari_ward": adjusted_rand_score(lab, ward),
                "silhouette_gmm": silhouette_score(z, gmm) if len(set(gmm)) > 1 else np.nan,
                "ari_gmm": adjusted_rand_score(lab, gmm),
            }
        )
    return pd.DataFrame(rows)


def pilih_k(metrik: pd.DataFrame, min_size: int, ari_min: float) -> tuple[int, str]:
    """k dengan silhouette tertinggi di antara k yang semua klasternya >= min_size dan median ARI
    bootstrap >= ari_min. Bila tidak ada yang stabil: silhouette tertinggi di antara k yang
    ukurannya cukup (dicatat sebagai cadangan)."""
    cukup = metrik[metrik["ukuran_min"] >= min_size]
    if cukup.empty:
        raise ValueError(f"Tidak ada k dengan semua klaster >= {min_size} responden.")
    stabil = cukup[cukup["ari_boot_median"] >= ari_min]
    if not stabil.empty:
        return int(stabil.loc[stabil["silhouette"].idxmax(), "k"]), "stabil"
    return int(cukup.loc[cukup["silhouette"].idxmax(), "k"]), "cadangan_tidak_stabil"


# ---------------------------------------------------------------------------
# Nama dan profil segmen
# ---------------------------------------------------------------------------
def z_pusat(x: pd.DataFrame, segmen: pd.Series) -> pd.DataFrame:
    """Rata-rata fitur (setelah transformasi) tiap segmen dalam satuan SD dari rata-rata semua."""
    z = (x - x.mean()) / x.std(ddof=1)
    return z.groupby(segmen).mean()


def nama_segmen(zp: pd.DataFrame, batas: float) -> dict[int, str]:
    """Nama segmen dari deskriptor fitur yang |z| rata-ratanya melewati batas."""
    out = {}
    for seg, r in zp.iterrows():
        bag = []
        for f, (rendah, sedang, tinggi) in DESKRIPTOR.items():
            if f not in r:
                continue
            d = tinggi if r[f] > batas else rendah if r[f] < -batas else sedang
            if d:
                bag.append(d)
        nama = ", ".join(bag) if bag else "profil rata-rata"
        out[int(seg)] = nama[:1].upper() + nama[1:]
    # nama kembar (deskriptor sama) dibedakan dengan nomor segmen
    for nm in {v for v in out.values() if list(out.values()).count(v) > 1}:
        for seg in [s for s, v in out.items() if v == nm]:
            out[seg] = f"{nm} ({seg})"
    return out


def _omzet(df: pd.DataFrame) -> pd.Series:
    return np.expm1(df["log_omzet_sebelum"])


def profil_segmen(df: pd.DataFrame, segmen: pd.Series, nama: dict[int, str]) -> pd.DataFrame:
    """Profil tiap segmen (+ baris 'Semua'): ukuran, profil, platform, strategi, dan kinerja.

    Kinerja (naik_penjualan, y_obj) hanya pada sampel utama (D14); profil dan strategi pada 149.
    """
    d = df.assign(segmen=segmen.to_numpy(), omzet_sebelum=_omzet(df))
    grup = [(s, d[d["segmen"] == s]) for s in sorted(nama)] + [("Semua", d)]
    rows = []
    for s, g in grup:
        u = g[g["sampel_utama"] == 1]
        r = {
            "segmen": s,
            "nama_segmen": nama.get(s, "Semua UMKM"),
            "n": len(g),
            "persen": len(g) / len(d),
            "n_sampel_utama": len(u),
            "n_tanpa_baseline": int(g["tanpa_baseline"].sum()),
            "omzet_sebelum_median": g["omzet_sebelum"].median(),
            "omzet_sebelum_q1": g["omzet_sebelum"].quantile(0.25),
            "omzet_sebelum_q3": g["omzet_sebelum"].quantile(0.75),
        }
        for lab in SKALA_LABELS:
            r[f"persen_{lab}"] = (g["skala_omzet"] == lab).mean()
        for c in ("lama_usaha_pra_mp", "lama_di_mp"):
            r[f"{c}_median"] = g[c].median()
            r[f"{c}_rata"] = g[c].mean()
        r["jumlah_platform_rata"] = g["jumlah_platform"].mean()
        r["persen_1_platform"] = (g["jumlah_platform"] == 1).mean()
        for c in PLATFORM_COLS:
            r[f"persen_{c}"] = g[c].mean()
        for c in STRATEGI_COLS:
            r[f"{c}_rata"] = g[c].mean()
            r[f"{c}_median"] = g[c].median()
        r["y_persepsi_rata"] = g["y_persepsi"].mean()
        r["n_naik_utama"] = int(u["naik_penjualan"].sum())
        r["persen_naik_utama"] = u["naik_penjualan"].mean()
        r["y_obj_rata_utama"] = u["y_obj"].mean()
        r["pelanggan_baru_median"] = np.expm1(g["y_pelanggan_baru"]).median()
        rows.append(r)
    return pd.DataFrame(rows)


def uji_beda_segmen(df: pd.DataFrame, segmen: pd.Series) -> pd.DataFrame:
    """Beda antar-segmen pada variabel yang TIDAK dipakai membentuk segmen (strategi, kinerja).

    Fitur profil tidak diuji (pasti berbeda karena segmen dibentuk darinya). Holm per keluarga.
    """
    from umkm import stats

    d = df.assign(segmen=segmen.to_numpy())
    u = d[d["sampel_utama"] == 1]
    rows = []
    uji_num = [(c, "strategi", d) for c in STRATEGI_COLS + ["y_persepsi"]] + [
        ("y_obj", "kinerja", u),
        ("y_pelanggan_baru", "kinerja", u),
    ]
    for c, kel, data in uji_num:
        r = stats.kruskal_eps([g[c] for _, g in data.groupby("segmen")])
        rows.append(
            {
                "variabel": c,
                "keluarga": kel,
                "sampel": "utama" if data is u else "semua",
                "uji": "Kruskal-Wallis",
                "n": r["n"],
                "statistik": r["H"],
                "p": r["p"],
                "efek": r["efek"],
                "ukuran_efek": "epsilon-kuadrat",
            }
        )
    r = stats.chi2_cramer(u["segmen"], u["naik_penjualan"])
    rows.append(
        {
            "variabel": "naik_penjualan",
            "keluarga": "kinerja",
            "sampel": "utama",
            "uji": r["uji"],
            "n": r["n"],
            "statistik": r["statistik"],
            "p": r["p"],
            "efek": r["efek"],
            "ukuran_efek": "Cramer V",
        }
    )
    out = pd.DataFrame(rows)
    # y_persepsi pendukung, diuji terpisah dari keluarga strategi (sama seperti D23)
    out.loc[out["variabel"] == "y_persepsi", "keluarga"] = "persepsi"
    out["p_holm"] = out.groupby("keluarga")["p"].transform(stats.holm)
    return out


# ---------------------------------------------------------------------------
# Analisis lengkap
# ---------------------------------------------------------------------------
@dataclass
class SegmenReport:
    """Data bersegmen, tabel, info, dan path grafik Tahap 5."""

    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    tabel: dict[str, pd.DataFrame] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    grafik: dict[str, Any] = field(default_factory=dict)
    pipa: Pipeline | None = None


def _sensitivitas(
    df: pd.DataFrame, c: dict[str, Any], k: int, label: pd.Series, seed: int
) -> pd.DataFrame:
    """ARI solusi alternatif terhadap solusi utama (seluruh 149 baris diprediksi)."""
    x = siapkan_fitur(df, c["fitur"], c["fitur_log1p"])
    varian = {
        "fit hanya sampel utama (116)": (x, df["sampel_utama"] == 1),
        "tanpa transformasi log1p": (siapkan_fitur(df, c["fitur"], []), None),
        "profil + strategi (X1-X4)": (
            siapkan_fitur(df, c["fitur"] + c["fitur_pembanding"], c["fitur_log1p"]),
            None,
        ),
    }
    rows = []
    for nm, (xv, mask) in varian.items():
        latih = xv if mask is None else xv[mask]
        p = pipa_kmeans(k, seed, c["n_init"]).fit(latih)
        lab = p.predict(xv)
        rows.append(
            {
                "varian": nm,
                "k": k,
                "n_latih": len(latih),
                "ari_vs_utama": adjusted_rand_score(label, lab),
                "silhouette": silhouette_score(p.named_steps["skala"].transform(xv), lab),
            }
        )
    return pd.DataFrame(rows)


def analisis(df: pd.DataFrame, cfg: dict[str, Any]) -> SegmenReport:
    """Jalankan seluruh analisis Tahap 5 dan kembalikan hasil (tanpa menulis berkas)."""
    c = cfg["segmentation"]
    seed = cfg["seed"]
    ks = range(c["k_min"], c["k_max"] + 1)
    rep = SegmenReport()

    x = siapkan_fitur(df, c["fitur"], c["fitur_log1p"])
    x_pemb = siapkan_fitur(df, c["fitur"] + c["fitur_pembanding"], c["fitur_log1p"])
    met = []
    for nm, xv in ((SET_UTAMA, x), (SET_PEMBANDING, x_pemb)):
        m = metrik_k(xv, ks, seed, c["n_init"], c["bootstrap_n"], c["n_init_bootstrap"])
        met.append(m.assign(set_fitur=nm))
    metrik = pd.concat(met, ignore_index=True)
    k, aturan = pilih_k(
        metrik[metrik["set_fitur"] == SET_UTAMA], c["min_cluster_size"], c["ari_min"]
    )
    k_pemb, aturan_pemb = pilih_k(
        metrik[metrik["set_fitur"] == SET_PEMBANDING], c["min_cluster_size"], c["ari_min"]
    )

    pipa = pipa_kmeans(k, seed, c["n_init"]).fit(x)
    urutan = urutan_segmen(pipa)
    segmen = tetapkan_segmen(pipa, x, urutan)
    zp = z_pusat(x, segmen)
    nama = nama_segmen(zp, c["batas_deskriptor"])

    ari, jac = stabilitas_bootstrap(
        x, k, segmen.to_numpy(), c["bootstrap_n"], seed, c["n_init_bootstrap"]
    )
    kel = np.unique(segmen)
    stab = pd.DataFrame(
        {
            "segmen": kel,
            "nama_segmen": [nama[s] for s in kel],
            "jaccard_rata": jac.mean(axis=0),
            "jaccard_median": np.median(jac, axis=0),
            "jaccard_p05": np.percentile(jac, 5, axis=0),
            "persen_bubar": (jac < 0.5).mean(axis=0),
        }
    )
    z = pipa.named_steps["skala"].transform(x)
    sil = silhouette_score(z, segmen)
    jarak = np.linalg.norm(z - pipa.named_steps["kmeans"].cluster_centers_[pipa.predict(x)], axis=1)

    pca = PCA(2, random_state=seed).fit(z)
    rep.pipa = pipa
    rep.data = df[
        ["id_responden", "sampel_utama", "tanpa_baseline", "skala_omzet", *c["fitur"][1:]]
    ].assign(
        skala_omzet_ord=x["skala_omzet_ord"],
        segmen=segmen.to_numpy(),
        nama_segmen=segmen.map(nama).to_numpy(),
        jarak_pusat=jarak,
    )
    rep.data = rep.data.join(df[PLATFORM_COLS + STRATEGI_COLS + ["naik_penjualan", "y_obj"]])
    rep.data.insert(4, "omzet_sebelum", _omzet(df).round())
    pemb = pipa_kmeans(k_pemb, seed, c["n_init"]).fit(x_pemb)
    zp_all = z_pusat(x_pemb, segmen)
    rep.tabel = {
        "pemilihan_k": metrik,
        "stabilitas": stab,
        "pusat_z": zp_all.reset_index(names="segmen"),
        "uji_beda": uji_beda_segmen(df, segmen),
        "sensitivitas": _sensitivitas(df, c, k, segmen, seed),
    }
    rep.tabel["profil"] = profil_segmen(df, segmen, nama)
    rep.info = {
        "k": k,
        "aturan_k": aturan,
        "ari_min": c["ari_min"],
        "batas_deskriptor": c["batas_deskriptor"],
        "min_cluster_size": c["min_cluster_size"],
        "k_pembanding": k_pemb,
        "aturan_k_pembanding": aturan_pemb,
        "ari_pembanding_vs_utama": adjusted_rand_score(segmen, pemb.predict(x_pemb)),
        "silhouette": sil,
        "ari_boot": ari,
        "nama": nama,
        "n": len(df),
        "fitur": c["fitur"],
        "pca_xy": pca.transform(z),
        "pca_var": pca.explained_variance_ratio_,
        "pca_muatan": pd.DataFrame(pca.components_.T, index=c["fitur"], columns=["PC1", "PC2"]),
    }
    return rep


# ---------------------------------------------------------------------------
# Grafik
# ---------------------------------------------------------------------------
def buat_grafik(rep: SegmenReport) -> dict[str, Any]:
    """Grafik Tahap 5: pemilihan k, profil segmen (heatmap), dan peta PCA."""
    from umkm import viz

    m = rep.tabel["pemilihan_k"]
    k = rep.info["k"]
    piv = {
        kol: m.pivot(index="k", columns="set_fitur", values=kol)[[SET_UTAMA, SET_PEMBANDING]]
        for kol in ("silhouette", "inersia", "ari_boot_median")
    }
    figs = {
        "segmen_pemilihan_k": viz.garis_panel(
            {
                "Silhouette (tinggi = terpisah)": piv["silhouette"],
                "Inersia K-Means (elbow)": piv["inersia"],
                "Stabilitas: median ARI bootstrap": piv["ari_boot_median"],
            },
            "Pemilihan jumlah segmen (k) untuk K-Means",
            "Jumlah segmen k",
            subjudul=(
                f"149 UMKM; pita abu-abu = k terpilih ({k}); garis putus-putus = batas stabil "
                f"ARI {rep.info['ari_min']:.1f}"
            ).replace(".", ","),
            garis_ref={"Stabilitas: median ARI bootstrap": rep.info["ari_min"]},
            sorot_x=k,
        )
    }

    p = rep.tabel["profil"]
    seg = p[p["segmen"] != "Semua"]
    d = rep.data
    u = d["sampel_utama"] == 1
    # (label, kolom profil untuk angka, kolom responden untuk warna, hanya sampel utama, pembagi,
    #  format angka)
    baris = [
        ("Omzet sebelum (median, Rp jt)", "omzet_sebelum_median", "skala_omzet_ord", 0, 1e6, ".1f"),
        (
            "Lama usaha sebelum MP (median, th)",
            "lama_usaha_pra_mp_median",
            "lama_usaha_pra_mp",
            0,
            1,
            ".1f",
        ),
        ("Lama di marketplace (median, th)", "lama_di_mp_median", "lama_di_mp", 0, 1, ".1f"),
        ("Jumlah platform (rata-rata)", "jumlah_platform_rata", "jumlah_platform", 0, 1, ".2f"),
        *[
            (f"Memakai {NAMA_PLATFORM[c]} (%)", f"persen_{c}", c, 0, 0.01, ".0f")
            for c in PLATFORM_COLS
        ],
        *[(NAMA_FITUR[c] + " (rata-rata)", f"{c}_rata", c, 0, 1, ".2f") for c in STRATEGI_COLS],
        ("Naik penjualan, sampel utama (%)", "persen_naik_utama", "naik_penjualan", 1, 0.01, ".0f"),
        ("y_obj, sampel utama (rata-rata)", "y_obj_rata_utama", "y_obj", 1, 1, ".2f"),
    ]
    nilai, anot = [], []
    for _, kol_p, kol_r, utama, pembagi, fmt in baris:
        v = d.loc[u, kol_r] if utama else d[kol_r]
        if kol_r in ("lama_usaha_pra_mp", "lama_di_mp"):
            v = np.log1p(v)  # sama dengan ruang fitur klaster
        g = d.loc[v.index, "segmen"]
        nilai.append(((v.groupby(g).mean() - v.mean()) / v.std(ddof=1)).to_numpy())
        anot.append([format(x / pembagi, fmt).replace(".", ",") for x in seg[kol_p].astype(float)])
    kolom = [f"Segmen {s}\n(n={n})" for s, n in zip(seg["segmen"], seg["n"])]
    idx = [b[0] for b in baris]
    figs["segmen_profil"] = viz.heatmap(
        pd.DataFrame(nilai, index=idx, columns=kolom),
        "Profil tiap segmen dibanding semua UMKM",
        "Segmen",
        "",
        subjudul="Angka = nilai segmen; warna = selisih rata-rata segmen dari semua UMKM dalam SD "
        "(biru lebih tinggi, merah lebih rendah)",
        anotasi=pd.DataFrame(anot, index=idx, columns=kolom),
        batas=1.0,
        garis_pemisah=(4, 4 + len(PLATFORM_COLS), 4 + len(PLATFORM_COLS) + len(STRATEGI_COLS)),
        label_skala="selisih (SD)",
    )

    var = rep.info["pca_var"]
    figs["segmen_peta_pca"] = viz.scatter_kelompok(
        rep.info["pca_xy"],
        rep.data["segmen"],
        {s: f"Segmen {s}: {rep.info['nama'][s]}" for s in sorted(rep.info["nama"])},
        "Sebaran UMKM pada dua komponen utama fitur profil",
        f"Komponen 1 ({var[0]:.0%} variasi)",
        f"Komponen 2 ({var[1]:.0%} variasi)",
        subjudul="Tiap titik = satu UMKM; tumpang-tindih menandakan batas segmen tidak tajam",
    )
    return figs


def run(cfg: dict[str, Any] | None = None) -> SegmenReport:
    """Baca data_features, jalankan Tahap 5, tulis data_segmen, tabel, grafik, log, ringkasan."""
    from umkm import config, io, viz
    from umkm.segmentasi_teks import build_log, build_ringkasan

    cfg = cfg or config.load_config()
    reports = config.path("reports")
    df = pd.read_csv(config.path("processed") / "data_features.csv")
    rep = analisis(df, cfg)
    io.write_csv(rep.data, config.path("processed") / "data_segmen.csv")
    io.write_csv(rep.tabel["profil"], reports / "tables" / "profil_segmen.csv")
    for nm, tab in rep.tabel.items():
        if nm != "profil":
            io.write_csv(tab, reports / "tables" / f"segmen_{nm}.csv")
    for nm, fig in buat_grafik(rep).items():
        rep.grafik[nm] = viz.simpan(fig, reports / "figures" / f"{nm}.png")
    io.write_text(build_log(rep, cfg), reports / "segmentasi_log.md")
    io.write_text(build_ringkasan(rep, cfg), reports / "segmentasi_ringkasan.md")
    return rep
