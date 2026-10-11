# Report: which employee characteristics are associated with attrition?

Numbers are quoted from [generated/results.md](generated/results.md), rendered from
`results/20261011T003047Z-42a5167` (clean commit `42a5167`). Intervals are 95%: Wilson for rates,
bootstrap for model metrics, Wald for odds ratios.

**Read this first.** The data are IBM's *fictional* HR attrition dataset: 1,470 synthetic
employees, one snapshot, a flag for who left. Every finding describes that synthetic workforce,
and every finding is an association. Nothing here shows what would happen if a policy changed.

## 1. Set-up

Employee records are loaded into DuckDB, checked (12 checks: no missing values, duplicates or
internal inconsistencies; three constant columns and three unexplained "rate" columns set aside),
modelled as a star (one fact row per employee, department, role and level dimensions), and
measured in SQL. Python adds Wilson intervals, 27 association tests with Holm correction, a
Mantel–Haenszel stratification, k-means segmentation, and an interpretable logistic model compared
with two baselines and gradient boosting. A causal-language audit scans every document, the
dashboard source and the run's recommendations; it passes (0 findings in 28 files and texts) and
runs in CI.

Overall, 237 of 1,470 employees left: **16.1%**.

## 2. Results by question

### Q1. Attrition by department, role and level (H1: Sales highest)

| Department | Employees | Rate (95% CI) |
|---|---:|---:|
| Sales | 446 | 20.6% (17.1–24.6%) |
| Human Resources | 63 | 19.0% (11.2–30.4%) |
| Research & Development | 961 | 13.8% (11.8–16.2%) |

Sales has the highest point estimate, as hypothesised, but its interval overlaps Human Resources',
and the department association is weak (Cramér's V 0.09, Holm p = 0.045). **H1 is weakly
supported.** Roles and levels separate far more: Sales Representatives 39.8% (29.9–50.5%) against
Research Directors 2.5%; job level 1 26.3% against 4.7–14.7% for levels 2–5 (V 0.22).

### Q2. Pay, tenure, age, overtime, performance, promotion, satisfaction (H2)

- **Overtime:** 30.5% with overtime against 10.4% without (V 0.25, the strongest single association).
- **Job level and income:** lowest income quintile 31.3%, highest 9.2%; leavers' median income
  3,202 against 5,204 (rank-biserial r −0.31).
- **Tenure:** 34.9% in the first two years (0–1 completed years) against 6.7% at 11–20 years.
- **Age:** 35.8% at 18–25, 9.2% at 36–45.
- **Performance rating:** 16.1% (Excellent) and 16.4% (Outstanding); V 0.00, Holm p = 1.00.
- **Promotion:** years since last promotion is not significant on its own (Holm p = 0.33).
- **Satisfaction:** low job satisfaction 22.8% against very high 11.3%; bad work-life balance
  31.2%.

18 of 27 tests are significant after Holm correction. **H2 is supported** for every named
characteristic: overtime, low level, low income, short tenure and young age are associated with
higher attrition, and performance rating is not.

### Q3. Do associations survive adjustment? (H3)

- **Overtime within job level.** Crude odds ratio 3.77 (2.83–5.03); pooled within job levels
  (Mantel–Haenszel) 4.05 (3.01–5.46), with no clear difference between levels (p = 0.084).
  Holding all model characteristics fixed, the odds ratio is 6.75 (4.66–9.77).
- **Income once job level is in.** Adjusted odds ratio per 1,000 of monthly income 1.01
  (0.86–1.18); job level 1.00 (0.54–1.84). Their variance inflation factors are 10.8 and 11.2: the
  two are so strongly related that the model cannot attribute the association to either.

**H3 is supported**: overtime's association remains (and grows) after adjustment, and income's
shrinks to nothing once job level is included. The reading is "pay and level together", not
"pay does not matter".

Other adjusted associations, all within this dataset: years since last promotion 2.27 per 5 years
(1.52–3.39), frequent business travel 2.39 (1.59–3.60), previous employers 1.21 per employer,
distance from home 1.56 per 10 units; each satisfaction and involvement scale point 0.58–0.78.
Years at the company is 1.57 per 5 years once years in role, with manager and total working years
are held fixed: the sign flips from the raw comparison because those four measures move together.

### Q4. Segments

k-means on 12 standardised characteristics chose **k = 2** (silhouette 0.28, falling for every
larger k; stable across seeds, adjusted Rand 0.94–1.00). The segments split by seniority: 1,167
employees with lower income, level and experience (17.9% left, 15.8–20.2%) and 303 senior
employees (9.2%, 6.5–13.0%). Overtime is 28% in both, so the segmentation does not isolate the
strongest association; the model does.

### Q5. Separation and the cost of interpretability (H4)

| Model (368 test employees, 59 leavers) | AUROC (95% CI) | Average precision | Brier |
|---|---:|---:|---:|
| Prevalence only | 0.500 | 0.160 | 0.135 |
| Overtime only | 0.658 (0.587–0.729) | 0.244 | 0.126 |
| **Logistic regression** | **0.839 (0.770–0.902)** | **0.631** | **0.092** |
| Gradient boosting (untuned reference) | 0.797 (0.721–0.864) | 0.574 | 0.100 |

Logistic minus boosting: +0.043 (0.002 to 0.086). Out-of-fold AUROC on all employees 0.834;
calibration slope 0.97. **H4 (within 0.03) is not just met: the interpretable model is ahead**,
though the boosting model was not tuned (D7) and the interval nearly reaches zero. Refitted
without stock options the logistic model reaches 0.824.

Out-of-fold risk bands are well ordered: low (< 10%) 4.7% observed, moderate 12.8%, elevated
18.1%, high (≥ 35%) 61.6%. The high band holds 130 of the 237 leavers in 211 employees, and 69% of
it works overtime.

### Q6. Is the model equally good across groups?

| Group | Observed | Mean predicted | AUROC |
|---|---:|---:|---:|
| Female / Male | 14.8% / 17.0% | 17.1% / 15.8% | 0.83 / 0.84 |
| Age 18–25 / 46+ | 35.8% / 12.5% | 30.9% / 9.2% | 0.85 / 0.70 |
| Married / Single | 12.5% / 25.5% | 14.1% / 22.4% | 0.75 / 0.86 |

Ranking quality is similar by gender; it is weaker for employees aged 46+ and for married
employees, and risk is under-predicted for the youngest and oldest groups. Single employees all
have stock option level 0, so the model reaches marital status through stock options. Removing
stock options does not help: singles' mean prediction falls to 17.9% against 25.5% observed (D6).

## 3. What this means (for this fictional workforce)

1. **Overtime** is the clearest pattern: about three times the attrition, with an odds ratio above
   1 at every job level (clearly so at levels 1 and 2, where most employees are). Where overtime is concentrated is worth reviewing; whether reducing it would
   change attrition is not something these data can show.
2. **Entry level, low pay and short tenure come together.** Level 1 holds 143 of the 237 leavers;
   pay and level cannot be separated statistically, so pay should be evaluated, not assumed to be
   the lever.
3. **The first two years** account for 32% of leavers.
4. **Sales Representatives** (40%) stand out even after adjusting for level and the rest
   (odds ratio 2.72 against Sales Executives).
5. **Satisfaction scores** are associated with attrition but were recorded once, undated; they may
   have been measured after a decision to leave.

The six recommendations on the dashboard follow these findings; each states its evidence and that
no change has been tested.

## 4. Threats to validity

- **Synthetic data.** The joint distribution reflects how IBM generated it, which is not
  documented. Findings may not hold in any real organisation.
- **One cross-section.** No ordering in time between characteristics and leaving; reverse
  direction (a leaver's survey answers, overtime in a notice period) cannot be excluded.
- **Collinearity.** Income, level, age and the tenure measures move together; individual
  adjusted odds ratios for them are fragile.
- **Small groups.** Several roles and levels have under 100 employees; intervals are wide.
- **Untuned reference model,** and a single 75/25 split for the test metrics (the out-of-fold
  AUROC, 0.834, agrees).
- **Power BI** is pending; the web dashboard is the built BI layer.

## 5. Reproducibility

`make all` checks the CSV's hash, runs SQL, statistics and models into
`results/<UTC>-<sha7>` with provenance, renders the generated results and runs the audit; `LATEST`
moves only on a clean tree. The run takes about 51 seconds on one CPU core. Fresh-clone checks
are recorded in [REVIEW.md](REVIEW.md).
