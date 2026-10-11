"""The SQL layer: builds the DuckDB model from the employee CSV and runs measures.

SQL files use ``${name}`` placeholders filled from the config. Values and the factor identifiers are
inserted by this module from fixed lists, never from user input.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from wfintel.config import config
from wfintel.paths import ROOT, SQL

MODEL_FILES = ("01_staging.sql", "02_checks.sql", "03_model.sql")
FACTORS = (
    "department", "job_role", "job_level", "income_band", "pay_position", "tenure_band", "age_band", "overtime",
    "business_travel", "performance_rating", "promotion_band", "job_satisfaction", "environment_satisfaction",
    "relationship_satisfaction", "work_life_balance", "job_involvement", "stock_option_level", "education",
    "education_field", "gender", "marital_status",
)  # fmt: skip
_PLACEHOLDER = re.compile(r"\$\{(\w+)\}")


def band_labels(bounds: list[int], unit: str = "") -> list[str]:
    """Labels for integer bands with inclusive lower bounds: [0, 2, 4] -> 0–1, 2–3, 4+."""
    out = []
    for i, lo in enumerate(bounds):
        hi = bounds[i + 1] - 1 if i + 1 < len(bounds) else None
        text = f"{lo}+" if hi is None else (str(lo) if hi == lo else f"{lo}–{hi}")
        out.append(f"{text}{unit}")
    return out


def band_case(column: str, bounds: list[int], unit: str = "") -> str:
    labels = band_labels(bounds, unit)
    parts = [f"WHEN {column} >= {lo} THEN '{lab}'" for lo, lab in zip(reversed(bounds), reversed(labels), strict=True)]
    return "CASE " + " ".join(parts) + " END"


def params(source: Path | None = None) -> dict[str, Any]:
    cfg = config()
    b = cfg["bands"]
    return {
        "source": str(source or ROOT / cfg["source"]["file"]),
        "income_quantiles": int(b["income_quantiles"]),
        "pay_tol": float(b["pay_position_tolerance"]),
        "tenure_band": band_case("years_at_company", b["tenure_years"], " yrs"),
        "age_band": band_case("age", b["age"]),
        "promotion_band": band_case("years_since_last_promotion", b["promotion_years"], " yrs"),
    }


def render(sql: str, p: dict[str, Any]) -> str:
    return _PLACEHOLDER.sub(lambda m: str(p[m.group(1)]), sql)


def build(source: Path | None = None, path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(path)
    con.execute("SET threads TO 2")
    p = params(source)
    for f in MODEL_FILES:
        con.execute(render((SQL / f).read_text(encoding="utf-8"), p))
    return con


def measure(con: duckdb.DuckDBPyConnection, name: str, **extra: str) -> pd.DataFrame:
    p = params()
    if "factor" in extra and extra["factor"] not in FACTORS:
        raise ValueError(f"unknown factor {extra['factor']!r}")
    p.update(extra)
    return con.execute(render((SQL / "measures" / f"{name}.sql").read_text(encoding="utf-8"), p)).df()


def attrition_by(con: duckdb.DuckDBPyConnection, factor: str) -> pd.DataFrame:
    return measure(con, "attrition_by", factor=factor)


def table(con: duckdb.DuckDBPyConnection, name: str) -> pd.DataFrame:
    if not re.fullmatch(r"[a-z_]+", name):
        raise ValueError(name)
    return con.execute(f"SELECT * FROM {name}").df()


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return list(json.loads(df.to_json(orient="records", double_precision=6)))
