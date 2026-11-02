"""Dashboard lokal ringkasan proyek: `python -m umkm.dashboard [--port 8000]`.

Menyajikan satu halaman (static/dashboard.html) yang membaca `data.json`. JSON dibangun ulang dari
status tahap, reports/tables, dan data_features.csv pada setiap permintaan, sehingga angka selalu
mengikuti hasil pipeline terakhir. Grafik PNG diambil dari reports/figures.
Sebelum browser dibuka, pipeline dijalankan otomatis bila hasilnya belum ada (lihat `siapkan`).
Server hanya mendengarkan 127.0.0.1 (komputer sendiri) dan hanya melayani tiga jenis alamat.
Tidak ada data per responden yang dikirim ke halaman; hanya angka ringkasan.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pandas as pd

from umkm import config

STATIC = Path(__file__).parent / "static" / "dashboard.html"
STATUS_KODE = {
    "SELESAI": "done",
    "MENUNGGU PERSETUJUAN": "wait",
    "BERJALAN": "run",
    "BELUM": "todo",
}
STRATEGI = {
    "x1_unggah": "X1 Unggah produk",
    "x2_promosi": "X2 Promosi",
    "x3_komunikasi": "X3 Komunikasi pelanggan",
    "x4_konsistensi": "X4 Konsistensi toko",
}
PROFIL = {
    "lama_usaha_pra_mp": "Lama usaha sebelum MP",
    "lama_di_mp": "Lama di marketplace",
    "jumlah_platform": "Jumlah platform",
    "log_omzet_sebelum": "Omzet sebelum (log)",
}
NAMA_FIGUR = re.compile(r"^[A-Za-z0-9_\-]+\.png$")
# Keluaran pipeline yang wajib ada agar dashboard terisi (tabel dari reports/tables, model dari Tahap 6)
TABEL_WAJIB = (
    "eda_sebelum_sesudah",
    "pengaruh_gabungan",
    "sem_jalur",
    "profil_segmen",
    "rekomendasi_per_segmen",
)


# ---------------------------------------------------------------------------
# Status tahap
# ---------------------------------------------------------------------------
def _baris_tabel(teks: str) -> list[list[str]]:
    """Baris tabel markdown (tanpa header dan pemisah) sebagai daftar sel."""
    rows = []
    for line in teks.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= {"-", " "}:
            continue
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:] if rows else []


def tahap_dari_progress(teks: str) -> list[dict[str, Any]]:
    """Daftar tahap dari tabel progress.md: nomor, nama, status (kode), keluaran, tanggal selesai."""
    out = []
    for r in _baris_tabel(teks):
        if len(r) >= 5 and r[0].isdigit():
            out.append(
                {
                    "n": int(r[0]),
                    "nama": r[1],
                    "status": STATUS_KODE.get(r[2].upper(), "todo"),
                    "status_teks": r[2],
                    "keluaran": [k.strip() for k in r[3].split(",") if k.strip()],
                    "selesai": r[4],
                }
            )
    return out


# ---------------------------------------------------------------------------
# Angka ringkasan dari hasil pipeline
# ---------------------------------------------------------------------------
def _csv(nama: str) -> pd.DataFrame | None:
    path = config.path("reports") / "tables" / f"{nama}.csv"
    return pd.read_csv(path) if path.exists() else None


def _bersih(obj: Any) -> Any:
    """Ubah NaN/inf menjadi None agar JSON valid."""
    if isinstance(obj, dict):
        return {k: _bersih(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_bersih(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def ringkasan_hasil() -> dict[str, Any]:
    """Angka kunci, data grafik, dan catatan kualitas dari tabel Tahap 2-3 (None bila belum ada)."""
    out: dict[str, Any] = {}
    feat_path = config.path("processed") / "data_features.csv"
    if feat_path.exists():
        f = pd.read_csv(feat_path)
        utama = f[f["sampel_utama"] == 1]
        seragam = utama[utama["flag_jawaban_seragam"] == 1]
        out["angka"] = {
            "n_semua": len(f),
            "n_utama": len(utama),
            "n_tanpa_baseline": int(f["tanpa_baseline"].sum()),
            "n_naik": int(utama["naik_penjualan"].sum()),
            "n_seragam_utama": len(seragam),
            "n_seragam_naik": int(seragam["naik_penjualan"].sum()),
            "n_turun_tajam": int(f["flag_omzet_turun_tajam"].sum()),
            "n_trx_dikosongkan": int(f["flag_trx_dikosongkan"].sum()),
        }

    ss = _csv("eda_sebelum_sesudah")
    if ss is not None:
        u = ss[ss["sampel"] == "utama"].set_index("variabel")
        out["arah"] = [
            {
                "k": "Omzet" if v.startswith("omzet") else "Transaksi",
                "naik": int(r["n_naik"]),
                "sama": int(r["n_sama"]),
                "turun": int(r["n_turun"]),
                "kosong": out.get("angka", {}).get("n_utama", int(r["n_pasangan"]))
                - int(r["n_pasangan"]),
                "median_selisih": float(r["median_selisih"]),
                "p": float(r["p"]),
            }
            for v, r in u.iterrows()
        ]

    kor, mw = _csv("eda_spearman_kinerja"), _csv("eda_mw_naik_penjualan")
    if kor is not None and mw is not None:
        k = kor.query("sampel == 'utama' and y == 'y_obj'").set_index("x")
        m = mw.set_index(["varian", "variabel"])
        out["korelasi"] = sorted(
            [
                {
                    "k": STRATEGI[x],
                    "rho": float(k.loc[x, "rho"]),
                    "p_holm": float(k.loc[x, "p_holm"]),
                    "rb": float(m.loc[("utama", x), "r_rank_biserial"]),
                    "p_mw": float(m.loc[("utama", x), "p_holm"]),
                    "p_mw_tanpa_seragam": float(m.loc[("utama_tanpa_seragam", x), "p_holm"]),
                }
                for x in STRATEGI
            ],
            key=lambda d: -d["rho"],
        )

    dk = _csv("eda_distribusi_konstruk")
    if dk is not None:
        d = dk[dk["sampel"] == "semua_149"].set_index("konstruk")
        out["skor"] = sorted(
            [{"k": STRATEGI[x], "v": float(d.loc[x, "rata_rata"])} for x in STRATEGI],
            key=lambda r: -r["v"],
        )
        out["pct_persepsi_tepat_3"] = float(d.loc["y_persepsi", "pct_tepat_3"])

    plat = _csv("eda_profil_platform")
    if plat is not None:
        out["platform"] = [
            {"k": r["platform"], "n": int(r["n_semua_149"]), "pct": float(r["pct_semua_149"])}
            for _, r in plat.iterrows()
        ]
    combo = _csv("eda_profil_kombinasi_platform")
    if combo is not None:
        out["kombinasi_teratas"] = {"k": combo.iloc[0]["kombinasi"], "n": int(combo.iloc[0]["n"])}

    sb, vif = _csv("eda_sebaran_butir"), _csv("eda_vif")
    if sb is not None:
        out["butir_netral"] = {"n": int(sb["dominasi_netral"].sum()), "total": len(sb)}
    if vif is not None:
        out["vif_maks"] = float(vif["vif"].max())

    rel = _csv("reliabilitas")
    if rel is not None:
        r = rel[rel["peran"] == "strategi"]
        out["alpha"] = {"min": float(r["alpha"].min()), "max": float(r["alpha"].max())}

    cv = _csv("pengaruh_cv_ringkas")
    if cv is not None:
        cv_naik = cv[cv["target"] == "naik_penjualan"].set_index(["model", "metrik"])
        models_list = [
            ("random_forest", "Random Forest"),
            ("logistik", "Regresi Logistik"),
            ("dummy_mayoritas", "Baseline Mayoritas"),
        ]
        out["model_performa"] = []
        for m_key, m_nama in models_list:
            if (m_key, "auc") in cv_naik.index:
                out["model_performa"].append(
                    {
                        "model": m_nama,
                        "auc": float(cv_naik.loc[(m_key, "auc"), "rata_rata"]),
                        "auc_sd": float(cv_naik.loc[(m_key, "auc"), "sd"]),
                        "f1": float(cv_naik.loc[(m_key, "f1_macro"), "rata_rata"]),
                        "akurasi": float(cv_naik.loc[(m_key, "akurasi_seimbang"), "rata_rata"]),
                    }
                )

    perm = _csv("pengaruh_permutation")
    if perm is not None:
        g = perm.groupby("variabel")["importance"].agg(["mean", "std", "count"])
        out["rf_importance"] = sorted(
            [
                {
                    "var": v,
                    "nama": STRATEGI.get(v) or PROFIL.get(v, v),
                    "jenis": "strategi" if v in STRATEGI else "profil",
                    "mean": float(r["mean"]),
                    "sd": float(r["std"]),
                    "n_lipatan": int(r["count"]),
                }
                for v, r in g.iterrows()
            ],
            key=lambda d: -d["mean"],
        )

    conf = _csv("pengaruh_confusion")
    if conf is not None and (conf["model"] == "random_forest").any():
        c = conf.set_index("model").loc["random_forest"]
        out["rf_confusion"] = {k: int(c[k]) for k in ("tn", "fp", "fn", "tp")}

    seg = _csv("profil_segmen")
    if seg is not None:
        out["segmen"] = [
            {
                "segmen": str(r["segmen"]),
                "nama": str(r["nama_segmen"]),
                "n": int(r["n"]),
                "omzet_median": float(r["omzet_sebelum_median"]),
                "lama_usaha_median": float(r["lama_usaha_pra_mp_median"]),
                "lama_mp_median": float(r["lama_di_mp_median"]),
                "jumlah_platform_rata": float(r["jumlah_platform_rata"]),
                "n_utama": int(r["n_sampel_utama"]),
                "n_naik_utama": int(r["n_naik_utama"]),
            }
            for _, r in seg.iterrows()
        ]

    gap = _csv("rekomendasi_gap")
    if gap is not None:
        out["gap"] = [
            {
                "segmen": str(r["segmen"]),
                "strategi": STRATEGI.get(r["strategi"], r["strategi"]),
                "skor": float(r["skor"]),
                "benchmark": float(r["benchmark"]),
                "gap": float(r["gap"]),
            }
            for _, r in gap.iterrows()
        ]

    gab = _csv("pengaruh_gabungan")
    if gab is not None:
        out["rf_pengaruh"] = [
            {
                "strategi": r["strategi"],
                "nama": STRATEGI.get(r["strategi"], r["nama"]),
                "perm_importance": float(r["perm_importance"]),
                "p_logit": float(r["p_logit"]),
                "shap": float(r["mean_abs_shap"]),
                "pengaruh": float(r["pengaruh"]),
                "bobot": float(r["bobot_rekomendasi"]),
                "peringkat": int(r["peringkat"]),
                "p_p1": float(r["p_peringkat_1"]),
                "or_logit": float(r["or_logit"]),
                "meyakinkan": bool(r["meyakinkan"]),
            }
            for _, r in gab.iterrows()
        ]

    wif = _csv("rekomendasi_whatif")
    if wif is not None:
        out["simulasi_whatif"] = [
            {
                "segmen": str(r["segmen"]),
                "model": str(r["model"]),
                "strategi": STRATEGI.get(r["strategi"], r["strategi"]),
                "selisih_pp": float(r["selisih_pp"]),
                "peluang_dasar": float(r["peluang_dasar_persen"]),
            }
            for _, r in wif.iterrows()
        ]

    sem = ringkasan_sem()
    if sem:
        out["sem"] = sem

    rek = _csv("rekomendasi_per_segmen")
    if rek is not None:
        out["rekomendasi_segmen"] = [
            {
                "segmen": str(r["segmen"]),
                "nama_segmen": str(r["nama_segmen"]),
                "peringkat": int(r["peringkat"]),
                "strategi": STRATEGI.get(r["strategi"], r["nama_strategi"]),
                "prioritas": float(r["prioritas"]),
                "gap": float(r["gap"]),
                "bobot": float(r["bobot"]),
                "tindakan": str(r["tindakan"]),
                "alasan": str(r["alasan"]),
            }
            for _, r in rek.iterrows()
        ]
    return out


def ringkasan_sem() -> dict[str, Any] | None:
    """Hasil analisis pembanding PLS-SEM (tabel sem_*.csv); None bila belum dijalankan."""
    mdl, jal, rel, ht, bnd = (
        _csv(f"sem_{n}") for n in ("model", "jalur", "reliabilitas", "htmt", "perbandingan")
    )
    if any(t is None for t in (mdl, jal, rel, ht, bnd)):
        return None
    jal = jal[jal["jenis"] == "strategi"]
    return {
        "model": [
            {
                "model": r["model"],
                "nama": r["nama"],
                "n": int(r["n"]),
                "r2": float(r["r2"]),
                "auc": float(r["auc"]) if pd.notna(r["auc"]) else None,
                "q2": float(r["q2_predict"]) if pd.notna(r["q2_predict"]) else None,
            }
            for _, r in mdl.iterrows()
        ],
        "jalur": [
            {
                "model": r["model"],
                "strategi": STRATEGI[r["prediktor"]],
                "koef": float(r["koef"]),
                "ci_bawah": float(r["ci_bawah"]),
                "ci_atas": float(r["ci_atas"]),
                "p_holm": float(r["p_holm"]),
                "f2": float(r["f2"]),
            }
            for _, r in jal.iterrows()
        ],
        "pengukuran": {
            "alpha": [float(rel["alpha"].min()), float(rel["alpha"].max())],
            "rho_c": [float(rel["rho_c"].min()), float(rel["rho_c"].max())],
            "ave": [float(rel["ave"].min()), float(rel["ave"].max())],
            "htmt_maks": float(ht["htmt"].max()),
            "htmt_ci_maks": float(ht["htmt_ci_atas"].max()),
        },
        "peringkat_sama": bool((bnd["peringkat_pls_naik"] == bnd["peringkat_tahap4"]).all()),
        "n_boot": int(config.load_config()["sem"]["n_bootstrap"]),
    }


def info_model() -> dict[str, Any] | None:
    """Ringkasan model tersimpan (models/<versi>): data latih, fitur, skema CV, parameter. None bila belum ada."""
    from umkm import recommend as rk

    try:
        art = rk.muat_artefak(str(rk.dir_model_default()))
    except FileNotFoundError:
        return None
    meta, m = art["meta"], art["model"]
    par = m["model"].get_params()
    return {
        "versi": meta["versi_model"],
        "dibuat": meta["dibuat"],
        "nama": m["nama"],
        "target": meta["target_model"],
        "n_latih": meta["n_latih_model"],
        "n_naik_latih": meta["n_naik_latih"],
        "fitur": meta["fitur_model"],
        "skema_cv": meta["skema_cv"],
        "seed": meta["seed"],
        "k_segmen": meta["k_segmen"],
        "param": {k: par.get(k) for k in ("n_estimators", "max_depth", "min_samples_leaf")},
    }


def ringkasan_aktivitas() -> dict[str, Any]:
    """Angka pendukung rangkuman tahap 1-7: segmentasi, reliabilitas, jumlah keluaran."""
    out: dict[str, Any] = {}
    k = _csv("segmen_pemilihan_k")
    if k is not None:
        r = k[k["set_fitur"] == "profil"].sort_values("ari_boot_median").iloc[-1]
        out["segmentasi"] = {
            "k": int(r["k"]),
            "silhouette": float(r["silhouette"]),
            "ari_median": float(r["ari_boot_median"]),
            "ukuran": str(r["ukuran"]),
        }
    stab = _csv("segmen_stabilitas")
    if stab is not None:
        out.setdefault("segmentasi", {})["jaccard_min"] = float(stab["jaccard_rata"].min())
    rel = _csv("reliabilitas")
    if rel is not None:
        out["n_butir_strategi"] = int(rel.loc[rel["peran"] == "strategi", "n_butir"].sum())
    rep = config.path("reports")
    out["n_tabel"] = len(list((rep / "tables").glob("*.csv")))
    out["n_figur"] = len(list((rep / "figures").glob("*.png")))
    return out


def daftar_figur() -> list[str]:
    """Nama berkas PNG di reports/figures (urut abjad)."""
    folder = config.path("reports") / "figures"
    return sorted(p.name for p in folder.glob("*.png")) if folder.exists() else []


def bangun_data() -> dict[str, Any]:
    """Seluruh isi data.json untuk halaman dashboard."""
    prog = config.project_dir() / ".claude" / "progress.md"
    hasil = [config.path("processed") / "data_features.csv"]
    hasil += list((config.path("reports") / "tables").glob("*.csv"))
    waktu = [p.stat().st_mtime for p in hasil if p.exists()]
    return _bersih(
        {
            "diperbarui": pd.Timestamp.now().strftime("%d-%m-%Y %H:%M"),
            "data_dari": (
                pd.Timestamp.fromtimestamp(max(waktu)).strftime("%d-%m-%Y %H:%M") if waktu else None
            ),
            "tahap": tahap_dari_progress(prog.read_text(encoding="utf-8")) if prog.exists() else [],
            "hasil": ringkasan_hasil(),
            "aktivitas": ringkasan_aktivitas(),
            "model": info_model(),
            "figur": daftar_figur(),
        }
    )


def simulasi(profil: dict[str, Any]) -> dict[str, Any]:
    """Keluaran `recommend()` ditambah `ilustrasi_model`: peluang prediksi Random Forest untuk
    profil ini dan selisihnya bila tiap strategi +1 poin. Kontrak `recommend()` tidak diubah;
    angka ini ilustrasi model (asosiasi), bukan jaminan hasil."""
    from umkm import recommend as rk

    hasil = rk.recommend(profil)
    p = rk.ProfilUMKM.model_validate(profil)
    art = rk.muat_artefak(str(rk.dir_model_default()))
    m = art["model"]
    x = rk.baris_profil(p, art["benchmark"]["batas_skala_omzet"])[m["fitur"]]
    delta = rk.selisih_prediksi(m["model"], x, rk.STRATEGI, art["meta"]["whatif_tambah"])
    hasil["ilustrasi_model"] = {
        "model": m["nama"],
        "peluang_naik_persen": round(float(m["model"].predict_proba(x)[0, 1] * 100), 1),
        "selisih_plus1_pp": {s: round(float(delta[s]), 1) for s in rk.STRATEGI},
    }
    return hasil


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
def figur_aman(nama: str) -> Path | None:
    """Path PNG di reports/figures bila nama valid dan berkasnya ada; selain itu None."""
    if not NAMA_FIGUR.match(nama):
        return None
    path = config.path("reports") / "figures" / nama
    return path if path.is_file() else None


class _Handler(BaseHTTPRequestHandler):
    def _kirim(self, kode: int, isi: bytes, jenis: str) -> None:
        self.send_response(kode)
        self.send_header("Content-Type", jenis)
        self.send_header("Content-Length", str(len(isi)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(isi)

    def do_GET(self) -> None:
        jalur = self.path.split("?", 1)[0]
        if jalur in ("/", "/index.html"):
            self._kirim(200, STATIC.read_bytes(), "text/html; charset=utf-8")
        elif jalur == "/data.json":
            isi = json.dumps(bangun_data(), ensure_ascii=False).encode("utf-8")
            self._kirim(200, isi, "application/json; charset=utf-8")
        elif jalur.startswith("/figures/") and (p := figur_aman(jalur[len("/figures/") :])):
            self._kirim(200, p.read_bytes(), "image/png")
        else:
            self._kirim(404, b"Tidak ditemukan", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        jalur = self.path.split("?", 1)[0]
        if jalur == "/api/recommend":
            try:
                panjang = int(self.headers.get("Content-Length", 0))
                badan = self.rfile.read(panjang)
                masukan = json.loads(badan.decode("utf-8"))
                hasil = simulasi(masukan)
                self._kirim(
                    200,
                    json.dumps(hasil, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception as e:  # noqa: BLE001
                pesan_err = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
                self._kirim(400, pesan_err, "application/json; charset=utf-8")
        else:
            self._kirim(404, b"Tidak ditemukan", "text/plain; charset=utf-8")

    def log_message(self, fmt: str, *args: Any) -> None:  # senyapkan log per permintaan
        return


def keluaran_hilang() -> list[str]:
    """Keluaran pipeline wajib yang belum ada (kosong = dashboard bisa langsung terisi)."""
    from umkm import recommend as rk

    wajib = [
        config.path("processed") / "data_features.csv",
        rk.dir_model_default() / "model_meta.json",
    ]
    wajib += [config.path("reports") / "tables" / f"{t}.csv" for t in TABEL_WAJIB]
    return [str(p.relative_to(config.base_dir())) for p in wajib if not p.exists()]


def siapkan(jalankan_pipeline: bool = True) -> None:
    """Pastikan hasil analisis tersedia sebelum halaman dibuka: jalankan pipeline Tahap 1-7 bila
    keluaran wajib belum ada, lalu bangun data.json sekali agar impor berat (sklearn, model) sudah
    selesai saat browser meminta data pertama kali."""
    hilang = keluaran_hilang()
    if hilang and jalankan_pipeline:
        if config.path("raw").exists():
            from umkm import pipeline

            print(
                f"Hasil analisis belum lengkap ({', '.join(hilang)}); menjalankan pipeline Tahap 1-7..."
            )
            pipeline.main(["--all"])
        else:
            print(
                f"Peringatan: hasil analisis belum ada dan data mentah tidak ditemukan di {config.path('raw')}."
            )
    elif hilang:
        print(
            f"Peringatan: hasil analisis belum lengkap ({', '.join(hilang)}); dashboard bisa kosong sebagian."
        )
    print("Menyiapkan data dashboard...")
    bangun_data()


def ekspor(folder: Path, pipeline: bool = True) -> Path:
    """Tulis dashboard sebagai situs statis (tanpa server Python) untuk dipublikasikan:
    index.html, data.json (angka ringkasan, ditandai `statis`), figures/*.png, dan .nojekyll
    (GitHub Pages). Hanya berkas-berkas itu yang ditimpa; PNG lama di figures/ dibersihkan."""
    siapkan(pipeline)
    folder = Path(folder)
    fig = folder / "figures"
    fig.mkdir(parents=True, exist_ok=True)
    for lama in fig.glob("*.png"):
        lama.unlink()
    data = bangun_data() | {"statis": True}
    for nama in data["figur"]:
        shutil.copyfile(config.path("reports") / "figures" / nama, fig / nama)
    (folder / "index.html").write_bytes(STATIC.read_bytes())
    (folder / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (folder / ".nojekyll").touch()
    return folder


def serve(
    port: int = 8000, host: str = "127.0.0.1", buka: bool = True, pipeline: bool = True
) -> None:
    """Siapkan data lalu jalankan server dashboard sampai dihentikan dengan Ctrl+C."""
    siapkan(pipeline)
    server = ThreadingHTTPServer((host, port), _Handler)
    url = f"http://localhost:{port}" if host == "127.0.0.1" else f"http://{host}:{port}"
    print(f"Dashboard berjalan di {url}  (Ctrl+C untuk berhenti)")
    if buka:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard dihentikan.")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Dashboard lokal ringkasan proyek UMKM.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="jangan buka browser otomatis")
    parser.add_argument(
        "--no-pipeline",
        action="store_true",
        help="jangan jalankan pipeline otomatis bila hasil belum ada",
    )
    parser.add_argument(
        "--export",
        metavar="FOLDER",
        help="tulis situs statis ke FOLDER (untuk hosting publik) lalu keluar, tanpa menjalankan server",
    )
    args = parser.parse_args(argv)
    if args.export:
        out = ekspor(Path(args.export), pipeline=not args.no_pipeline)
        print(f"Situs statis ditulis ke {out.resolve()}")
        return
    serve(args.port, buka=not args.no_browser, pipeline=not args.no_pipeline)


if __name__ == "__main__":
    main()
