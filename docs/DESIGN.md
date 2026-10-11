# Design

## Pipeline

```
make data   data/source/emp_attrition.csv, SHA-256 checked (committed; --download refetches)
make run    DuckDB:  sql/01_staging.sql   typed, decoded staging view
                     sql/02_checks.sql    12 data checks → data_checks; employees table
                     sql/03_model.sql     fact_employee (bands, pay position) + dim_department,
                                          dim_job_role, dim_job_level
                     sql/measures/*.sql   attrition_by (one factor), overview, departments,
                                          compensation, income_bands, tenure_curve, model_tables
            Python:  stats.py      Wilson intervals, chi-square / Mann–Whitney with Holm,
                                   Mantel–Haenszel stratification
                     model.py      logistic regression (C by CV), baselines, gradient boosting,
                                   bootstrap, adjusted odds ratios, VIF, out-of-fold risk
                     segments.py   k-means segments, risk bands, fairness tables
                     recommend.py  six rules over the results → recommendations with evidence
                     audit.py      causal-language audit of docs, Power BI notes, dashboard
                                   source and this run's recommendations
            → results/<UTC>-<sha7>/{overview,quality,attrition,departments,compensation,tenure,
                                    risk,recommendations,audit,provenance}.json + LATEST
            → data/processed/model/*.parquet (star model for BI tools)
make report docs/generated/results.md (every number in the report)
make audit  rerun the audit on the current files; exit 1 on any finding (also in CI)
make serve  read-only API + dashboard on 127.0.0.1:8014
```

Band edges, test settings, model features and the grid are in `configs/pipeline.yaml`. SQL
placeholders (`${tenure_band}` …) are filled from that file by `db.params`, never from user input;
`db.attrition_by` only accepts factor names from a fixed whitelist.

## Model

Pre-specified features (config `model:`): 14 numeric, 6 ordinal, overtime, and three categorical
(job role, business travel, education field), one-hot with the most common level as reference.
Gender and marital status are excluded from the model and used only in the fairness tables.

- Stratified 75/25 split (seed 0); C chosen by 5-fold cross-validated log loss on the training
  part; the test part scored once.
- Baselines: prevalence only, overtime only. Reference: gradient boosting (fixed, untuned settings;
  D7).
- 2,000 bootstrap resamples of the test set for intervals and paired AUROC differences.
- Out-of-fold predictions on all 1,470 employees (5 folds) give each employee a risk estimated
  without their own record; risk bands and fairness use these.
- Adjusted odds ratios: an unpenalised statsmodels logit on all employees, numeric terms in
  natural units (age per 10 years, income per 1,000 …), with variance inflation factors.
- A sensitivity refit without stock option level (D6).

## Provenance

`provenance.json` records run id, commit, dirty flag (changes under `src`, `sql`, `configs`),
runtime, Python and package versions, the CSV's SHA-256, a hash of every SQL and config file and
the config. `LATEST` only moves for runs on a clean tree.

## API

Read-only FastAPI: `GET /api/health`, `GET /api/topics/{topic}` for the ten files of the latest
run (unknown topics are 404). Bearer token (`WFINTEL_TOKEN`) required when set; `wfintel serve`
refuses a non-loopback bind without one; per-client rate limit; CSP and related headers; the
dashboard is served as a single-page app.

## Dashboard (`web/`)

React 18 + TypeScript + Vite in an enterprise BI layout: top bar, section tabs, KPI cards, tables
that scroll sideways on phones, SVG charts with text alternatives, light and dark themes.

| Page | Content |
|---|---|
| Executive overview | headline KPIs, the audit result, the eight groups with the highest attrition, recommendations with evidence |
| Attrition | rate by any of 21 characteristics with intervals; 27 association tests with Holm correction; overtime within job level |
| Departments | rates by department and job role; role profiles (pay, overtime, satisfaction, tenure, level) |
| Compensation | pay by job level for stayers and leavers; income band, pay position, stock options; stock options by marital status |
| Tenure | employees and attrition by completed years; tenure, promotion, age and work-life balance bands |
| Risk segments | model comparison with intervals; adjusted odds ratios (forest plots); risk bands; k-means segments; fairness with and without stock options |
| Data & method | source (fictional), data checks, data model, audit result, Power BI status, definitions |

No page shows a score for an individual employee. Keyboard navigation and axe-core checks run in
both themes at desktop and phone width (`make test-ui`).
