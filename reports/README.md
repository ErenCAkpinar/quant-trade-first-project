# Reports Directory

Generated performance reports, trade logs, and live PnL outputs are written here by the CLI commands:

```bash
python -m src.quantbobe.cli backtest --config src/quantbobe/config/default.yaml
python -m src.quantbobe.cli report --config src/quantbobe/config/default.yaml
python -m src.quantbobe.live.run_live --config src/quantbobe/config/default.yaml
```

The repository only keeps lightweight summary artifacts. Full HTML reports, CSV exports, and large JSON files are excluded from version control.

## Sample Output

The image below shows a condensed example of the equity curve card that the HTML report renders.

![Sample report card](sample-report.png)

Re-generate the full report locally after every backtest:

```bash
make report
```

The command will write fresh outputs to this directory.
