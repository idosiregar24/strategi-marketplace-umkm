"""Fungsi plot standar (matplotlib) dengan gaya seragam untuk laporan.

Setiap fungsi mengembalikan Figure dan tidak menulis berkas; penyimpanan lewat `simpan`.
Palet: biru/oranye kategorikal (lolos cek CVD), divergen biru (positif/naik) <-> merah
(negatif/turun) dengan titik tengah abu-abu.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib
import matplotlib.patches
import matplotlib.ticker

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure

# Warna (palet referensi, mode terang)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERI_1 = "#2a78d6"  # biru
SERI_2 = "#eb6834"  # oranye
NETRAL = "#cfcdc4"
BIRU_MUDA = "#86b6ef"
BIRU_TUA = "#1c5cab"
MERAH = "#d64140"
MERAH_MUDA = "#f0a3a2"
LIKERT_WARNA = [MERAH, MERAH_MUDA, NETRAL, BIRU_MUDA, BIRU_TUA]  # skor 1..5
ARAH_WARNA = {"naik": SERI_1, "sama": NETRAL, "turun": MERAH, "kosong": "#ecebe6"}
CMAP_DIVERGEN = LinearSegmentedColormap.from_list("umkm_div", [MERAH, "#f0efec", SERI_1])

DPI = 150


def _gaya() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": AXIS,
            "axes.labelcolor": INK_2,
            "axes.titlecolor": INK,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.frameon": False,
            "legend.fontsize": 8.5,
            "font.size": 9.5,
            "figure.titlesize": 12.5,
            "figure.titleweight": "bold",
        }
    )


_gaya()


def _judul(
    fig: Figure, judul: str, subjudul: str | None = None, ruang_legenda: float = 0.0
) -> float:
    """Judul + subjudul rata kiri dengan jarak tetap (inci) dari tepi atas, lalu tight_layout.

    `ruang_legenda` (inci) dicadangkan di bawah subjudul; mengembalikan posisi y (fraksi figur)
    tepi atas ruang itu untuk menaruh legenda figur.
    """
    h = fig.get_figheight()
    sup = fig.suptitle(judul, x=0.01, y=1 - 0.12 / h, ha="left", va="top", color=INK)
    sup.set_in_layout(False)  # ruang judul sudah dicadangkan lewat `rect`
    if subjudul:
        fig.text(0.01, 1 - 0.42 / h, subjudul, ha="left", va="top", color=INK_2, fontsize=9)
    atas = (0.68 if subjudul else 0.42) / h
    fig.tight_layout(rect=(0, 0, 1, 1 - atas - ruang_legenda / h))
    sup.set_in_layout(True)  # tetap ikut terhitung saat disimpan dengan bbox_inches="tight"
    return 1 - atas


def simpan(fig: Figure, path: Path) -> Path:
    """Simpan Figure ke PNG (folder dibuat bila belum ada) lalu tutup."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def bar_horizontal(
    nilai: pd.Series,
    judul: str,
    xlabel: str,
    subjudul: str | None = None,
    label_fmt: str = "{:.0f}",
    teks_tambahan: Sequence[str] | None = None,
) -> Figure:
    """Bar horizontal satu seri (indeks = kategori), urutan sesuai Series, nilai di ujung bar."""
    fig, ax = plt.subplots(figsize=(7.5, 0.45 * len(nilai) + 1.6))
    y = np.arange(len(nilai))[::-1]
    ax.barh(y, nilai.values, height=0.62, color=SERI_1, edgecolor=SURFACE, linewidth=2)
    ax.set_yticks(y, nilai.index)
    ax.set_xlabel(xlabel)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    vmax = float(nilai.max())
    for yi, v, extra in zip(y, nilai.values, teks_tambahan or [""] * len(nilai)):
        txt = label_fmt.format(v) + (f"  {extra}" if extra else "")
        ax.text(v + vmax * 0.01, yi, txt, va="center", ha="left", color=INK_2, fontsize=8.5)
    ax.set_xlim(0, vmax * 1.22)
    _judul(fig, judul, subjudul)
    return fig


def histogram_panel(
    df: pd.DataFrame,
    cols: Sequence[str],
    nama: Sequence[str],
    judul: str,
    xlabel: str,
    bins: Sequence[float] | int,
    subjudul: str | None = None,
    ncol: int = 2,
    garis_median: bool = True,
) -> Figure:
    """Small multiples histogram (satu panel per kolom, sumbu x sama)."""
    nrow = int(np.ceil(len(cols) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.0 * ncol, 2.6 * nrow + 0.8), squeeze=False)
    for ax, col, nm in zip(axes.flat, cols, nama):
        x = df[col].dropna()
        ax.hist(x, bins=bins, color=SERI_1, edgecolor=SURFACE, linewidth=1.5)
        if garis_median:
            med = x.median()
            ax.axvline(med, color=INK, linewidth=1)
            ax.text(
                med,
                ax.get_ylim()[1] * 0.97,
                f" median {med:.2f}".rstrip("0").rstrip("."),
                color=INK,
                fontsize=8,
                va="top",
                bbox={"facecolor": SURFACE, "edgecolor": "none", "alpha": 0.85, "pad": 1},
            )
        ax.set_title(f"{nm} (n={len(x)})", fontsize=9.5, loc="left")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Jumlah responden")
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
    for ax in list(axes.flat)[len(cols) :]:
        ax.set_visible(False)
    _judul(fig, judul, subjudul)
    return fig


def stacked_100(
    prop: pd.DataFrame,
    warna: Sequence[str],
    judul: str,
    xlabel: str = "Persentase responden",
    subjudul: str | None = None,
    label_min: float = 0.07,
    legend_judul: str | None = None,
) -> Figure:
    """Bar horizontal bertumpuk 100% (baris = kategori di sumbu y, kolom = segmen, nilai 0-1)."""
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(prop) + 1.9))
    y = np.arange(len(prop))[::-1]
    kiri = np.zeros(len(prop))
    for col, c in zip(prop.columns, warna):
        v = prop[col].to_numpy(dtype=float)
        ax.barh(y, v, left=kiri, height=0.66, color=c, edgecolor=SURFACE, linewidth=1.5, label=col)
        for yi, k, vi in zip(y, kiri, v):
            if vi >= label_min:
                gelap = c in (SERI_1, BIRU_TUA, MERAH)
                ax.text(
                    k + vi / 2,
                    yi,
                    f"{vi:.0%}",
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color="white" if gelap else INK,
                )
        kiri += v
    ax.set_yticks(y, prop.index)
    ax.set_ylim(-0.55, len(prop) - 0.45)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel(xlabel)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles, labels = ax.get_legend_handles_labels()
    y_leg = _judul(fig, judul, subjudul, ruang_legenda=0.32)
    if legend_judul:
        labels = [f"{legend_judul}:"] + labels
        handles = [matplotlib.patches.Patch(visible=False)] + handles
    fig.legend(
        handles,
        labels,
        ncol=len(labels),
        loc="upper left",
        bbox_to_anchor=(0.005, y_leg),
        handlelength=1.2,
        columnspacing=1.2,
        handletextpad=0.5,
    )
    return fig


def scatter_sebelum_sesudah(
    panel: Sequence[tuple[str, pd.Series, pd.Series]],
    judul: str,
    subjudul: str | None = None,
) -> Figure:
    """Scatter nilai sebelum vs sesudah per responden (skala log1p) dengan garis y = x.

    `panel` berisi (nama, sebelum, sesudah). Titik di atas garis = naik, di bawah = turun.
    """
    fig, axes = plt.subplots(1, len(panel), figsize=(5.0 * len(panel), 4.6), squeeze=False)
    for ax, (nm, seb, ses) in zip(axes.flat, panel):
        pair = pd.concat([seb, ses], axis=1).dropna()
        a, b = pair.iloc[:, 0].to_numpy(float), pair.iloc[:, 1].to_numpy(float)
        warna = np.where(b > a, SERI_1, np.where(b < a, MERAH, MUTED))
        ax.scatter(a, b, s=26, c=warna, edgecolors=SURFACE, linewidths=1, alpha=0.9, zorder=3)
        semua = np.concatenate([a, b])
        positif = semua[semua > 0].min()
        ada_nol = bool((semua == 0).any())
        lim = (0 if ada_nol else positif / 1.6, semua.max() * 1.6)
        ax.plot(lim, lim, color=INK_2, linewidth=1, zorder=2)
        for setel in (ax.set_xscale, ax.set_yscale):
            setel("symlog", linthresh=positif) if ada_nol else setel("log")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel(f"{nm} sebelum marketplace (skala log)")
        ax.set_ylabel(f"{nm} sesudah marketplace (skala log)")
        ax.grid(True)
        ax.set_axisbelow(True)
        n_naik, n_turun = int((b > a).sum()), int((b < a).sum())
        n_sama = len(a) - n_naik - n_turun
        ax.set_title(f"{nm} (n={len(a)})", fontsize=9.5, loc="left")
        ax.text(
            0.03,
            0.97,
            f"naik {n_naik}",
            color=SERI_1,
            transform=ax.transAxes,
            va="top",
            fontsize=8.5,
            fontweight="bold",
        )
        ax.text(
            0.03,
            0.91,
            f"sama {n_sama} (di garis)",
            color=INK_2,
            transform=ax.transAxes,
            va="top",
            fontsize=8.5,
        )
        ax.text(
            0.97,
            0.03,
            f"turun {n_turun}",
            color=MERAH,
            transform=ax.transAxes,
            ha="right",
            fontsize=8.5,
            fontweight="bold",
        )
    _judul(fig, judul, subjudul)
    return fig


def heatmap(
    nilai: pd.DataFrame,
    judul: str,
    xlabel: str,
    ylabel: str,
    subjudul: str | None = None,
    anotasi: pd.DataFrame | None = None,
    batas: float | None = None,
    garis_pemisah: Sequence[int] = (),
    label_skala: str = "rho Spearman",
) -> Figure:
    """Heatmap divergen (merah negatif, biru positif, abu-abu nol) dengan anotasi di tiap sel."""
    v = nilai.to_numpy(dtype=float)
    lim = batas or max(0.1, float(np.ceil(np.nanmax(np.abs(v)) * 10) / 10))
    fig, ax = plt.subplots(figsize=(1.35 * v.shape[1] + 3.2, 0.62 * v.shape[0] + 1.9))
    im = ax.imshow(v, cmap=CMAP_DIVERGEN, vmin=-lim, vmax=lim, aspect="auto")
    teks = anotasi if anotasi is not None else nilai.map(lambda t: f"{t:.2f}")
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            gelap = abs(v[i, j]) > lim * 0.65
            ax.text(
                j,
                i,
                teks.iat[i, j],
                ha="center",
                va="center",
                fontsize=8.5,
                color="white" if gelap else INK,
            )
    ax.set_xticks(range(v.shape[1]), nilai.columns, rotation=0)
    ax.set_yticks(range(v.shape[0]), nilai.index)
    ax.set_xticks(np.arange(-0.5, v.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, v.shape[0]), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for g in garis_pemisah:
        ax.axhline(g - 0.5, color=INK_2, linewidth=1.2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label(label_skala, color=INK_2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(color=MUTED, labelcolor=INK_2, labelsize=8)
    _judul(fig, judul, subjudul)
    return fig


def boxplot_kelompok(
    df: pd.DataFrame,
    cols: Sequence[str],
    nama: Sequence[str],
    grup: str,
    label_grup: dict[int, str],
    judul: str,
    ylabel: str,
    subjudul: str | None = None,
    teks_panel: Sequence[str] | None = None,
    ncol: int = 4,
    seed: int = 42,
) -> Figure:
    """Boxplot per kolom untuk dua kelompok (urutan sesuai `label_grup`) + titik jitter."""
    rng = np.random.default_rng(seed)
    kode = list(label_grup)
    warna = [SERI_1, SERI_2]
    nrow = int(np.ceil(len(cols) / ncol))
    fig, axes = plt.subplots(
        nrow, ncol, figsize=(2.8 * ncol, 3.4 * nrow + 0.9), squeeze=False, sharey=True
    )
    for idx, (ax, col, nm) in enumerate(zip(axes.flat, cols, nama)):
        data = [df.loc[df[grup] == k, col].dropna().to_numpy(float) for k in kode]
        bp = ax.boxplot(
            data,
            positions=range(len(kode)),
            widths=0.5,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": INK, "linewidth": 1.6},
            whiskerprops={"color": INK_2, "linewidth": 1},
            capprops={"color": INK_2, "linewidth": 1},
        )
        for patch, c in zip(bp["boxes"], warna):
            patch.set_facecolor(c)
            patch.set_alpha(0.28)
            patch.set_edgecolor(c)
        for i, (d, c) in enumerate(zip(data, warna)):
            ax.scatter(
                i + rng.uniform(-0.17, 0.17, len(d)),
                d + rng.uniform(-0.04, 0.04, len(d)),
                s=11,
                color=c,
                alpha=0.75,
                edgecolors="none",
                zorder=3,
            )
        ax.set_xticks(
            range(len(kode)), [f"{label_grup[k]}\n(n={len(d)})" for k, d in zip(kode, data)]
        )
        ax.set_title(nm, fontsize=9.5, loc="left")
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.set_ylim(0.7, 5.3)
        ax.set_yticks([1, 2, 3, 4, 5])
        if idx % ncol == 0:
            ax.set_ylabel(ylabel)
        if teks_panel:
            ax.text(
                0.5,
                -0.27,
                teks_panel[idx],
                transform=ax.transAxes,
                ha="center",
                va="top",
                fontsize=8,
                color=INK_2,
            )
    for ax in list(axes.flat)[len(cols) :]:
        ax.set_visible(False)
    _judul(fig, judul, subjudul)
    return fig
