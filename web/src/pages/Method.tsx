import { DataTable } from "../components/DataTable";
import { Gate, useTopic } from "../components/Topic";
import { PageHead } from "../components/ui";
import type { Audit, DataCheck, Provenance, Quality, TableCount } from "../lib/api";
import { num } from "../lib/format";

const TABLES: Record<string, string> = {
  employees: "one row per employee: every recorded characteristic and the attrition flag, typed and decoded",
  fact_employee: "one row per employee with derived bands (tenure, age, promotion, income) and pay position",
  dim_department: "department",
  dim_job_role: "job role and its department",
  dim_job_level: "job level 1–5 with its median income",
};

export function Method() {
  const q = useTopic<Quality>("quality");
  const pv = useTopic<Provenance>("provenance");
  const au = useTopic<Audit>("audit");
  return (
    <Gate state={q} title="Data & method" what="data quality">
      {(d) => (
        <>
          <PageHead title="Data & method">
            Where the numbers come from: the source data, the checks run on it, the SQL data model, the causal-language audit and how each measure
            is defined.
          </PageHead>
          <section className="panel" aria-labelledby="src-head">
            <div className="panel-head">
              <h2 id="src-head">Source</h2>
            </div>
            <div className="panel-body small secondary">
              <p>
                IBM HR Analytics Employee Attrition &amp; Performance: 1,470 employees and 35 columns, one row per employee with a flag for whether
                they left. The dataset is <strong>fictional</strong>, created by IBM data scientists, and licensed ODbL (database) and DbCL
                (contents). The CSV is checked against its SHA-256 before anything runs. No public dataset from a real employer has these variables
                under an open licence, so every result describes this fictional workforce.
              </p>
              <p>
                It is a single snapshot. There is no order in time between a characteristic and leaving and no intervention, so every result is an
                association, and the model describes observed attrition rather than forecasting it.
              </p>
              {pv.data && (
                <p style={{ margin: 0 }}>
                  Run <code>{pv.data.run_id}</code>, commit <code>{pv.data.commit.slice(0, 7)}</code>
                  {pv.data.dirty ? " (uncommitted changes)" : ""}, Python {pv.data.python}, DuckDB {pv.data.packages.duckdb}, scikit-learn{" "}
                  {pv.data.packages["scikit-learn"]}.
                </p>
              )}
            </div>
          </section>
          <section className="panel" aria-labelledby="chk-head">
            <div className="panel-head">
              <h2 id="chk-head">Data checks</h2>
            </div>
            <DataTable<DataCheck>
              caption="Checks run in SQL on the staged data"
              rows={d.data_checks}
              rowKey={(r) => String(r.id)}
              columns={[
                { key: "c", label: "Check", render: (r) => r.check_name, wrap: true },
                { key: "v", label: "Result", align: "r", render: (r) => `${num(r.value)} ${r.unit}` },
                { key: "a", label: "Action", render: (r) => r.action, wrap: true },
              ]}
            />
          </section>
          <section className="panel" aria-labelledby="model-head">
            <div className="panel-head">
              <h2 id="model-head">Data model (DuckDB)</h2>
            </div>
            <DataTable<TableCount>
              caption="Tables of the data model with row counts"
              rows={d.model_tables}
              rowKey={(r) => r.table_name}
              columns={[
                { key: "t", label: "Table", render: (r) => <code>{r.table_name}</code> },
                { key: "d", label: "Grain and content", render: (r) => TABLES[r.table_name] ?? "", wrap: true },
                { key: "n", label: "Rows", align: "r", render: (r) => num(r.rows) },
              ]}
            />
            <div className="panel-body small secondary">
              <p>
                SQL lives in <code>sql/</code>: staging, checks and model, then one file per measure in <code>sql/measures/</code>. Python adds the
                statistics: Wilson intervals, chi-square and Mann–Whitney tests with Holm correction, Mantel–Haenszel stratification, k-means, the
                logistic model with cross-validation and bootstrap intervals.
              </p>
              <p style={{ margin: 0 }}>
                <span className="pending-tag">Power BI: pending</span> Power BI Desktop cannot run in this environment. The model is exported as
                Parquet for import and the measures are written as DAX in <code>powerbi/MEASURES.md</code>, but no .pbix file has been built and no
                Power BI screenshots exist. This web dashboard is the equivalent, built from the same tables.
              </p>
            </div>
          </section>
          <section className="panel" aria-labelledby="audit-head">
            <div className="panel-head">
              <h2 id="audit-head">Causal-language audit</h2>
            </div>
            <div className="panel-body small secondary">
              {au.data ? (
                <>
                  <p>
                    <strong>{au.data.passed ? "Pass" : "Fail"}</strong>: {au.data.findings.length} {au.data.findings.length === 1 ? "finding" : "findings"} in {au.data.files.length} files and texts
                    (documents, Power BI notes, dashboard source and this run&apos;s recommendations). The audit looks for {au.data.rules.length} kinds
                    of causal wording and CI fails if any is found.
                  </p>
                  {au.data.findings.length > 0 && (
                    <ul>
                      {au.data.findings.map((f) => (
                        <li key={`${f.file}-${f.line}-${f.rule}`}>
                          <code>
                            {f.file}:{f.line}
                          </code>{" "}
                          {f.rule}: {f.text}
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              ) : (
                <p>The audit result is not available.</p>
              )}
            </div>
          </section>
          <section className="panel" aria-labelledby="def-head">
            <div className="panel-head">
              <h2 id="def-head">Definitions</h2>
            </div>
            <div className="panel-body small">
              <dl className="defs">
                <dt>Attrition rate</dt>
                <dd>employees flagged as having left ÷ all employees in the group, with a Wilson 95% interval</dd>
                <dt>Pay position</dt>
                <dd>monthly income against the median of the employee&apos;s job level; within ±10% counts as at the median</dd>
                <dt>Income band</dt>
                <dd>quintile of monthly income across all employees</dd>
                <dt>Adjusted odds ratio</dt>
                <dd>from a logistic regression holding the other characteristics fixed; 1 means no association</dd>
                <dt>Mantel–Haenszel odds ratio</dt>
                <dd>the overtime odds ratio pooled across job levels, so that job level is held fixed</dd>
                <dt>AUROC</dt>
                <dd>chance that a random leaver is ranked above a random stayer; 0.5 is no separation</dd>
                <dt>Out-of-fold risk</dt>
                <dd>each employee&apos;s predicted risk from a model fitted without them (5 folds); used for risk bands and fairness checks</dd>
              </dl>
            </div>
          </section>
        </>
      )}
    </Gate>
  );
}
