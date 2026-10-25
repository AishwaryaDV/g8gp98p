// Typed client for the backend API. One place that knows the response shapes.

const BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://localhost:8000";

export interface Summary {
  count: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  nmae_pct: number | null;
  mean_actual_mw: number | null;
  mean_forecast_mw: number | null;
  max_over_forecast_mw: number | null;
  max_under_forecast_mw: number | null;
}

export interface SeriesPoint {
  start_time: string;
  forecast: number | null;
  actual: number | null;
  error: number | null;
}

export interface DayResponse {
  delivery_day: string;
  decision_cutoff_utc: string;
  series: SeriesPoint[];
  summary: Summary;
}

export interface HourMetric {
  hour: number;
  mae_mw: number;
  bias_mw: number;
}

export interface DayMetric {
  date: string;
  mae_mw: number;
  bias_mw: number;
  mean_actual_mw: number;
}

export interface HistogramBin {
  bin_start_mw: number;
  bin_end_mw: number;
  count: number;
}

export interface MetricsResponse {
  date_from: string;
  date_to: string;
  summary: Summary;
  by_hour: HourMetric[];
  by_day: DayMetric[];
  histogram: HistogramBin[];
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed (${res.status}) for ${path}`);
  }
  return (await res.json()) as T;
}

export const api = {
  days: () =>
    getJSON<{ days: string[]; decision_cutoff_hour_utc: number }>("/api/days"),
  forecastDay: (day: string) => getJSON<DayResponse>(`/api/forecast/${day}`),
  metrics: (from?: string, to?: string) => {
    const q = new URLSearchParams();
    if (from) q.set("from", from);
    if (to) q.set("to", to);
    const qs = q.toString();
    return getJSON<MetricsResponse>(`/api/metrics${qs ? `?${qs}` : ""}`);
  },
};
