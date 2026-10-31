"""Teks Tahap 6: interpretasi grafik, reports/rekomendasi_log.md, rekomendasi_ringkas.md, dan
reports/integration_contract.md.

Semua kalimat disusun dari angka di tabel agar tetap benar bila data berubah. Bahasa asosiasi:
rekomendasi adalah prioritas berbasis pola, bukan jaminan hasil.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from umkm import recommend as rc
from umkm.eda_teks import _a, _daftar, _pct
from umkm.features import _md
from umkm.rekomendasi import KODE, SEMUA, STRATEGI, VARIAN, RekomendasiReport
from umkm.schemas import HasilRekomendasi, ProfilUMKM


def _seg(rep: RekomendasiReport) -> list[int]:
    return sorted(rep.info["nama"])


def _gap_seg(rep: RekomendasiReport) -> pd.DataFrame:
    """Gap + bootstrap untuk segmen saja (tanpa Semua)."""
    g = rep.tabel["gap"].merge(rep.tabel["bootstrap"], on=["segmen", "strategi"])
    return g[g["segmen"] != SEMUA]


def _urutan(rep: RekomendasiReport, varian: str = "utama") -> dict[Any, str]:
    s = rep.tabel["sensitivitas"]
    return s[s["varian"] == varian].set_index("segmen")["urutan"].to_dict()


def _nama_s(s: str) -> str:
    return rc.NAMA_STRATEGI[s]


def _wf(rep: RekomendasiReport, key: Any, s: str, model: str | None = None) -> float:
    w = rep.tabel["whatif"]
    m = model or rep.info["model_terbaik"]
    return float(
        w[(w["segmen"] == key) & (w["strategi"] == s) & (w["model"] == m)]["selisih_pp"].iloc[0]
    )


def _pp(x: float) -> str:
    return f"{'+' if x >= 0 else ''}{_a(x, 1)} poin persen"


# ---------------------------------------------------------------------------
# Ringkasan angka
# ---------------------------------------------------------------------------
def fakta(rep: RekomendasiReport) -> dict[str, Any]:
    """Angka kunci yang dipakai berulang di log dan ringkasan."""
    g = _gap_seg(rep)
    sens = rep.tabel["sensitivitas"]
    seg_sens = sens[sens["segmen"] != SEMUA]
    urut = _urutan(rep)
    teratas = seg_sens["urutan"].str.split(" > ").str[0]
    return {
        "urutan_sama": len(set(urut.values())) == 1,
        "urutan_umum": urut[SEMUA],
        "gap_min": g["gap_mentah"].min(),
        "gap_maks": g["gap_mentah"].max(),
        "n_gap": len(g),
        "n_ci_nol": int((g["gap_ci_bawah"] <= 0).sum()),
        "ci_positif": [
            f"{KODE[r['strategi']]} di segmen {r['segmen']}"
            for _, r in g[g["gap_ci_bawah"] > 0].iterrows()
        ],
        "p_gap_min": g["p_gap_positif"].min(),
        "p_gap_maks": g["p_gap_positif"].max(),
        "n_varian": seg_sens["varian"].nunique(),
        "n_sama": int(seg_sens.groupby("varian")["sama_dengan_utama"].all().sum()),
        "varian_beda": [
            VARIAN[v]
            for v, ok in seg_sens.groupby("varian", sort=False)["sama_dengan_utama"].all().items()
            if not ok
        ],
        "teratas_x3": int((teratas == KODE["x3_komunikasi"]).sum()),
        "n_baris_sens": len(seg_sens),
        "butir_gap_min": rep.tabel["butir"].query("segmen != @SEMUA")["gap"].min(),
        "butir_gap_maks": rep.tabel["butir"].query("segmen != @SEMUA")["gap"].max(),
    }


def interpretasi(rep: RekomendasiReport) -> dict[str, str]:
    """Satu kalimat interpretasi untuk tiap grafik."""
    f = fakta(rep)
    g = rep.tabel["gap"]
    top = g[(g["peringkat"] == 1) & (g["segmen"] != SEMUA)]
    bob = rep.tabel["bobot"].set_index("strategi")["bobot"]
    s1 = top["strategi"].iloc[0]
    return {
        "rekomendasi_prioritas": (
            (
                f"Urutan prioritas sama di semua segmen dan seluruh UMKM ({f['urutan_umum']}). "
                if f["urutan_sama"]
                else "Urutan prioritas berbeda antar-segmen. "
            )
            + f"{_nama_s(s1)} mendapat skor prioritas tertinggi ("
            + _daftar([_a(v, 3) for v in top["prioritas"]])
            + f") terutama karena bobotnya paling besar ({_a(bob[s1])}); gap keempat strategi "
            f"hampir sama ({_a(f['gap_min'])}-{_a(f['gap_maks'])} poin)."
        ),
        "rekomendasi_gap": (
            f"Semua gap positif (skor segmen sedikit di bawah UMKM yang penjualannya naik), tetapi "
            f"kecil ({_a(f['gap_min'])}-{_a(f['gap_maks'])} poin pada skala 1-5); interval "
            f"bootstrap {f['n_ci_nol']} dari {f['n_gap']} gap mencakup nol"
            + (
                f", hanya {_daftar(f['ci_positif'])} yang seluruhnya di atas nol."
                if f["ci_positif"]
                else "."
            )
        ),
    }


def keterbatasan(rep: RekomendasiReport) -> list[str]:
    """Daftar keterbatasan Tahap 6 (dari angka)."""
    f = fakta(rep)
    auc = rep.info["auc"]
    naik = rep.tabel["gap"].drop_duplicates("segmen").set_index("segmen")["n_naik"]
    out = [
        (
            f"Gap kecil ({_a(f['gap_min'])}-{_a(f['gap_maks'])} poin pada skala 1-5) dan interval "
            f"bootstrap {f['n_ci_nol']} dari {f['n_gap']} gap segmen mencakup nol. Arahnya konsisten "
            f"(peluang gap > 0: {_pct(f['p_gap_min'])}-{_pct(f['p_gap_maks'])}), tetapi beda skor "
            "UMKM yang naik dan rata-rata segmen tidak besar."
        ),
        (
            "Karena gap keempat strategi hampir sama, urutan prioritas terutama ditentukan oleh bobot "
            f"Tahap 4. Urutan utama bertahan di {f['n_sama']} dari {f['n_varian']} varian "
            "sensitivitas; berubah pada " + _daftar(f["varian_beda"]) + ". X3 tetap teratas di "
            f"{f['teratas_x3']} dari {f['n_baris_sens']} kombinasi varian x segmen."
        ),
        (
            "Benchmark = UMKM yang melaporkan kenaikan penjualan. Di sampel utama pembandingnya adalah "
            "UMKM yang menulis angka omzet dan transaksi sama persis (D26), bukan UMKM yang turun."
        ),
        (
            "Kedua segmen tidak berbeda bermakna pada skor strategi maupun kinerja (Tahap 5), sehingga "
            "perbedaan rekomendasi antar-segmen hanya pada penyesuaian tindakan. Teks penyesuaian "
            "adalah templat yang disusun dari kondisi usaha segmen, bukan hasil uji data."
        ),
        (
            f"Butir fokus dipilih dari selisih butir yang kecil dan mirip ({_a(f['butir_gap_min'])}-"
            f"{_a(f['butir_gap_maks'])} poin); urutan butir hanya panduan, bukan temuan yang kuat."
        ),
        (
            f"Simulasi +1 poin memakai model {rep.info['model_terbaik']} (AUC CV "
            f"{_a(auc[rep.info['model_terbaik']])}) yang dilatih pada seluruh sampel utama; ini "
            "menggambarkan pola yang dipelajari model, bukan perkiraan dampak bila UMKM mengubah "
            "strateginya."
        ),
        (
            "Benchmark segmen bertumpu pada "
            + _daftar([f"{int(naik[s])} UMKM naik di segmen {s}" for s in _seg(rep)])
            + f"; seluruh data adalah survei satu waktu dari {rep.info['n']} UMKM (isian sendiri)."
        ),
        (
            "Untuk UMKM baru, segmen ditentukan dari profil usaha; struktur segmen lemah (silhouette "
            "Tahap 5 sekitar 0,25), sehingga UMKM di dekat batas bisa masuk segmen mana pun. Omzet "
            "masukan dibandingkan dengan kuartil omzet sebelum marketplace di data latih."
        ),
    ]
    return out


# ---------------------------------------------------------------------------
# Log teknis
# ---------------------------------------------------------------------------
def _tabel_gap_md(rep: RekomendasiReport) -> pd.DataFrame:
    g = rep.tabel["gap"].merge(rep.tabel["bootstrap"], on=["segmen", "strategi"])
    g = g.assign(strategi=g["strategi"].map(KODE))
    return g[
        [
            "segmen",
            "strategi",
            "skor",
            "benchmark",
            "gap",
            "gap_ci_bawah",
            "gap_ci_atas",
            "p_gap_positif",
            "bobot",
            "prioritas",
            "peringkat",
            "p_peringkat_1",
            "p_tiga_besar",
        ]
    ]


def _gambar(nama: str, interp: dict[str, str]) -> str:
    return f"![{nama}](figures/{nama}.png)\n\n**Interpretasi:** {interp[nama]}\n"


def _json(obj: Any) -> str:
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```\n"


def build_log(rep: RekomendasiReport, cfg: dict[str, Any]) -> str:
    """Susun reports/rekomendasi_log.md (pengaturan, tabel, grafik, pengecekan)."""
    r = cfg["recommendation"]
    interp = interpretasi(rep)
    t = rep.tabel
    s = ["# Log Tahap 6: Rekomendasi Strategi\n"]
    s.append(
        f"Dibuat oleh `umkm.rekomendasi` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. "
        f"{rep.info['n']} UMKM ({rep.info['n_utama']} sampel utama, {rep.info['n_naik']} naik), "
        f"seed {cfg['seed']}.\n"
    )
    s.append("## Pengaturan (D28)\n")
    s += [
        (
            "- Benchmark_s(segmen) = rata-rata skor strategi s pada UMKM `naik_penjualan` = 1 di sampel "
            f"utama segmen itu (D14); bila kurang dari {r['min_naik_benchmark']} UMKM, benchmark seluruh "
            "UMKM yang naik."
        ),
        (
            "- Skor_s(segmen) = rata-rata skor seluruh anggota segmen (149 UMKM, termasuk tanpa baseline; "
            "D27). gap = max(0, benchmark - skor); prioritas = bobot x gap; ambil "
            f"{r['n_prioritas']} teratas dengan prioritas > 0."
        ),
        (
            "- Rata-rata vs rata-rata (pilihan pengguna, 2026-10-30): rumus plan awal (median UMKM naik "
            "vs rata-rata segmen) mencampur dua ukuran dan, karena skor Likert menumpuk di angka bulat, "
            "hanya memberi 2 strategi berprioritas > 0 per segmen. Dihitung sebagai sensitivitas."
        ),
        (
            "- Bobot dari Tahap 4 (D26), sama untuk semua segmen. Penyajian: satu urutan umum + "
            "penyesuaian tindakan per segmen (pilihan pengguna, 2026-10-30)."
        ),
        (
            f"- Butir fokus: {r['n_butir_fokus']} butir kuesioner dengan gap terbesar per strategi; "
            "penyesuaian tindakan dipilih dari kondisi usaha segmen (pusat skala omzet di bawah rata-rata "
            "= 'kecil', selain itu 'besar')."
        ),
        (
            f"- Bootstrap {rep.info['n_boot']}x (baris di dalam tiap kelompok, bobot tetap). Simulasi: skor "
            f"satu strategi +{_a(r['whatif_tambah'], 0)} poin (maks 5) pada model terbaik Tahap 4 "
            f"({rep.info['model_terbaik']}, AUC CV tertinggi) yang dilatih pada sampel utama; logistik "
            "sebagai pembanding."
        ),
        "",
    ]
    s.append("## Bobot strategi (Tahap 4)\n")
    s.append(_md(t["bobot"], "{:.3f}"))
    s.append("\n## Skor, benchmark, gap, prioritas\n")
    s.append(_md(_tabel_gap_md(rep), "{:.3f}"))
    s.append(
        "\n`gap` sudah dipotong di 0; `gap_ci_*` = interval bootstrap 95% dari selisih mentah. "
        "`p_tiga_besar` = peluang bootstrap strategi masuk tiga prioritas teratas.\n"
    )
    s.append(_gambar("rekomendasi_prioritas", interp))
    s.append(_gambar("rekomendasi_gap", interp))
    s.append("## Butir fokus per segmen\n")
    b = t["butir"][t["butir"]["fokus"]].copy()
    s.append(
        _md(b[["segmen", "strategi", "butir", "tindakan", "skor", "benchmark", "gap"]], "{:.2f}")
    )
    s.append("\nTabel semua butir: `tables/rekomendasi_butir.csv`.\n")
    s.append("## Sensitivitas urutan prioritas\n")
    s.append(_md(t["sensitivitas"].drop(columns="varian"), "{:.3f}"))
    s.append("\n## Simulasi +1 poin (ilustrasi model)\n")
    w = t["whatif"].assign(strategi=t["whatif"]["strategi"].map(KODE))
    s.append(_md(w, "{:.2f}"))
    s.append(
        "\n`selisih_pp` = rata-rata selisih peluang prediksi naik_penjualan (poin persen) bila satu "
        "skor strategi dinaikkan, profil dan strategi lain tetap. Dilatih dan dievaluasi pada data "
        "yang sama (in-sample); bukan perkiraan dampak.\n"
    )
    s.append("## Tabel rekomendasi\n")
    p = t["per_segmen"]
    s.append(
        _md(
            p[
                ["segmen", "peringkat", "nama_strategi", "skor_segmen", "benchmark", "gap", "bobot"]
                + ["prioritas", "p_tiga_besar", "selisih_prediksi_plus1_pp", "fokus_butir"]
            ],
            "{:.3f}",
        )
    )
    s.append("\nAlasan dan tindakan lengkap: `tables/rekomendasi_per_segmen.csv`.\n")
    s.append("## Artefak inferensi\n")
    s += [
        f"- `{p_.relative_to(p_.parents[2]).as_posix()}`"
        for p_ in rep.info["path_artefak"].values()
    ]
    s.append("")
    s.append("## Pengecekan: recommend() vs tabel\n")
    s.append(_md(t["konsistensi"], "{:.6f}"))
    s.append(
        "\nProfil wakil = median profil segmen + rata-rata skor strategi segmen, dijalankan lewat "
        "`recommend()` yang hanya memuat artefak `models/` (tanpa data survei).\n"
    )
    s.append("## Tiga contoh masukan\n")
    for c in rep.contoh:
        h = c["keluaran"]
        urut = " > ".join(KODE[q["strategi"]] for q in h["prioritas"]) or "tidak ada prioritas"
        s.append(f"- `{c['masukan']['id_umkm']}`: segmen {h['segmen']['id']}, prioritas {urut}.")
    s.append("\nMasukan dan keluaran lengkap: `integration_contract.md`.\n")
    s.append("## Keterbatasan\n")
    s += [f"- {x}" for x in keterbatasan(rep)]
    s.append("")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Ringkasan awam
# ---------------------------------------------------------------------------
def _blok_segmen(rep: RekomendasiReport, key: int) -> list[str]:
    p = rep.tabel["per_segmen"]
    g = rep.tabel["gap"]
    sub = p[p["segmen"] == key].sort_values("peringkat")
    n = int(g.loc[g["segmen"] == key, "n"].iloc[0])
    n_naik = int(g.loc[g["segmen"] == key, "n_naik"].iloc[0])
    s = [
        f"### Segmen {key}: {rep.info['nama'][key]}\n",
        f"{n} UMKM; benchmark dari {n_naik} UMKM di segmen ini yang melaporkan kenaikan penjualan.\n",
    ]
    for _, r in sub.iterrows():
        s.append(
            f"{int(r['peringkat'])}. **{r['nama_strategi']}** (prioritas {_a(r['prioritas'], 3)}; "
            f"masuk tiga besar di {_pct(r['p_tiga_besar'])} ulangan bootstrap). {r['alasan']}\n"
            f"   - *Tindakan:* {r['tindakan']}"
        )
    s.append("")
    return s


def build_ringkasan(rep: RekomendasiReport, cfg: dict[str, Any]) -> str:
    """Susun reports/rekomendasi_ringkas.md (bahasa sederhana)."""
    f = fakta(rep)
    interp = interpretasi(rep)
    g = rep.tabel["gap"]
    bob = rep.tabel["bobot"].set_index("strategi")
    m = rep.info["model_terbaik"]
    s = ["# Ringkasan Tahap 6: Rekomendasi Strategi per Segmen\n"]
    s.append(
        f"Dibuat oleh `umkm.rekomendasi` pada {pd.Timestamp.now():%Y-%m-%d %H:%M}. Untuk tiap "
        "segmen, skor rata-rata tiap strategi dibandingkan dengan rata-rata UMKM di segmen yang sama "
        "yang melaporkan kenaikan penjualan. Selisihnya (gap) dikalikan bobot hubungan strategi "
        "dengan kenaikan penjualan dari Tahap 4. Hasilnya adalah prioritas berbasis pola asosiasi, "
        "bukan jaminan hasil.\n"
    )
    s.append("## Prioritas umum\n")
    if f["urutan_sama"]:
        s.append(
            f"Urutan prioritas **sama di kedua segmen dan seluruh UMKM: {f['urutan_umum']}**. Ini "
            "sejalan dengan Tahap 5: segmen membedakan kondisi usaha, bukan tingkat strategi atau "
            "kinerja, dan bobot strategi sama untuk semua segmen. Perbedaan antar-segmen ada pada "
            "butir yang paling tertinggal dan penyesuaian tindakan.\n"
        )
    else:
        s.append(
            "Urutan prioritas berbeda antar-segmen: "
            + _daftar([f"segmen {k}: {v}" for k, v in _urutan(rep).items() if k != SEMUA])
            + ".\n"
        )
    kol = [*_seg(rep), SEMUA]
    s.append(
        "| Strategi | Bobot | "
        + " | ".join(f"Segmen {k}" if k != SEMUA else "Semua UMKM" for k in kol)
        + " |"
    )
    s.append("|---|---|" + "---|" * len(kol))
    for st_ in STRATEGI:
        sel = []
        for k in kol:
            r = g[(g["segmen"] == k) & (g["strategi"] == st_)].iloc[0]
            urut = f"#{int(r['peringkat'])} " if r["peringkat"] > 0 else ""
            sel.append(f"{urut}{_a(r['prioritas'], 3)} (gap {_a(r['gap'])})")
        s.append(f"| {_nama_s(st_)} | {_a(bob.at[st_, 'bobot'])} | " + " | ".join(sel) + " |")
    s.append(
        "\nAngka = skor prioritas (bobot x gap); #n = peringkat. "
        + interp["rekomendasi_prioritas"]
        + "\n"
    )
    s.append("## Rekomendasi per segmen\n")
    for k in _seg(rep):
        s += _blok_segmen(rep, k)
    s.append("## Seberapa pasti\n")
    x3 = "x3_komunikasi"
    s += [
        f"- {interp['rekomendasi_gap']}",
        (
            f"- Urutan bertumpu pada bobot Tahap 4: {_nama_s(x3)} dan X1 berhubungan meyakinkan "
            "dengan laporan kenaikan penjualan, X2 dan X4 tidak (bobot diturunkan menjadi "
            f"{_a(bob.at['x2_promosi', 'bobot'])} dan {_a(bob.at['x4_konsistensi', 'bobot'])}). Bila "
            "bobot dibuat sama rata, urutan berubah (lihat log); urutan utama bertahan di "
            f"{f['n_sama']} dari {f['n_varian']} varian sensitivitas."
        ),
        (
            f"- Ilustrasi model ({m}): bila skor {_nama_s(x3)} dinaikkan 1 poin dengan profil tetap, "
            "peluang naik penjualan yang diprediksi model rata-rata berubah "
            + _daftar([f"{_pp(_wf(rep, k, x3))} di segmen {k}" for k in _seg(rep)])
            + "; untuk X1 "
            + _daftar([_pp(_wf(rep, k, "x1_unggah")) for k in _seg(rep)])
            + ", X2 "
            + _daftar([_pp(_wf(rep, k, "x2_promosi")) for k in _seg(rep)])
            + ". Ini pola yang dipelajari model dari data yang sama, bukan perkiraan dampak."
        ),
        "",
    ]
    s.append("## Keterbatasan\n")
    s += [f"- {x}" for x in keterbatasan(rep)]
    s.append("\n## Grafik\n")
    s.append("| Grafik | Interpretasi |\n|---|---|")
    for nm in ("rekomendasi_prioritas", "rekomendasi_gap"):
        s.append(f"| `figures/{nm}.png` | {interp[nm]} |")
    s.append(
        "\n_Rekomendasi ini perlu divalidasi kewajarannya dengan pembimbing/pelaku UMKM sebelum "
        "difinalkan (plan/06 langkah 6)._\n"
    )
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Kontrak integrasi
# ---------------------------------------------------------------------------
def _tabel_skema(model: type) -> pd.DataFrame:
    sk = model.model_json_schema()
    wajib = set(sk.get("required", []))
    rows = []
    for nm, f in sk["properties"].items():
        tipe = f.get("type") or " / ".join(a.get("type", "?") for a in f.get("anyOf", []))
        if tipe == "array":
            item = f.get("items", {})
            tipe = f"list[{' / '.join(item.get('enum', [])) or item.get('type', item.get('$ref', '?').split('/')[-1])}]"
        if "$ref" in f:
            tipe = f["$ref"].split("/")[-1]
        rentang = []
        for k, lab in (("minimum", ">="), ("maximum", "<="), ("minItems", "min item")):
            if k in f:
                rentang.append(f"{lab} {f[k]:g}")
        rows.append(
            {
                "field": nm,
                "tipe": tipe,
                "wajib": "ya" if nm in wajib else "tidak",
                "rentang": ", ".join(rentang) or "-",
                "keterangan": f.get("description", "-"),
            }
        )
    return pd.DataFrame(rows)


def build_kontrak(rep: RekomendasiReport, cfg: dict[str, Any]) -> str:
    """Susun reports/integration_contract.md dari skema Pydantic dan artefak yang baru dibuat."""
    meta = rep.artefak["meta"]
    bm = rep.artefak["benchmark"]
    versi = meta["versi_model"]
    contoh = rep.contoh
    s = ["# Kontrak Integrasi: `recommend(profil) -> dict`\n"]
    s.append(
        f"Dibuat ulang oleh Tahap 6 (`python -m umkm.pipeline --stage 6`) pada {meta['dibuat']}. "
        f"Versi artefak: **{versi}**. Aplikasi/API belum dibangun (D09); dokumen ini menjelaskan "
        "cara sistem lain memanggil kode yang sudah ada.\n"
    )
    s.append("## Ringkas\n")
    s += [
        "- Pintu masuk tunggal: `umkm.recommend.recommend(profil: dict, dir_model=None) -> dict`.",
        (
            f"- Hanya memuat artefak di `models/{versi}/` (lewat config + env `UMKM_BASE_DIR`); tidak "
            "membaca data survei, xlsx, atau state notebook."
        ),
        (
            "- Masukan divalidasi `umkm.schemas.ProfilUMKM`; keluaran mengikuti "
            "`umkm.schemas.HasilRekomendasi` (dict/list/angka/teks, siap `json.dumps`)."
        ),
        (
            "- Dependensi minimal: pandas, numpy, scikit-learn, joblib, pydantic, pyyaml "
            "(`pip install -e .`, tanpa `[analysis]`)."
        ),
        "",
    ]
    s.append("## Cara memakai\n")
    s.append(
        "```python\nfrom umkm.recommend import recommend\n\nhasil = recommend({\n"
        + "".join(
            f"    {json.dumps(k)}: {json.dumps(v)},\n" for k, v in contoh[2]["masukan"].items()
        )
        + '})\nprint(hasil["prioritas"][0]["strategi"])\n```\n'
    )
    s.append(
        "Dari terminal (skrip terpisah, tanpa notebook): `python -m umkm.recommend profil.json` "
        "atau `cat profil.json | python -m umkm.recommend -`. Folder artefak lain: "
        "`--dir-model path/ke/models/v1`.\n"
    )
    s.append("## Skema masukan (`ProfilUMKM`)\n")
    s.append(_md(_tabel_skema(ProfilUMKM)))
    s.append(
        "\nField lain ditolak (`extra = forbid`) agar salah ketik nama field langsung ketahuan. "
        "`platform` dinormalkan (huruf kecil, tanpa spasi, tanpa duplikat); platform di luar lima "
        "nilai itu ditolak. `jumlah_platform` dihitung dari panjang `platform`.\n"
    )
    s.append("### Rentang data latih\n")

    def _ribuan(x: float) -> str:
        return f"{x:,.0f}".replace(",", ".")

    rl = pd.DataFrame(
        [
            {"field": k, "min": _ribuan(v[0]), "maks": _ribuan(v[1])}
            for k, v in meta["rentang_latih"].items()
        ]
    )
    s.append(_md(rl))
    s.append(
        "\nNilai di luar rentang tetap diproses, tetapi keluaran memberi `peringatan`. Batas kuartil "
        "omzet (skala omzet untuk segmen): "
        + ", ".join(f"Rp{b:,.0f}".replace(",", ".") for b in bm["batas_skala_omzet"])
        + ". Di data latih, omzet = omzet per bulan SEBELUM masuk marketplace; untuk UMKM baru "
        "pakai omzet per bulan saat ini.\n"
    )
    s.append("## Skema keluaran (`HasilRekomendasi`)\n")
    s.append(_md(_tabel_skema(HasilRekomendasi)))
    s.append("\nTiap elemen `skor` (`SkorStrategi`) dan `prioritas` (`Prioritas`):\n")
    from umkm.schemas import Prioritas

    s.append(_md(_tabel_skema(Prioritas)))
    s += [
        "",
        (
            "- `skor` selalu berisi 4 strategi; `prioritas` berisi 0-3 strategi dengan prioritas > 0, "
            "urut `peringkat`. Daftar kosong = semua skor sudah setara atau di atas benchmark (ada "
            "kalimat di `peringatan`)."
        ),
        (
            "- `gap` = max(0, benchmark - skor); `prioritas` = `bobot` x `gap`. `benchmark` = rata-rata "
            "skor UMKM yang melaporkan kenaikan penjualan di segmen yang sama (D28)."
        ),
        (
            "- `selisih_prediksi_plus1` = ilustrasi model: selisih peluang prediksi naik penjualan (poin "
            "persen) bila skor strategi itu +1 (maks 5). Bukan perkiraan dampak."
        ),
        (
            "- `fokus_butir` = kode butir kuesioner (lihat data_dictionary.md) dengan gap terbesar di "
            "segmen itu; `tindakan` menerjemahkannya ke langkah konkret."
        ),
        (
            "- Teks (`alasan`, `tindakan`, `catatan`) berasal dari templat di `umkm/recommend.py` dan "
            "boleh diganti/diterjemahkan oleh sistem tujuan."
        ),
        "",
    ]
    s.append("## Galat\n")
    s += [
        (
            "- Masukan tidak sah -> `pydantic.ValidationError` (turunan `ValueError`); pesannya menyebut "
            "field dan aturan yang dilanggar. Bungkus API sebaiknya mengembalikan HTTP 422."
        ),
        "- Artefak tidak ada -> `FileNotFoundError` dengan petunjuk menjalankan Tahap 6.",
        "- Versi scikit-learn berbeda dari saat artefak dibuat -> tetap jalan, ada `peringatan`.",
        "",
    ]
    s.append(f"## Artefak `models/{versi}/`\n")
    s.append("| Berkas | Isi |\n|---|---|")
    s += [
        (
            "| `segmen.joblib` | dict: `pipa` (StandardScaler + K-Means), `urutan` (label -> nomor "
            "segmen), `fitur`, `fitur_log1p` |"
        ),
        "| `model.joblib` | dict: `model` (" + meta["model_terbaik"] + ", target naik_penjualan), "
        "`fitur`, `nama`, `target` |",
        (
            "| `benchmark_per_segmen.json` | batas kuartil omzet, n prioritas, per segmen: nama, "
            "konteks, n, benchmark, skor rata-rata, median, butir fokus |"
        ),
        "| `pengaruh_strategi.json` | bobot, skor pengaruh, P(koef > 0), meyakinkan, OR, p (Tahap 4) |",
        "| `model_meta.json` | tanggal, seed, versi pustaka, fitur, metrik CV, rentang latih, hash data |",
        "",
        (
            "Memuat: `umkm.recommend.muat_artefak(str(path))` (di-cache per folder). Berkas `.joblib` "
            "adalah pickle: hanya muat artefak yang dibuat pipeline proyek ini sendiri. Perubahan model "
            "atau data = folder versi baru (`v2/`), ubah `recommendation.versi_model` di config.yaml. "
            "`*.joblib` tidak masuk git (`.gitignore`); buat ulang dengan Tahap 6."
        ),
        "",
    ]
    s.append("### Versi pustaka saat artefak dibuat\n")
    s.append(" | ".join(f"{k} {v}" for k, v in meta["versi_pustaka"].items()) + "\n")
    s.append("### Metrik CV model (naik_penjualan, " + meta["skema_cv"] + ")\n")
    mc = pd.DataFrame(
        [
            {"model": m, **{k: v["rata_rata"] for k, v in d.items()}}
            for m, d in meta["metrik_cv_naik_penjualan"].items()
        ]
    )
    s.append(_md(mc, "{:.3f}"))
    s.append("\n### Hash data latih (SHA-256)\n")
    s += [f"- `{k}`: `{v}`" for k, v in meta["hash_data_sha256"].items()]
    s.append("")
    s.append("## Contoh\n")
    for c in contoh:
        s.append(f"### `{c['masukan']['id_umkm']}`\n")
        s.append("Masukan:\n")
        s.append(_json(c["masukan"]))
        s.append("Keluaran:\n")
        s.append(_json(c["keluaran"]))
    s.append("## Jalur integrasi nanti (belum dikerjakan)\n")
    s += [
        "- Sistem Python: `pip install` paket `umkm` lalu panggil `recommend()` langsung.",
        (
            "- Sistem non-Python: bungkus dengan FastAPI (`POST /recommend` -> `recommend(body)`, "
            "`GET /health` -> versi artefak dari `model_meta.json`)."
        ),
        "- Semua jalur memakai kontrak dan artefak yang sama.",
        "",
    ]
    return "\n".join(s)
