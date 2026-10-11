"""A synthetic employee file in the source's exact layout, with known associations and planted problems."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import pytest

HEADER = [
    "Age",
    "Attrition",
    "BusinessTravel",
    "DailyRate",
    "Department",
    "DistanceFromHome",
    "Education",
    "EducationField",
    "EmployeeCount",
    "EmployeeNumber",
    "EnvironmentSatisfaction",
    "Gender",
    "HourlyRate",
    "JobInvolvement",
    "JobLevel",
    "JobRole",
    "JobSatisfaction",
    "MaritalStatus",
    "MonthlyIncome",
    "MonthlyRate",
    "NumCompaniesWorked",
    "Over18",
    "OverTime",
    "PercentSalaryHike",
    "PerformanceRating",
    "RelationshipSatisfaction",
    "StandardHours",
    "StockOptionLevel",
    "TotalWorkingYears",
    "TrainingTimesLastYear",
    "WorkLifeBalance",
    "YearsAtCompany",
    "YearsInCurrentRole",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
]
ROLES = {"Sales": ["Sales Executive", "Sales Representative"], "Research & Development": ["Research Scientist", "Laboratory Technician"],
         "Human Resources": ["Human Resources"]}  # fmt: skip
N = 800
# Planted: two rows whose years in role exceed years at the company; one row starting work before 14.
INCONSISTENT_ROLE = (5, 6)
EARLY_START = 7


def make_rows(n: int = N, seed: int = 1) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for i in range(n):
        dept = str(rng.choice(list(ROLES), p=[0.35, 0.6, 0.05]))
        level = int(rng.integers(1, 6))
        years = int(rng.integers(0, 15))
        working = years + int(rng.integers(0, 10))
        age = int(rng.integers(max(22, 18 + working), 62))
        overtime = rng.random() < 0.3
        marital = rng.choice(["Single", "Married", "Divorced"])
        # Known associations: overtime and level 1 raise the probability of having left.
        p = 1 / (1 + np.exp(-(-2.2 + 1.6 * overtime + 0.8 * (level == 1) - 0.05 * years)))
        rows.append({
            "Age": age, "Attrition": "Yes" if rng.random() < p else "No",
            "BusinessTravel": rng.choice(["Travel_Rarely", "Travel_Frequently", "Non-Travel"], p=[0.7, 0.2, 0.1]),
            "DailyRate": int(rng.integers(100, 1500)), "Department": dept,
            "DistanceFromHome": int(rng.integers(1, 30)), "Education": int(rng.integers(1, 6)),
            "EducationField": rng.choice(["Life Sciences", "Medical", "Marketing"]), "EmployeeCount": 1,
            "EmployeeNumber": i + 1, "EnvironmentSatisfaction": int(rng.integers(1, 5)), "Gender": rng.choice(["Male", "Female"]),
            "HourlyRate": int(rng.integers(30, 100)), "JobInvolvement": int(rng.integers(1, 5)), "JobLevel": level,
            "JobRole": rng.choice(ROLES[dept]), "JobSatisfaction": int(rng.integers(1, 5)), "MaritalStatus": marital,
            "MonthlyIncome": int(2000 * level + rng.integers(0, 2000)), "MonthlyRate": int(rng.integers(2000, 27000)),
            "NumCompaniesWorked": int(rng.integers(0, 9)), "Over18": "Y", "OverTime": "Yes" if overtime else "No",
            "PercentSalaryHike": int(rng.integers(11, 25)), "PerformanceRating": int(rng.choice([3, 4], p=[0.85, 0.15])),
            "RelationshipSatisfaction": int(rng.integers(1, 5)), "StandardHours": 80,
            "StockOptionLevel": 0 if marital == "Single" else int(rng.integers(0, 4)),
            "TotalWorkingYears": working, "TrainingTimesLastYear": int(rng.integers(0, 7)),
            "WorkLifeBalance": int(rng.integers(1, 5)), "YearsAtCompany": years,
            "YearsInCurrentRole": int(rng.integers(0, years + 1)), "YearsSinceLastPromotion": int(rng.integers(0, years + 1)),
            "YearsWithCurrManager": int(rng.integers(0, years + 1)),
        })  # fmt: skip
    for i in INCONSISTENT_ROLE:
        rows[i]["YearsInCurrentRole"] = int(rows[i]["YearsAtCompany"]) + 2
    rows[EARLY_START]["Age"], rows[EARLY_START]["TotalWorkingYears"] = 25, 15
    rows[EARLY_START]["YearsAtCompany"] = rows[EARLY_START]["YearsInCurrentRole"] = 3
    rows[EARLY_START]["YearsSinceLastPromotion"] = rows[EARLY_START]["YearsWithCurrManager"] = 1
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    return path


@pytest.fixture(scope="session")
def employees_csv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_csv(tmp_path_factory.mktemp("data") / "employees.csv", make_rows())
