interface RoadmapStep {
  title: string;
  tag: string;
  description: string;
  bullets: string[];
}

const STEPS: RoadmapStep[] = [
  {
    title: "Main Output",
    tag: "Introductory",
    description: "Craft a welcoming landing page that frames the AI-enabled quant stack and links every deep dive.",
    bullets: [
      "Hero copy ties together formulas, redundancy, and tooling",
      "Immediate CTAs to docs, performance, and roadmap"
    ]
  },
  {
    title: "Summary",
    tag: "Analysis",
    description: "Concise synthesis of what the stack delivers and why redundancy matters before any deep content.",
    bullets: [
      "Highlight unified knowledge base and execution-first mindset",
      "Make clear the double-entry validation philosophy"
    ]
  },
  {
    title: "Additional Information",
    tag: "Analysis",
    description: "Surface the formula playbook, execution-aware add-ons, and redundancy tests without forcing a PDF download.",
    bullets: [
      "Organise formulas by domain (returns, technicals, risk, options)",
      "Embed execution-aware metrics like capacity Sharpe and EK Kelly"
    ]
  },
  {
    title: "Posts & Insights",
    tag: "Analysis",
    description: "Create a repeating block for publishing analyses, checklists, and playbooks derived from the blueprint.",
    bullets: [
      "Supports iterative updates without redesigning the layout",
      "Keeps historical decisions visible for governance"
    ]
  },
  {
    title: "Post Loops",
    tag: "Analysis",
    description: "Automate updates so that every new backtest or live report re-validates redundancy checks before publishing.",
    bullets: [
      "Trigger regression notebooks from CI/CD",
      "Raise alerts when any tolerance is breached"
    ]
  },
  {
    title: "Additional Topics",
    tag: "Deep Dive",
    description: "Dedicated area for niche material—options hedging, Almgren–Chriss execution, or capacity-aware Kelly research.",
    bullets: [
      "Link to notebooks, whitepapers, or videos",
      "Mark which topics feed back into the live system"
    ]
  },
  {
    title: "Profile & Personalisation",
    tag: "Analysis",
    description: "Profile page that summarises paper-trading stats, followers, and saved playbooks as outlined in the sketch.",
    bullets: [
      "Expose equity curves, live trade feed, and analytics widgets",
      "Surface follower/subscriber counts and a curated post book"
    ]
  },
  {
    title: "Login & Access Control",
    tag: "Execution",
    description: "Secure login with personal credentials that unlocks strategy toggles and connects to the trading loop.",
    bullets: [
      "Gate sensitive configuration behind authentication",
      "Tie session state to Alpaca paper/live credentials"
    ]
  },
  {
    title: "Subscription Hub",
    tag: "Governance",
    description: "Stable account management for special or personal features—users must subscribe before advanced tooling unlocks.",
    bullets: [
      "Plan payment tiers for analytics versus execution",
      "Automate revocation when subscription lapses"
    ]
  },
  {
    title: "Paper Trading Community",
    tag: "Engagement",
    description: "Complete the loop from the sketch: within the profile, show followers, subscribers, post book, and live dashboards.",
    bullets: [
      "Broadcast live or simulated trades with chart widgets (line/circle views)",
      "Offer comment threads and save-to-playbook workflows"
    ]
  }
];

export function Roadmap() {
  return (
    <div className="space-y-6">
      {STEPS.map((step, index) => (
        <article key={step.title} className="card space-y-3">
          <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <span className="badge">Step {index + 1}</span>
              <h3 className="text-xl font-semibold text-white">{step.title}</h3>
            </div>
            <span className="text-xs uppercase tracking-wide text-primary/80">{step.tag}</span>
          </header>
          <p className="text-sm text-zinc-300">{step.description}</p>
          <ul className="space-y-2 text-sm text-zinc-300">
            {step.bullets.map((bullet) => (
              <li key={bullet} className="leading-relaxed">• {bullet}</li>
            ))}
          </ul>
        </article>
      ))}
    </div>
  );
}
