import { AccountSummary } from "@/components/trading/account-summary";
import { PositionsTable } from "@/components/trading/positions-table";
import { OrdersPanel } from "@/components/trading/orders-panel";
import { LivePnlCard } from "@/components/trading/live-pnl-card";
import { PortfolioHistory } from "@/components/trading/portfolio-history";
import { MarketOverview } from "@/components/trading/market-overview";
import { loadTradingData, WATCH_SYMBOLS } from "@/lib/server/trading-data";

export const dynamic = "force-dynamic";

export default async function TradingPage() {
  const { snapshot, pnlHistory, orderHistory, portfolioHistory, watchlist } = await loadTradingData();

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold text-white">Trading Control Center</h1>
        <p className="max-w-3xl text-sm text-zinc-400">
          Live account telemetry, execution posture, and market dashboards powered directly by Alpaca and Yahoo Finance.
          Keep the Python paper/live loop running to continuously stream fills and P&L back to this console.
        </p>
      </header>

      <div className="grid gap-6 xl:grid-cols-3">
        <AccountSummary initialAccount={snapshot.account} initialClock={snapshot.clock} />
        <LivePnlCard initial={pnlHistory} />
        <MarketOverview symbols={WATCH_SYMBOLS} initialQuotes={watchlist} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <PortfolioHistory series={portfolioHistory} />
          <PositionsTable initialPositions={snapshot.positions} />
        </div>
        <OrdersPanel initialOpenOrders={snapshot.openOrders} initialHistory={orderHistory} />
      </div>
    </div>
  );
}
