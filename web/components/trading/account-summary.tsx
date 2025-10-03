"use client";

import { useMemo } from "react";
import { usePolling } from "@/components/hooks/usePolling";

interface AccountPayload {
  equity?: string;
  cash?: string;
  buying_power?: string;
  portfolio_value?: string;
  daytrade_count?: number;
  created_at?: string;
  status?: string;
  last_equity?: string;
}

interface MarketClockPayload {
  is_open: boolean;
  next_open: string;
  next_close: string;
  timestamp: string;
}

interface AccountSummaryProps {
  initialAccount: AccountPayload | null;
  initialClock: MarketClockPayload | null;
}

function formatCurrency(value?: string, fallback = "--") {
  if (!value) return fallback;
  const num = Number(value);
  if (!Number.isFinite(num)) return fallback;
  return num.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function AccountSummary({ initialAccount, initialClock }: AccountSummaryProps) {
  const { data: account } = usePolling<AccountPayload | null>(
    "/api/alpaca/account",
    initialAccount,
    { transform: (payload) => payload ?? null, interval: 7000 }
  );

  const { data: clock } = usePolling<MarketClockPayload | null>(
    "/api/alpaca/clock",
    initialClock,
    { transform: (payload) => ("error" in payload ? null : payload), interval: 15000 }
  );

  const statusBadge = useMemo(() => {
    if (!clock) return { label: "Market", tone: "bg-zinc-700 text-zinc-200" };
    return clock.is_open
      ? { label: "Market Open", tone: "bg-emerald-500/20 text-emerald-300" }
      : { label: "Market Closed", tone: "bg-orange-500/20 text-orange-300" };
  }, [clock]);

  return (
    <section className="card space-y-4">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Account Overview</h2>
          <p className="text-sm text-zinc-400">
            Snapshot fetched directly from Alpaca paper/live account endpoints.
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusBadge.tone}`}>
          {statusBadge.label}
        </span>
      </header>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="Equity" value={formatCurrency(account?.equity)} />
        <Metric label="Cash" value={formatCurrency(account?.cash)} />
        <Metric label="Buying Power" value={formatCurrency(account?.buying_power)} />
        <Metric label="Last Equity" value={formatCurrency(account?.last_equity)} />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Detail label="Status" value={account?.status ?? "--"} />
        <Detail
          label="Account Created"
          value={account?.created_at ? new Date(account.created_at).toLocaleString() : "--"}
        />
        <Detail
          label="Market Session"
          value={clock ? `${new Date(clock.timestamp).toLocaleString()}` : "--"}
        />
      </div>
      {clock && (
        <div className="grid gap-4 md:grid-cols-2">
          <Detail label="Next Open" value={new Date(clock.next_open).toLocaleString()} />
          <Detail label="Next Close" value={new Date(clock.next_close).toLocaleString()} />
        </div>
      )}
    </section>
  );
}

interface MetricProps {
  label: string;
  value: string;
}

function Metric({ label, value }: MetricProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-wide text-zinc-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

interface DetailProps {
  label: string;
  value: string;
}

function Detail({ label, value }: DetailProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-surface/80 p-4 text-sm text-zinc-300">
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-base text-white">{value}</p>
    </div>
  );
}
