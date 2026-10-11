from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wfintel import db, model, pipeline, segments, stats
from wfintel.config import config


def test_wilson_matches_reference_values() -> None:
    lo, hi = stats.wilson(237, 1470)
    assert lo == pytest.approx(0.1434, abs=5e-4) and hi == pytest.approx(0.1807, abs=5e-4)
    assert stats.wilson(0, 10)[0] == 0.0


def test_holm_is_monotone_and_bounded() -> None:
    adj = stats.holm([0.01, 0.04, 0.03, 0.5])
    assert adj == pytest.approx([0.04, 0.09, 0.09, 0.5])


def test_tests_and_stratified_odds_ratio(employees_csv: Path) -> None:
    df = db.table(db.build(employees_csv), "fact_employee")
    tests = {t["factor"]: t for t in stats.association_tests(df, 0.05)}
    assert tests["overtime"]["significant"]
    assert 0 <= tests["gender"]["effect"] <= 1
    assert tests["years_at_company"]["effect"] < 0  # leavers have shorter tenure in the synthetic data
    s = stats.stratified(df, "overtime", "job_level")
    assert s["mantel_haenszel"]["odds_ratio"] > 2
    assert len(s["strata"]) == 5


def test_calibration_of_true_probabilities_is_near_ideal() -> None:
    rng = np.random.default_rng(0)
    p = rng.uniform(0.02, 0.9, 20000)
    y = (rng.random(20000) < p).astype(int)
    intercept, slope = model.calibration(y, p)
    assert abs(intercept) < 0.05 and abs(slope - 1) < 0.05


def test_model_beats_baselines_and_reports_odds_ratios(employees_csv: Path) -> None:
    df = db.table(db.build(employees_csv), "fact_employee")
    cfg = config() | {"model": config()["model"] | {"bootstrap": 200}}
    fit = model.run(df, cfg)
    assert fit["test"]["logistic"]["auroc"] > fit["test"]["prevalence"]["auroc"]
    assert len(fit["oof"]) == len(df) and fit["split"]["test"] == len(fit["test_index"])
    orr = {t["term"]: t for t in model.odds_ratios(df, cfg)["terms"]}
    assert orr["overtime"]["odds_ratio"] > 2
    assert "gender" not in str(list(orr)) and "marital_status" not in str(list(orr))


def test_risk_bands_and_fairness(employees_csv: Path) -> None:
    df = db.table(db.build(employees_csv), "fact_employee")
    bands = segments.risk_band(np.array([0.05, 0.1, 0.2, 0.5]), [0.1, 0.2, 0.35])
    assert list(bands) == ["Low", "Moderate", "Elevated", "High"]
    rows = segments.fairness(df, np.full(len(df), 0.2), config())
    assert {r["attribute"] for r in rows} == {"gender", "age_band", "marital_status"}
    assert sum(r["employees"] for r in rows if r["attribute"] == "gender") == len(df)


def test_full_analysis_on_synthetic_data(employees_csv: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from wfintel import audit

    cfg = config() | {"model": config()["model"] | {"bootstrap": 100}}
    monkeypatch.setattr(pipeline, "config", lambda: cfg)
    r = pipeline.analyse(db.build(employees_csv))
    assert r["kpis"]["employees"] == len(pd.read_csv(employees_csv))
    assert [x["level"] for x in r["factors"]["pay_position"]["levels"]] == [
        "Below level median",
        "At level median",
        "Above level median",
    ]
    assert r["recommendations"], "the overtime rule should fire on the synthetic data"
    text = "\n".join(
        " ".join([x["title"], x["finding"], *x["evidence"], x["action"], x["basis"]]) for x in r["recommendations"]
    )
    assert audit.scan_text(text) == []
