import { useState } from "react";
import { DataTable } from "../components/DataTable";
import { RatePanel } from "../components/Rates";
import { Gate, useTopic } from "../components/Topic";
import { PageHead } from "../components/ui";
import type { Attrition as AttritionData, Overview, TestRow } from "../lib/api";
import { num, pct, pval, signed } from "../lib/format";

const ORDER = [
  "overtime", "job_level", "income_band", "pay_position", "tenure_band", "age_band", "business_travel", "stock_option_level",
  "job_satisfaction", "environment_satisfaction", "work_life_balance", "job_involvement", "relationship_satisfaction",
  "promotion_band", "performance_rating", "department", "job_role", "education", "education_field", "marital_status", "gender",
];

export function Attrition() {
  const st = useTopic<AttritionData>("attrition");
  const ov = useTopic<Overview>("overview");
  const [factor, setFactor] = useState("overtime");
  return (
    <Gate state={st} title="Attrition" what="attrition by characteristic">
      {(d) => {
        const overall = ov.data?.kpis.rate ?? 0;
        const f = d.factors[factor];
        const s = d.stratified[0];
        const sig = d.tests.filter((t) => t.significant).length;
        return (
          <>
            <PageHead title="Attrition">
              Who left, by every recorded characteristic, with 95% intervals; which associations survive a correction for testing many at once; and
              how the overtime association looks within job levels.
            </PageHead>
            <div className="toolbar">
              <label htmlFor="factor" className="small">
                Characteristic
              </label>{" "}
              <select id="factor" className="factor-pick" value={factor} onChange={(e) => setFactor(e.target.value)}>
                {ORDER.filter((k) => d.factors[k]).map((k) => (
                  <option key={k} value={k}>
                    {d.factors[k]?.name}
                  </option>
                ))}
              </select>
            </div>
            {f && <RatePanel id="factor" factor={f} overall={overall} />}
            <section className="panel" aria-labelledby="tests-head">
              <div className="panel-head">
                <h2 id="tests-head">Association tests</h2>
                <span className="small muted">
                  {sig} of {d.tests.length} significant after Holm correction
                </span>
              </div>
              <DataTable<TestRow>
                caption="Association tests with Holm-corrected p-values"
                rows={d.tests}
                rowKey={(t) => t.factor}
                columns={[
                  { key: "n", label: "Characteristic", render: (t) => t.name },
                  { key: "t", label: "Test", render: (t) => t.test },
                  { key: "e", label: "Effect size", align: "r", render: (t) => `${signed(t.effect)}`, title: "Cramér's V (categories) or rank-biserial r (numbers)" },
                  {
                    key: "m",
                    label: "Leavers vs stayers",
                    align: "r",
                    render: (t) => (t.median_left !== undefined ? `median ${num(t.median_left)} vs ${num(t.median_stayed)}` : "–"),
                  },
                  { key: "p", label: "p (Holm)", align: "r", render: (t) => pval(t.p_holm) },
                  { key: "s", label: "Significant", render: (t) => (t.significant ? "yes" : "no") },
                ]}
              />
              <p className="panel-body small muted">
                Cramér's V for categories (0 = no association, 1 = complete); rank-biserial r for numbers (negative = leavers tend to have lower values).
                Holm correction across all {d.tests.length} tests.
              </p>
            </section>
            {s && (
            <section className="panel" aria-labelledby="mh-head">
              <div className="panel-head">
                <h2 id="mh-head">Overtime within job level</h2>
              </div>
              <div className="panel-body small">
                <p style={{ marginTop: 0 }}>
                  Across all employees the odds of having left are {num(s.crude.odds_ratio, 2)} times as high with overtime ({num(s.crude.ci[0], 2)}–
                  {num(s.crude.ci[1], 2)}). Comparing only employees at the same job level, the pooled (Mantel–Haenszel) odds ratio is{" "}
                  {num(s.mantel_haenszel.odds_ratio, 2)} ({num(s.mantel_haenszel.ci[0], 2)}–{num(s.mantel_haenszel.ci[1], 2)}); test of equal odds ratios
                  across levels p = {pval(s.homogeneity_p)}. Comparing within levels does not remove the pattern. It remains an association: overtime
                  and leaving were recorded in the same snapshot, and other differences between the groups are not held fixed.
                </p>
              </div>
              <DataTable
                caption="Overtime and attrition by job level"
                rows={s.strata}
                rowKey={(r) => r.stratum}
                columns={[
                  { key: "l", label: "Job level", render: (r) => `Level ${r.stratum}` },
                  { key: "n", label: "Employees", align: "r", render: (r) => num(r.employees) },
                  { key: "x", label: "With overtime", align: "r", render: (r) => num(r.exposed) },
                  { key: "a", label: "Left, with overtime", align: "r", render: (r) => pct(r.rate_exposed) },
                  { key: "b", label: "Left, without", align: "r", render: (r) => pct(r.rate_unexposed) },
                  { key: "o", label: "Odds ratio (95% CI)", align: "r", render: (r) => `${num(r.odds_ratio, 2)} (${num(r.ci[0], 2)}–${num(r.ci[1], 2)})` },
                ]}
              />
            </section>
            )}
          </>
        );
      }}
    </Gate>
  );
}
