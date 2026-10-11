# Power BI build: pending

**Status: pending.** Power BI Desktop runs only on Windows and needs an interactive session; neither
is available in the environment this project was built in. No `.pbix` file exists in this
repository and no Power BI screenshots have been made. The web dashboard (`web/`) is the
equivalent, built from the same tables and measures.

What is ready for the build:

- **Data model.** `make all` exports the star model to `data/processed/model/*.parquet`
  (`fact_employee`, `dim_department`, `dim_job_role`, `dim_job_level`). Grain and relationships:
  [MODEL.md](MODEL.md).
- **Measures.** DAX for every headline measure, each paired with the SQL that computes it here:
  [MEASURES.md](MEASURES.md). The DAX has not been executed; the SQL has, and its results are in
  `results/LATEST`. Each card should be checked against `docs/generated/results.md`.
- **Pages.** The dashboard's pages map onto the specified report pages: Executive Overview,
  Attrition, Departments, Compensation, Tenure, Risk Segments, plus Data & method.
- **Model results.** Odds ratios, model metrics, risk bands, segments and fairness tables are
  computed in Python; in Power BI they would be loaded from `results/LATEST/risk.json` as static
  tables, not recomputed in DAX.

Every visual title and text box must stay associational ("associated with", "higher among"); run
`make audit` on any text added here.

To build: Power BI Desktop → Get data → Parquet → load the four files → create the relationships
in MODEL.md → add the measures in MEASURES.md → build the pages → save as
`powerbi/workforce-intelligence.pbix` and screenshot it into `docs/screenshots/powerbi/`.
