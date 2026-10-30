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


STAGES: dict[int, Callable[[], None]] = {1: _stage1, 2: _stage2, 3: _stage3, 4: _stage4}


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
