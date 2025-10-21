from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pandas as pd
from loguru import logger
from zoneinfo import ZoneInfo

from .backtest import BacktestEngine, ReportBuilder
from .live.run_live import run_live
from .strategy import (
    aggregate_target_weights,
    build_context,
    compute_sleeve_weights,
)


def ingest_command(config_path: str) -> None:
    ctx = build_context(config_path)
    output_dir = Path(ctx.settings.data.path) / "cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    daily_path = output_dir / "daily.parquet"
    ctx.daily.to_parquet(daily_path)
    logger.info("Saved daily history to {}", daily_path)
    if not ctx.fundamentals.empty:
        fund_path = output_dir / "fundamentals.parquet"
        ctx.fundamentals.to_parquet(fund_path)
        logger.info("Saved fundamentals to {}", fund_path)


def _prepare_run_dir(ctx, config_path: str) -> Path:
    runs_root = Path(ctx.settings.reports.runs_dir)
    try:
        tz = ZoneInfo(ctx.settings.project.timezone)
    except Exception:
        tz = timezone.utc
    now = datetime.now(tz)
    run_dir = runs_root / now.strftime("%Y%m%dT%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    config_src = Path(config_path)
    if config_src.exists():
        shutil.copy(config_src, run_dir / "config.yaml")
    return run_dir


def _write_run_artifacts(
    run_dir: Path,
    result,
    trades_df: pd.DataFrame,
    summary: Dict[str, float],
) -> None:
    metrics = {}
    for key, value in summary.items():
        if value is None or (isinstance(value, float) and math.isnan(value)):
            metrics[key] = None
        else:
            metrics[key] = float(value)
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")

    trades_df.to_csv(run_dir / "trades.csv", index=False)
    result.positions.to_csv(run_dir / "positions.csv")
    result.equity_curve.to_csv(run_dir / "equity.csv", header=["equity"])
    result.pnl.to_csv(run_dir / "pnl.csv", header=["pnl"])

    summary_lines = ["# Backtest Summary"]
    for key, value in metrics.items():
        display = "N/A" if value is None else f"{value:.4f}"
        summary_lines.append(f"- **{key}**: {display}")
    (run_dir / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    logger.info("Saved reproducibility bundle to {}", run_dir)


def backtest_command(config_path: str) -> None:
    ctx = build_context(config_path)
    sleeve_weights = compute_sleeve_weights(ctx)
    closes = ctx.daily["close"].unstack("symbol")
    dates = closes.index
    aggregate = aggregate_target_weights(ctx, sleeve_weights)
    aggregate = aggregate.reindex(dates).ffill().fillna(0.0)
    daily_targets: Dict[str, pd.DataFrame] = {"portfolio": aggregate}
    engine = BacktestEngine(ctx.settings.costs)
    result = engine.run(ctx.daily, daily_targets)
    trades_df = pd.DataFrame([t.__dict__ for t in result.trades])
    if trades_df.empty:
        trades_df = pd.DataFrame(
            columns=["date", "symbol", "quantity", "price", "notional", "sleeve"]
        )
    report = ReportBuilder(result.equity_curve, trades_df, result.positions)
    report.to_html(ctx.settings.reports.html)
    report.trades_to_csv(ctx.settings.reports.trades_csv)
    summary = report.build_summary()
    run_dir = _prepare_run_dir(ctx, config_path)
    _write_run_artifacts(run_dir, result, trades_df, summary)
    logger.info("Backtest summary:")
    for key, value in summary.items():
        logger.info("  {}: {:.4f}", key, value)
    equity_out = Path(ctx.settings.reports.html).with_suffix(".equity.csv")
    result.equity_curve.to_csv(equity_out, header=["equity"])
    logger.info("Saved equity curve to {}", equity_out)


def report_command(config_path: str) -> None:
    logger.info("Regenerating backtest and report")
    backtest_command(config_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quant BOBE CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Ingest data")
    ingest.add_argument("--config", required=True)

    backtest = subparsers.add_parser("backtest", help="Run backtest")
    backtest.add_argument("--config", required=True)

    report = subparsers.add_parser("report", help="Run report generation")
    report.add_argument("--config", required=True)

    live = subparsers.add_parser("live", help="Run live paper trading")
    live.add_argument("--config", required=True)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "ingest":
        ingest_command(args.config)
    elif args.command == "backtest":
        backtest_command(args.config)
    elif args.command == "report":
        report_command(args.config)
    elif args.command == "live":
        run_live(args.config)
    else:
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
