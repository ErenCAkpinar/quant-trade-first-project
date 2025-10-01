import { Section } from "@/components/section";
import { StrategySleeves } from "@/components/strategy-sleeves";

export default function StrategyPage() {
  return (
    <Section
      title="Strategy Architecture"
      subtitle="Dive into the sleeves powering Quant BOBE and how regime awareness steers risk budgets across the book."
    >
      <StrategySleeves />
    </Section>
  );
}
