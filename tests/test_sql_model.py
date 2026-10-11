from __future__ import annotations

import csv
from pathlib import Path

import pytest
from conftest import EARLY_START, INCONSISTENT_ROLE, N, make_rows, write_csv

from wfintel import db


def _check(con: object, cid: int) -> float:
    return float(db.table(con, "data_checks").set_index("id").loc[cid, "value"])  # type: ignore[arg-type]


def test_checks_count_each_planted_problem(employees_csv: Path) -> None:
    con = db.build(employees_csv)
    assert _check(con, 1) == 0
    assert _check(con, 4) == 3  # employee count, over 18, standard hours
    assert _check(con, 5) == len(INCONSISTENT_ROLE)
    assert _check(con, 9) == 1
    assert abs(_check(con, 10)) < 20  # monthly rate unrelated to income
    flagged = set(db.table(con, "employees").query("has_inconsistency")["employee_number"])
    assert flagged >= {i + 1 for i in (*INCONSISTENT_ROLE, EARLY_START)}


def test_missing_and_duplicates_are_counted(tmp_path: Path) -> None:
    rows = make_rows(50)
    rows[3]["Department"] = ""
    rows.append(dict(rows[10]))
    con = db.build(write_csv(tmp_path / "e.csv", rows))
    assert _check(con, 1) == 1
    assert _check(con, 2) == 1
    assert _check(con, 3) == 1


def test_model_tables_and_bands(employees_csv: Path) -> None:
    con = db.build(employees_csv)
    fact = db.table(con, "fact_employee")
    assert len(fact) == N
    assert "employee_count" not in fact and "daily_rate" not in fact
    assert set(fact["tenure_band"]) <= set(db.band_labels([0, 2, 4, 6, 11, 21], " yrs"))
    assert fact["income_band"].between(1, 5).all()
    by = db.attrition_by(con, "overtime").set_index("level")
    assert by["rate"].to_dict()[1] > by["rate"].to_dict()[0]
    assert int(by["employees"].sum()) == N


def test_measures_run(employees_csv: Path) -> None:
    con = db.build(employees_csv)
    for name in ("overview", "departments", "compensation", "income_bands", "tenure_curve", "model_tables"):
        assert len(db.measure(con, name)) > 0
    with pytest.raises(ValueError):
        db.attrition_by(con, "1; DROP TABLE x")


def test_band_labels() -> None:
    assert db.band_labels([0, 2, 4, 6, 11, 21], " yrs") == [
        "0–1 yrs",
        "2–3 yrs",
        "4–5 yrs",
        "6–10 yrs",
        "11–20 yrs",
        "21+ yrs",
    ]
    assert db.band_labels([0, 1, 3]) == ["0", "1–2", "3+"]


def test_committed_source_has_the_expected_layout() -> None:
    from wfintel.fetch import verify

    with verify().open(encoding="utf-8-sig") as f:
        header = next(csv.reader(f))
    from conftest import HEADER

    assert header == HEADER
