"""Pydantic response models — the API contract the frontend codes against."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SeriesPoint(BaseModel):
    start_time: str
    forecast: Optional[float] = None
    actual: Optional[float] = None
    error: Optional[float] = None


class Summary(BaseModel):
    count: int
    mae_mw: Optional[float] = None
    rmse_mw: Optional[float] = None
    bias_mw: Optional[float] = None
    nmae_pct: Optional[float] = None
    mean_actual_mw: Optional[float] = None
    mean_forecast_mw: Optional[float] = None
    max_over_forecast_mw: Optional[float] = None
    max_under_forecast_mw: Optional[float] = None


class DayResponse(BaseModel):
    delivery_day: str
    decision_cutoff_utc: str
    series: list[SeriesPoint]
    summary: Summary


class HourMetric(BaseModel):
    hour: int
    mae_mw: float
    bias_mw: float


class DayMetric(BaseModel):
    date: str
    mae_mw: float
    bias_mw: float
    mean_actual_mw: float


class HistogramBin(BaseModel):
    bin_start_mw: float
    bin_end_mw: float
    count: int


class MetricsResponse(BaseModel):
    date_from: str
    date_to: str
    summary: Summary
    by_hour: list[HourMetric]
    by_day: list[DayMetric]
    histogram: list[HistogramBin]


class DaysResponse(BaseModel):
    days: list[str]
    decision_cutoff_hour_utc: int
