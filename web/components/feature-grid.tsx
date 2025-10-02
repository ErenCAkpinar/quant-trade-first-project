const FEATURES = [
  {
    title: "0 · Data Sanity",
    body: "Start with adjusted prices, clamp outliers at 0.1/99.9, and cross-check with MAD so raw inputs never poison signals."
  },
  {
    title: "1 · Returns Block",
    body: "Compute simple and log returns, reconcile CAGR via both algebraic forms, and assert sum(log) ≈ ln(Vend/Vstart)."
  },
  {
    title: "2 · Volatility & Risk",
    body: "Contrast sample versus population stdev, run EWMA volatility, and align drawdowns across equity and cumulative log curves."
  },
  {
    title: "3 · Core Signals",
    body: "Pair every momentum, mean-reversion, and technical metric with a redundant twin—12–2 vs log momentum, RSI Wilder vs SMA, ATR Wilder vs MA."
  },
  {
    title: "4 · Position Sizing",
    body: "Target volatility, enforce inverse-vol and equal-risk weights, and cap execution-aware Kelly below its plain counterpart."
  },
  {
    title: "5 · Execution & Reporting",
    body: "Benchmark fills against VWAP/TWAP, guard slippage with square-root impact, and reconcile Sharpe, Sortino, Calmar, and information ratios."
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
