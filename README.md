# Quant BOBE (Equities + Alpaca Paper)

Best-of-Breed Ensemble (BOBE) equities strategy scaffold with Alpaca paper trading. The public repository covers research, backtesting, reporting and the Alpaca paper-trading adapter; proprietary data and live-money execution stay private.

## Quickstart

```bash
python3 -V
make setup
cp .env.example .env
# fill in Alpaca paper credentials

# Pull sample market data and fundamentals
python -m src.quantbobe.cli ingest --config src/quantbobe/config/default.yaml

# Run a full backtest + report (results saved under reports/ and reports/runs/)
python -m src.quantbobe.cli backtest --config src/quantbobe/config/default.yaml

# During market hours
python -m src.quantbobe.live.run_live --config src/quantbobe/config/default.yaml
```

## Architecture

```text
            ┌──────────────┐
            │   CLI / UI   │
            └──────┬───────┘
                   │
          ┌────────▼────────┐
          │   Strategy API  │
          └────────┬────────┘
                   │
    ┌──────────────▼──────────────┐
    │ Feature Sleeves (C, D, …)   │
    └──────────────┬──────────────┘
                   │
        ┌──────────▼──────────┐
        │ Portfolio & Costs   │
        └──────────┬──────────┘
                   │
          ┌────────▼────────┐
          │ Execution Layer │
          └─────────────────┘
```

Signals are generated per sleeve, combined under shared risk constraints, passed through transaction-cost-aware sizing, and executed via the broker adapters.

## Event Loop & Costs Model

- **Backtest engine** replays daily bars, applies sleeves, and sizes trades at portfolio level.
- **Costs** combine bid/ask spread, market-impact (Kyle lambda), borrow for shorts, and slippage buffers.
- **Live loop** (see `LIVE_TRADING_SETUP.md`) refreshes data every `poll_interval_sec`, reconciles filled orders, and records live P&L snapshots.

## Research Workflow

- Configurable rebalance frequency (for example monthly or daily) and rolling lookback windows per sleeve.
- `RegimeDetector` computes rolling breadth, volatility, dispersion and correlation scores that scale sleeve risk.
- Use `tests/test_backtest_engine.py` and the `reports/runs/` artifacts to compare quantitative changes across commits.
- Walk-forward validation (rolling train/test windows) is not implemented yet; see the roadmap.

## Reports & Reproducibility

- `python -m src.quantbobe.cli backtest` now writes run artifacts to `reports/runs/<timestamp>/`:
  - `metrics.json` with CAGR, Sharpe, drawdowns, VaR, turnover.
  - `positions.csv`, `equity.csv`, `pnl.csv`, and `trades.csv` snapshots.
  - `config.yaml` (exact config used) and `summary.md` (human-readable log).

## Configuration Example

```yaml
reports:
  html: "reports/equities_bobe.html"
  trades_csv: "reports/trades.csv"
  runs_dir: "reports/runs"
portfolio:
  target_vol_ann: 0.10
  max_name_weight: 0.02
```

Fine-tune sleeves under `src/quantbobe/config/default.yaml` or author new YAML files and point the CLI at them.

## Project Layout

- `src/quantbobe/` — strategy, features, portfolio sizing, execution adapters.
- `tests/` — pytest suite covering engine invariants, costs, and regimes.
- `data/` — curated reference universes (`sp100.csv`); generated caches ignored by Git.
- `reports/` — reproducibility artifacts (HTML, CSV, metrics) written locally.
- `web/` — Next.js dashboard for visualization (optional).

## Make Targets

- `make setup` — install Python + Node dependencies.
- `make backtest` — run the default backtest.
- `make report` — regenerate HTML report.
- `make live` — start live Alpaca paper loop.

## Known Limitations

- Alpaca data feed latencies can impact minute-level rebalancing; swap adapters for production.
- Backtests assume daily bars; intraday extensions require new ingestion paths.
- Position reconciliation is paper-trading only; production brokers need custom compliance layers.

## Roadmap

- [ ] Walk-forward validation with rolling train/test windows.
- [ ] Expand `features/` to include volatility breakout sleeve.
- [ ] Add Docker image publishing in CI.
- [ ] Surface backtest runs in `web/` dashboard via API.
- Track issues and progress: https://github.com/ErenCAkpinar/quant-trade-first-project/issues

## Public vs Private Scope

Public repo = research tooling, reproducible backtests, sample data, and web demo.  
Private repo = proprietary data ingestion, live execution adapters, AutoML/GA/RL discovery, and hyperparameter archives.

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.
