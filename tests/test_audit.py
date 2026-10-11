from __future__ import annotations

import pytest

from wfintel import audit


@pytest.mark.parametrize(
    "text",
    [
        "Overtime causes attrition.",
        "Low pay drives turnover",
        "Long commutes lead to resignations",
        "Overtime leads to attrition",
        "attrition is due to low pay",
        "Raising pay reduces attrition",
        "a programme that improves retention",
        "The impact of overtime",
        "the effect of travel",
        "satisfaction affects attrition",
        "This explains attrition",
        "why employees leave",
        "the main reasons for leaving",
        "people left because they were underpaid",
        "a key determinant",
    ],
)
def test_causal_wording_is_flagged(text: str) -> None:
    assert audit.scan_text(text), text


@pytest.mark.parametrize(
    "text",
    [
        "Overtime is associated with higher attrition.",
        "Employees who work overtime left more often (31% vs 10%).",
        "odds ratio 6.75 (95% CI 4.66–9.77), effect sizes by Cramér's V",
        'The rule forbids "overtime causes attrition" and `drives`.',
        "observed attrition risk",
        "a causal-language audit",
    ],
)
def test_associational_wording_passes(text: str) -> None:
    assert audit.scan_text(text) == [], text


def test_repository_wording_passes_the_audit() -> None:
    res = audit.run()
    assert res["passed"], res["findings"]
    assert any(f.startswith("docs/") for f in res["files"])
