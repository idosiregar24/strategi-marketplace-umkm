"""Menjalankan tahap pipeline dari CLI: `python -m umkm.pipeline --stage N` atau `--all`."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from umkm import cleaning, features


def _stage1() -> None:
    df, _ = cleaning.run()
    print(f"Tahap 1 selesai: data_clean.csv {df.shape[0]} baris x {df.shape[1]} kolom")


def _stage2() -> None:
    df, _ = features.run()
    print(f"Tahap 2 selesai: data_features.csv {df.shape[0]} baris x {df.shape[1]} kolom")


def _stage3() -> None:
    from umkm import eda  # butuh pustaka analisis (scipy, statsmodels, matplotlib)

    rep = eda.run()
    print(f"Tahap 3 selesai: {len(rep.tabel)} tabel eda_*.csv, {len(rep.grafik)} grafik eda_*.png")


def _stage4() -> None:
    from umkm import pengaruh  # butuh pustaka analisis (statsmodels, shap)

    rep = pengaruh.run()
    print(
        f"Tahap 4 selesai: {len(rep.tabel)} tabel pengaruh_*.csv, {len(rep.grafik)} grafik, "
        f"bootstrap {rep.info['n_boot']}x"
    )


def _stage5() -> None:
    from umkm import segmentation  # butuh pustaka analisis (matplotlib, statsmodels)

    rep = segmentation.run()
    print(
        f"Tahap 5 selesai: data_segmen.csv {rep.data.shape[0]} baris, k = {rep.info['k']}, "
        f"silhouette {rep.info['silhouette']:.3f}, {len(rep.grafik)} grafik"
    )


def _stage6() -> None:
    from umkm import rekomendasi  # butuh pustaka analisis (scipy, matplotlib)

    rep = rekomendasi.run()
    cocok = bool(rep.tabel["konsistensi"]["cocok"].all())
    print(
        f"Tahap 6 selesai: {len(rep.tabel['per_segmen'])} baris rekomendasi, model "
        f"{rep.info['model_terbaik']}, artefak {len(rep.info['path_artefak'])} berkas, "
        f"recommend() cocok dengan tabel: {cocok}"
    )


def _stage7() -> None:
    from umkm import pelaporan

    res = pelaporan.run()
    print(
        f"Tahap 7 selesai: laporan_final.md dibuat, {res.angka_tervalidasi} tabel terhubung, "
        f"inferensi recommend(): {'VALID' if res.inferensi_valid else 'GAGAL'}"
    )


STAGES: dict[int, Callable[[], None]] = {
    1: _stage1,
    2: _stage2,
    3: _stage3,
    4: _stage4,
    5: _stage5,
    6: _stage6,
    7: _stage7,
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stage", type=int, choices=range(1, 8))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    stages = sorted(STAGES) if args.all else [args.stage]
    for n in stages:
        if n not in STAGES:
            raise SystemExit(f"Tahap {n} belum diimplementasikan.")
        STAGES[n]()


if __name__ == "__main__":
    main()
