import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type MetricsResponse } from "../api";
import SummaryCards from "./SummaryCards";

const axis = { stroke: "var(--muted)", tick: { fontSize: 12, fill: "var(--muted)" } };
const tooltipStyle = {
  background: "var(--panel)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--text)",
};

export default function AccuracyView() {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api.metrics().then(setData).catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="state">Could not load metrics. {error}</div>;
  if (!data) return <div className="state">Loading accuracy metrics...</div>;

  const dayData = data.by_day.map((d) => ({
    date: d.date.slice(5), // MM-DD
    MAE: d.mae_mw,
    Bias: d.bias_mw,
  }));
  const hourData = data.by_hour.map((h) => ({ hour: `${h.hour}:00`, MAE: h.mae_mw }));
  const histData = data.histogram.map((b) => ({
    bin: `${b.bin_start_mw / 1000}k`,
    count: b.count,
  }));

  return (
    <section>
      <div className="note">
        Across <b>{data.date_from}</b> to <b>{data.date_to}</b>, the day-ahead
        forecast has a mean bias of <b>{data.summary.bias_mw} MW</b>. A positive
        bias means it systematically over-forecasts wind, so trusting it blindly
        would leave the team repeatedly short on thermal cover.
      </div>

      <SummaryCards summary={data.summary} />

      <div className="panel">
        <h3>Daily accuracy across the month</h3>
        <p className="hint">MAE and bias per delivery day, MW.</p>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dayData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="date" {...axis} />
            <YAxis {...axis} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <ReferenceLine y={0} stroke="var(--muted)" />
            <Line type="monotone" dataKey="MAE" stroke="var(--accent)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="Bias" stroke="var(--warn)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3>Error by hour of day</h3>
          <p className="hint">Mean absolute error, MW. Shows when the forecast is weakest.</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={hourData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="hour" {...axis} interval={2} />
              <YAxis {...axis} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--panel-2)" }} />
              <Bar dataKey="MAE" fill="var(--accent)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h3>Distribution of hourly errors</h3>
          <p className="hint">
            Count of hours per error band (MW, forecast minus actual). Helps size a
            procurement buffer.
          </p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={histData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="bin" {...axis} interval={1} />
              <YAxis {...axis} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--panel-2)" }} />
              <Bar dataKey="count" fill="var(--actual)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
