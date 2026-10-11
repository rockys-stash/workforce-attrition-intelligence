# Decisions

Made during the build, after `docs/PLAN.md`; each says what changed and why.

**D1. A fictional dataset, said everywhere.** The IBM HR attrition data are synthetic. Openly
licensed employee records from a real employer with the specified variables do not exist (public
HR datasets are either synthetic, scraped without a licence, or lack pay and tenure). Rather than
use a dataset of unclear origin, the project uses the well-documented synthetic one and states its
nature in the dashboard header, every page that reports numbers, the report and the README.

**D2. DuckDB for the SQL layer.** As in the companion retail project: an embedded engine, the same
SQL in CI and locally, and a Parquet star model for Power BI.

**D3. Constant and unexplained columns left out.** `EmployeeCount`, `Over18` and `StandardHours`
take one value; the daily, hourly and monthly "rates" are uncorrelated with monthly income
(|r| ≤ 0.03) and undocumented. They are excluded from analysis; both facts are data checks that
every run recomputes.

**D4. Job role, not department, in the model.** Each role sits in one department (Manager appears
in all three), so department adds almost nothing once role is known and makes the coefficients
unstable. Department is analysed descriptively and tested; role enters the model.

**D5. Gender and marital status only audit the model.** They are protected or sensitive
characteristics; the model does not use them, and they define the groups of the fairness table.
Age is a model input (it is a recorded workforce characteristic named in the specification) and
also a fairness group, so its row shows whether the model treats age groups consistently.

**D6. Stock options and marital status are confounded: a sensitivity model.** Found while
analysing the first run: all 470 single employees have stock option level 0. A model that uses
stock options therefore partly encodes marital status. Kept as specified, and refitted without
stock option level: test AUROC 0.839 → 0.824, and the fairness table is shown for both models.
Without stock options, singles' mean predicted risk falls further below their observed rate
(17.9% vs 25.5%), so removing the variable does not make the model fairer by that measure.

**D7. Gradient boosting is a reference, untuned.** Histogram gradient boosting with fixed settings
(learning rate 0.05, 200 iterations, depth 3) shows what a flexible model reaches without effort.
It was not tuned, so "logistic regression beats boosting" means only that a tuned boosting model
would be needed to show otherwise. On 1,470 rows a gain from tuning is plausible but small.

**D8. Odds ratios from an unpenalised fit on all employees.** The prediction model is
regularised and fitted on the training part; coefficients for interpretation come from a separate
unpenalised logit on everyone, in natural units (age per 10 years, income per 1,000), with VIFs
reported because income and job level are collinear (VIF ≈ 11).

**D9. Overtime stratified by job level only.** The plan named one stratification to show how an
association moves with adjustment. Job level is the strongest correlate of both pay and overtime
exposure here; the full adjustment is the odds-ratio table.

**D10. k-means picks k = 2.** Silhouette is highest at k = 2 (0.28) and falls steadily; the two
segments split mainly by seniority (age, level, income). Reported as found, with the scores for
every k, rather than forcing more segments for a richer story.

**D11. No per-employee scores anywhere.** Out-of-fold risk is computed for every employee but only
aggregated (bands, groups) leaves the pipeline. The API has no endpoint that returns an
individual's record or risk.

**D12. Wording changed for the audit, content unchanged.** After the audit was written, its first
run flagged three passages: two in PLAN (a quoted example of forbidden wording split across a
line break, so the quote was not recognised; and "a profile, not a cause"), two in the dashboard
and recommendation texts ("effect of acting", "record why people leave"), and later the header
label "Associations, not causes", now "Associations only". The PLAN lines
were rewrapped and "not a cause" became "not an explanation"; the dashboard texts were reworded.
The PLAN's questions, hypotheses and analysis plan are unchanged since commit `05238b3`
(`git diff 05238b3 -- docs/PLAN.md` shows only these two lines).

**D13. Power BI pending.** Power BI Desktop needs Windows and an interactive session, neither
available here. The model is exported as Parquet, relationships and DAX measures are written in
`powerbi/`, and the web dashboard is the equivalent. No `.pbix` and no Power BI screenshots exist.
