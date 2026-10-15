"""Dashboard lokal ringkasan proyek: `python -m umkm.dashboard [--port 8000]`.

Menyajikan satu halaman (static/dashboard.html) yang membaca `data.json`. JSON dibangun ulang dari
progress.md, decisions.md, reports/tables, dan data_features.csv pada setiap permintaan, sehingga
angka selalu mengikuti hasil pipeline terakhir. Grafik PNG diambil dari reports/figures.
Server hanya mendengarkan 127.0.0.1 (komputer sendiri) dan hanya melayani tiga jenis alamat.
Tidak ada data per responden yang dikirim ke halaman; hanya angka ringkasan.
"""

from __future__ import annotations

import argparse
import json
import math
import re
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
    "x3_komunikasi": "X3 Komunikasi",
    "x4_konsistensi": "X4 Konsistensi toko",
}
NAMA_FIGUR = re.compile(r"^[A-Za-z0-9_\-]+\.png$")


# ---------------------------------------------------------------------------
# Membaca berkas markdown .claude/
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


def keputusan_terbuka(teks: str) -> list[dict[str, str]]:
    """Keputusan berstatus DIUSULKAN atau BELUM DISEPAKATI dari decisions.md."""
    out = []
    for r in _baris_tabel(teks):
        if len(r) >= 4 and r[0].startswith("D") and r[3] in ("DIUSULKAN", "BELUM DISEPAKATI"):
            out.append({"id": r[0], "topik": r[1], "isi": r[2], "status": r[3]})
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
    return out


def daftar_figur() -> list[str]:
    """Nama berkas PNG di reports/figures (urut abjad)."""
    folder = config.path("reports") / "figures"
    return sorted(p.name for p in folder.glob("*.png")) if folder.exists() else []


def bangun_data() -> dict[str, Any]:
    """Seluruh isi data.json untuk halaman dashboard."""
    claude = config.project_dir() / ".claude"
    prog = claude / "progress.md"
    dec = claude / "decisions.md"
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
            "keputusan_terbuka": (
                keputusan_terbuka(dec.read_text(encoding="utf-8")) if dec.exists() else []
            ),
            "hasil": ringkasan_hasil(),
            "figur": daftar_figur(),
        }
    )


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

    def log_message(self, fmt: str, *args: Any) -> None:  # senyapkan log per permintaan
        return


def serve(port: int = 8000, host: str = "127.0.0.1", buka: bool = True) -> None:
    """Jalankan server dashboard sampai dihentikan dengan Ctrl+C."""
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
    args = parser.parse_args(argv)
    serve(args.port, buka=not args.no_browser)


if __name__ == "__main__":
    main()
