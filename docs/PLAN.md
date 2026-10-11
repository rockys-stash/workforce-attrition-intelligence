# Plan

Written before the data were analysed; changes made afterwards are in [DECISIONS](DECISIONS.md).

## Goal

A workforce analytics system that finds which employee characteristics are *associated* with
attrition: employee records → SQL data model → data checks → exploratory analysis → statistical
tests → segmentation → an interpretable model of observed attrition → BI dashboard, with a report
whose wording has passed a causal-language audit. One command reproduces everything; every figure
on the dashboard is computed.

## Data

IBM HR Analytics Employee Attrition & Performance: 1,470 employees, 35 columns, one row per
employee with an attrition flag. It is a **fictional** dataset created by IBM data scientists
(stated in its Kaggle description), licensed ODbL (database) and DbCL (contents), redistributed in
IBM's `employee-attrition-aif360` repository. No public real-employer dataset with these variables
exists under an open licence; results therefore describe this synthetic workforce, not any real
company, and say so.

Coverage of the specified variables: department, salary (monthly income), tenure (years at
company), age, job level, overtime, performance (rating), promotion history (years since last
promotion), job satisfaction, workload (overtime, business travel and work-life balance as proxies;
there are no hours or output measures).

## What can and cannot be claimed

The data are a single cross-section: each employee's attributes and whether they left. There is no
time order between a characteristic and leaving, no intervention and no natural experiment. So:

- Every result is an association: "Overtime is associated with higher attrition",
  never "overtime causes attrition", "drives", "leads to", "reduces" or "impact".
- The model estimates *observed attrition risk*: how much an employee's profile resembles those who
  left. It is not a forecast of who will leave and not an estimate of what a policy would change.
- An automated audit checks every document, the generated results and the dashboard's text for
  causal wording, and CI fails if it finds any.

## Questions and hypotheses (written before the analysis)

1. What is the attrition rate overall and by department, role and job level?
   *H1: rates differ by department, with Sales highest.*
2. How is attrition associated with pay, tenure, age, overtime, performance, promotion and
   satisfaction? *H2: overtime, low job level, low income, short tenure and young age are each
   associated with higher attrition; performance rating is not.*
3. Do associations survive adjustment for the others? *H3: overtime remains associated with
   attrition after adjusting for job level, income, tenure and age; the income association shrinks
   once job level is in the model, because the two are strongly related.*
4. Are there distinct employee segments, and do their attrition rates differ?
5. How well does an interpretable model separate leavers from stayers, and how much accuracy does
   interpretability cost against a flexible model? *H4: logistic regression is within 0.03 AUROC
   of gradient boosting on held-out data.*
6. Is the model equally well calibrated across gender and age groups?

## Analysis plan

- **SQL** (DuckDB): staging with types and decoded labels; data checks (missing values, duplicates,
  ranges, constant columns, internal consistency); a star model (`fact_employee` with department,
  role, band dimensions); one SQL file per measure.
- **Descriptive**: attrition rate with Wilson 95% intervals by every specified variable and by
  salary, tenure and age bands.
- **Tests**: chi-square with Cramér's V for categorical factors, Mann–Whitney U with rank-biserial
  correlation for numeric ones; Holm correction across all tests.
- **Stratification**: overtime within job level (Mantel–Haenszel odds ratio) to show how an
  association changes with adjustment.
- **Segmentation**: k-means on standardised workforce characteristics (k by silhouette); attrition
  rate per segment, described as a profile, not an explanation.
- **Model**: logistic regression on a pre-specified feature set. Gender and marital status are left
  out of the risk model and used only to check it (fairness). Stratified 75/25 split, seed fixed;
  model choices (regularisation strength) by 5-fold cross-validation on the training part; the test
  part scored once. Baselines: prevalence only, overtime only. Reference: gradient boosting.
  Metrics: AUROC, average precision, Brier score, calibration intercept and slope, with bootstrap
  intervals. Adjusted odds ratios with 95% intervals from an unpenalised fit on all employees.
- **Risk segments**: bands of out-of-fold predicted risk, profiled in aggregate. The dashboard shows
  no per-employee scores.

## Dashboard

Executive Overview → Attrition → Departments → Compensation → Tenure → Risk Segments, plus Data &
method (with the audit result). Enterprise BI style, light and dark, accessible.

## Power BI

Same contingency as Project 13: if Power BI Desktop cannot run here, deliver the SQL and Python
layer, the exported model, written DAX measures and the equivalent web dashboard, and mark the
`.pbix` pending. No mocked Power BI screenshots.

## Acceptance

Analysis and model executed and validated; dashboard figures computed; the causal-language audit
passes; one command reproduces everything.
