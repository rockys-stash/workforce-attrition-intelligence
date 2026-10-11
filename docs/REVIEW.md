# Internal review board

Reviewed 2026-10-11 against [REPORT.md](REPORT.md) and the result directory it cites
(`results/20261011T003047Z-42a5167`, clean commit `42a5167`). **Overall: pass, with the Power BI
build pending.**

| Reviewer | Verdict | Required fixes |
|---|---|---|
| Statistics | Pass | Fixed during review: one overstated sentence about overtime within job levels |
| Wording (causal-language audit) | Pass | Fixed during review: four phrases (D12), one DAX note |
| Engineering | Pass | None open |
| QA | Pass | None open |
| Security and privacy | Pass | None open |
| UX | Pass | Fixed during review: rate bars misaligned between rows; forest plot labels oversized |
| Release | Pass, Power BI pending | The `.pbix` cannot be built here (D13) |

## Statistics reviewer

- Every figure in the report is in `docs/generated/results.md`, rendered from the result files.
- Hypotheses were committed before any analysis (`05238b3`); later PLAN edits are wording only
  (D12, verifiable with `git diff 05238b3 -- docs/PLAN.md`). Each hypothesis is reported as
  supported, weakly supported or not, including H1, which the data only weakly support.
- Rates carry Wilson intervals; 27 tests are Holm-corrected; the model's test set was scored once
  after C was chosen by cross-validation on the training part; model metrics carry bootstrap
  intervals and the out-of-fold AUROC agrees with the test AUROC.
- Collinearity is reported, not hidden (income and job level VIF ≈ 11), and the report says the
  model cannot attribute their shared association to either.
- The stock-option and marital-status confound was found and handled with a sensitivity model and
  a second fairness table (D6); the boosting reference is labelled untuned (D7).
- Fixed during review: the report said the overtime association "holds within every job level";
  the intervals at levels 3–5 include 1, so it now says the odds ratio is above 1 at every level
  and clearly so at levels 1 and 2.

## Wording reviewer

- `wfintel audit` scans README, every document, the generated results, the Power BI notes, the
  dashboard source and each run's recommendation texts against 17 causal-wording rules; it passes
  with 0 findings and runs in CI and in `make all`.
- During the build it flagged four phrases (D12) and, later, "results in" in a DAX note
  (reworded). The dashboard header now reads "Associations only".
- The data's fictional nature is stated in the dashboard header, the overview, the method page,
  the README, DATASET and the report.

## Engineering reviewer

- `make all` checks the CSV's SHA-256, runs SQL (DuckDB) and Python, writes a versioned result
  with config, commit, dirty flag, package versions and input hashes, renders the results and runs
  the audit; `LATEST` moves only for a clean run.
- SQL is in plain files, placeholders filled from the config only; factor names pass a whitelist.
- ruff, ruff format, mypy strict, ESLint and `tsc`. CI runs unit tests, the audit, a real-data
  smoke run into `results/scratch`, the dashboard build, `npm audit` and the browser tests.

## QA reviewer

- 38 SQL, statistics, model, audit and API tests and 26 browser tests pass (`make test`,
  `make test-ui`). Unit tests run the SQL on 800 synthetic employees with planted issues and check
  each data check's count, the intervals, the tests, the model and the audit rules (including the
  quoted-text exemption).
- Browser tests cover every page at desktop and mobile width, the characteristic picker, the
  fairness toggle, the absence of individual scores, the link from the overview, the fictional-data
  and Power BI labels, keyboard navigation and axe-core (WCAG 2.1 A/AA and best practice) in both
  themes.
- 21 screenshots from the running dashboard (7 pages × desktop, desktop dark, mobile).
- **Fresh clone** (2026-10-11): a new clone of `78e1993` ran `make setup test lint all test-ui`
  and passed. `docs/generated/results.md` was identical to the committed file except the
  provenance line and the number of files the audit scanned (28 → 30, because the report and
  README were added after the committed run).

## Security and privacy reviewer

- Read-only API with rate limiting and security headers; `wfintel serve` refuses a non-loopback
  bind without `WFINTEL_TOKEN`; topic names are checked against a fixed list.
- The data are fictional. Even so, nothing below group level leaves the pipeline: no employee
  numbers, records or individual risk scores are served (D11). Gender and marital status are used
  only to check the model.

## UX reviewer

- Seven pages matching the specified dashboard order plus Data & method; every chart has a text
  alternative; tables scroll sideways on phones.
- Fixed during review: each rate-bar row sized its own columns, so the bars and the dashed
  overall-rate line did not line up between rows (now a shared grid); the forest plot scaled its
  labels to the page width (now capped).
- Known limit: the tenure chart is small on phones; its numbers are in the text alternative and
  the table views.

## Release reviewer

- README, PLAN, DESIGN, METRICS, DATASET, DECISIONS, REPORT and this review are present.
- **Power BI: pending.** The model is exported to Parquet, the relationships and DAX measures are
  written (`powerbi/`); no `.pbix` file and no Power BI screenshots exist, and none are mocked.
