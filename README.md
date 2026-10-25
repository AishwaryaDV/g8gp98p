# Day-Ahead Wind Forecast Portal

A web app for a GB energy utility's day-ahead power-procurement team. It helps them
(1) see the **latest wind generation forecast available at decision time**, and
(2) **quantify how accurate that forecast has been**, so they can size how much
thermal power to additionally procure from the day-ahead market.

Scope is deliberately limited (per the brief) to **national wind generation** —
actuals and forecasts from **Elexon BMRS** alone — for **purchase decisions made in
January 2026**.

## Why forecast accuracy matters here

Procurement decisions are locked in the day *before* delivery, using a wind
forecast. If the forecast is too optimistic, the utility under-buys thermal and is
exposed to expensive intraday/balancing prices; too pessimistic, and it over-buys.
Quantifying the forecast error is therefore quantifying procurement risk.

## Data sources (Elexon BMRS, public, no auth)

| Dataset | Use | Key fields |
|---|---|---|
| `WINDFOR` | Wind generation **forecast** (hourly, re-issued over time) | `publishTime`, `startTime`, `generation` |
| `FUELHH` (`fuelType=WIND`) | **Actual** wind generation (half-hourly) | `startTime`, `generation` |

## Repository structure

```
.
├── backend/                 # Python FastAPI service (all domain logic)
│   ├── app/
│   │   ├── config.py        # scope + assumptions (decision cut-off, month, URLs)
│   │   ├── elexon.py        # Elexon BMRS client + in-memory cache
│   │   ├── alignment.py     # no-look-ahead vintage selection + resolution align
│   │   ├── metrics.py       # MAE / RMSE / bias / nMAE, by hour / day / histogram
│   │   ├── schemas.py       # Pydantic response models (the API contract)
│   │   └── main.py          # FastAPI routes
│   ├── tests/               # pytest unit tests (metrics + vintage selection)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # React + TypeScript (Vite) UI  [in progress]
└── README.md
```

## Key engineering decisions & assumptions

These were reasoned from the brief and the shape of the data:

1. **No look-ahead (decision-time forecast).** For a delivery day `D`, we only use
   forecasts published at or before **11:00 UTC on `D-1`** — a realistic GB
   day-ahead auction cut-off. Per target hour we take the *latest* such vintage.
   Using a later forecast would leak information the trader never had and overstate
   accuracy. The cut-off is a single configurable value in `config.py`.
2. **Resolution alignment.** Actuals are half-hourly, forecasts hourly. The forecast
   carries no sub-hourly information, so we aggregate actuals to the hourly grid
   (mean MW of the two settlement periods) rather than fabricate 30-minute forecast
   detail.
3. **Metrics.** MAE (typical miss), RMSE (penalises large misses), **bias/MBE**
   (directional — reveals systematic over/under-forecasting), and **nMAE %**
   (MAE ÷ mean actual) in preference to MAPE, which is unstable during low-wind hours.
4. **Error sign convention.** `error = forecast − actual`; positive = over-forecast.

## Running locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload       # http://localhost:8000
pytest -q                           # run unit tests
```

API docs (Swagger) are served at `http://localhost:8000/docs`.

Key endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/days` | Available January-2026 delivery days + the cut-off hour |
| `GET /api/forecast/{YYYY-MM-DD}` | Decision-time forecast vs actual for one day + summary |
| `GET /api/metrics?from=&to=` | Accuracy metrics over a range (summary, by hour, by day, histogram) |

### With Docker

```bash
cd backend
docker build -t wind-backend .
docker run -p 8000:8000 wind-backend
```

### Frontend

_In progress — see `frontend/` (React + TypeScript + Vite)._

## Deployment

- **Backend:** Render (builds the `backend/Dockerfile` in the cloud).
- **Frontend:** Vercel (static Vite build).

> **Live app:** _link to be added once deployed._

## Use of AI tools

AI coding assistance (Claude Code) was used to help with implementation,
scaffolding, and boilerplate. **All technical and engineering decisions — the
no-look-ahead vintage-selection approach, the day-ahead cut-off assumption, the
resolution-alignment method, the choice of accuracy metrics, and the overall
architecture — were made and reasoned by the author** after studying the scope and
requirements. AI was used to accelerate writing the code that implements those
decisions, not to make them.
