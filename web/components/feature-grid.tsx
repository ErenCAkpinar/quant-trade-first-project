const FEATURES = [
  {
    title: "Multi-Sleeve Engine",
    body: "Blend cross-sectional quality-value with intraday reversal, sector and beta neutrality enforced automatically."
  },
  {
    title: "Data Flexibility",
    body: "Pluggable providers (Alpaca, Yahoo, local CSV) with typed configuration and schema validation."
  },
  {
    title: "Paper Execution",
    body: "Order routing through Alpaca with participation caps, slippage modeling, and live PnL logging."
  },
  {
    title: "Robust Reports",
    body: "Plotly HTML equity reports, CSV trade logs, and governance summaries ready for audit trails."
  },
  {
    title: "Extensible CLI",
    body: "Commands to ingest data, run backtests, regenerate reports, and launch live loops."
  },
  {
    title: "Developer Friendly",
    body: "Pytest suite, Ruff linting, type checking, and modular design for rapid experimentation."
  }
];

export function FeatureGrid() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {FEATURES.map((feature) => (
        <article key={feature.title} className="card space-y-2">
          <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
          <p className="text-sm text-zinc-300">{feature.body}</p>
        </article>
      ))}
    </div>
  );
}
