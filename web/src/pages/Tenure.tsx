import { TenureChart } from "../components/charts";
import { RatePanel } from "../components/Rates";
import { Gate, useTopic } from "../components/Topic";
import { PageHead } from "../components/ui";
import type { Attrition, Overview, Tenure as TenureData } from "../lib/api";

export function Tenure() {
  const st = useTopic<TenureData>("tenure");
  const at = useTopic<Attrition>("attrition");
  const ov = useTopic<Overview>("overview");
  return (
    <Gate state={st} title="Tenure" what="tenure">
      {(d) => {
        const overall = ov.data?.kpis.rate ?? 0;
        const f = at.data?.factors;
        return (
          <>
            <PageHead title="Tenure">
              Attrition by years at the company, years since the last promotion and age. These move together: newer employees are also younger and more
              junior, so each panel shows one view of the same people.
            </PageHead>
            <section className="panel" aria-labelledby="curve-head">
              <div className="panel-head">
                <h2 id="curve-head">Employees and attrition by completed years at the company</h2>
              </div>
              <div className="panel-body">
                <TenureChart title="Employees and the share who left, by completed years at the company" rows={d.tenure_curve} />
                <p className="small muted">
                  A cross-section: each employee appears once, at the tenure they had when the data were recorded. This is not a survival curve.
                </p>
              </div>
            </section>
            {f && (
              <div className="grid-2">
                {f.tenure_band && <RatePanel id="tb" factor={f.tenure_band} overall={overall} />}
                {f.promotion_band && <RatePanel id="pb" factor={f.promotion_band} overall={overall} />}
                {f.age_band && <RatePanel id="ab" factor={f.age_band} overall={overall} />}
                {f.work_life_balance && <RatePanel id="wl" factor={f.work_life_balance} overall={overall} />}
              </div>
            )}
          </>
        );
      }}
    </Gate>
  );
}
