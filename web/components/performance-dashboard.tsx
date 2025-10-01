import { readLivePnlCsv, readTradesCsv } from "@/lib/repo";
import { LineChart } from "@/components/charts/line-chart";

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp);
  return Number.isNaN(date.valueOf()) ? timestamp : date.toLocaleString();
}

export async function PerformanceDashboard() {
  const pnl = await readLivePnlCsv();
  const trades = await readTradesCsv();

  const pnlSeries = pnl.map((point) => ({ x: formatTimestamp(point.timestamp), y: point.equity }));
  const cashSeries = pnl.map((point) => ({ x: formatTimestamp(point.timestamp), y: point.cash }));

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <LineChart title="Equity Curve" data={pnlSeries} yLabel="Equity" />
        <LineChart title="Cash Balance" data={cashSeries} yLabel="Cash" />
      </div>
      <div className="card">
        <header className="flex items-center justify-between pb-4">
          <h3 className="text-lg font-semibold text-white">Trades Ledger</h3>
          <span className="badge">{trades.length} total trades</span>
        </header>
        {trades.length === 0 ? (
          <p className="text-sm text-zinc-400">No trades recorded yet. Run a backtest to populate reports/trades.csv.</p>
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-zinc-400">
                <tr>
                  <th className="pb-2">Date</th>
                  <th className="pb-2">Symbol</th>
                  <th className="pb-2 text-right">Qty</th>
                  <th className="pb-2 text-right">Price</th>
                  <th className="pb-2 text-right">Notional</th>
                  <th className="pb-2">Sleeve</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/90">
                {trades.slice(-200).reverse().map((trade) => (
                  <tr key={`${trade.date}-${trade.symbol}-${trade.notional}`} className="hover:bg-white/5">
                    <td className="py-2">{trade.date}</td>
                    <td className="py-2 uppercase">{trade.symbol}</td>
                    <td className="py-2 text-right font-mono">{trade.quantity.toFixed(2)}</td>
                    <td className="py-2 text-right font-mono">${trade.price.toFixed(2)}</td>
                    <td className="py-2 text-right font-mono">${trade.notional.toFixed(2)}</td>
                    <td className="py-2 font-mono">{trade.sleeve}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
