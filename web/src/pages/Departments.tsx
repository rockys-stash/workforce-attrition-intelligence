import { DataTable } from "../components/DataTable";
import { RatePanel } from "../components/Rates";
import { Gate, useTopic } from "../components/Topic";
import { PageHead } from "../components/ui";
import type { Attrition, Departments as DeptData, Overview, RoleRow } from "../lib/api";
import { num, pct } from "../lib/format";
import { wilson } from "../lib/stats";

export function Departments() {
  const st = useTopic<DeptData>("departments");
  const at = useTopic<Attrition>("attrition");
  const ov = useTopic<Overview>("overview");
  return (
    <Gate state={st} title="Departments" what="departments and roles">
      {(d) => {
        const overall = ov.data?.kpis.rate ?? 0;
        const dept = at.data?.factors.department;
        const roles = at.data?.factors.job_role;
        return (
          <>
            <PageHead title="Departments">
              Attrition by department and job role, with each role's pay, overtime, satisfaction and tenure profile. Roles sit inside departments, so a
              department's rate is the mix of its roles' rates.
            </PageHead>
            <div className="grid-2">
              {dept && <RatePanel id="dept" factor={dept} overall={overall} />}
              {roles && (
                <RatePanel
                  id="role"
                  factor={{ ...roles, levels: [...roles.levels].sort((a, b) => b.rate - a.rate) }}
                  overall={overall}
                  note="Small roles have wide intervals: read the interval, not only the bar."
                />
              )}
            </div>
            <section className="panel" aria-labelledby="roles-head">
              <div className="panel-head">
                <h2 id="roles-head">Role profiles</h2>
                <span className="small muted">by department; the Manager role appears in three departments</span>
              </div>
              <DataTable<RoleRow>
                caption="Role profiles by department"
                rows={d.departments}
                rowKey={(r) => `${r.department}-${r.job_role}`}
                columns={[
                  { key: "d", label: "Department", render: (r) => r.department },
                  { key: "r", label: "Role", render: (r) => r.job_role },
                  { key: "n", label: "Employees", align: "r", render: (r) => num(r.employees) },
                  {
                    key: "a",
                    label: "Left (95% CI)",
                    align: "r",
                    render: (r) => {
                      const [lo, hi] = wilson(r.leavers, r.employees);
                      return `${pct(r.rate)} (${pct(lo)}–${pct(hi)})`;
                    },
                  },
                  { key: "i", label: "Median income", align: "r", render: (r) => num(r.median_income) },
                  { key: "o", label: "Overtime", align: "r", render: (r) => pct(r.overtime_share) },
                  { key: "s", label: "Job satisfaction (1–4)", align: "r", render: (r) => num(r.mean_job_satisfaction, 2) },
                  { key: "t", label: "Median years", align: "r", render: (r) => num(r.median_tenure) },
                  { key: "l", label: "Mean level", align: "r", render: (r) => num(r.mean_job_level, 1) },
                ]}
              />
            </section>
          </>
        );
      }}
    </Gate>
  );
}
