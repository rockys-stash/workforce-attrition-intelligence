"""An interpretable model of observed attrition risk, validated on held-out employees.

"Risk" here means how closely an employee's recorded profile resembles the profiles of employees
who left, in a single cross-section. It is not a forecast of future leaving and not an estimate of
what changing any characteristic would do.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

LABEL = {
    "age": "Age (per 10 years)", "monthly_income": "Monthly income (per 1,000)", "job_level": "Job level (per level)",
    "years_at_company": "Years at the company (per 5 years)", "years_in_current_role": "Years in current role (per 5 years)",
    "years_since_last_promotion": "Years since last promotion (per 5 years)",
    "years_with_curr_manager": "Years with current manager (per 5 years)",
    "total_working_years": "Total working years (per 10 years)", "num_companies_worked": "Previous employers (per employer)",
    "distance_from_home": "Distance from home (per 10 units)", "percent_salary_hike": "Last salary rise (per 5 points)",
    "training_times_last_year": "Trainings last year (per training)", "stock_option_level": "Stock option level (per level)",
    "education": "Education level (per level)", "job_satisfaction": "Job satisfaction (per scale point)",
    "environment_satisfaction": "Environment satisfaction (per scale point)",
    "relationship_satisfaction": "Relationship satisfaction (per scale point)",
    "job_involvement": "Job involvement (per scale point)", "work_life_balance": "Work-life balance (per scale point)",
    "performance_rating": "Performance rating (outstanding vs excellent)", "overtime": "Works overtime (yes vs no)",
}  # fmt: skip
# Natural units for the odds ratios: one unit of the scaled column equals this many raw units.
UNIT = {"age": 10, "monthly_income": 1000, "years_at_company": 5, "years_in_current_role": 5,
        "years_since_last_promotion": 5, "years_with_curr_manager": 5, "total_working_years": 10,
        "distance_from_home": 10, "percent_salary_hike": 5}  # fmt: skip


def features(cfg: dict[str, Any]) -> tuple[list[str], list[str]]:
    m = cfg["model"]
    return list(m["numeric"]) + list(m["ordinal"]) + list(m["binary"]), list(m["categorical"])


def design(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    num, cat = features(cfg)
    x = df[num + cat].copy()
    for c in num:
        x[c] = x[c].astype(float)
    return x


def logistic(cfg: dict[str, Any], c: float) -> Pipeline:
    num, cat = features(cfg)
    pre = ColumnTransformer([("num", StandardScaler(), num),
                             ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), cat)])  # fmt: skip
    return Pipeline([("pre", pre), ("clf", LogisticRegression(C=c, max_iter=5000))])


def overtime_only() -> Pipeline:
    pre = ColumnTransformer([("ot", "passthrough", ["overtime"])])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=1000))])


def boosting(cfg: dict[str, Any], seed: int) -> Pipeline:
    num, cat = features(cfg)
    pre = ColumnTransformer([("num", "passthrough", num),
                             ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat)])  # fmt: skip
    clf = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=200, max_depth=3, random_state=seed)
    return Pipeline([("pre", pre), ("clf", clf)])


def calibration(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """Calibration intercept (mean offset, slope fixed at 1) and slope, on the logit scale."""
    import statsmodels.api as sm

    lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    slope = sm.GLM(y, sm.add_constant(lp), family=sm.families.Binomial()).fit().params[1]
    intercept = sm.GLM(y, np.ones_like(lp), family=sm.families.Binomial(), offset=lp).fit().params[0]
    return float(intercept), float(slope)


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    out = {"brier": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)))}
    if len(np.unique(p)) > 1:
        ci, cs = calibration(y, p)
        out |= {"auroc": float(roc_auc_score(y, p)), "average_precision": float(average_precision_score(y, p)),
                "calibration_intercept": ci, "calibration_slope": cs}  # fmt: skip
    else:
        out |= {"auroc": 0.5, "average_precision": float(y.mean()), "calibration_intercept": float("nan"),
                "calibration_slope": float("nan")}  # fmt: skip
    return out


def bootstrap(y: np.ndarray, preds: dict[str, np.ndarray], n: int, seed: int) -> dict[str, Any]:
    """Percentile intervals for AUROC, AP and Brier of each model, and paired AUROC differences."""
    rng = np.random.default_rng(seed)
    names = list(preds)
    draws: dict[str, dict[str, list[float]]] = {m: {"auroc": [], "average_precision": [], "brier": []} for m in names}
    diff: dict[str, list[float]] = {m: [] for m in names if m != "logistic"}
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        auc = {}
        for m in names:
            p = preds[m][i]
            auc[m] = roc_auc_score(y[i], p) if len(np.unique(p)) > 1 else 0.5
            draws[m]["auroc"].append(auc[m])
            draws[m]["average_precision"].append(average_precision_score(y[i], p))
            draws[m]["brier"].append(brier_score_loss(y[i], p))
        for m in diff:
            diff[m].append(auc["logistic"] - auc[m])

    def ci(v: list[float]) -> list[float]:
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]

    return {"models": {m: {k: ci(v) for k, v in d.items()} for m, d in draws.items()},
            "auroc_diff_logistic_minus": {m: {"diff": float(np.mean(v)), "ci": ci(v)} for m, v in diff.items()}}  # fmt: skip


def choose_c(x: pd.DataFrame, y: np.ndarray, cfg: dict[str, Any]) -> tuple[float, list[dict[str, float]]]:
    m = cfg["model"]
    cv = StratifiedKFold(n_splits=m["cv_folds"], shuffle=True, random_state=m["seed"])
    grid = []
    for c in m["c_grid"]:
        p = cross_val_predict(logistic(cfg, c), x, y, cv=cv, method="predict_proba")[:, 1]
        grid.append({"c": float(c), "log_loss": float(log_loss(y, p)), "auroc": float(roc_auc_score(y, p))})
    best = min(grid, key=lambda g: g["log_loss"])
    return best["c"], grid


def odds_ratios(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    """Adjusted odds ratios (unpenalised logistic regression on every employee), in natural units."""
    import statsmodels.api as sm

    num, cat = features(cfg)
    x = df[num].astype(float).copy()
    for c, u in UNIT.items():
        if c in x:
            x[c] = x[c] / u
    x["performance_rating"] = (df["performance_rating"] == 4).astype(float)
    ref = {}
    for c in cat:
        top = df[c].value_counts().idxmax()
        ref[c] = str(top)
        d = pd.get_dummies(df[c], prefix=c, dtype=float).drop(columns=f"{c}_{top}")
        x = pd.concat([x, d], axis=1)
    fit = sm.Logit(df["left_company"].astype(float), sm.add_constant(x)).fit(disp=0, maxiter=200)
    ci = fit.conf_int()
    rows = []
    for name in x.columns:
        base = next((c for c in cat if name.startswith(c + "_")), None)
        label = LABEL.get(
            name, f"{base.replace('_', ' ').capitalize()}: {name[len(base) + 1 :]} vs {ref[base]}" if base else name
        )
        rows.append({"term": name, "label": label, "group": "category" if base else "numeric",
                     "odds_ratio": float(np.exp(fit.params[name])), "ci": [float(np.exp(ci.loc[name, 0])), float(np.exp(ci.loc[name, 1]))],
                     "p": float(fit.pvalues[name])})  # fmt: skip
    # Variance inflation factors of the numeric terms: how entangled each is with the others.
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    xv = sm.add_constant(x[num].to_numpy(float))
    vif = {c: float(variance_inflation_factor(xv, i + 1)) for i, c in enumerate(num)}
    return {"terms": rows, "reference_levels": ref, "n": int(fit.nobs), "pseudo_r2": float(fit.prsquared),
            "converged": bool(fit.mle_retvals["converged"]), "vif": vif}  # fmt: skip


def run(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    m = cfg["model"]
    seed = int(m["seed"])
    x, y = design(df, cfg), df["left_company"].to_numpy(int)
    x_tr, x_te, y_tr, y_te, _, i_te = train_test_split(
        x, y, np.arange(len(y)), test_size=m["test_size"], stratify=y, random_state=seed
    )
    c, grid = choose_c(x_tr, y_tr, cfg)
    models = {
        "prevalence": None,
        "overtime_only": overtime_only(),
        "logistic": logistic(cfg, c),
        "boosting": boosting(cfg, seed),
    }
    preds: dict[str, np.ndarray] = {}
    for name, est in models.items():
        if est is None:
            preds[name] = np.full(len(y_te), y_tr.mean())
        else:
            est.fit(x_tr, y_tr)
            preds[name] = est.predict_proba(x_te)[:, 1]
    test = {name: metrics(y_te, p) for name, p in preds.items()}
    boot = bootstrap(y_te, preds, int(m["bootstrap"]), seed)
    # Out-of-fold risk for every employee (same specification and C), for segments and the fairness check.
    cv = StratifiedKFold(n_splits=m["cv_folds"], shuffle=True, random_state=seed)
    oof = cross_val_predict(logistic(cfg, c), x, y, cv=cv, method="predict_proba")[:, 1]
    # Standardised coefficients of the validated (penalised) model, fitted on the training part.
    lr = models["logistic"]
    assert lr is not None
    names = [n.split("__", 1)[1] for n in lr.named_steps["pre"].get_feature_names_out()]
    coef = sorted(({"term": n, "coef": float(b)} for n, b in zip(names, lr.named_steps["clf"].coef_[0], strict=True)),
                  key=lambda r: -abs(r["coef"]))  # fmt: skip
    return {
        "split": {"train": len(y_tr), "test": len(y_te), "train_leavers": int(y_tr.sum()), "test_leavers": int(y_te.sum()),
                  "seed": seed},
        "c_grid": grid, "c": c,
        "test": test, "bootstrap": boot,
        "standardised_coefficients": coef,
        "oof": oof, "test_index": i_te,
    }  # fmt: skip
