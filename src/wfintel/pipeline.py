"""The one pipeline: employee CSV → SQL model → measures → tests → segments → model → recommendations → audit.

Writes ``results/<UTC>-<sha7>/`` (JSON per dashboard topic + provenance) and moves ``results/LATEST``.
The star schema is exported to ``data/processed/model/`` as Parquet for BI tools.
"""

from __future__ import annotations

import copy
import json
import os
import platform
import subprocess
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any, cast

import duckdb
import numpy as np
import pandas as pd

from wfintel import audit, db, labels, model, recommend, segments, stats
from wfintel.config import config
from wfintel.fetch import sha256, verify
from wfintel.paths import CONFIGS, PROCESSED, RESULTS, ROOT, SQL

MODEL_TABLES = ("fact_employee", "dim_department", "dim_job_role", "dim_job_level")


def git_commit() -> tuple[str, bool]:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "sql", "configs", "data/source"],
                                    cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "0000000", True
    return sha, dirty


def _clean(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 6)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def write(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(_clean(obj), indent=1, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def factor_table(con: duckdb.DuckDBPyConnection, factor: str) -> list[dict[str, Any]]:
    df = stats.with_intervals(db.attrition_by(con, factor))
    natural = labels.order(factor)
    if natural is not None:
        rank = {v: i for i, v in enumerate(natural)}
        df = df.assign(_o=df["level"].map(lambda v: rank.get(v, len(rank)))).sort_values("_o").drop(columns="_o")
    else:
        df = df.sort_values("employees", ascending=False)
    df = df.assign(label=[labels.label(factor, v) for v in df["level"]])
    return db.records(df)


def analyse(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    cfg = config()
    df = db.table(con, "fact_employee")
    r: dict[str, Any] = {}
    r["kpis"] = db.records(db.measure(con, "overview"))[0]
    r["data_checks"] = db.records(db.table(con, "data_checks"))
    r["model_tables"] = db.records(db.measure(con, "model_tables"))
    r["factors"] = {f: {"name": labels.NAMES[f], "levels": factor_table(con, f)} for f in db.FACTORS}
    tests = stats.association_tests(df, cfg["tests"]["alpha"])
    for t in tests:
        t["name"] = labels.NAMES[t["factor"]]
    r["tests"] = sorted(tests, key=lambda t: t["p"])
    r["stratified"] = [stats.stratified(df, "overtime", "job_level")]
    r["departments"] = db.records(db.measure(con, "departments"))
    r["compensation"] = db.records(db.measure(con, "compensation"))
    r["income_bands"] = db.records(db.measure(con, "income_bands"))
    r["tenure_curve"] = db.records(db.measure(con, "tenure_curve"))
    st = pd.crosstab(df["marital_status"], df["stock_option_level"])
    r["stock_by_marital"] = [
        {"marital_status": str(m), "levels": {str(k): int(v) for k, v in row.items()}} for m, row in st.iterrows()
    ]
    r["income_by_level"] = []
    for key, g in df.groupby(["job_level", "left_company"]):
        lvl, y = (int(v) for v in cast(tuple[int, int], key))
        r["income_by_level"].append(
            {"job_level": lvl, "left": y, "incomes": sorted(float(v) for v in g["monthly_income"])}
        )
    fit = model.run(df, cfg)
    oof = fit.pop("oof")
    test_index = fit.pop("test_index")
    r["model"] = fit | {
        "odds_ratios": model.odds_ratios(df, cfg),
        "oof_metrics": model.metrics(df["left_company"].to_numpy(), oof),
    }
    r["model"]["test_size_employees"] = len(test_index)
    # Sensitivity: stock option level is zero for every single employee, so it can stand in for marital
    # status, which the model is meant not to use. Refit without it and compare.
    alt = copy.deepcopy(cfg)
    alt["model"]["numeric"] = [c for c in alt["model"]["numeric"] if c != "stock_option_level"]
    fit_alt = model.run(df, alt)
    r["model"]["without_stock_options"] = {
        "test": fit_alt["test"]["logistic"],
        "c": fit_alt["c"],
        "oof_metrics": model.metrics(df["left_company"].to_numpy(), fit_alt["oof"]),
    }
    r["fairness_without_stock_options"] = segments.fairness(df, fit_alt["oof"], cfg)
    r["risk_segments"] = segments.risk_segments(df, oof, cfg)
    r["segments"] = segments.kmeans_segments(df, cfg)
    r["fairness"] = segments.fairness(df, oof, cfg)
    r["recommendations"] = recommend.build(r)
    return r


def input_hashes() -> dict[str, str]:
    files = [*sorted(SQL.rglob("*.sql")), *sorted(CONFIGS.glob("*.yaml"))]
    return {str(f.relative_to(ROOT)): sha256(f) for f in files}


TOPICS = {
    "overview": ["kpis", "model_tables"],
    "quality": ["data_checks", "model_tables"],
    "attrition": ["factors", "tests", "stratified"],
    "departments": ["departments"],
    "compensation": ["compensation", "income_bands", "income_by_level", "stock_by_marital"],
    "tenure": ["tenure_curve"],
    "risk": ["model", "risk_segments", "segments", "fairness", "fairness_without_stock_options"],
    "recommendations": ["recommendations"],
}


def run(results: Path = RESULTS, export: bool = True) -> Path:
    t0 = time.perf_counter()
    src = verify()
    con = db.build()
    r = analyse(con)
    sha, dirty = git_commit()
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{sha[:7]}"
    out = results / run_id
    out.mkdir(parents=True, exist_ok=False)
    for name, keys in TOPICS.items():
        write(out / f"{name}.json", {k: r[k] for k in keys})
    rec_text = "\n".join(
        " ".join([x["title"], x["finding"], *x["evidence"], x["action"], x["basis"]]) for x in r["recommendations"]
    )
    write(out / "audit.json", audit.run(extra={"recommendations (this run)": rec_text}))
    write(out / "provenance.json", {
        "run_id": run_id, "commit": sha, "dirty": dirty, "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "runtime_seconds": round(time.perf_counter() - t0, 1), "python": platform.python_version(),
        "cpus": os.cpu_count(), "source_sha256": {src.name: sha256(src)},
        "packages": {p: metadata.version(p) for p in ("duckdb", "pandas", "numpy", "scipy", "scikit-learn", "statsmodels")},
        "inputs_sha256": input_hashes(), "config": config(),
    })  # fmt: skip
    if export:
        mdir = PROCESSED / "model"
        mdir.mkdir(parents=True, exist_ok=True)
        for t in MODEL_TABLES:
            con.execute(f"COPY {t} TO '{mdir / (t + '.parquet')}' (FORMAT PARQUET)")
    if not dirty or results != RESULTS:
        (results / "LATEST").write_text(run_id + "\n", encoding="utf-8")
    return out
