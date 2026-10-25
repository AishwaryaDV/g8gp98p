"""Tests for the no-look-ahead vintage selection and resolution alignment."""
from datetime import date

import pandas as pd

from app import alignment, elexon


def test_cutoff_is_11utc_day_before():
    c = alignment.decision_cutoff(date(2026, 1, 15))
    assert c.isoformat() == "2026-01-14T11:00:00+00:00"


def test_vintage_selection_excludes_future_forecasts(monkeypatch):
    """For a 15 Jan delivery, a forecast published after the 14 Jan 11:00
    cut-off must be ignored, even though it targets the same hour."""
    target = pd.Timestamp("2026-01-15T06:00:00Z")
    fake = pd.DataFrame(
        {
            "publish_time": pd.to_datetime(
                [
                    "2026-01-14T05:00:00Z",  # before cutoff (older)
                    "2026-01-14T10:30:00Z",  # before cutoff (latest valid) -> win
                    "2026-01-15T05:00:00Z",  # AFTER cutoff -> must be excluded
                ],
                utc=True,
            ),
            "start_time": [target, target, target],
            "generation": [9000, 9500, 9800],
        }
    )
    monkeypatch.setattr(elexon, "load_forecasts", lambda: fake)

    fc = alignment.decision_time_forecast(date(2026, 1, 15))
    assert len(fc) == 1
    assert float(fc.iloc[0]["generation"]) == 9500  # not 9800


def test_actuals_aggregated_to_hourly_mean(monkeypatch):
    """Two half-hour actuals in an hour collapse to their mean MW."""
    act = pd.DataFrame(
        {
            "start_time": pd.to_datetime(
                ["2026-01-15T06:00:00Z", "2026-01-15T06:30:00Z"], utc=True
            ),
            "generation": [8000, 9000],
        }
    )
    monkeypatch.setattr(elexon, "load_actuals", lambda: act)
    hourly = alignment.actuals_hourly(
        pd.Timestamp("2026-01-15T00:00:00Z"), pd.Timestamp("2026-01-16T00:00:00Z")
    )
    assert len(hourly) == 1
    assert float(hourly.iloc[0]["generation"]) == 8500
