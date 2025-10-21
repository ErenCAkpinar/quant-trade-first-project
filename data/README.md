# Data Directory

The repository keeps only lightweight reference data (e.g. `sp100.csv`).
All downloaded bars, cached universes, and derived analytics are generated
locally by the CLI commands and excluded from version control.

```bash
python -m src.quantbobe.cli ingest --config src/quantbobe/config/default.yaml
```

Use the command above (or your custom configs) to populate `data/local/`
with fresh market data before running backtests or live trading.
