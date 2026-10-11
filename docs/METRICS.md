# Metrics

Population: all 1,470 employees. Outcome: `left_company` (the dataset's Attrition = Yes). Income
is monthly, in the dataset's own units (no currency is documented).

## Rates

- **Attrition rate** = employees who left ÷ employees, overall or in a group, with a **Wilson
  95% interval**. A group is drawn in the "above" colour only when its whole interval lies above
  the overall rate.
- **Bands** (`configs/pipeline.yaml`): years at the company 0–1, 2–3, 4–5, 6–10, 11–20, 21+;
  age 18–25, 26–35, 36–45, 46+; years since last promotion 0, 1–2, 3–5, 6+; income in
  quintiles over all employees.
- **Pay position** = monthly income ÷ the median income of the employee's job level − 1; within
  ±10% is "at level median", below −10% "below", above +10% "above".

## Tests

- **Chi-square** test of independence for categorical and ordinal characteristics, effect size
  **Cramér's V** (0 none, 1 complete).
- **Mann–Whitney U** for numeric characteristics, effect size **rank-biserial r** (negative when
  leavers tend to have lower values), with medians for leavers and stayers.
- **Holm** correction across all 27 tests; significant = Holm-adjusted p < 0.05.
- **Mantel–Haenszel** odds ratio of overtime, pooled across job levels, with its 95% interval and
  the Breslow–Day test (statsmodels) of equal odds ratios across levels; the crude odds ratio alongside.

## Model

- **AUROC**: probability that a random leaver gets a higher predicted risk than a random stayer.
- **Average precision**: area under the precision–recall curve (the prevalence is the baseline).
- **Brier score**: mean squared difference between predicted risk and outcome (lower is better).
- **Calibration intercept and slope**: from a logistic regression of the outcome on the logit of
  the predicted risk; perfect calibration is intercept 0, slope 1.
- **Intervals**: 2,000 bootstrap resamples of the 368 test employees; **paired AUROC
  differences** use the same resamples for both models.
- **Out-of-fold**: 5-fold cross-validated predictions on all employees; used for the out-of-fold
  AUROC, the risk bands and the fairness tables.
- **Adjusted odds ratio**: exp(coefficient) from the unpenalised logit on all employees, per the
  stated unit, with a Wald 95% interval. **VIF**: variance inflation factor of each numeric term.

## Segments and fairness

- **k-means**: 12 standardised characteristics (config `segmentation.features`), k = 2…8, chosen
  by silhouette; stability = adjusted Rand index against refits with five other seeds. Segment
  labels name the three characteristics furthest from the average.
- **Risk bands**: out-of-fold predicted risk < 10% low, 10–20% moderate, 20–35% elevated,
  ≥ 35% high.
- **Fairness, per group** (gender, age band, marital status): observed rate, mean predicted risk,
  AUROC within the group, share flagged (high band), true-positive rate (share of the group's
  leavers flagged) and false-positive rate (share of its stayers flagged).

## Audit

17 regular-expression rules for causal wording ("causes", "drives", "leads to", "impact",
"effect of", "due to", "reasons for leaving" …). Text in double quotes, curly quotes or backticks
is skipped, so documents can name the forbidden phrases. Scanned: README, `docs/*.md`,
`docs/generated/*.md`, `powerbi/*.md`, `web/src/` and, inside the pipeline, the run's
recommendation texts.
