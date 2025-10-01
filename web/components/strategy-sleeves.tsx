import { readYamlConfig } from "@/lib/repo";

function sleeveCopy(key: string) {
  switch (key) {
    case "C_xsec_qv":
      return "Cross-sectional quality + value ensemble, built from momentum and fundamentals with sector constraints.";
    case "D_intraday_rev":
      return "Intraday mean reversion sleeve targeting one-day horizon with volatility normalization and participation caps.";
    case "A_tsmom":
      return "Time-series momentum sleeve scaffolded for future expansion.";
    case "B_carry":
      return "Cross-asset carry placeholder; disabled by default awaiting data feed.";
    default:
      return "User-defined sleeve.";
  }
}

export async function StrategySleeves() {
  const config = await readYamlConfig();
  const sleeves = Object.entries((config?.sleeves ?? {}) as Record<string, any>);

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {sleeves.map(([key, value]) => {
        const enabled = Boolean(value?.enabled);
        const badge = enabled ? "Enabled" : "Disabled";
        return (
          <article key={key} className="card space-y-3">
            <header className="flex items-start justify-between gap-2">
              <div>
                <h3 className="text-xl font-semibold text-white">{key}</h3>
                <p className="text-sm text-zinc-300">{sleeveCopy(key)}</p>
              </div>
              <span className={`badge ${enabled ? "text-primary" : "text-zinc-400"}`}>{badge}</span>
            </header>
            <dl className="grid gap-2 text-xs text-zinc-300">
              {value?.rebalance ? (
                <div>
                  <dt className="uppercase tracking-wide text-zinc-500">Rebalance</dt>
                  <dd className="font-mono text-white/90">{value.rebalance}</dd>
                </div>
              ) : null}
              {value?.risk_budget ? (
                <div>
                  <dt className="uppercase tracking-wide text-zinc-500">Risk Budget</dt>
                  <dd className="font-mono text-white/90">{(value.risk_budget * 100).toFixed(0)}%</dd>
                </div>
              ) : null}
              {value?.params ? (
                <div>
                  <dt className="uppercase tracking-wide text-zinc-500">Params</dt>
                  <dd className="font-mono text-white/90">
                    {Object.entries(value.params)
                      .map(([paramKey, paramValue]) => `${paramKey}: ${Array.isArray(paramValue) ? paramValue.join("/") : paramValue}`)
                      .join(" · ")}
                  </dd>
                </div>
              ) : null}
            </dl>
          </article>
        );
      })}
    </div>
  );
}
