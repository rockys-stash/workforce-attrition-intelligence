"""Display labels and orders for coded values."""

from __future__ import annotations

from typing import Any

from wfintel.config import config
from wfintel.db import band_labels

SCALE4 = {1: "Low", 2: "Medium", 3: "High", 4: "Very high"}
CODES: dict[str, dict[Any, str]] = {
    "job_satisfaction": SCALE4, "environment_satisfaction": SCALE4, "relationship_satisfaction": SCALE4,
    "job_involvement": SCALE4,
    "work_life_balance": {1: "Bad", 2: "Good", 3: "Better", 4: "Best"},
    "education": {1: "Below college", 2: "College", 3: "Bachelor", 4: "Master", 5: "Doctor"},
    "performance_rating": {1: "Low", 2: "Good", 3: "Excellent", 4: "Outstanding"},
    "overtime": {0: "No overtime", 1: "Overtime"},
    "job_level": {i: f"Level {i}" for i in range(1, 6)},
    "stock_option_level": {i: f"Level {i}" for i in range(4)},
    "income_band": {1: "Lowest 20%", 2: "20–40%", 3: "40–60%", 4: "60–80%", 5: "Highest 20%"},
}  # fmt: skip
NAMES = {
    "department": "Department", "job_role": "Job role", "job_level": "Job level", "income_band": "Income band",
    "pay_position": "Pay vs job-level median", "tenure_band": "Years at the company", "age_band": "Age",
    "overtime": "Overtime", "business_travel": "Business travel", "performance_rating": "Performance rating",
    "promotion_band": "Years since last promotion", "job_satisfaction": "Job satisfaction",
    "environment_satisfaction": "Environment satisfaction", "relationship_satisfaction": "Relationship satisfaction",
    "work_life_balance": "Work-life balance", "job_involvement": "Job involvement",
    "stock_option_level": "Stock option level", "education": "Education", "education_field": "Education field",
    "gender": "Gender", "marital_status": "Marital status", "age": "Age", "monthly_income": "Monthly income",
    "years_at_company": "Years at the company", "total_working_years": "Total working years",
    "years_in_current_role": "Years in current role", "years_since_last_promotion": "Years since last promotion",
    "years_with_curr_manager": "Years with current manager", "num_companies_worked": "Previous employers",
    "distance_from_home": "Distance from home", "percent_salary_hike": "Last salary rise (%)",
    "training_times_last_year": "Trainings last year",
}  # fmt: skip


def order(factor: str) -> list[Any] | None:
    """Natural order of a factor's levels, or None to sort by size."""
    b = config()["bands"]
    if factor in CODES:
        return list(CODES[factor])
    return {
        "tenure_band": band_labels(b["tenure_years"], " yrs"),
        "age_band": band_labels(b["age"]),
        "promotion_band": band_labels(b["promotion_years"], " yrs"),
        "pay_position": ["Below level median", "At level median", "Above level median"],
        "business_travel": ["None", "Rarely", "Frequently"],
    }.get(factor)


def label(factor: str, value: Any) -> str:
    return CODES.get(factor, {}).get(value, str(value))
