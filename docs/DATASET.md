# Dataset

## Source

**IBM HR Analytics Employee Attrition & Performance.** One CSV, one row per employee, 1,470 rows
and 35 columns, with a Yes/No attrition flag (237 Yes).

- **Nature: fictional.** The dataset's Kaggle description states that it is a fictional dataset
  created by IBM data scientists. No result here
  describes a real company or real people.
- **Licence:** Open Database License (database) and Database Contents License (contents), as
  listed on Kaggle (`pavansubhasht/ibm-hr-analytics-attrition-dataset`).
- **Copy used:** `data/source/emp_attrition.csv`, committed, fetched from IBM's public
  `employee-attrition-aif360` repository
  (`https://raw.githubusercontent.com/IBM/employee-attrition-aif360/master/data/emp_attrition.csv`).
- **SHA-256:** `a5c31e38bd7fafc9bc333884eb181b06b41b8e5e488e8f7ccb27199fb3be7659`. `make data`
  checks it; `uv run wfintel data --download` fetches it again and checks the same hash.

Why this dataset: the specification names department, salary, tenure, age, job level, overtime,
performance, promotion history, satisfaction and workload. No openly licensed dataset from a real
employer carries these; this one does (workload only through overtime, business travel and
work-life balance). The cost is that it is synthetic, which every page and document states
([DECISIONS](DECISIONS.md) D1).

## Columns used

| Group | Columns |
|---|---|
| Outcome | `Attrition` (Yes/No) → `left_company` |
| Organisation | `Department` (3), `JobRole` (9), `JobLevel` (1–5) |
| Pay | `MonthlyIncome`, `PercentSalaryHike`, `StockOptionLevel` (0–3) |
| Time | `Age`, `YearsAtCompany`, `YearsInCurrentRole`, `YearsSinceLastPromotion`, `YearsWithCurrManager`, `TotalWorkingYears`, `NumCompaniesWorked` |
| Workload | `OverTime`, `BusinessTravel`, `WorkLifeBalance` (1–4), `DistanceFromHome` |
| Survey scales (1–4) | `JobSatisfaction`, `EnvironmentSatisfaction`, `RelationshipSatisfaction`, `JobInvolvement` |
| Performance | `PerformanceRating` (only 3 and 4 occur) |
| Background | `Education` (1–5), `EducationField`, `TrainingTimesLastYear` |
| Audit only | `Gender`, `MaritalStatus` (not model inputs) |

Decoded labels follow the dataset's documentation (education 1 = Below College … 5 = Doctor;
satisfaction 1 = Low … 4 = Very high; work-life balance 1 = Bad … 4 = Best; performance
3 = Excellent, 4 = Outstanding).

## Not used

- `EmployeeCount`, `Over18`, `StandardHours`: one value for every row (data check 4).
- `DailyRate`, `HourlyRate`, `MonthlyRate`: uncorrelated with monthly income (|r| ≤ 0.03,
  checks 10–12), with no documented meaning; left out of the pay analysis.
- `EmployeeNumber`: an identifier, used only for the duplicate check and stable ordering.

## Quality

No missing values, no duplicate employee numbers, no duplicate records, and no internal
inconsistencies (years in role or since promotion beyond years at the company, and so on). The
counts are recomputed by every run (`sql/02_checks.sql`) and shown on the Data & method page.

## Limits

A single cross-section with no dates: whether a characteristic (a satisfaction score, an overtime
flag) was recorded before or after someone decided to leave is unknown. Satisfaction and
performance are on short ordinal scales. Performance takes only two values. Being synthetic, the
data's joint structure reflects how it was generated, which is undocumented.
