const PANELS = [
  {
    title: "Tools & Libraries",
    subtitle: "Python plus JS stack you can stand up today.",
    items: [
      "NumPy, Pandas, and TA-Lib for vectorized indicators",
      "vectorbt and mlfinlab for modern research patterns",
      "Zipline, QSTrader, or PyAlgoTrade for full backtests",
      "Plotly, FastAPI, and Node file access for reporting",
      "Numba or GPU acceleration when Monte Carlo or ML workloads spike"
    ]
  },
  {
    title: "Strategy Categories",
    subtitle: "Diverse edges to plug into the pipeline.",
    items: [
      "Momentum and trend: 12–2, MACD, moving-average slope",
      "Mean reversion: RSI(2), Bollinger, residual z-scores",
      "Factor and rotation: quality-value, size, cross-asset shifts",
      "Calendar and event effects: turn-of-month, post-earnings drift",
      "Options and volatility overlays for hedging or expression"
    ]
  },
  {
    title: "Machine Learning & AI",
    subtitle: "Advanced layer when the basics are solid.",
    items: [
      "Supervised learning for return or direction classification",
      "Unsupervised clustering and PCA for factor reduction",
      "Deep learning (LSTM or RNN) for sequential signals",
      "Reinforcement learning for execution and market making",
      "NLP sentiment via FinBERT or custom LLM prompts"
    ]
  },
  {
    title: "System Pillars",
    subtitle: "Workflow captured in the sketch: discover → test → execute → protect.",
    items: [
      "Strategy identification with redundant analytics",
      "Backtesting and walk-forward validation with cost modeling",
      "Execution benchmarking versus VWAP or TWAP plus impact guardrails",
      "Risk management via vol targeting, drawdown brakes, subscriptions and gating"
    ]
  }
];

export function ToolingMap() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {PANELS.map((panel) => (
        <article key={panel.title} className="card space-y-3">
          <header>
            <h3 className="text-xl font-semibold text-white">{panel.title}</h3>
            <p className="text-sm text-zinc-300">{panel.subtitle}</p>
          </header>
          <ul className="space-y-2 text-sm text-zinc-300">
            {panel.items.map((item) => (
              <li key={item} className="leading-relaxed">{item}</li>
            ))}
          </ul>
        </article>
      ))}
    </div>
  );
}
