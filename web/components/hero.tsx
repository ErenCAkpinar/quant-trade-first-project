import Link from "next/link";

export function Hero() {
  return (
    <section className="mx-auto flex w-full flex-col items-start gap-6 rounded-3xl border border-white/10 bg-surface-muted/60 p-8 shadow-xl shadow-black/30 backdrop-blur md:flex-row md:items-center md:gap-12 md:p-12">
      <div className="flex-1 space-y-4">
        <span className="badge">Quantum Trading with AI & ML</span>
        <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
          A Unified <span className="text-primary">Quant Playbook</span> from Idea to Execution
        </h1>
        <p className="max-w-xl text-lg text-zinc-300">
          Merge the encyclopedic formula sheet, redundancy-driven analytics, and tooling roadmap into one launchpad. Build
          signals, validate them twice, and route them to Alpaca-ready execution without losing sight of risk.
        </p>
        <div className="flex flex-col gap-3 text-sm md:flex-row">
          <Link
            href="/docs"
            className="rounded-full bg-primary px-5 py-2 font-medium text-surface shadow-lg shadow-primary/60 transition hover:bg-primary-dark"
          >
            Explore the Knowledge Base
          </Link>
          <Link href="/performance" className="rounded-full border border-white/20 px-5 py-2 font-medium text-white/80">
            Inspect Live Analytics
          </Link>
        </div>
      </div>
      <div className="flex w-full max-w-sm flex-col gap-3 rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 to-transparent p-6 text-sm text-zinc-200">
        <h3 className="text-lg font-semibold text-white">Stack Snapshot</h3>
        <ul className="space-y-2">
          <li className="flex items-center justify-between">
            <span>Formula Coverage</span>
            <span className="font-mono text-primary">Returns · Risk · Options</span>
          </li>
          <li className="flex items-center justify-between">
            <span>Execution Guardrails</span>
            <span className="font-mono">Vol-target · EK Kelly</span>
          </li>
          <li className="flex items-center justify-between">
            <span>Validation</span>
            <span className="font-mono">10 Redundancy Checks</span>
          </li>
        </ul>
        <p className="text-xs text-zinc-400">Everything on this page is sourced from the merged blueprint you shared.</p>
      </div>
    </section>
  );
}
