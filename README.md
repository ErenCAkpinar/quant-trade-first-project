# Quant BOBE (Equities + Alpaca Paper)

Production-ready scaffold for the Best-of-Breed Ensemble (BOBE) equities strategy with Alpaca paper trading.

## Quickstart

```bash
python -V
make setup
cp .env.example .env  # add your Alpaca paper credentials
python -m src.quantbobe.cli ingest --config src/quantbobe/config/default.yaml
python -m src.quantbobe.cli backtest --config src/quantbobe/config/default.yaml
python -m src.quantbobe.cli report --config src/quantbobe/config/default.yaml
# During market hours
python -m src.quantbobe.live.run_live --config src/quantbobe/config/default.yaml
```

## Project Layout

- `src/quantbobe/` — core library code
- `tests/` — pytest suite covering features, portfolio controls, costs, regimes
- `data/` — sample universe definitions and cached data
- `reports/` — generated performance reports and live PnL logs
- `.github/workflows/ci.yml` — CI pipeline with lint, type-check, tests

## Make Targets

- `make setup` — install dependencies
- `make backtest` — run the default backtest
- `make report` — regenerate the HTML report
- `make live` — start live Alpaca paper loop

## Notes

- Default config is equities-only using Yahoo Finance for history and Alpaca paper for execution.
- Signals and portfolio construction enforce sector and beta neutrality with volatility-targeted sizing.
- Live trading loop reconciles paper positions every minute and logs fills to `reports/live_pnl.csv`.
