import { useState } from "react";
import ForecastView from "./components/ForecastView";
import AccuracyView from "./components/AccuracyView";

type Tab = "forecast" | "accuracy";

export default function App() {
  const [tab, setTab] = useState<Tab>("forecast");

  return (
    <div className="app">
      <header className="site-header">
        <h1>Day-Ahead Wind Forecast Portal</h1>
        <p>
          National wind generation forecast vs actuals (Elexon BMRS) for GB
          day-ahead procurement, January 2026.
        </p>
      </header>

      <nav className="tabs">
        <button
          className={`tab ${tab === "forecast" ? "active" : ""}`}
          onClick={() => setTab("forecast")}
        >
          Forecast
        </button>
        <button
          className={`tab ${tab === "accuracy" ? "active" : ""}`}
          onClick={() => setTab("accuracy")}
        >
          Forecast accuracy
        </button>
      </nav>

      {tab === "forecast" ? <ForecastView /> : <AccuracyView />}

      <footer className="footer">
        Data: Elexon BMRS (WINDFOR, FUELHH). Forecast shown is the latest vintage
        published by 11:00 UTC the day before delivery, so it reflects only what a
        trader knew at decision time.
      </footer>
    </div>
  );
}
