import Link from "next/link";

export function CTA() {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-primary/30 via-surface to-surface-muted p-10 shadow-2xl shadow-black/40">
      <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="max-w-xl space-y-3">
          <h3 className="text-2xl font-semibold text-white">Run the Stack Locally</h3>
          <p className="text-sm text-white/80">
            Clone the repo, configure your Alpaca paper keys, and execute the CLI to ingest data, backtest, and launch the live
            trading loop.
          </p>
        </div>
        <div className="flex flex-col gap-3 text-sm md:flex-row">
          <Link
            href="https://github.com/ErenCAkpinar/quant-trade-first-project"
            target="_blank"
            rel="noreferrer"
            className="rounded-full bg-white px-5 py-2 font-medium text-surface"
          >
            View on GitHub
          </Link>
          <Link href="/docs" className="rounded-full border border-white/40 px-5 py-2 font-medium text-white">
            Quickstart Guide
          </Link>
        </div>
      </div>
      <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-primary/40 blur-3xl" />
    </section>
  );
}
