# Reports Directory

Generated performance reports, trade logs, and live PnL outputs are written here by the CLI commands:

```bash
python -m src.quantbobe.cli backtest --config src/quantbobe/config/default.yaml
python -m src.quantbobe.cli report --config src/quantbobe/config/default.yaml
python -m src.quantbobe.live.run_live --config src/quantbobe/config/default.yaml
```

The repository keeps no generated reports. Full HTML reports, CSV exports and large JSON files are excluded from version control.

Re-generate the full report locally after every backtest:

```bash
make report
```

The command will write fresh outputs to this directory.
