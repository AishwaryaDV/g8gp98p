# Day-Ahead Wind Forecast Portal

A web app for a GB energy utility's day-ahead power procurement team. It helps them
do two things: first, see the latest wind generation forecast available at decision
time, and second, quantify how accurate that forecast has been. With both in hand
they can size how much thermal power to additionally procure from the day-ahead
market.

Scope is deliberately limited (per the brief) to national wind generation, using
actuals and forecasts from Elexon BMRS alone, for purchase decisions made in
January 2026.

## Why forecast accuracy matters here

Procurement decisions are locked in the day before delivery, using a wind forecast.
If the forecast is too optimistic, the utility under buys thermal and is exposed to
expensive intraday and balancing prices. If it is too pessimistic, the utility over
buys. Quantifying the forecast error is therefore the same as quantifying
procurement risk.

## Data sources (Elexon BMRS, public, no auth)

| Dataset | Use | Key fields |
|---|---|---|
| `WINDFOR` | Wind generation forecast (hourly, re-issued over time) | `publishTime`, `startTime`, `generation` |
| `FUELHH` (`fuelType=WIND`) | Actual wind generation (half-hourly) | `startTime`, `generation` |

## Repository structure

```
.
├── backend/                 # Python FastAPI service (all domain logic)
│   ├── app/
│   │   ├── config.py        # scope and assumptions (decision cut-off, month, URLs)
│   │   ├── elexon.py        # Elexon BMRS client and in-memory cache
│   │   ├── alignment.py     # no-lookahead vintage selection and resolution align
│   │   ├── metrics.py       # MAE, RMSE, bias, nMAE, by hour / day / histogram
│   │   ├── schemas.py       # Pydantic response models (the API contract)
│   │   └── main.py          # FastAPI routes
│   ├── tests/               # pytest unit tests (metrics and vintage selection)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # React and TypeScript (Vite) UI
└── README.md
```

## Key engineering decisions and assumptions

These were reasoned from the brief and the shape of the data:

1. No lookahead (decision-time forecast). For a delivery day `D`, we only use
   forecasts published at or before 11:00 UTC on `D-1`, a realistic GB day-ahead
   auction cut-off. Per target hour we take the latest such vintage. Using a later
   forecast would leak information the trader never had and would overstate
   accuracy. The cut-off is a single configurable value in `config.py`.
2. Resolution alignment. Actuals are half-hourly, forecasts are hourly. The forecast
   carries no sub-hourly information, so we aggregate actuals to the hourly grid
   (mean MW of the two settlement periods) rather than fabricate 30 minute forecast
   detail.
3. Metrics. MAE (typical miss), RMSE (penalises large misses), bias or MBE
   (directional, reveals systematic over or under forecasting), and nMAE percent
   (MAE divided by mean actual) in preference to MAPE, which is unstable during low
   wind hours.
4. Error sign convention. `error = forecast - actual`, so positive means over
   forecast.

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
| `GET /api/days` | Available January 2026 delivery days and the cut-off hour |
| `GET /api/forecast/{YYYY-MM-DD}` | Decision-time forecast vs actual for one day, plus summary |
| `GET /api/metrics?from=&to=` | Accuracy metrics over a range (summary, by hour, by day, histogram) |

### Frontend

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

Set `VITE_API_URL` to point at the backend (defaults to `http://localhost:8000`).

### With Docker

```bash
cd backend
docker build -t wind-backend .
docker run -p 8000:8000 wind-backend
```

## Deployment

Both services are hosted on Render (free tier):

- Backend: Render Web Service, built from `backend/Dockerfile`.
- Frontend: Render Static Site, built from the Vite project.

Note on the brief: it suggested Vercel or Heroku. We use Render instead because
Heroku no longer offers a free tier, and Render lets us host both the Docker backend
and the static frontend for free on one platform. The deployment is public and
reachable, which is the underlying requirement.

> Live app: link to be added once deployed.

## Use of AI tools

AI coding assistance (Claude Code) was used to help with implementation,
scaffolding, and boilerplate. All technical and engineering decisions, including the
no-lookahead vintage selection approach, the day-ahead cut-off assumption, the
resolution alignment method, the choice of accuracy metrics, and the overall
architecture, were made and reasoned by the author after studying the scope and
requirements. AI was used to speed up writing the code that implements those
decisions, not to make them.
