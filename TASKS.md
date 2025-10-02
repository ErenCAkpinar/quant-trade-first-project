# Suggested Follow-Up Tasks

## 1. Fix spelling in the web feature grid copy
* **Issue**: Marketing copy in `web/components/feature-grid.tsx` uses the British spelling "modelling", which is inconsistent with American spellings used elsewhere in the project. Standardizing the wording avoids distracting typos in the UI copy.
* **Recommendation**: Update the string at line 12 to read "slippage modeling".

## 2. Harden regime breadth utilities against missing adjusted closes
* **Issue**: `trend_breadth` (and downstream `corr_spike`) blindly index the `adj_close` column. When the data provider only delivers raw `close` prices (e.g., reduced CSV history or fallback feeds), this raises a `KeyError` and breaks regime detection.
* **Recommendation**: Change both helpers to fall back to `close` when `adj_close` is unavailable, mirroring the defensive logic already used in `strategy.compute_sleeve_weights`.

## 3. Align README notes with the default configuration
* **Issue**: The README claims the default configuration "uses Yahoo Finance for history", but `src/quantbobe/config/default.yaml` sets `data.provider` to `"alpaca"`. The mismatch can mislead newcomers during setup.
* **Recommendation**: Update the README note (or adjust the config) so the documented default data source matches the shipped configuration.

## 4. Strengthen the backtest engine regression test
* **Issue**: `tests/test_backtest_engine.py::test_backtest_engine_executes_trades_and_applies_costs` only asserts that *some* trade occurs and the ending equity differs from the starting equity. It never checks that trading costs or borrow charges were actually applied.
* **Recommendation**: Extend the test to inspect the resulting trades or equity curve—for example, assert that trade notional reflects slippage costs or that equity declines by the estimated transaction cost on the first day—so future changes cannot silently drop execution cost logic.
