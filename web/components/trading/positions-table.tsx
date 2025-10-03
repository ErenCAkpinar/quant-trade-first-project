"use client";

import { useMemo, useState } from "react";
import classNames from "classnames";

import { usePolling } from "@/components/hooks/usePolling";

interface AlpacaPosition {
  symbol: string;
  qty: string;
  avg_entry_price: string;
  current_price: string;
  market_value: string;
  unrealized_pl: string;
  unrealized_plpc: string;
  side: "long" | "short";
  change_today: string;
}

interface PositionsTableProps {
  initialPositions: AlpacaPosition[];
}

export function PositionsTable({ initialPositions }: PositionsTableProps) {
  const { data: positions } = usePolling<AlpacaPosition[]>(
    "/api/alpaca/positions",
    initialPositions,
    { transform: (payload) => (Array.isArray(payload) ? payload : []), interval: 6000 }
  );

  const [view, setView] = useState<"all" | "long" | "short">("all");

  const filtered = useMemo(() => {
    if (!positions) return [];
    if (view === "all") return positions;
    return positions.filter((pos) => pos.side === view);
  }, [positions, view]);

  return (
    <section className="card space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Portfolio Positions</h2>
          <p className="text-sm text-zinc-400">Live positions streaming from Alpaca.</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {[
            { key: "all", label: "All" },
            { key: "long", label: "Long" },
            { key: "short", label: "Short" }
          ].map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setView(key as any)}
              className={classNames(
                "rounded-full px-3 py-1 transition",
                view === key ? "bg-primary/20 text-primary" : "bg-white/5 text-zinc-300 hover:text-white"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </header>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10 text-sm">
          <thead className="text-left text-xs uppercase text-zinc-400">
            <tr>
              <th className="py-2 pr-4">Symbol</th>
              <th className="py-2 pr-4">Side</th>
              <th className="py-2 pr-4 text-right">Quantity</th>
              <th className="py-2 pr-4 text-right">Avg Price</th>
              <th className="py-2 pr-4 text-right">Last Price</th>
              <th className="py-2 pr-4 text-right">Market Value</th>
              <th className="py-2 pr-4 text-right">Unrealized P/L</th>
              <th className="py-2 pr-4 text-right">P/L %</th>
              <th className="py-2 pr-4 text-right">Change Today</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-zinc-200">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="py-6 text-center text-zinc-500">
                  No positions in this view.
                </td>
              </tr>
            )}
            {filtered.map((position) => (
              <tr key={position.symbol}>
                <td className="py-2 pr-4 font-semibold">{position.symbol}</td>
                <td className="py-2 pr-4 capitalize">{position.side}</td>
                <td className="py-2 pr-4 text-right">{formatNumber(position.qty)}</td>
                <td className="py-2 pr-4 text-right">{formatCurrency(position.avg_entry_price)}</td>
                <td className="py-2 pr-4 text-right">{formatCurrency(position.current_price)}</td>
                <td className="py-2 pr-4 text-right">{formatCurrency(position.market_value)}</td>
                <td className="py-2 pr-4 text-right" data-positive={Number(position.unrealized_pl) >= 0}>
                  {formatCurrency(position.unrealized_pl)}
                </td>
                <td
                  className={classNames(
                    "py-2 pr-4 text-right",
                    Number(position.unrealized_plpc) >= 0 ? "text-emerald-300" : "text-rose-300"
                  )}
                >
                  {formatPercent(position.unrealized_plpc)}
                </td>
                <td className="py-2 pr-4 text-right">{formatPercent(position.change_today)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function formatNumber(value?: string) {
  const num = Number(value ?? "0");
  return Number.isFinite(num) ? num.toLocaleString() : "0";
}

function formatCurrency(value?: string) {
  const num = Number(value ?? "0");
  return Number.isFinite(num)
    ? num.toLocaleString(undefined, { style: "currency", currency: "USD" })
    : "$0";
}

function formatPercent(value?: string) {
  const num = Number(value ?? "0");
  if (!Number.isFinite(num)) return "0%";
  return `${(num * 100).toFixed(2)}%`;
}
