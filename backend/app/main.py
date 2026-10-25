"""FastAPI application: serves decision-time forecasts and accuracy metrics."""
from __future__ import annotations

from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import alignment, config, elexon, metrics, schemas

app = FastAPI(
    title="Day-Ahead Wind Forecast Portal",
    description="National wind forecast vs actuals (Elexon BMRS) for GB "
    "day-ahead procurement decisions, January 2026.",
    version="1.0.0",
)

# The frontend is served from a different origin (Vercel), so allow it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    # Best-effort warm of the in-memory cache; don't crash if Elexon is slow.
    try:
        elexon.warm_cache()
    except Exception:  # pragma: no cover - startup resilience
        pass


def _series(df: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        out.append(
            {
                "start_time": r["start_time"].isoformat(),
                "forecast": None if pd.isna(r.get("forecast")) else float(r["forecast"]),
                "actual": None if pd.isna(r.get("actual")) else float(r["actual"]),
                "error": None if pd.isna(r.get("error")) else float(r["error"]),
            }
        )
    return out


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/days", response_model=schemas.DaysResponse)
def days() -> dict:
    return {
        "days": [d.isoformat() for d in alignment.available_days()],
        "decision_cutoff_hour_utc": config.DECISION_CUTOFF_HOUR_UTC,
    }


@app.get("/api/forecast/{delivery_day}", response_model=schemas.DayResponse)
def forecast_for_day(delivery_day: date) -> dict:
    if not (config.MONTH_START <= delivery_day <= config.MONTH_END):
        raise HTTPException(422, "Date must be within January 2026.")
    df = alignment.aligned_day(delivery_day)
    if df.empty:
        raise HTTPException(404, "No data for that delivery day.")
    return {
        "delivery_day": delivery_day.isoformat(),
        "decision_cutoff_utc": alignment.decision_cutoff(delivery_day).isoformat(),
        "series": _series(df),
        "summary": metrics.summary_metrics(df),
    }


@app.get("/api/metrics", response_model=schemas.MetricsResponse)
def accuracy_metrics(
    date_from: date = Query(config.MONTH_START, alias="from"),
    date_to: date = Query(config.MONTH_END, alias="to"),
) -> dict:
    date_from = max(date_from, config.MONTH_START)
    date_to = min(date_to, config.MONTH_END)
    if date_from > date_to:
        raise HTTPException(422, "`from` must be on or before `to`.")
    df = alignment.aligned_range(date_from, date_to)
    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "summary": metrics.summary_metrics(df),
        "by_hour": metrics.metrics_by_hour(df),
        "by_day": metrics.metrics_by_day(df),
        "histogram": metrics.error_histogram(df),
    }
