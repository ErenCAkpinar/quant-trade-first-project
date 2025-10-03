"use client";

import { useMemo } from "react";
import { usePolling } from "@/components/hooks/usePolling";

interface LivePnlRow {
  timestamp: string;
  equity: number;
  cash: number;
}

interface LivePnlResponse {
  pnl: LivePnlRow[];
}

interface LivePnlCardProps {
  initial: LivePnlRow[];
}

export function LivePnlCard({ initial }: LivePnlCardProps) {
  const { data } = usePolling<LivePnlResponse>(
    "/api/pnl",
    { pnl: initial },
    { interval: 5000, transform: (payload) => (payload?.pnl ? payload : { pnl: [] }) }
  );

  const latest = useMemo(() => (data.pnl.length ? data.pnl[data.pnl.length - 1] : null), [data.pnl]);

  return (
    <section className="card space-y-3">
      <header className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Live P&L</h2>
          <p className="text-sm text-zinc-400">Streamed from the Python live loop (reports/live_pnl.csv).</p>
        </div>
        <span className="rounded-full bg-white/5 px-3 py-1 text-xs text-zinc-300">Refreshes 5s</span>
      </header>
      <div className="rounded-2xl border border-white/10 bg-surface/80 p-5">
        <div className="grid gap-4 md:grid-cols-3">
          <Detail label="Timestamp" value={latest ? new Date(latest.timestamp).toLocaleString() : "--"} />
          <Detail label="Equity" value={latest ? formatCurrency(latest.equity) : "--"} />
          <Detail label="Cash" value={latest ? formatCurrency(latest.cash) : "--"} />
        </div>
      </div>
      {data.pnl.length > 1 && (
        <small className="text-xs text-zinc-500">
          History length: {data.pnl.length.toLocaleString()} pts. Hook this feed into dashboards or alerts as needed.
        </small>
      )}
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function formatCurrency(value: number) {
  return value.toLocaleString(undefined, { style: "currency", currency: "USD" });
}
