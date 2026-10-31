from umkm import pelaporan


def test_susun_laporan_memuat_seksi_kunci():
    teks = pelaporan.susun_laporan()
    assert "# Laporan Akhir Penelitian" in teks
    assert "Temuan Utama" in teks
    assert "Keterbatasan Metodologis" in teks
    assert "Kesiapan Integrasi Sistem" in teks


def test_run_pelaporan_sukses_dan_inferensi_valid():
    res = pelaporan.run()
    assert res.path_laporan.exists()
    assert res.path_laporan.stat().st_size > 1000
    assert res.inferensi_valid is True
    assert len(res.tabel_terhubung) >= 4
