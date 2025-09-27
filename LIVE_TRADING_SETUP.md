# 🚀 Live Paper Trading Setup Guide

## Quick Start

Your system is now ready! Here's how to set up live paper trading:

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
touch .env
```

Add your Alpaca credentials to `.env`:

```env
# Alpaca API Credentials (Paper Trading)
ALPACA_API_KEY_ID=your_paper_api_key_here
ALPACA_API_SECRET_KEY=your_paper_secret_key_here
ALPACA_PAPER_BASE_URL=https://paper-api.alpaca.markets
```

### 2. Get Alpaca Paper Trading Credentials

1. **Sign up**: Go to [https://alpaca.markets/](https://alpaca.markets/)
2. **Create Paper Account**: Navigate to "Paper Trading" section
3. **Generate API Keys**: Create new API keys for paper trading
4. **Copy credentials** to your `.env` file

### 3. Run the Complete Workflow

```bash
# Activate virtual environment
source venv/bin/activate

# Run backtest (already done)
make backtest

# Generate reports
make report

# Start live paper trading
python -m src.quantbobe.live.run_live --config src/quantbobe/config/default.yaml
```

### 4. What the Live System Does

- **📊 Fetches Data**: Downloads latest market data every 60 seconds
- **🧠 Runs Strategy**: Calculates momentum, quality-value, and regime signals
- **📈 Generates Orders**: Creates target portfolio weights
- **💼 Executes Trades**: Sends orders to Alpaca paper trading
- **📋 Logs Performance**: Saves P&L data to `reports/live_pnl.csv`

### 5. Monitoring

The system will show output like:
```
2025-09-26 22:51:55.123 | INFO | Starting live paper trading loop...
2025-09-26 22:51:55.123 | INFO | Fetched 1000 bars for 32 symbols
2025-09-26 22:51:55.123 | INFO | Generated target weights for 15 positions
2025-09-26 22:51:55.123 | INFO | Submitted 3 orders to Alpaca
```

### 6. Stopping the System

- Press `Ctrl+C` to stop gracefully
- The system will complete the current cycle and save state

### 7. Generated Files

- `reports/live_pnl.csv` - Real-time P&L tracking
- `reports/equities_bobe.html` - Performance reports
- Console logs with trading activity

### 8. Safety Notes

- ✅ **Paper Trading Only** - No real money at risk
- ✅ **Simulated Environment** - All trades are fake
- ✅ **Test First** - Run backtests to understand the strategy
- ✅ **Monitor Performance** - Watch the live P&L

## Troubleshooting

- **Network errors**: Check internet connection
- **Alpaca API errors**: Verify API credentials
- **Data errors**: Ensure Yahoo Finance is accessible
- **Config errors**: Check YAML syntax

## Configuration

Modify `src/quantbobe/config/default.yaml` to adjust:
- Polling frequency (`poll_interval_sec`)
- Starting cash (`paper_start_cash`)
- Strategy parameters

Your system is ready for live paper trading! 🎯
