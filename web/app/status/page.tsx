import { Suspense } from "react";
import { Section } from "@/components/section";
import { StatusPanel } from "@/components/status-panel";

export default function StatusPage() {
  return (
    <Section
      title="Live Operations"
      subtitle="Monitor live cash, equity, and the most recent Alpaca paper orders directly from the Quant BOBE runtime artifacts."
    >
      <Suspense fallback={<p className="text-sm text-zinc-400">Fetching latest status…</p>}>
        <StatusPanel />
      </Suspense>
    </Section>
  );
}
