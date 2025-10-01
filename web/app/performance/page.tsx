import { Suspense } from "react";
import { Section } from "@/components/section";
import { PerformanceDashboard } from "@/components/performance-dashboard";

export default function PerformancePage() {
  return (
    <Section
      title="Performance & Analytics"
      subtitle="Interactive equity curves, drawdowns, sleeve exposure, and trade logs sourced directly from the Quant BOBE reports directory."
    >
      <Suspense fallback={<p className="text-sm text-zinc-400">Loading analytics…</p>}>
        <PerformanceDashboard />
      </Suspense>
    </Section>
  );
}
