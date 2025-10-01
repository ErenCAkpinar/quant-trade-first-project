import Link from "next/link";

export function Hero() {
  return (
    <section className="mx-auto flex w-full flex-col items-start gap-6 rounded-3xl border border-white/10 bg-surface-muted/60 p-8 shadow-xl shadow-black/30 backdrop-blur md:flex-row md:items-center md:gap-12 md:p-12">
      <div className="flex-1 space-y-4">
        <span className="badge">Open-Source Quant Platform</span>
        <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
          Best-of-Breed Ensemble <span className="text-primary">for Equities</span>
        </h1>
        <p className="max-w-xl text-lg text-zinc-300">
          Quant BOBE delivers institutional-grade research, portfolio construction, and live execution using Alpaca paper
          trading. Spin up backtests, inspect trades, and run live loops in minutes.
        </p>
        <div className="flex flex-col gap-3 text-sm md:flex-row">
          <Link
            href="/docs"
            className="rounded-full bg-primary px-5 py-2 font-medium text-surface shadow-lg shadow-primary/60 transition hover:bg-primary-dark"
          >
            Read the Docs
          </Link>
          <Link href="/performance" className="rounded-full border border-white/20 px-5 py-2 font-medium text-white/80">
            View Metrics
          </Link>
        </div>
      </div>
      <div className="flex w-full max-w-sm flex-col gap-3 rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 to-transparent p-6 text-sm text-zinc-200">
        <h3 className="text-lg font-semibold text-white">Live Snapshot</h3>
        <ul className="space-y-2">
          <li className="flex items-center justify-between">
            <span>Broker</span>
            <span className="font-mono text-primary">Alpaca Paper</span>
          </li>
          <li className="flex items-center justify-between">
            <span>Sleeves Enabled</span>
            <span className="font-mono">C_xsec_qv · D_intraday_rev</span>
          </li>
          <li className="flex items-center justify-between">
            <span>Target Vol</span>
            <span className="font-mono">10% annualized</span>
          </li>
        </ul>
        <p className="text-xs text-zinc-400">Data sourced from repo configuration. Update configs to customize.</p>
      </div>
    </section>
  );
}
