# Data model

Built in DuckDB by `sql/01_staging.sql`, `sql/02_checks.sql` and `sql/03_model.sql`; exported to
`data/processed/model/` by `make all`.

| Table | Grain | Key | Main columns |
|---|---|---|---|
| `fact_employee` | one employee | `employee_number` | `left_company` (0/1), `overtime` (0/1), `age`, `monthly_income`, `job_level`, `stock_option_level`, years columns, survey scales, `department_key`, `job_role_key`; derived `income_band` (1–5), `tenure_band`, `age_band`, `promotion_band`, `pay_vs_level_median`, `pay_position`; `gender`, `marital_status` (for audit views only) |
| `dim_department` | one department | `department_key` | `department`, `employees` |
| `dim_job_role` | one role within a department | `job_role_key` | `job_role`, `department`, `employees` |
| `dim_job_level` | one job level (1–5) | `job_level` | `employees`, `median_income`, `min_income`, `max_income` |

Relationships (many-to-one, single direction from dimension to fact):

- `fact_employee[department_key]` → `dim_department[department_key]`
- `fact_employee[job_role_key]` → `dim_job_role[job_role_key]`
- `fact_employee[job_level]` → `dim_job_level[job_level]`

Band orders for sorting: tenure 0–1, 2–3, 4–5, 6–10, 11–20, 21+ yrs; age 18–25, 26–35, 36–45,
46+; promotion 0, 1–2, 3–5, 6+ yrs; pay position below, at, above level median.
