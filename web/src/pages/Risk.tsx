import { useState } from "react";
import { ForestPlot } from "../components/charts";
import { DataTable } from "../components/DataTable";
import { Gate, useTopic } from "../components/Topic";
import { PageHead, Segmented } from "../components/ui";
import type { FairRow, Metrics, Risk as RiskData } from "../lib/api";
import { MODEL_LABEL, num, pct } from "../lib/format";

const ORDER = ["prevalence", "overtime_only", "logistic", "boosting"];
const ATTR: Record<string, string> = { gender: "Gender", age_band: "Age", marital_status: "Marital status" };

function ci(v: [number, number] | undefined, d = 3) {
  return v ? `${num(v[0], d)}–${num(v[1], d)}` : "";
}

export function Risk() {
  const st = useTopic<RiskData>("risk");
  const [fair, setFair] = useState<"all" | "nostock">("all");
  return (
    <Gate state={st} title="Risk segments" what="the risk model">
      {(d) => {
        const m = d.model;
        const boot = m.bootstrap.models;
        const rows = ORDER.filter((k) => m.test[k]).map((k) => ({ k, v: m.test[k] as Metrics }));
        const fr: FairRow[] = fair === "all" ? d.fairness : d.fairness_without_stock_options;
        const numeric = m.odds_ratios.terms.filter((t) => t.group === "numeric");
        const cats = m.odds_ratios.terms.filter((t) => t.group === "category");
        const diffB = m.bootstrap.auroc_diff_logistic_minus.boosting;
        return (
          <>
            <PageHead title="Risk segments">
              An interpretable model of <em>observed</em> attrition: how closely an employee&apos;s record resembles those of people who left. It is not a
              forecast of who will leave and says nothing about what a change in policy would do. The dashboard shows groups only, never a score for a
              named or numbered employee.
            </PageHead>
            <section className="panel" aria-labelledby="perf-head">
              <div className="panel-head">
                <h2 id="perf-head">How well the model separates leavers from stayers</h2>
              </div>
              <DataTable
                caption={`Held-out test set: ${num(m.split.test)} employees, ${num(m.split.test_leavers)} leavers. Intervals: 95% bootstrap.`}
                rows={rows}
                rowKey={(r) => r.k}
                columns={[
                  { key: "m", label: "Model", render: (r) => MODEL_LABEL[r.k] ?? r.k },
                  { key: "a", label: "AUROC", align: "r", render: (r) => `${num(r.v.auroc, 3)}` },
                  { key: "ai", label: "95% interval", align: "r", render: (r) => ci(boot[r.k]?.auroc) },
                  { key: "p", label: "Average precision", align: "r", render: (r) => num(r.v.average_precision, 3) },
                  { key: "b", label: "Brier score", align: "r", render: (r) => num(r.v.brier, 3) },
                  { key: "s", label: "Calibration slope", align: "r", render: (r) => (r.v.calibration_slope == null ? "–" : num(r.v.calibration_slope, 2)) },
                ]}
              />
              <div className="panel-body small secondary">
                <p>
                  Logistic regression minus gradient boosting, AUROC: {diffB ? `${num(diffB.diff, 3)} (${ci(diffB.ci)})` : "–"}. Out-of-fold AUROC on
                  all {num(m.split.train + m.split.test)} employees: {num(m.oof_metrics.auroc, 3)}. Refitted without stock options:{" "}
                  {num(m.without_stock_options.test.auroc, 3)} on the test set. Regularisation C = {m.c}, chosen by 5-fold cross-validated log loss on the
                  training part.
                </p>
              </div>
            </section>
            <section className="panel" aria-labelledby="or-head">
              <div className="panel-head">
                <h2 id="or-head">Adjusted odds ratios</h2>
              </div>
              <div className="panel-body">
                <p className="small secondary">
                  From an unpenalised logistic regression on all {num(m.odds_ratios.n)} employees; each ratio holds the other characteristics fixed.
                  Numeric characteristics are per unit (income per 1,000). These are associations within this dataset.
                </p>
                <ForestPlot title="Adjusted odds ratios for numeric and binary characteristics" terms={numeric} />
                {cats.length > 0 && (
                  <ForestPlot
                    title="Adjusted odds ratios for categories, against their reference level"
                    terms={cats}
                  />
                )}
                <p className="small muted">
                  Reference levels:{" "}
                  {Object.entries(m.odds_ratios.reference_levels)
                    .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)
                    .join("; ")}
                  . Highest variance inflation factor: {num(Math.max(...Object.values(m.odds_ratios.vif)), 1)}; correlated characteristics such as
                  income and job level share their association, so neither ratio alone is its full size.
                </p>
              </div>
            </section>
            <section className="panel" aria-labelledby="band-head">
              <div className="panel-head">
                <h2 id="band-head">Risk bands</h2>
              </div>
              <DataTable
                caption="Employees grouped by out-of-fold predicted risk"
                rows={d.risk_segments.bands}
                rowKey={(r) => r.band}
                columns={[
                  { key: "b", label: "Band", render: (r) => `${r.band} (${pct(r.range[0])}–${pct(r.range[1])})` },
                  { key: "n", label: "Employees", align: "r", render: (r) => num(r.employees) },
                  { key: "p", label: "Mean predicted", align: "r", render: (r) => pct(r.mean_predicted, 1) },
                  { key: "o", label: "Observed left", align: "r", render: (r) => `${pct(r.rate, 1)} (${pct(r.ci[0])}–${pct(r.ci[1])})` },
                  { key: "ot", label: "Overtime", align: "r", render: (r) => pct(r.overtime_share) },
                  { key: "a", label: "Median age", align: "r", render: (r) => num(r.median_age) },
                  { key: "t", label: "Median tenure", align: "r", render: (r) => num(r.median_tenure) },
                  { key: "i", label: "Median income", align: "r", render: (r) => num(r.median_income) },
                ]}
              />
            </section>
            <section className="panel" aria-labelledby="seg-head">
              <div className="panel-head">
                <h2 id="seg-head">Workforce segments (k-means, k = {d.segments.k})</h2>
              </div>
              <DataTable
                caption="Segments found from recorded characteristics, without the attrition flag"
                rows={d.segments.segments}
                rowKey={(r) => String(r.segment)}
                columns={[
                  { key: "s", label: "Segment", render: (r) => `${r.segment}: ${r.label}`, wrap: true },
                  { key: "n", label: "Employees", align: "r", render: (r) => num(r.employees) },
                  { key: "o", label: "Left", align: "r", render: (r) => `${pct(r.rate, 1)} (${pct(r.ci[0])}–${pct(r.ci[1])})` },
                  { key: "a", label: "Median age", align: "r", render: (r) => num(r.median_age) },
                  { key: "l", label: "Mean job level", align: "r", render: (r) => num(r.mean_job_level, 1) },
                  { key: "i", label: "Median income", align: "r", render: (r) => num(r.median_income) },
                ]}
              />
              <div className="panel-body small muted">
                <p style={{ margin: 0 }}>
                  k chosen by silhouette ({Object.entries(d.segments.silhouette)
                    .map(([k, v]) => `k=${k}: ${num(v, 2)}`)
                    .join(", ")}
                  ); stability across seeds, adjusted Rand index {num(Math.min(...d.segments.stability_ari), 2)}–{num(Math.max(...d.segments.stability_ari), 2)}.
                  A segment is a profile, not an explanation.
                </p>
              </div>
            </section>
            <section className="panel" aria-labelledby="fair-head">
              <div className="panel-head">
                <h2 id="fair-head">Does the model work equally well across groups?</h2>
                <Segmented
                  label="Model"
                  options={[
                    { id: "all", label: "Main model" },
                    { id: "nostock", label: "Without stock options" },
                  ]}
                  value={fair}
                  onChange={setFair}
                />
              </div>
              <DataTable
                caption={`Out-of-fold predictions by group. Flagged: predicted risk of ${pct(d.risk_segments.bounds[d.risk_segments.bounds.length - 1] ?? 0)} or more.`}
                rows={fr}
                rowKey={(r) => `${r.attribute}-${r.group}`}
                columns={[
                  { key: "a", label: "Group", render: (r) => `${ATTR[r.attribute] ?? r.attribute}: ${r.group}` },
                  { key: "n", label: "Employees", align: "r", render: (r) => num(r.employees) },
                  { key: "o", label: "Observed", align: "r", render: (r) => pct(r.observed_rate, 1) },
                  { key: "p", label: "Mean predicted", align: "r", render: (r) => pct(r.mean_predicted, 1) },
                  { key: "u", label: "AUROC", align: "r", render: (r) => (r.auroc == null ? "–" : num(r.auroc, 2)) },
                  { key: "f", label: "Flagged", align: "r", render: (r) => pct(r.flagged_share) },
                  { key: "t", label: "Leavers flagged", align: "r", render: (r) => (r.true_positive_rate == null ? "–" : pct(r.true_positive_rate)) },
                  { key: "x", label: "Stayers flagged", align: "r", render: (r) => (r.false_positive_rate == null ? "–" : pct(r.false_positive_rate)) },
                ]}
              />
              <div className="panel-body small muted">
                <p style={{ margin: 0 }}>
                  Gender and marital status are not model inputs. Single employees all have stock option level 0, so the main model reaches marital
                  status through stock options; the second table shows the same check with stock options left out.
                </p>
              </div>
            </section>
          </>
        );
      }}
    </Gate>
  );
}
