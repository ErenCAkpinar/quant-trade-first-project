import { AccountSummary } from "@/components/trading/account-summary";
import { PositionsTable } from "@/components/trading/positions-table";
import { OrdersPanel } from "@/components/trading/orders-panel";
import { LivePnlCard } from "@/components/trading/live-pnl-card";
import { PortfolioHistory } from "@/components/trading/portfolio-history";
import { MarketOverview } from "@/components/trading/market-overview";
import { TradeLedger } from "@/components/trading/trade-ledger";
import { loadTradingData, WATCH_SYMBOLS } from "@/lib/server/trading-data";

export const dynamic = "force-dynamic";

export default async function LiveTradingPage() {
  const data = await loadTradingData();

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold text-white">Live Trading Oversight</h1>
        <p className="max-w-3xl text-sm text-zinc-400">
          Production telemetry consolidating Alpaca account health, execution flow, live P&amp;L, and market context. Pair this
          with incident response and governance procedures before allowing unattended trading.
        </p>
      </header>

      <div className="grid gap-6 xl:grid-cols-3">
        <AccountSummary initialAccount={data.snapshot.account} initialClock={data.snapshot.clock} />
        <LivePnlCard initial={data.pnlHistory} />
        <MarketOverview symbols={WATCH_SYMBOLS} initialQuotes={data.watchlist} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <PortfolioHistory series={data.portfolioHistory} title="Live Portfolio Equity" />
          <PositionsTable initialPositions={data.snapshot.positions} />
        </div>
        <OrdersPanel initialOpenOrders={data.snapshot.openOrders} initialHistory={data.orderHistory} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <TradeLedger trades={data.trades} title="Execution Ledger" />
        <section className="card space-y-4">
          <header>
            <h2 className="text-xl font-semibold text-white">Risk &amp; Controls</h2>
            <p className="text-sm text-zinc-400">
              Monitor these guardrails continuously during live sessions.
            </p>
          </header>
          <ul className="space-y-3 text-sm text-zinc-300">
            <li>🛑 Enable manual kill switch on broker plus infrastructure runbooks.</li>
            <li>📉 Track drawdown braking via execution-aware Kelly (check redundancy report).</li>
            <li>📈 Compare realized slippage vs square-root impact guardrail in redundancy checklist.</li>
            <li>🧾 Archive account snapshots and order logs for compliance each session.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
