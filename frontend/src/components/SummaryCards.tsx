import type { Summary } from "../api";

function fmt(n: number | null, unit = ""): string {
  if (n === null || n === undefined) return "n/a";
  return `${n.toLocaleString()}${unit}`;
}

export default function SummaryCards({ summary }: { summary: Summary }) {
  const bias = summary.bias_mw ?? 0;
  const biasDir = bias > 0 ? "over-forecast" : bias < 0 ? "under-forecast" : "neutral";

  return (
    <div className="cards">
      <div className="card">
        <div className="label">MAE</div>
        <div className="value">{fmt(summary.mae_mw, " MW")}</div>
        <div className="sub">typical miss size</div>
      </div>
      <div className="card">
        <div className="label">RMSE</div>
        <div className="value">{fmt(summary.rmse_mw, " MW")}</div>
        <div className="sub">penalises large misses</div>
      </div>
      <div className="card">
        <div className="label">Bias (MBE)</div>
        <div className="value warn">{fmt(summary.bias_mw, " MW")}</div>
        <div className="sub">{biasDir}</div>
      </div>
      <div className="card">
        <div className="label">nMAE</div>
        <div className="value">{fmt(summary.nmae_pct, " %")}</div>
        <div className="sub">MAE / mean actual</div>
      </div>
    </div>
  );
}
