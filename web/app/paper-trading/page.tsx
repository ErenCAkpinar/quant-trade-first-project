import Link from "next/link";

import { AccountSummary } from "@/components/trading/account-summary";
import { PositionsTable } from "@/components/trading/positions-table";
import { OrdersPanel } from "@/components/trading/orders-panel";
import { LivePnlCard } from "@/components/trading/live-pnl-card";
import { PortfolioHistory } from "@/components/trading/portfolio-history";
import { MarketOverview } from "@/components/trading/market-overview";
import { TradeLedger } from "@/components/trading/trade-ledger";
import { loadTradingData, WATCH_SYMBOLS } from "@/lib/server/trading-data";

export const dynamic = "force-dynamic";

export default async function PaperTradingPage() {
  const data = await loadTradingData();

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold text-white">Paper Trading Operations</h1>
        <p className="max-w-3xl text-sm text-zinc-400">
          Mirror the live stack in a safe environment. Keep the Python live runner on, monitor fills in real time, and
          graduate flows to production once checklist gates turn green.
        </p>
      </header>

      <section className="card space-y-3">
        <h2 className="text-xl font-semibold text-white">Runbook</h2>
        <p className="text-sm text-zinc-300">
          Start the continuous paper loop from the CLI. The site streams the resulting P&amp;L directly from
          <code className="mx-1 rounded bg-black/40 px-1 py-0.5 text-xs">reports/live_pnl.csv</code>.
        </p>
        <div className="rounded-2xl border border-white/10 bg-black/40 p-4 text-xs font-mono text-zinc-200">
          <pre>
{`python3 -m src.quantbobe.live.run_live --config src/quantbobe/config/default.yaml
# ensure ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY are exported in this shell`}
          </pre>
        </div>
        <p className="text-xs text-zinc-500">
          Need credentials? Store them in <code className="mx-1 rounded bg-black/40 px-1 py-0.5">.env</code> and load with
          <code className="mx-1 rounded bg-black/40 px-1 py-0.5">python -m dotenv</code> or export manually.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-3">
        <AccountSummary initialAccount={data.snapshot.account} initialClock={data.snapshot.clock} />
        <LivePnlCard initial={data.pnlHistory} />
        <MarketOverview symbols={WATCH_SYMBOLS} initialQuotes={data.watchlist} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <PortfolioHistory series={data.portfolioHistory} title="Paper Portfolio Equity" />
          <PositionsTable initialPositions={data.snapshot.positions} />
        </div>
        <OrdersPanel initialOpenOrders={data.snapshot.openOrders} initialHistory={data.orderHistory} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <TradeLedger trades={data.trades} />
        <section className="card space-y-4">
          <header>
            <h2 className="text-xl font-semibold text-white">Promotion Checklist</h2>
            <p className="text-sm text-zinc-400">
              Graduate to live once controls, redundancy, and guardrails are satisfied.
            </p>
          </header>
          <ul className="space-y-3 text-sm text-zinc-300">
            <li>✔️ Redundancy checklist from <Link href="/status" className="text-primary">Status</Link> page passes.</li>
            <li>✔️ Impact &amp; slippage remain within <code>k√(Q/ADV)</code> limits.</li>
            <li>✔️ Execution-aware Kelly ≤ 0.5 × plain Kelly.</li>
            <li>✔️ Manual review of latest fills and portfolio drift.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
