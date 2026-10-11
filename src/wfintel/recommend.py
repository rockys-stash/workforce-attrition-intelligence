"""Recommendations generated from the measured associations.

Each rule fires only when its evidence threshold is met, cites the numbers that triggered it, and
states its basis. The data are an observational cross-section (and fictional), so every
recommendation is a place to look and a thing to test, not a predicted outcome.
"""

from __future__ import annotations

from typing import Any

BASIS = "Association in a cross-section of a fictional workforce; no change has been tested here."


def _pct(v: float) -> str:
    return f"{100 * v:.0f}%"


def _level(r: dict[str, Any], factor: str, level: Any) -> dict[str, Any]:
    return next(x for x in r["factors"][factor]["levels"] if x["level"] == level)


def _or(r: dict[str, Any], term: str) -> dict[str, Any] | None:
    return next((t for t in r["model"]["odds_ratios"]["terms"] if t["term"] == term), None)


def _ci(t: dict[str, Any]) -> str:
    return f"{t['odds_ratio']:.2f} (95% CI {t['ci'][0]:.2f}–{t['ci'][1]:.2f})"


def build(r: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    overall = r["kpis"]["rate"]

    ot, no = _level(r, "overtime", 1), _level(r, "overtime", 0)
    mh = r["stratified"][0]["mantel_haenszel"]
    adj = _or(r, "overtime")
    if mh["ci"][0] > 1.5:
        roles = sorted((d for d in r["departments"] if d["employees"] >= 30), key=lambda d: -d["overtime_share"])[:3]
        out.append({
            "area": "Workload", "title": "Review overtime load",
            "finding": f"{_pct(ot['rate'])} of employees who work overtime left, against {_pct(no['rate'])} of those who do not.",
            "evidence": [
                f"Within the same job level the odds of having left are {mh['odds_ratio']:.1f} times as high with overtime "
                f"(Mantel–Haenszel, 95% CI {mh['ci'][0]:.1f}–{mh['ci'][1]:.1f})",
                f"Adjusted for the other model variables, odds ratio {_ci(adj)}" if adj else "",
                "Overtime is most common among " + ", ".join(f"{d['job_role']} ({_pct(d['overtime_share'])})" for d in roles),
            ],
            "action": "Look at how overtime is distributed and whether it is planned; if it is reduced somewhere, compare "
                      "attrition there with comparable teams before drawing conclusions.",
            "basis": BASIS,
        })  # fmt: skip

    t0 = r["factors"]["tenure_band"]["levels"][0]
    if t0["rate"] > 1.5 * overall:
        out.append({
            "area": "Tenure", "title": "Pay attention to the first two years",
            "finding": f"{_pct(t0['rate'])} of employees in their first two years ({t0['label']}) left, against "
                       f"{_pct(overall)} overall.",
            "evidence": [f"{t0['leavers']} of the {r['kpis']['leavers']} leavers ({_pct(t0['leavers'] / r['kpis']['leavers'])}) "
                         f"had under two years at the company",
                         "Years at the company is entangled with age and job level; the tenure page shows both"],
            "action": "Check in with new joiners at fixed points in their first two years and keep exit-interview records, "
                      "so later data can separate tenure from age and level.",
            "basis": BASIS,
        })  # fmt: skip

    l1 = _level(r, "job_level", 1)
    inc = _or(r, "monthly_income")
    below, at = _level(r, "pay_position", "Below level median"), _level(r, "pay_position", "At level median")
    if l1["rate"] == max(x["rate"] for x in r["factors"]["job_level"]["levels"]) and below["rate"] > at["rate"]:
        out.append({
            "area": "Compensation", "title": "Review pay position at entry level",
            "finding": f"Level 1 has the highest attrition ({_pct(l1['rate'])}), and employees paid more than 10% below "
                       f"their level's median left more often ({_pct(below['rate'])}) than those near it ({_pct(at['rate'])}).",
            "evidence": [f"Level 1 holds {l1['leavers']} of {r['kpis']['leavers']} leavers",
                         f"Adjusted for job level, tenure and the other model variables, the odds ratio per 1,000 of monthly "
                         f"income is {_ci(inc)}; pay and level move together (variance inflation "
                         f"{r['model']['odds_ratios']['vif']['monthly_income']:.0f}), so the two are hard to separate" if inc else ""],
            "action": "Compare entry-level pay with the market and within roles; treat pay changes as something to evaluate, "
                      "not as a known lever.",
            "basis": BASIS,
        })  # fmt: skip

    js_low, js_high = _level(r, "job_satisfaction", 1), _level(r, "job_satisfaction", 4)
    env_low = _level(r, "environment_satisfaction", 1)
    if js_low["ci_low"] > js_high["ci_high"]:
        out.append({
            "area": "Engagement", "title": "Use low satisfaction scores as an early signal",
            "finding": f"Employees reporting low job satisfaction left more often ({_pct(js_low['rate'])}) than those "
                       f"reporting very high satisfaction ({_pct(js_high['rate'])}).",
            "evidence": [f"Low environment satisfaction: {_pct(env_low['rate'])} left",
                         "Satisfaction was recorded once, with no date, so it may have been measured after the decision to leave"],
            "action": "Follow up low survey scores with a conversation; re-survey regularly so satisfaction can be "
                      "measured before anyone leaves.",
            "basis": BASIS,
        })  # fmt: skip

    s0 = _level(r, "stock_option_level", 0)
    rest = [x for x in r["factors"]["stock_option_level"]["levels"] if x["level"] != 0]
    rest_rate = sum(x["leavers"] for x in rest) / sum(x["employees"] for x in rest)
    if s0["ci_low"] > rest_rate:
        single = _level(r, "marital_status", "Single")
        sm = next(x for x in r["stock_by_marital"] if x["marital_status"] == "Single")
        single_none = sm["levels"].get("0", 0) / sum(sm["levels"].values())
        out.append({
            "area": "Compensation", "title": "Check who has no stock options",
            "finding": f"{_pct(s0['rate'])} of employees without stock options left, against {_pct(rest_rate)} of those with any.",
            "evidence": [f"{s0['employees']} employees have none",
                         f"{_pct(single_none)} of single employees have no stock options, and {_pct(single['rate'])} of "
                         "single employees left, so stock options and marital status cannot be separated in these data"],
            "action": "Review eligibility rules for stock options before reading anything into this pattern.",
            "basis": BASIS,
        })  # fmt: skip

    roles = sorted((x for x in r["factors"]["job_role"]["levels"] if x["employees"] >= 30), key=lambda x: -x["rate"])
    top = roles[0]
    if top["ci_low"] > overall:
        out.append({
            "area": "Departments", "title": f"Look closely at the {top['label']} role",
            "finding": f"{_pct(top['rate'])} of {top['label']}s left ({top['leavers']} of {top['employees']}), the highest "
                       f"rate of any role with at least 30 employees.",
            "evidence": [f"Next: {roles[1]['label']} {_pct(roles[1]['rate'])}, {roles[2]['label']} {_pct(roles[2]['rate'])}",
                         f"Overall rate {_pct(overall)}"],
            "action": "Review the role's workload, pay position and tenure profile on the Departments page and talk to the team.",
            "basis": BASIS,
        })  # fmt: skip
    for x in out:
        x["evidence"] = [e for e in x["evidence"] if e]
    return out
