import Link from "next/link";
import { Hero } from "@/components/hero";
import { Section } from "@/components/section";
import { FeatureGrid } from "@/components/feature-grid";
import { CTA } from "@/components/cta";
import { MasterGuide } from "@/components/master-guide";
import { RedundancyChecklist } from "@/components/redundancy-checklist";
import { ToolingMap } from "@/components/tooling-map";
import { Roadmap } from "@/components/roadmap";

const SUMMARY_CARDS = [
  {
    title: "Unified Knowledge Base",
    body:
      "All three blueprints—encyclopedic formulas, redundancy-first analytics, and tooling guidance—now live in one interface."
  },
  {
    title: "Execution-Grade Validation",
    body:
      "Capacity-aware Sharpe, execution-aware Kelly, and drawdown brakes ensure research ideas survive contact with the market."
  },
  {
    title: "Scalable System Design",
    body:
      "Strategy discovery, backtesting, execution, and risk management map cleanly to the AI and ML powered workflow from your sketch."
  }
];

const ANALYSIS_NOTES = [
  {
    title: "Data to Decision",
    body:
      "Start with corporate-action-cleaned prices, clamp outliers, and walk through returns, volatility, and sizing with a redundant pair for every formula."
  },
  {
    title: "Governance Built-In",
    body:
      "Redundancy checks, subscription gates, and login plans make it clear how to keep human oversight on every deployment."
  },
  {
    title: "AI and ML Ready",
    body:
      "From classical factors to LSTMs and RL execution, the roadmap shows where to plug learning systems without skipping basics."
  }
];

export default function HomePage() {
  return (
    <>
      <Hero />
      <Section
        title="Summary"
        subtitle="High-level synthesis of the merged instructions so newcomers understand the promise before diving into formulas."
      >
        <div className="grid gap-6 md:grid-cols-3">
          {SUMMARY_CARDS.map((item) => (
            <article key={item.title} className="card space-y-2">
              <h3 className="text-xl font-semibold text-white">{item.title}</h3>
              <p className="text-sm leading-relaxed text-zinc-300">{item.body}</p>
            </article>
          ))}
        </div>
      </Section>
      <Section
        title="Analysis Blueprint"
        subtitle="Follow the numbered pipeline from the sketch—each block comes with its twin for cross-checking."
      >
        <FeatureGrid />
        <div className="grid gap-6 md:grid-cols-3">
          {ANALYSIS_NOTES.map((item) => (
            <article key={item.title} className="card space-y-2">
              <h3 className="text-lg font-semibold text-white">{item.title}</h3>
              <p className="text-sm leading-relaxed text-zinc-300">{item.body}</p>
            </article>
          ))}
          <Link href="/status" className="card group flex flex-col justify-between">
            <div>
              <span className="badge">Keep it honest</span>
              <h3 className="mt-3 text-xl font-semibold group-hover:text-primary">Live System Status</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-300">
                Check ingestion, backtest, and live trading jobs before promoting new analytics.
              </p>
            </div>
            <span className="text-xs text-primary/80">See status page →</span>
          </Link>
        </div>
        <RedundancyChecklist />
      </Section>
      <Section
        title="Formula Playbook"
        subtitle="Use this as the always-on reference for every calculation, execution tweak, and governance guardrail."
      >
        <MasterGuide />
      </Section>
      <Section
        title="Tooling, Strategies & ML"
        subtitle="Your sketch called out the supporting libraries and AI or ML layers—this map shows where each piece plugs in."
      >
        <ToolingMap />
      </Section>
      <Section
        title="Product Roadmap"
        subtitle="Direct translation of the hand-drawn plan so you can track progress from landing page to subscription-ready platform."
      >
        <Roadmap />
      </Section>
      <CTA />
    </>
  );
}
