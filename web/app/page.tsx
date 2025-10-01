import Link from "next/link";
import { Hero } from "@/components/hero";
import { Section } from "@/components/section";
import { FeatureGrid } from "@/components/feature-grid";
import { CTA } from "@/components/cta";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Section
        title="Best-of-Breed Ensemble"
        subtitle="Quant BOBE blends cross-sectional quality-value, intraday mean reversion, and governance controls to deliver institutional-grade performance with retail-friendly infrastructure."
      >
        <FeatureGrid />
      </Section>
      <Section
        title="Production-Ready Stack"
        subtitle="Alpaca paper trading integration, reproducible CLI, CI/CD, and rich reporting out of the box."
      >
        <div className="grid gap-6 md:grid-cols-3">
          {[
            {
              title: "Turn-key CLI",
              body: "Ingest, backtest, report, and run live trading from a single command line interface.",
              href: "/docs"
            },
            {
              title: "Risk-first Portfolio",
              body: "Sector/beta neutrality, volatility targeting, and governance guardrails baked in.",
              href: "/strategy"
            },
            {
              title: "Transparent Analytics",
              body: "Plotly reports, CSV trade logs, and live PnL streaming to keep you in command.",
              href: "/performance"
            }
          ].map((item) => (
            <Link key={item.title} href={item.href} className="card group">
              <span className="badge">Explore</span>
              <h3 className="mt-3 text-xl font-semibold group-hover:text-primary">
                {item.title}
              </h3>
              <p className="mt-2 text-sm text-zinc-300">{item.body}</p>
            </Link>
          ))}
        </div>
      </Section>
      <CTA />
    </>
  );
}
