import type { Factor } from "../lib/api";
import { RateBars, RateLegend } from "./charts";

/** One panel: attrition by the levels of one characteristic. */
export function RatePanel({ id, factor, overall, note }: { id: string; factor: Factor; overall: number; note?: string }) {
  return (
    <section className="panel" aria-labelledby={`${id}-head`}>
      <div className="panel-head">
        <h2 id={`${id}-head`}>Attrition by {factor.name.toLowerCase()}</h2>
      </div>
      <div className="panel-body">
        <RateBars label={`Attrition rate by ${factor.name.toLowerCase()}, with 95% intervals`} levels={factor.levels} overall={overall} />
        <RateLegend overall={overall} />
        {note && <p className="small muted">{note}</p>}
      </div>
    </section>
  );
}
