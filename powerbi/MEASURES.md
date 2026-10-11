# Measure definitions

Each measure is defined in SQL (executed; output in `results/LATEST`) and written here in DAX for
the pending Power BI build (**not executed**).

| Measure | Definition | SQL |
|---|---|---|
| Employees | rows of `fact_employee` | `sql/measures/overview.sql` |
| Leavers | Σ `left_company` | `overview.sql`, `attrition_by.sql` |
| Attrition rate | leavers ÷ employees (Wilson interval computed in Python) | `attrition_by.sql` |
| Median monthly income | median of `monthly_income` | `overview.sql`, `compensation.sql` |
| Overtime share | mean of `overtime` | `overview.sql`, `departments.sql` |
| Median income, stayed / left | median of `monthly_income` where `left_company` = 0 / 1 | `compensation.sql` |
| No-stock share | share with `stock_option_level` = 0 | `compensation.sql` |
| Income band range | min and max income per `income_band` | `income_bands.sql` |
| Attrition by completed years | employees, leavers, rate per `years_at_company` | `tenure_curve.sql` |
| Role profile | rate, median income, overtime, mean job satisfaction, median tenure, mean level per role | `departments.sql` |

```dax
Employees = COUNTROWS ( fact_employee )
Leavers = SUM ( fact_employee[left_company] )
Attrition Rate = DIVIDE ( [Leavers], [Employees] )
Overall Attrition Rate = CALCULATE ( [Attrition Rate], ALL ( fact_employee ) )
Median Monthly Income = MEDIAN ( fact_employee[monthly_income] )
Overtime Share = AVERAGE ( fact_employee[overtime] )
Median Income Stayed = CALCULATE ( [Median Monthly Income], fact_employee[left_company] = 0 )
Median Income Left = CALCULATE ( [Median Monthly Income], fact_employee[left_company] = 1 )
No Stock Share =
    DIVIDE (
        CALCULATE ( [Employees], fact_employee[stock_option_level] = 0 ),
        [Employees]
    )
Mean Job Satisfaction = AVERAGE ( fact_employee[job_satisfaction] )
Median Tenure = MEDIAN ( fact_employee[years_at_company] )
Rate Above Overall = [Attrition Rate] - [Overall Attrition Rate]
```

The Wilson interval in DAX (z = 1.96), for a visual that needs it:

```dax
Wilson Low =
VAR n = [Employees]
VAR p = [Attrition Rate]
VAR z = 1.96
RETURN DIVIDE ( p + z * z / ( 2 * n ) - z * SQRT ( p * ( 1 - p ) / n + z * z / ( 4 * n * n ) ), 1 + z * z / n )
Wilson High =
VAR n = [Employees]
VAR p = [Attrition Rate]
VAR z = 1.96
RETURN DIVIDE ( p + z * z / ( 2 * n ) + z * SQRT ( p * ( 1 - p ) / n + z * z / ( 4 * n * n ) ), 1 + z * z / n )
```

Statistical tests, the model, odds ratios, risk bands, segments and fairness tables are not DAX
measures; they come from `results/LATEST/attrition.json` and `risk.json`.
