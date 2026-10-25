"""Application configuration and domain assumptions.

Everything the business logic depends on that is a *judgment call* (rather than
something the brief hands us) lives here, so it is easy to find, change, and
explain during review.
"""
from __future__ import annotations

from datetime import date

# --- Scope: the brief restricts us to purchase decisions for January 2026. ---
MONTH_START = date(2026, 1, 1)
MONTH_END = date(2026, 1, 31)

# --- Elexon BMRS (Insights) public API. No auth required. ---
ELEXON_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
WINDFOR_STREAM = f"{ELEXON_BASE}/datasets/WINDFOR/stream"
FUELHH_STREAM = f"{ELEXON_BASE}/datasets/FUELHH/stream"

# --- Decision-time assumption (OUR judgment, stated openly) --------------------
# The brief says purchase decisions are made "one day before the delivery day".
# The GB day-ahead auction (EPEX/N2EX) gate closes late morning the day before
# delivery. We therefore treat the information cut-off for a delivery day D as
# 11:00 UTC on D-1, and only use WIND forecasts published at or before that
# instant. Using a later forecast would leak information the trader never had.
DECISION_CUTOFF_HOUR_UTC = 11

# Sign convention for forecast error used everywhere in the app:
#   error = forecast - actual
#   positive error  -> we OVER-forecast wind (risk: under-bought thermal)
#   negative error  -> we UNDER-forecast wind (risk: over-bought thermal)
ERROR_IS_FORECAST_MINUS_ACTUAL = True
