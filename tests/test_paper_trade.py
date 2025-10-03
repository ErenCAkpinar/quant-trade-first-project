from __future__ import annotations

import pandas as pd
import pytest

from quantbobe.execution.broker_dummy import DummyBroker
from quantbobe.execution.router import ExecutionRouter
from quantbobe.execution.slippage import SlippageModel


def test_dummy_broker_paper_trade_generates_expected_return():
    broker = DummyBroker(cash=100_000.0)
    slippage = SlippageModel(spread_bps=0.0, impact_k=0.0)
    router = ExecutionRouter(slippage)

    prices = pd.Series({"AAA": 100.0})
    starting_equity = broker.mark_to_market(prices)

    target_weights = pd.Series({"AAA": 0.5})
    current_weights = pd.Series({"AAA": 0.0})
    slices = router.reconcile_positions(
        target_weights,
        current_weights,
        prices,
        starting_equity,
    )
    orders = router.build_orders(slices, starting_equity)
    for ticket in orders:
        trade_price = ticket.limit_price or prices[ticket.symbol]
        qty = ticket.qty if ticket.side == "buy" else -ticket.qty
        broker.submit_order(ticket.symbol, qty, trade_price)

    # Mark-to-market with unchanged prices should keep equity steady after execution
    equity_after_trade = broker.mark_to_market(prices)
    assert equity_after_trade == pytest.approx(starting_equity, rel=1e-6)

    new_prices = pd.Series({"AAA": 110.0})
    ending_equity = broker.mark_to_market(new_prices)
    paper_return = (ending_equity - starting_equity) / starting_equity

    assert paper_return == pytest.approx(0.05, rel=1e-6)
