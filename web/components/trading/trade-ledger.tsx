import { TradeLogRow } from "@/lib/repo";

interface TradeLedgerProps {
  trades: TradeLogRow[];
  title?: string;
}

export function TradeLedger({ trades, title = "Recent Trades" }: TradeLedgerProps) {
  const rows = trades.slice(-20).reverse();
  return (
    <section className="card space-y-4">
      <header>
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        <p className="text-sm text-zinc-400">Last 20 executions from combined sleeves and live runs.</p>
      </header>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10 text-sm">
          <thead className="text-left text-xs uppercase text-zinc-400">
            <tr>
              <th className="py-2 pr-4">Date</th>
              <th className="py-2 pr-4">Symbol</th>
              <th className="py-2 pr-4 text-right">Quantity</th>
              <th className="py-2 pr-4 text-right">Price</th>
              <th className="py-2 pr-4 text-right">Notional</th>
              <th className="py-2 pr-4">Sleeve</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-zinc-200">
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-zinc-500">
                  No trades recorded yet. Run the backtest or live loop to populate this table.
                </td>
              </tr>
            )}
            {rows.map((trade, idx) => (
              <tr key={`${trade.date}-${trade.symbol}-${idx}`}>
                <td className="py-2 pr-4">{trade.date}</td>
                <td className="py-2 pr-4 font-semibold">{trade.symbol}</td>
                <td className="py-2 pr-4 text-right">{trade.quantity.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                <td className="py-2 pr-4 text-right">${trade.price.toFixed(2)}</td>
                <td className="py-2 pr-4 text-right">${trade.notional.toFixed(2)}</td>
                <td className="py-2 pr-4 uppercase tracking-wide">{trade.sleeve}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
