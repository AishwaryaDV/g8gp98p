import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type DayResponse } from "../api";
import SummaryCards from "./SummaryCards";

function hourLabel(iso: string): string {
  return new Date(iso).toUTCString().slice(17, 22); // "HH:MM"
}

export default function ForecastView() {
  const [days, setDays] = useState<string[]>([]);
  const [day, setDay] = useState<string>("");
  const [data, setData] = useState<DayResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api
      .days()
      .then((r) => {
        setDays(r.days);
        setDay(r.days[14] ?? r.days[0] ?? "");
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!day) return;
    setData(null);
    api
      .forecastDay(day)
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [day]);

  const chartData =
    data?.series.map((p) => ({
      time: hourLabel(p.start_time),
      Forecast: p.forecast,
      Actual: p.actual,
    })) ?? [];

  return (
    <section>
      <div className="toolbar">
        <label htmlFor="day">Delivery day</label>
        <select id="day" value={day} onChange={(e) => setDay(e.target.value)}>
          {days.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="state">Could not load data. {error}</div>}

      {data && (
        <>
          <div className="note">
            Decision cut-off: <b>{data.decision_cutoff_utc.replace("T", " ")}</b>.
            This is the latest forecast available the day before delivery, so it is
            what the procurement team would actually have used.
          </div>

          <SummaryCards summary={data.summary} />

          <div className="panel">
            <h3>Forecast vs actual wind generation</h3>
            <p className="hint">
              Hourly, MW. Gap between the lines is the error the team has to cover
              with thermal procurement.
            </p>
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="#272e3a" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#8b97a7" tick={{ fontSize: 12 }} />
                <YAxis stroke="#8b97a7" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "#161b22",
                    border: "1px solid #272e3a",
                    borderRadius: 8,
                    color: "#e6edf3",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="Forecast"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Actual"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {!data && !error && <div className="state">Loading forecast...</div>}
    </section>
  );
}
