# Quant BOBE Web

Next.js front-end that surfaces the Quant BOBE strategy, performance analytics, and documentation.

## Getting Started

```bash
cd web
npm install
npm run dev
```

The app reads live artefacts from the repository root:

- `src/quantbobe/config/default.yaml` – configuration summary
- `reports/trades.csv` – trade ledger (backtests + live)
- `reports/live_pnl.csv` – live equity and cash series
- `README.md` – documentation content

Update those files via the existing Python CLI (ingest/backtest/live) and refresh the UI to see changes.

## Tech Stack

- Next.js 14 (App Router, TypeScript)
- Tailwind CSS + Typography plugin
- Plotly for interactive charts
- Node file-system APIs for zero-setup data access

## Directory Layout

```
web/
├─ app/                # Route segments & API handlers
├─ components/         # UI primitives & dashboards
├─ lib/                # Data access helpers
└─ public/             # Static assets
```

## Deployment Notes

- Configure environment variables to point to Alpaca keys if needed by future server actions.
- On Vercel/Netlify, set the root directory to `web` and install dependencies automatically.
- The site expects repository artefacts at runtime; include them when deploying or adjust the data layer to fetch from an API.
