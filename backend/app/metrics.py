"""Forecast-accuracy metrics, framed for a procurement decision.

All metrics operate on a frame with `forecast`, `actual`, `error` columns
(error = forecast - actual, in MW). We keep the maths explicit and pure so the
tech lead can read and unit-test it without running the whole app.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop hours missing either side; metrics need matched pairs."""
    return df.dropna(subset=["forecast", "actual"]).copy()


def summary_metrics(df: pd.DataFrame) -> dict:
    """Headline accuracy numbers over the supplied rows."""
    d = _clean(df)
    n = len(d)
    if n == 0:
        return {"count": 0}

    err = d["error"].to_numpy()
    actual = d["actual"].to_numpy()
    mean_actual = float(actual.mean())

    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    bias = float(np.mean(err))  # MBE: +ve = systematic over-forecast

    # Normalised MAE (by mean actual) is a stable % that avoids the divide-by-
    # near-zero blow-ups of classic MAPE during low-wind hours.
    nmae_pct = float(mae / mean_actual * 100) if mean_actual else None

    return {
        "count": n,
        "mae_mw": round(mae, 1),
        "rmse_mw": round(rmse, 1),
        "bias_mw": round(bias, 1),
        "nmae_pct": round(nmae_pct, 1) if nmae_pct is not None else None,
        "mean_actual_mw": round(mean_actual, 1),
        "mean_forecast_mw": round(float(d["forecast"].mean()), 1),
        "max_over_forecast_mw": round(float(err.max()), 1),
        "max_under_forecast_mw": round(float(err.min()), 1),
    }


def metrics_by_hour(df: pd.DataFrame) -> list[dict]:
    """MAE and bias grouped by hour-of-day: shows *when* the forecast is weakest."""
    d = _clean(df)
    if d.empty:
        return []
    d["hod"] = d["start_time"].dt.hour
    out = []
    for hod, g in d.groupby("hod"):
        err = g["error"].to_numpy()
        out.append(
            {
                "hour": int(hod),
                "mae_mw": round(float(np.mean(np.abs(err))), 1),
                "bias_mw": round(float(np.mean(err)), 1),
            }
        )
    return sorted(out, key=lambda r: r["hour"])


def metrics_by_day(df: pd.DataFrame) -> list[dict]:
    """Daily MAE/bias: the accuracy trend across the month."""
    d = _clean(df)
    if d.empty:
        return []
    d["day"] = d["start_time"].dt.date
    out = []
    for day, g in d.groupby("day"):
        err = g["error"].to_numpy()
        out.append(
            {
                "date": day.isoformat(),
                "mae_mw": round(float(np.mean(np.abs(err))), 1),
                "bias_mw": round(float(np.mean(err)), 1),
                "mean_actual_mw": round(float(g["actual"].mean()), 1),
            }
        )
    return sorted(out, key=lambda r: r["date"])


def error_histogram(df: pd.DataFrame, bin_mw: int = 500) -> list[dict]:
    """Distribution of hourly errors, for sizing a procurement buffer."""
    d = _clean(df)
    if d.empty:
        return []
    err = d["error"].to_numpy()
    lo = np.floor(err.min() / bin_mw) * bin_mw
    hi = np.ceil(err.max() / bin_mw) * bin_mw
    edges = np.arange(lo, hi + bin_mw, bin_mw)
    counts, _ = np.histogram(err, bins=edges)
    return [
        {"bin_start_mw": float(edges[i]), "bin_end_mw": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]
