"use client";

import { useState } from "react";
import classNames from "classnames";

import { usePolling } from "@/components/hooks/usePolling";

interface AlpacaOrder {
  id: string;
  symbol: string;
  qty: string;
  filled_qty: string;
  side: string;
  type: string;
  status: string;
  submitted_at: string;
  filled_at?: string | null;
  limit_price?: string | null;
  stop_price?: string | null;
}

interface OrdersPanelProps {
  initialOpenOrders: AlpacaOrder[];
  initialHistory: AlpacaOrder[];
}

export function OrdersPanel({ initialOpenOrders, initialHistory }: OrdersPanelProps) {
  const [tab, setTab] = useState<"open" | "history">("open");

  const { data: openOrders } = usePolling<AlpacaOrder[]>(
    "/api/alpaca/orders",
    initialOpenOrders,
    { transform: (payload) => (Array.isArray(payload) ? payload : []), interval: 5000 }
  );
  const { data: history } = usePolling<AlpacaOrder[]>(
    "/api/alpaca/orders?scope=history",
    initialHistory,
    { transform: (payload) => (Array.isArray(payload) ? payload : []), interval: 15000 }
  );

  const rows = tab === "open" ? openOrders : history;

  return (
    <section className="card space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Order Flow</h2>
          <p className="text-sm text-zinc-400">
            Open orders refresh every 5s; recent executions update every 15s.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {[
            { key: "open", label: "Open Orders" },
            { key: "history", label: "Recent Executions" }
          ].map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key as any)}
              className={classNames(
                "rounded-full px-3 py-1 transition",
                tab === key ? "bg-primary/20 text-primary" : "bg-white/5 text-zinc-300 hover:text-white"
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
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4 text-right">Quantity</th>
              <th className="py-2 pr-4 text-right">Filled</th>
              <th className="py-2 pr-4 text-right">Limit</th>
              <th className="py-2 pr-4 text-right">Stop</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Submitted</th>
              <th className="py-2 pr-4">Filled</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-zinc-200">
            {rows.length === 0 && (
              <tr>
                <td colSpan={10} className="py-6 text-center text-zinc-500">
                  {tab === "open" ? "No open orders." : "No executions found in recent history."}
                </td>
              </tr>
            )}
            {rows.map((order) => (
              <tr key={order.id}>
                <td className="py-2 pr-4 font-semibold">{order.symbol}</td>
                <td className="py-2 pr-4 capitalize">{order.side}</td>
                <td className="py-2 pr-4 uppercase">{order.type}</td>
                <td className="py-2 pr-4 text-right">{Number(order.qty).toLocaleString()}</td>
                <td className="py-2 pr-4 text-right">{Number(order.filled_qty).toLocaleString()}</td>
                <td className="py-2 pr-4 text-right">{formatPrice(order.limit_price)}</td>
                <td className="py-2 pr-4 text-right">{formatPrice(order.stop_price)}</td>
                <td className="py-2 pr-4 text-xs uppercase tracking-wide">{order.status}</td>
                <td className="py-2 pr-4">{new Date(order.submitted_at).toLocaleString()}</td>
                <td className="py-2 pr-4">{order.filled_at ? new Date(order.filled_at).toLocaleString() : "--"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function formatPrice(value?: string | null) {
  if (!value) return "--";
  const num = Number(value);
  return Number.isFinite(num) ? `$${num.toFixed(2)}` : "--";
}
