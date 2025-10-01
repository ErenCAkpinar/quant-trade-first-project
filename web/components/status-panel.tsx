import { readSummary } from "@/lib/repo";

export async function StatusPanel() {
  const summary = await readSummary();
  const config = summary.config as any;
  const { pnl, recentTrades } = summary;
  const liveSettings = config?.live ?? {};
  const broker = liveSettings.broker ?? "alpaca";

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <article className="card space-y-4">
        <header className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Runtime Snapshot</h3>
          <span className="badge">Broker: {String(broker).toUpperCase()}</span>
        </header>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-zinc-400">Poll Interval</dt>
            <dd className="font-mono">{liveSettings.poll_interval_sec ?? 60}s</dd>
          </div>
          <div>
            <dt className="text-zinc-400">Start Cash</dt>
            <dd className="font-mono">
              ${Number(liveSettings.paper_start_cash ?? 0).toLocaleString(undefined, { minimumFractionDigits: 0 })}
            </dd>
          </div>
          <div>
            <dt className="text-zinc-400">Symbols</dt>
            <dd className="font-mono">
              {Array.isArray(config?.data?.symbols) && config.data.symbols.length > 0
                ? `${config.data.symbols.length} custom`
                : config?.data?.equities_universe ?? "N/A"}
            </dd>
          </div>
          <div>
            <dt className="text-zinc-400">Sleeves Enabled</dt>
            <dd className="font-mono">
              {(Object.entries(config?.sleeves ?? {}) as Array<[string, any]>)
                .filter(([, val]) => val?.enabled)
                .map(([key]) => key)
                .join(", ") || "None"}
            </dd>
          </div>
        </dl>
        <div className="rounded-xl border border-white/5 bg-black/20 p-4 text-sm text-zinc-300">
          <p>
            Latest equity: {pnl ? `$${pnl.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "No live data"}
          </p>
          <p>
            Latest cash: {pnl ? `$${pnl.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "No live data"}
          </p>
        </div>
      </article>
      <article className="card space-y-4">
        <header className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Recent Trades</h3>
          <span className="badge">Last 5 fills</span>
        </header>
        {recentTrades.length === 0 ? (
          <p className="text-sm text-zinc-400">No trades recorded yet. Run a backtest or live session to populate logs.</p>
        ) : (
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-zinc-400">
                <tr>
                  <th className="pb-2">Date</th>
                  <th className="pb-2">Symbol</th>
                  <th className="pb-2 text-right">Qty</th>
                  <th className="pb-2 text-right">Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/90">
                {recentTrades.map((trade) => (
                  <tr key={`${trade.date}-${trade.symbol}`} className="hover:bg-white/5">
                    <td className="py-2">{trade.date}</td>
                    <td className="py-2 uppercase">{trade.symbol}</td>
                    <td className="py-2 text-right font-mono">{trade.quantity.toFixed(2)}</td>
                    <td className="py-2 text-right font-mono">${trade.price.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </div>
  );
}
