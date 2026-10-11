"""Descriptive rates with intervals, association tests with effect sizes, and stratified odds ratios.

Everything here measures association in a cross-section. Nothing estimates what would happen if a
characteristic were changed.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as st

NUMERIC_TESTS = (
    "age", "monthly_income", "years_at_company", "total_working_years", "years_in_current_role",
    "years_since_last_promotion", "years_with_curr_manager", "num_companies_worked", "distance_from_home",
    "percent_salary_hike", "training_times_last_year",
)  # fmt: skip
CATEGORICAL_TESTS = (
    "department", "job_role", "job_level", "overtime", "business_travel", "performance_rating", "job_satisfaction",
    "environment_satisfaction", "relationship_satisfaction", "work_life_balance", "job_involvement",
    "stock_option_level", "education", "education_field", "gender", "marital_status",
)  # fmt: skip


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def with_intervals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ci = [wilson(int(k), int(n)) for k, n in zip(out["leavers"], out["employees"], strict=True)]
    out["ci_low"] = [c[0] for c in ci]
    out["ci_high"] = [c[1] for c in ci]
    return out


def holm(p: list[float]) -> list[float]:
    """Holm–Bonferroni adjusted p-values, in the input order."""
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return [float(x) for x in adj]


def chi_square(df: pd.DataFrame, factor: str) -> dict[str, Any]:
    tab = pd.crosstab(df[factor], df["left_company"])
    chi2, p, dof, expected = st.chi2_contingency(tab.to_numpy(), correction=False)
    n = int(tab.to_numpy().sum())
    v = math.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    return {"factor": factor, "test": "chi-square", "statistic": float(chi2), "df": int(dof), "p": float(p),
            "effect": float(v), "effect_name": "Cramér's V", "min_expected": float(expected.min()), "n": n}  # fmt: skip


def mann_whitney(df: pd.DataFrame, column: str) -> dict[str, Any]:
    left = df.loc[df["left_company"] == 1, column].to_numpy(float)
    stayed = df.loc[df["left_company"] == 0, column].to_numpy(float)
    u, p = st.mannwhitneyu(left, stayed, alternative="two-sided")
    # Rank-biserial correlation: positive when leavers tend to have higher values.
    r = 2 * u / (len(left) * len(stayed)) - 1
    return {"factor": column, "test": "Mann–Whitney U", "statistic": float(u), "df": None, "p": float(p),
            "effect": float(r), "effect_name": "rank-biserial r", "median_left": float(np.median(left)),
            "median_stayed": float(np.median(stayed)), "n": len(left) + len(stayed)}  # fmt: skip


def association_tests(df: pd.DataFrame, alpha: float) -> list[dict[str, Any]]:
    rows = [chi_square(df, f) for f in CATEGORICAL_TESTS] + [mann_whitney(df, c) for c in NUMERIC_TESTS]
    for row, padj in zip(rows, holm([r["p"] for r in rows]), strict=True):
        row["p_holm"] = padj
        row["significant"] = padj < alpha
    return rows


def odds_ratio(a: float, b: float, c: float, d: float) -> tuple[float, float, float]:
    """Odds ratio for [[a, b], [c, d]] (exposed leavers, exposed stayers; unexposed ...), Woolf interval."""
    a, b, c, d = (x + 0.5 for x in (a, b, c, d)) if min(a, b, c, d) == 0 else (a, b, c, d)
    orr = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return orr, math.exp(math.log(orr) - 1.96 * se), math.exp(math.log(orr) + 1.96 * se)


def stratified(df: pd.DataFrame, exposure: str, stratum: str) -> dict[str, Any]:
    """Crude and Mantel–Haenszel odds ratios of leaving for a binary exposure, within strata."""
    from statsmodels.stats.contingency_tables import StratifiedTable

    def table(g: pd.DataFrame) -> list[list[float]]:
        e, y = g[exposure] == 1, g["left_company"] == 1
        return [[float((e & y).sum()), float((e & ~y).sum())], [float((~e & y).sum()), float((~e & ~y).sum())]]

    crude = odds_ratio(*(float(v) for v in np.ravel(table(df))))
    per, tables = [], []
    for level, g in df.groupby(stratum, sort=True):
        t = table(g)
        tables.append(np.array(t))
        o = odds_ratio(*(float(v) for v in np.ravel(t)))
        per.append({"stratum": str(level), "employees": len(g), "exposed": int(g[exposure].sum()),
                    "rate_exposed": float(g.loc[g[exposure] == 1, "left_company"].mean()),
                    "rate_unexposed": float(g.loc[g[exposure] == 0, "left_company"].mean()),
                    "odds_ratio": o[0], "ci": [o[1], o[2]]})  # fmt: skip
    s = StratifiedTable(tables)
    lo, hi = s.oddsratio_pooled_confint()
    return {
        "exposure": exposure, "stratum": stratum,
        "crude": {"odds_ratio": crude[0], "ci": [crude[1], crude[2]]},
        "mantel_haenszel": {"odds_ratio": float(s.oddsratio_pooled), "ci": [float(lo), float(hi)],
                            "p": float(s.test_null_odds().pvalue)},
        "homogeneity_p": float(s.test_equal_odds().pvalue),
        "strata": per,
    }  # fmt: skip
