import type { Level, OddsRatio } from "../lib/api";
import { niceTicks, num, pct } from "../lib/format";

/** Horizontal bars as a list: label, bar, value. Readable without the bar. */
export function HBars({
  label,
  rows,
  format,
}: {
  label: string;
  rows: { key: string; label: string; v: number; note?: string }[];
  format: (v: number) => string;
}) {
  const m = Math.max(...rows.map((r) => Math.abs(r.v)), 1e-9);
  return (
    <ul className="hbars" aria-label={label}>
      {rows.map((r) => (
        <li key={r.key} className="hbar">
          <span>{r.label}</span>
          <span className="hbar-track" aria-hidden="true">
            <span className="hbar-fill" style={{ width: `${(Math.abs(r.v) / m) * 100}%`, display: "block" }} />
          </span>
          <span className="num">
            {format(r.v)}
            {r.note ? <span className="muted"> · {r.note}</span> : null}
          </span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Attrition rate per group with its 95% interval, against the overall rate.
 * The bar is the observed rate; the whisker is the Wilson interval; the dashed line is the overall rate.
 */
export function RateBars({ label, levels, overall }: { label: string; levels: Level[]; overall: number }) {
  const hi = Math.max(overall, ...levels.map((l) => l.ci_high), 0.05);
  const scale = (v: number) => `${(v / hi) * 100}%`;
  return (
    <ul className="ratebars" aria-label={label}>
      {levels.map((l) => (
        <li key={String(l.level)} className="ratebar">
          <span className="ratebar-label">{l.label}</span>
          <span className="ratebar-track" aria-hidden="true">
            <span className={l.ci_low > overall ? "ratebar-fill above" : "ratebar-fill"} style={{ width: scale(l.rate) }} />
            <span className="ratebar-ci" style={{ left: scale(l.ci_low), width: `calc(${scale(l.ci_high)} - ${scale(l.ci_low)})` }} />
            <span className="ratebar-overall" style={{ left: scale(overall) }} />
          </span>
          <span className="num">
            {pct(l.rate)}
            <span className="muted">
              {" "}
              {l.leavers}/{num(l.employees)} · {pct(l.ci_low)}–{pct(l.ci_high)}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export function RateLegend({ overall }: { overall: number }) {
  return (
    <p className="legend small">
      <span>
        <i className="key-fill" aria-hidden="true" /> attrition rate
      </span>
      <span>
        <i className="key-above" aria-hidden="true" /> whole interval above the overall rate
      </span>
      <span>
        <i className="key-ci" aria-hidden="true" /> 95% interval
      </span>
      <span>
        <i className="key-overall" aria-hidden="true" /> overall {pct(overall, 1)}
      </span>
    </p>
  );
}

/** Odds ratios on a log scale with 95% intervals; 1 = no association. */
export function ForestPlot({ title, terms }: { title: string; terms: OddsRatio[] }) {
  const W = 760;
  const row = 24;
  const L = 330;
  const R = 110;
  const T = 26;
  const H = T + terms.length * row + 8;
  const lo = Math.log(Math.min(0.05, ...terms.map((t) => t.ci[0])));
  const hi = Math.log(Math.max(20, ...terms.map((t) => t.ci[1])));
  const X = (v: number) => L + ((Math.log(v) - lo) / (hi - lo)) * (W - L - R);
  const ticks = [0.05, 0.1, 0.25, 0.5, 1, 2, 4, 10, 20].filter((t) => Math.log(t) >= lo && Math.log(t) <= hi);
  return (
    <figure className="chart" style={{ maxWidth: 820 }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${title}. ${terms.map((t) => `${t.label}: ${num(t.odds_ratio, 2)} (${num(t.ci[0], 2)} to ${num(t.ci[1], 2)})`).join("; ")}`}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={X(t)} x2={X(t)} y1={T - 6} y2={H - 4} stroke={t === 1 ? "var(--ink-3)" : "var(--rule)"} strokeDasharray={t === 1 ? "4 3" : undefined} />
            <text x={X(t)} y={T - 10} textAnchor="middle" className="tick">
              {t}
            </text>
          </g>
        ))}
        {terms.map((t, i) => {
          const y = T + i * row + row / 2;
          const clear = t.ci[0] > 1 || t.ci[1] < 1;
          return (
            <g key={t.term}>
              <text x={L - 10} y={y + 4} textAnchor="end" className="flabel">
                {t.label}
              </text>
              <line x1={X(t.ci[0])} x2={X(t.ci[1])} y1={y} y2={y} stroke={clear ? "var(--accent)" : "var(--ink-3)"} strokeWidth={2} />
              <rect x={X(t.odds_ratio) - 4} y={y - 4} width={8} height={8} fill={clear ? "var(--accent)" : "var(--ink-3)"} />
              <text x={W - 4} y={y + 4} textAnchor="end" className="tick">
                {num(t.odds_ratio, 2)}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="legend">
        <span>Odds ratio, log scale; dashed line = 1 (no association). Coloured: the 95% interval excludes 1.</span>
      </figcaption>
    </figure>
  );
}

/** Employees at each completed year of tenure (bars) and the share of them who left (line, where at least `min` employees). */
export function TenureChart({
  title,
  rows,
  min = 15,
}: {
  title: string;
  rows: { years: number; employees: number; leavers: number; rate: number }[];
  min?: number;
}) {
  const W = 1000;
  const H = 280;
  const L = 52;
  const R = 52;
  const T = 12;
  const B = 34;
  const maxYears = Math.max(...rows.map((r) => r.years));
  const bw = (W - L - R) / (maxYears + 1);
  const X = (y: number) => L + (y + 0.5) * bw;
  const nTicks = niceTicks(0, Math.max(...rows.map((r) => r.employees)));
  const nMax = nTicks[nTicks.length - 1] ?? 1;
  const rTicks = [0, 0.1, 0.2, 0.3, 0.4];
  const shown = rows.filter((r) => r.employees >= min);
  const rMax = Math.max(0.4, ...shown.map((r) => r.rate));
  const Yn = (v: number) => T + (1 - v / nMax) * (H - T - B);
  const Yr = (v: number) => T + (1 - v / rMax) * (H - T - B);
  const path = shown.map((r, i) => `${i ? "L" : "M"}${X(r.years).toFixed(1)},${Yr(r.rate).toFixed(1)}`).join("");
  return (
    <figure className="chart">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${title}. ${shown.map((r) => `${r.years} years: ${r.employees} employees, ${pct(r.rate)} left`).join("; ")}`}
      >
        {nTicks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={Yn(t)} y2={Yn(t)} stroke="var(--rule)" />
            <text x={L - 6} y={Yn(t) + 4} textAnchor="end" className="tick">
              {t}
            </text>
          </g>
        ))}
        {rTicks.map((t) => (
          <text key={t} x={W - R + 6} y={Yr(t) + 4} className="tick">
            {pct(t)}
          </text>
        ))}
        {rows.map((r) => (
          <rect key={r.years} x={X(r.years) - bw * 0.35} width={bw * 0.7} y={Yn(r.employees)} height={H - B - Yn(r.employees)} fill="var(--bar-muted)" />
        ))}
        <path d={path} fill="none" stroke="var(--accent)" strokeWidth={2} />
        {shown.map((r) => (
          <circle key={r.years} cx={X(r.years)} cy={Yr(r.rate)} r={3} fill="var(--accent)" />
        ))}
        {rows
          .filter((r) => r.years % 5 === 0)
          .map((r) => (
            <text key={r.years} x={X(r.years)} y={H - 14} textAnchor="middle" className="tick">
              {r.years}
            </text>
          ))}
        <text x={(L + W - R) / 2} y={H - 1} textAnchor="middle" className="tick">
          completed years at the company
        </text>
      </svg>
      <figcaption className="legend">
        <span>
          <i style={{ background: "var(--bar-muted)" }} aria-hidden="true" /> Employees (left axis)
        </span>
        <span>
          <i style={{ background: "var(--accent)" }} aria-hidden="true" /> Share who left (right axis; years with at least {min} employees)
        </span>
      </figcaption>
    </figure>
  );
}
