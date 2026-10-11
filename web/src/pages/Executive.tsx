import { Link } from "react-router-dom";
import { HBars } from "../components/charts";
import { Gate, useTopic } from "../components/Topic";
import { PageHead, ProvenanceLine } from "../components/ui";
import type { Attrition, Audit, Overview, Provenance, Recommendations } from "../lib/api";
import { num, pct } from "../lib/format";

const KEY = ["department", "job_role", "job_level", "overtime", "tenure_band", "age_band", "business_travel", "marital_status", "stock_option_level"];

export function Executive() {
  const ov = useTopic<Overview>("overview");
  const at = useTopic<Attrition>("attrition");
  const rc = useTopic<Recommendations>("recommendations");
  const au = useTopic<Audit>("audit");
  const pv = useTopic<Provenance>("provenance");
  return (
    <Gate state={ov} title="Executive overview" what="the executive overview">
      {(d) => {
        const k = d.kpis;
        const groups = at.data
          ? KEY.flatMap((f) => (at.data?.factors[f]?.levels ?? []).filter((l) => l.employees >= 50).map((l) => ({ f, name: at.data?.factors[f]?.name ?? f, l })))
              .sort((a, b) => b.l.rate - a.l.rate)
              .slice(0, 8)
          : [];
        return (
          <>
            <PageHead title="Executive overview">
              Attrition in a workforce of {num(k.employees)} employees, from IBM's HR analytics dataset. The dataset is fictional, made by IBM data
              scientists; every figure describes it, not a real company. All results are associations in one snapshot: who had left, and what their
              records show.
            </PageHead>
            <dl className="kpis" aria-label="Headline measures">
              <div className="kpi">
                <dt>Attrition rate</dt>
                <dd>
                  {pct(k.rate, 1)}
                  <small>
                    {num(k.leavers)} of {num(k.employees)} employees left
                  </small>
                </dd>
              </div>
              <div className="kpi">
                <dt>Working overtime</dt>
                <dd>
                  {pct(k.overtime_share, 0)}
                  <small>of all employees</small>
                </dd>
              </div>
              <div className="kpi">
                <dt>Median monthly income</dt>
                <dd>
                  {num(k.median_income)}
                  <small>dataset units</small>
                </dd>
              </div>
              <div className="kpi">
                <dt>Median years at the company</dt>
                <dd>
                  {num(k.median_tenure)}
                  <small>median age {num(k.median_age)}</small>
                </dd>
              </div>
              <div className="kpi">
                <dt>Causal-language audit</dt>
                <dd>
                  {au.data ? (au.data.passed ? "Pass" : "Fail") : "–"}
                  <small>{au.data ? `${au.data.findings.length} ${au.data.findings.length === 1 ? "finding" : "findings"} in ${au.data.files.length} files and texts` : "loading"}</small>
                </dd>
              </div>
            </dl>
            {groups.length > 0 && (
              <section className="panel" aria-labelledby="hi-head">
                <div className="panel-head">
                  <h2 id="hi-head">Groups with the highest attrition</h2>
                  <Link to="/attrition" className="small">
                    Every characteristic, with intervals →
                  </Link>
                </div>
                <div className="panel-body">
                  <HBars
                    label="Attrition rate of the groups with the highest rates (at least 50 employees)"
                    rows={groups.map((g) => ({ key: `${g.f}-${g.l.level}`, label: `${g.name}: ${g.l.label}`, v: g.l.rate, note: `${g.l.leavers}/${g.l.employees}` }))}
                    format={(v) => pct(v)}
                  />
                  <p className="small muted">Groups of at least 50 employees. A group's rate describes who left in it; it does not say why they left.</p>
                </div>
              </section>
            )}
            {rc.data && (
              <section className="panel" aria-labelledby="rec-head">
                <div className="panel-head">
                  <h2 id="rec-head">Where to look</h2>
                  <span className="small muted">generated from the measured associations; none has been tested</span>
                </div>
                <div className="panel-body">
                  <div className="recs">
                    {rc.data.recommendations.map((r, i) => (
                      <article key={r.title} className="rec-card" aria-labelledby={`rec-${i}`}>
                        <span className="area">
                          {i + 1}. {r.area}
                        </span>
                        <h3 id={`rec-${i}`}>{r.title}</h3>
                        <p style={{ margin: 0 }}>{r.finding}</p>
                        <ul className="risks" aria-label="Evidence">
                          {r.evidence.map((e) => (
                            <li key={e}>{e}</li>
                          ))}
                        </ul>
                        <p className="action">{r.action}</p>
                        <p className="basis">Basis: {r.basis}</p>
                      </article>
                    ))}
                  </div>
                </div>
              </section>
            )}
            {pv.data && <ProvenanceLine p={pv.data} />}
          </>
        );
      }}
    </Gate>
  );
}
