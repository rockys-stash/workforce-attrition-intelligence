import { DataTable } from "../components/DataTable";
import { RatePanel } from "../components/Rates";
import { Gate, useTopic } from "../components/Topic";
import { PageHead } from "../components/ui";
import type { Attrition, Compensation as CompData, Overview } from "../lib/api";
import { num, pct } from "../lib/format";

export function Compensation() {
  const st = useTopic<CompData>("compensation");
  const at = useTopic<Attrition>("attrition");
  const ov = useTopic<Overview>("overview");
  return (
    <Gate state={st} title="Compensation" what="compensation">
      {(d) => {
        const overall = ov.data?.kpis.rate ?? 0;
        const f = at.data?.factors;
        const bands = d.income_bands;
        return (
          <>
            <PageHead title="Compensation">
              Pay by job level for those who stayed and those who left, attrition by income band and by pay relative to the job level's median, and
              stock options. Income is monthly, in the dataset's own units. Pay rises with level, so lower pay and junior roles go together.
            </PageHead>
            <section className="panel" aria-labelledby="lvl-head">
              <div className="panel-head">
                <h2 id="lvl-head">Pay and attrition by job level</h2>
              </div>
              <DataTable
                caption="Employees, attrition, income and overtime by job level"
                rows={d.compensation}
                rowKey={(r) => String(r.job_level)}
                columns={[
                  { key: "l", label: "Job level", render: (r) => `Level ${r.job_level}` },
                  { key: "n", label: "Employees", align: "r", render: (r) => num(r.employees) },
                  { key: "a", label: "Left", align: "r", render: (r) => `${pct(r.rate)} (${r.leavers})` },
                  { key: "m", label: "Median income", align: "r", render: (r) => num(r.median_income) },
                  { key: "s", label: "Median, stayed", align: "r", render: (r) => num(r.median_income_stayed) },
                  { key: "x", label: "Median, left", align: "r", render: (r) => num(r.median_income_left) },
                  { key: "o", label: "Overtime", align: "r", render: (r) => pct(r.overtime_share) },
                  { key: "k", label: "No stock options", align: "r", render: (r) => pct(r.no_stock_share) },
                ]}
              />
            </section>
            {f && (
              <div className="grid-2">
                {f.income_band && (
                  <RatePanel
                    id="band"
                    factor={{
                      ...f.income_band,
                      levels: f.income_band.levels.map((l) => {
                        const b = bands.find((x) => x.income_band === l.level);
                        return { ...l, label: b ? `${l.label} (${num(b.min_income)}–${num(b.max_income)})` : l.label };
                      }),
                    }}
                    overall={overall}
                    note="Quintiles of monthly income across all employees."
                  />
                )}
                {f.pay_position && (
                  <RatePanel id="pos" factor={f.pay_position} overall={overall} note="Within ±10% of the median income of the employee's own job level counts as at the median." />
                )}
                {f.stock_option_level && <RatePanel id="stock" factor={f.stock_option_level} overall={overall} />}
                <section className="panel" aria-labelledby="sm-head">
                  <div className="panel-head">
                    <h2 id="sm-head">Stock options by marital status</h2>
                  </div>
                  <DataTable
                    caption="Employees by marital status and stock option level"
                    rows={d.stock_by_marital}
                    rowKey={(r) => r.marital_status}
                    columns={[
                      { key: "m", label: "Marital status", render: (r) => r.marital_status },
                      ...["0", "1", "2", "3"].map((k) => ({ key: k, label: `Level ${k}`, align: "r" as const, render: (r: { levels: Record<string, number> }) => num(r.levels[k] ?? 0) })),
                    ]}
                  />
                  <p className="panel-body small muted">
                    Every single employee has stock option level 0, so in these data stock options and marital status cannot be told apart. The risk model
                    does not use marital status; the Risk segments page shows the model refitted without stock options.
                  </p>
                </section>
              </div>
            )}
          </>
        );
      }}
    </Gate>
  );
}
