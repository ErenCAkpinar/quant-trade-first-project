import { Suspense } from "react";
import { DocsContent } from "@/components/docs-content";
import { Section } from "@/components/section";

export default function DocsPage() {
  return (
    <Section
      title="Documentation"
      subtitle="Start building with the Quant BOBE stack. Generated from repository source files and enriched with quickstart recipes."
    >
      <Suspense fallback={<p className="text-sm text-zinc-400">Loading documentation…</p>}>
        <DocsContent />
      </Suspense>
    </Section>
  );
}
