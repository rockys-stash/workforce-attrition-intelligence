"""Workforce segments (k-means on recorded characteristics) and risk segments (bands of model risk).

Segments describe groups of employees who look alike. Their attrition rates are observed rates in
each group; they say nothing about why people in a group left.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from wfintel.stats import wilson

SHORT = {
    "age": "age", "monthly_income": "income", "job_level": "job level", "years_at_company": "tenure",
    "years_since_last_promotion": "time since promotion", "total_working_years": "experience",
    "job_satisfaction": "job satisfaction", "environment_satisfaction": "environment satisfaction",
    "work_life_balance": "work-life balance", "overtime": "overtime", "business_travel_frequent": "frequent travel",
    "stock_option_level": "stock options",
}  # fmt: skip


def _matrix(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    x = df.copy()
    x["business_travel_frequent"] = (x["business_travel"] == "Frequently").astype(float)
    return x[cols].astype(float)


def _profile(g: pd.DataFrame) -> dict[str, Any]:
    k, n = int(g["left_company"].sum()), len(g)
    lo, hi = wilson(k, n)
    return {
        "employees": n, "leavers": k, "rate": k / n, "ci": [lo, hi],
        "median_age": float(g["age"].median()), "median_income": float(g["monthly_income"].median()),
        "median_tenure": float(g["years_at_company"].median()), "mean_job_level": float(g["job_level"].mean()),
        "overtime_share": float(g["overtime"].mean()),
        "low_job_satisfaction_share": float((g["job_satisfaction"] == 1).mean()),
        "frequent_travel_share": float((g["business_travel"] == "Frequently").mean()),
        "no_stock_share": float((g["stock_option_level"] == 0).mean()),
        "departments": {str(d): int(c) for d, c in g["department"].value_counts().items()},
    }  # fmt: skip


def kmeans_segments(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    s = cfg["segmentation"]
    cols = list(s["features"])
    z = StandardScaler().fit_transform(_matrix(df, cols))
    lo, hi = s["k_range"]
    scores = {}
    fits = {}
    for k in range(lo, hi + 1):
        km = KMeans(n_clusters=k, n_init=20, random_state=s["seed"]).fit(z)
        scores[k] = float(silhouette_score(z, km.labels_))
        fits[k] = km
    best = max(scores, key=lambda k: scores[k])
    km = fits[best]
    # Stability: agreement between this solution and refits with other seeds.
    ari = [float(adjusted_rand_score(km.labels_, KMeans(n_clusters=best, n_init=20, random_state=s["seed"] + i).fit(z).labels_))
           for i in range(1, 6)]  # fmt: skip
    centres = pd.DataFrame(km.cluster_centers_, columns=cols)
    out: list[dict[str, Any]] = []
    for c in range(best):
        g = df[km.labels_ == c]
        top = pd.Series(centres.loc[c]).abs().sort_values(ascending=False).index[:3]
        words = [("high " if centres.loc[c, f] > 0 else "low ") + SHORT[f] for f in top]
        out.append({"segment": c + 1, "label": ", ".join(words).capitalize(),
                    "centre": {f: float(centres.loc[c, f]) for f in cols}} | _profile(g))  # fmt: skip
    out.sort(key=lambda r: -float(r["leavers"]) / float(r["employees"]))
    for i, r in enumerate(out, 1):
        r["segment"] = i
    return {"k": best, "silhouette": scores, "stability_ari": ari, "features": cols, "segments": out}


RISK_NAMES = ("Low", "Moderate", "Elevated", "High")


def risk_band(p: np.ndarray, bounds: list[float]) -> np.ndarray:
    return np.array([RISK_NAMES[int(np.searchsorted(bounds, v, side="right"))] for v in p])


def risk_segments(df: pd.DataFrame, oof: np.ndarray, cfg: dict[str, Any]) -> dict[str, Any]:
    bounds = list(cfg["model"]["risk_bands"])
    band = risk_band(oof, bounds)
    rows = []
    for i, name in enumerate(RISK_NAMES):
        g = df[band == name]
        if g.empty:
            continue
        lo = 0.0 if i == 0 else bounds[i - 1]
        hi = bounds[i] if i < len(bounds) else 1.0
        rows.append({"band": name, "range": [lo, hi], "mean_predicted": float(oof[band == name].mean())} | _profile(g))
    return {"bounds": bounds, "bands": rows}


def fairness(df: pd.DataFrame, oof: np.ndarray, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Out-of-fold calibration and error rates by group (groups the model does not use, plus age band)."""
    from sklearn.metrics import roc_auc_score

    flag = oof >= cfg["model"]["risk_bands"][-1]
    rows = []
    for attr in cfg["model"]["audit_groups"]:
        for level, idx in df.groupby(attr).indices.items():
            y, p, f = df["left_company"].to_numpy()[idx], oof[idx], flag[idx]
            rows.append({
                "attribute": attr, "group": str(level), "employees": len(idx), "leavers": int(y.sum()),
                "observed_rate": float(y.mean()), "mean_predicted": float(p.mean()),
                "auroc": float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else None,
                "flagged_share": float(f.mean()),
                "true_positive_rate": float(f[y == 1].mean()) if y.sum() else None,
                "false_positive_rate": float(f[y == 0].mean()) if (y == 0).any() else None,
            })  # fmt: skip
    return rows
