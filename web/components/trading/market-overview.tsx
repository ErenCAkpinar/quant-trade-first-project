"use client";

import { useMemo, useState } from "react";
import classNames from "classnames";

import { usePolling } from "@/components/hooks/usePolling";

interface QuotePayload {
  symbol: string;
  quote: {
    shortName?: string;
    regularMarketPrice?: number;
    regularMarketChangePercent?: number;
    regularMarketChange?: number;
    regularMarketVolume?: number;
  } | null;
}

interface MarketOverviewProps {
  symbols: string[];
  initialQuotes: QuotePayload[];
}

export function MarketOverview({ symbols, initialQuotes }: MarketOverviewProps) {
  const query = useMemo(() => symbols.join(","), [symbols]);

  const { data } = usePolling<QuotePayload[]>(
    `/api/market/watchlist?symbols=${encodeURIComponent(query)}`,
    initialQuotes,
    {
      transform: (payload) => (Array.isArray(payload) ? payload : []),
      interval: 10000
    }
  );

  const [selected, setSelected] = useState(symbols[0]);
  const selectedQuote = data.find((item) => item.symbol === selected)?.quote ?? null;

  return (
    <section className="card space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Market Watchlist</h2>
          <p className="text-sm text-zinc-400">Stocks & futures refreshed every 10s directly from Yahoo Finance.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {symbols.map((symbol) => (
            <button
              key={symbol}
              type="button"
              className={classNames(
                "rounded-full px-3 py-1 transition",
                selected === symbol ? "bg-primary/20 text-primary" : "bg-white/5 text-zinc-300 hover:text-white"
              )}
              onClick={() => setSelected(symbol)}
            >
              {symbol}
            </button>
          ))}
        </div>
      </header>
      <div className="rounded-2xl border border-white/10 bg-surface/80 p-5">
        <div className="grid gap-4 md:grid-cols-4">
          <Detail label="Name" value={selectedQuote?.shortName ?? selected} />
          <Detail label="Price" value={formatPrice(selectedQuote?.regularMarketPrice)} />
          <Detail label="Change" value={formatChange(selectedQuote?.regularMarketChange)} />
          <Detail
            label="Change %"
            value={formatPercent(selectedQuote?.regularMarketChangePercent)}
            tone={Number(selectedQuote?.regularMarketChangePercent ?? 0) >= 0 ? "text-emerald-300" : "text-rose-300"}
          />
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <Detail label="Volume" value={formatVolume(selectedQuote?.regularMarketVolume)} />
          <Detail label="Last updated" value={new Date().toLocaleTimeString()} />
        </div>
      </div>
    </section>
  );
}

function Detail({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className={classNames("mt-1 text-lg font-semibold", tone ?? "text-white")}>{value}</p>
    </div>
  );
}

function formatPrice(value?: number) {
  if (!Number.isFinite(value)) return "--";
  return value!.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function formatChange(value?: number) {
  if (!Number.isFinite(value)) return "--";
  const num = value!;
  const tone = num >= 0 ? "+" : "";
  return `${tone}${num.toLocaleString(undefined, { style: "currency", currency: "USD" })}`;
}

function formatPercent(value?: number) {
  if (!Number.isFinite(value)) return "0%";
  const num = value!;
  const sign = num >= 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}

function formatVolume(value?: number) {
  if (!Number.isFinite(value)) return "--";
  const num = value!;
  if (num > 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num > 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toLocaleString();
}
