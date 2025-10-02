import type { ReactNode } from "react";

interface GuideSection {
  title: string;
  blurb: string;
  topics: { heading: string; items: ReactNode[] }[];
}

const FOUNDATION_SECTIONS: GuideSection = {
  title: "Mathematical Foundations",
  blurb:
    "Core formulas spanning returns, technicals, statistics, and risk so you can reproduce every calculation in the stack.",
  topics: [
    {
      heading: "Returns & Growth",
      items: [
        <span key="simple">
          <strong>Simple return:</strong> <code>{"r_t = P_t / P_{t-1} - 1"}</code>
        </span>,
        <span key="log">
          <strong>Log return:</strong> <code>{"ell_t = ln(P_t / P_{t-1})"}</code>
        </span>,
        <span key="cagr">
          <strong>CAGR:</strong> <code>{"((V_end / V_start)^(1/n)) - 1"}</code>
        </span>,
        <span key="vol">
          <strong>Annualized vol:</strong> <code>{"sigma_ann = sigma_day * sqrt(252)"}</code>
        </span>,
        <span key="mdd">
          <strong>Max drawdown:</strong> <code>{"max_t((Peak_t - Trough_t) / Peak_t)"}</code>
        </span>
      ]
    },
    {
      heading: "Technical Indicators",
      items: [
        <span key="sma">
          <strong>SMA/EMA:</strong> <code>{"EMA_t = alpha * P_t + (1-alpha) * EMA_{t-1}"}</code>
        </span>,
        <span key="rsi">
          <strong>RSI (Wilder):</strong> <code>{"100 - 100 / (1 + RS)"}</code>
        </span>,
        <span key="macd">
          <strong>MACD:</strong> <code>{"EMA_{12} - EMA_{26}"}</code>
        </span>,
        <span key="boll">
          <strong>Bollinger(20,2):</strong> <code>{"Mid +- 2 * sigma"}</code>
        </span>,
        <span key="atr">
          <strong>ATR:</strong> <code>{"TR = max(H-L, |H-C_{-1}|, |L-C_{-1}|)"}</code>
        </span>
      ]
    },
    {
      heading: "Statistics & Relationships",
      items: [
        <span key="mean">
          <strong>Mean/variance:</strong> <code>{"mean = (1/n) sum x_i, s^2 = (1/(n-1)) sum (x_i - mean)^2"}</code>
        </span>,
        <span key="cov">
          <strong>Covariance:</strong> <code>{"cov = (1/(n-1)) sum (x_i-mean_x)(y_i-mean_y)"}</code>
        </span>,
        <span key="corr">
          <strong>Correlation:</strong> <code>{"rho = cov / (sigma_X * sigma_Y)"}</code>
        </span>,
        <span key="beta">
          <strong>Beta:</strong> <code>{"beta = cov(R_a, R_m) / var(R_m)"}</code>
        </span>,
        <span key="capm">
          <strong>CAPM:</strong> <code>{"E(R_i) = R_f + beta_i * (E(R_m) - R_f)"}</code>
        </span>
      ]
    }
  ]
};

const RISK_AND_EXECUTION: GuideSection = {
  title: "Risk, Performance & Execution",
  blurb:
    "Everything needed to size trades, benchmark execution, and communicate risk in one place, including options coverage.",
  topics: [
    {
      heading: "Risk & Performance",
      items: [
        <span key="sharpe">
          <strong>Sharpe:</strong> <code>{"(r_bar - R_f) / sigma"}</code>
        </span>,
        <span key="sortino">
          <strong>Sortino:</strong> <code>{"(r_bar - R_f) / sigma_down"}</code>
        </span>,
        <span key="info">
          <strong>Information Ratio:</strong> <code>{"(R_p - R_b) / sigma_active"}</code>
        </span>,
        <span key="var">
          <strong>VaR (normal):</strong> <code>{"mu - z_alpha * sigma"}</code>
        </span>,
        <span key="tstat">
          <strong>t-stat:</strong> <code>{"(r_bar - R_f) / (s / sqrt(T))"}</code>
        </span>
      ]
    },
    {
      heading: "Portfolio & Sizing",
      items: [
        <span key="voltarget">
          <strong>Vol targeting:</strong> <code>{"L_t = sigma_target / sigma_hat_t"}</code>
        </span>,
        <span key="riskparity">
          <strong>Risk parity proxy:</strong> <code>{"w_i proportional to 1 / sigma_i"}</code>
        </span>,
        <span key="erc">
          <strong>Equal risk contribution:</strong> <code>{"w_i (Sigma w)_i = (1/N) * w^T Sigma w"}</code>
        </span>,
        <span key="kelly">
          <strong>Kelly (fractional):</strong> <code>{"f_star = (b * p - q) / b"}</code>
        </span>,
        <span key="expectancy">
          <strong>Expectancy:</strong> <code>{"E[R] = p * W_bar - (1-p) * L_bar"}</code>
        </span>
      ]
    },
    {
      heading: "Execution & Microstructure",
      items: [
        <span key="vwap">
          <strong>VWAP/TWAP:</strong> <code>{"sum(PQ)/sum(Q)"}</code> and <code>{"(1/n) * sum(P)"}</code>
        </span>,
        <span key="impact">
          <strong>Square-root impact:</strong> <code>{"k * sqrt(Q / ADV)"}</code>
        </span>,
        <span key="spread">
          <strong>Spread %:</strong> <code>{"(Ask - Bid) / Mid"}</code>
        </span>,
        <span key="slippage">
          <strong>Slippage:</strong> <code>{"Executed - Expected"}</code>
        </span>,
        <span key="almgren">
          <strong>Almgren–Chriss:</strong> optimal execution schedule for participation caps
        </span>
      ]
    },
    {
      heading: "Options & Pairs",
      items: [
        <span key="bsm">
          <strong>Black–Scholes:</strong> <code>{"C = S0 * Phi(d1) - K * exp(-rT) * Phi(d2)"}</code>
        </span>,
        <span key="parity">
          <strong>Put–call parity:</strong> <code>{"C - P = S0 - K * exp(-rT)"}</code>
        </span>,
        <span key="greeks">
          <strong>Greeks:</strong> <code>{"Delta, Gamma, Vega, Theta, Rho"}</code>
        </span>,
        <span key="pairs">
          <strong>Pairs residual:</strong> <code>{"epsilon_t = A_t - alpha - beta * B_t"}</code>
        </span>,
        <span key="adf">
          <strong>ADF check:</strong> <code>{"Delta epsilon_t = gamma * epsilon_{t-1} + sum phi_i * Delta epsilon_{t-i} + eta_t"}</code>
        </span>
      ]
    }
  ]
};

const EXECUTION_AWARE = [
  {
    heading: "Capacity-adjusted Sharpe",
    detail:
      "S_cap = (mu_alpha - k * sqrt(Q/ADV) - c_turnover) / sqrt(sigma_alpha^2 + sigma_slip^2) keeps slippage and turnover in the denominator."
  },
  {
    heading: "Execution-aware Kelly",
    detail:
      "f_EK = (mu_alpha - k * sqrt(Q/ADV) - c_turnover) / sigma_alpha^2 with live fraction f = eta * f_EK, eta in [0.25, 0.5]."
  },
  {
    heading: "Vol-managed momentum",
    detail:
      "w_t = min(L_max, sigma_target / sigma_hat_t) * s_t with drawdown brake w_t_DD = w_t * (1 - lambda * DD_t^{(M)})."
  },
  {
    heading: "Alpha blender",
    detail:
      "w_alpha_t proportional to sum omega_j * z_t^{(j)} minus phi * sqrt(Q/ADV) to down-weight crowded sleeves."
  }
];

export function MasterGuide() {
  const blocks = [FOUNDATION_SECTIONS, RISK_AND_EXECUTION];

  return (
    <div className="space-y-8">
      {blocks.map((block) => (
        <article key={block.title} className="card space-y-6">
          <header className="space-y-2">
            <h3 className="text-2xl font-semibold text-white">{block.title}</h3>
            <p className="text-sm text-zinc-300">{block.blurb}</p>
          </header>
          <div className="grid gap-6 md:grid-cols-2">
            {block.topics.map((topic) => (
              <section key={topic.heading} className="space-y-2">
                <h4 className="text-sm font-semibold uppercase tracking-wide text-primary/80">{topic.heading}</h4>
                <ul className="space-y-2 text-sm text-zinc-300">
                  {topic.items.map((item, index) => (
                    <li key={index} className="leading-relaxed">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </article>
      ))}
      <article className="card space-y-4">
        <header className="space-y-1">
          <h3 className="text-2xl font-semibold text-white">Execution-Aware Enhancements</h3>
          <p className="text-sm text-zinc-300">
            Direct lifts from the redundancy-focused brief so you can keep capacity, impact, and governance in every sizing decision.
          </p>
        </header>
        <ul className="space-y-3 text-sm text-zinc-300">
          {EXECUTION_AWARE.map((item) => (
            <li key={item.heading} className="leading-relaxed">
              <strong className="text-white">{item.heading}:</strong> {item.detail}
            </li>
          ))}
        </ul>
      </article>
    </div>
  );
}
