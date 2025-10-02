const CHECKS = [
  {
    title: "Return identity",
    detail: "Sum log returns ≈ ln(V_end / V_start) with tolerance 1e-8."
  },
  {
    title: "Annualization consistency",
    detail: "EWMA volatility times sqrt(252) stays within 15% of the rolling volatility annualization."
  },
  {
    title: "Momentum parity",
    detail: "Sign of 12–2 momentum agrees with sign of EMA_fast minus EMA_slow on more than 70% of observations."
  },
  {
    title: "RSI smoothing",
    detail: "RSI using Wilder's moving average closely tracks RSI using SMA with a lower RMSE."
  },
  {
    title: "ATR variant",
    detail: "Wilder ATR should be slightly lower but directionally aligned with simple MA(TR, 14)."
  },
  {
    title: "Risk parity",
    detail: "Each asset's contribution to portfolio volatility stays within ±5% of the equal target."
  },
  {
    title: "Kelly sanity",
    detail: "Execution-aware Kelly never exceeds the plain Kelly fraction; live fraction eta ≤ 0.5."
  },
  {
    title: "Impact guardrail",
    detail: "Realized slippage ≤ k * sqrt(Q/ADV) plus the configured buffer."
  },
  {
    title: "Sharpe vs t-stat",
    detail: "Absolute difference between t and Sharpe * sqrt(T) is under 0.2 assuming IID residuals."
  },
  {
    title: "Put–call parity",
    detail: "Absolute of (C - P) - (S0 - K * exp(-rT)) stays within data noise."
  }
];

export function RedundancyChecklist() {
  return (
    <article className="card space-y-4">
      <header className="space-y-2">
        <h3 className="text-2xl font-semibold text-white">Redundancy Checklist</h3>
        <p className="text-sm text-zinc-300">
          Drop these assertions into notebooks or automated tests so every analytics run re-validates the merged blueprint.
        </p>
      </header>
      <ol className="list-decimal space-y-3 pl-5 text-sm text-zinc-300">
        {CHECKS.map((check) => (
          <li key={check.title} className="leading-relaxed">
            <strong className="text-white">{check.title}:</strong> {check.detail}
          </li>
        ))}
      </ol>
    </article>
  );
}
