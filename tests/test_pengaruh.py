import numpy as np
import pandas as pd
import pytest

from umkm import models, stats


@pytest.fixture
def data():
    rng = np.random.default_rng(42)
    n = 200
    x = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n), "c": rng.normal(size=n)})
    lin = 1.5 * x["a"] + 0.0 * x["b"] - 0.8 * x["c"]
    y_bin = pd.Series((lin + rng.logistic(size=n) > 0).astype(int), name="y")
    y_num = pd.Series(lin + rng.normal(scale=0.5, size=n), name="y")
    return x, y_bin, y_num


def test_standarkan():
    z = stats.standarkan(pd.DataFrame({"a": [1.0, 2.0, 3.0]}))
    assert z["a"].tolist() == pytest.approx([-1.0, 0.0, 1.0])


def test_ols_hc3_arah_dan_info(data):
    x, _, y = data
    tab, info = stats.ols_hc3(y, x)
    k = tab.set_index("variabel")["koef"]
    assert k["a"] > 0 > k["c"] and abs(k["b"]) < 0.2
    assert info["n"] == 200 and 0 < info["r2"] < 1


def test_logit_or_odds_ratio(data):
    x, y, _ = data
    tab, info = stats.logit_or(y, x)
    t = tab.set_index("variabel")
    assert t.at["a", "or"] == pytest.approx(np.exp(t.at["a", "koef"]))
    assert t.at["a", "or_ci_bawah"] > 1 and t.at["c", "or_ci_atas"] < 1
    assert info["n_1"] == int(y.sum())


def test_logit_separasi_melempar_valueerror():
    x = pd.DataFrame({"a": np.arange(20.0)})
    y = pd.Series((x["a"] > 9).astype(int), name="y")
    with pytest.raises(ValueError):
        stats.logit_or(y, x)


def test_normalkan_positif():
    v = models.normalkan_positif(pd.Series([2.0, -1.0, 1.0]))
    assert v.tolist() == [1.0, 0.0, 0.5]
    assert models.normalkan_positif(pd.Series([-1.0, -2.0])).tolist() == [0.0, 0.0]


def test_skor_gabungan_arah_negatif_jadi_nol():
    idx = ["s1", "s2"]
    g = models.skor_gabungan(
        pd.Series([1.0, 0.5], idx),
        pd.Series([0.1, 0.2], idx),
        pd.Series([0.3, 0.3], idx),
        pd.Series([0.8, -0.5], idx),  # s2 berarah negatif menurut SHAP
    )
    assert g.at["s1", "pengaruh"] == pytest.approx(1.0)
    assert g.at["s2", "n_perm"] == 0 and g.at["s2", "n_shap"] == 0


def test_cv_metrik_baseline_dan_tanda(data):
    x, y, y_num = data
    cv = models.skema_cv(True, 3, 1)
    rk = models.ringkas_cv(
        models.cv_metrik(
            models.kandidat_klasifikasi({"n_estimators": 20, "max_depth": 3}),
            x,
            y,
            cv,
            models.SKOR_KLASIFIKASI,
        )
    ).set_index(["model", "metrik"])["rata_rata"]
    assert rk[("dummy_mayoritas", "auc")] == pytest.approx(0.5)
    assert rk[("logistik", "auc")] > 0.7
    rr = models.cv_metrik(
        models.kandidat_regresi({"n_estimators": 20, "max_depth": 3}),
        x,
        y_num,
        models.skema_cv(False, 3, 1),
        models.SKOR_REGRESI,
    )
    assert (rr.loc[rr["metrik"] == "mae", "nilai"] > 0).all()  # neg_ dibalik


def test_ringkas_bootstrap_peluang_peringkat():
    boot = pd.DataFrame(
        {
            f"{u}_{s}": v
            for s, v in (("s1", [1.0, 1.0, 0.2]), ("s2", [0.5, 0.4, 1.0]))
            for u in ("koef", "perm", "shap", "pengaruh")
        }
    )
    r = models.ringkas_bootstrap(boot, ["s1", "s2"]).set_index("strategi")
    assert r.at["s1", "p_peringkat_1"] == pytest.approx(2 / 3)
    assert r.at["s1", "p_peringkat_1"] + r.at["s2", "p_peringkat_1"] == pytest.approx(1)


def test_skor_gabungan_perm_negatif_arah_negatif_tetap_nol():
    # bug lama: perm negatif x tanda negatif menjadi positif
    idx = ["s1", "s2"]
    g = models.skor_gabungan(
        pd.Series([1.0, -0.1], idx),
        pd.Series([0.1, -0.01], idx),
        pd.Series([0.3, 0.01], idx),
        pd.Series([0.8, -0.1], idx),
    )
    assert g.at["s2", "n_perm"] == 0 and g.at["s2", "pengaruh"] == 0


def test_peluang_logit():
    assert stats.peluang_logit(0.0, 1.0, 0) == pytest.approx(0.5)
    assert stats.peluang_logit(0.0, np.log(3), 1) == pytest.approx(0.75)


def test_logit_lr_blok(data):
    x, y, _ = data
    hasil = stats.logit_lr_blok(y, x, ["a"])
    assert hasil["df"] == 1 and hasil["p"] < 0.001
    assert hasil["pseudo_r2_penuh"] > hasil["pseudo_r2_tanpa_blok"]
    assert stats.logit_lr_blok(y, x, ["b"])["p"] > 0.01


def test_confusion_cv_menjumlah_semua_baris(data):
    x, y, _ = data
    cm = models.confusion_cv(
        models.kandidat_klasifikasi({"n_estimators": 10, "max_depth": 2})["logistik"],
        x,
        y,
        models.skema_cv(True, 4, 2),
    )
    assert sum(cm.values()) == 2 * len(y)


def test_r2_oof_baseline_mendekati_nol(data):
    x, _, y = data
    r = models.r2_oof(
        models.kandidat_regresi({"n_estimators": 10, "max_depth": 2}), x, y, 4, 2
    ).set_index("model")
    assert r.at["dummy_rata_rata", "r2_oof"] < 0.02
    assert r.at["linear", "r2_oof"] > 0.5


def test_bobot_rekomendasi_minimum():
    from umkm.pengaruh import bobot_rekomendasi

    gab = pd.DataFrame({"pengaruh": [1.0, 0.4, 0.0], "p_koef_positif": [1.0, 0.5, 0.3]})
    assert bobot_rekomendasi(gab, 0.1).tolist() == pytest.approx([1.0, 0.2, 0.1])
