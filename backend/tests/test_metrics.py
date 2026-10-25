"""Unit tests for the accuracy metrics (pure functions, no network)."""
import numpy as np
import pandas as pd

from app import metrics


def _frame(forecast, actual):
    start = pd.date_range("2026-01-15", periods=len(forecast), freq="h", tz="UTC")
    df = pd.DataFrame({"start_time": start, "forecast": forecast, "actual": actual})
    df["error"] = df["forecast"] - df["actual"]
    return df


def test_summary_basic_numbers():
    # errors: +100, -100, +200  (forecast - actual)
    df = _frame([1100, 900, 1200], [1000, 1000, 1000])
    s = metrics.summary_metrics(df)
    assert s["count"] == 3
    assert s["mae_mw"] == round((100 + 100 + 200) / 3, 1)
    assert s["bias_mw"] == round((100 - 100 + 200) / 3, 1)
    assert s["rmse_mw"] == round(float(np.sqrt((100**2 + 100**2 + 200**2) / 3)), 1)
    assert s["max_over_forecast_mw"] == 200.0
    assert s["max_under_forecast_mw"] == -100.0


def test_summary_ignores_unmatched_hours():
    df = _frame([1000, 1000], [1000, 1000])
    df.loc[1, "actual"] = np.nan  # unmatched hour dropped
    df["error"] = df["forecast"] - df["actual"]
    s = metrics.summary_metrics(df)
    assert s["count"] == 1


def test_perfect_forecast_is_zero_error():
    df = _frame([1000, 2000], [1000, 2000])
    s = metrics.summary_metrics(df)
    assert s["mae_mw"] == 0.0
    assert s["rmse_mw"] == 0.0
    assert s["bias_mw"] == 0.0
    assert s["nmae_pct"] == 0.0


def test_histogram_counts_sum_to_n():
    df = _frame([1000, 1100, 1900, 500], [1000, 1000, 1000, 1000])
    hist = metrics.error_histogram(df, bin_mw=500)
    assert sum(b["count"] for b in hist) == 4
