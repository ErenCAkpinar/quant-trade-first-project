import type { ReactNode } from "react";

interface SectionProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function Section({ title, subtitle, children }: SectionProps) {
  return (
    <section className="space-y-8">
      <header>
        <h2 className="section-heading">{title}</h2>
        {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
      </header>
      <div className="space-y-6">{children}</div>
    </section>
  );
}
