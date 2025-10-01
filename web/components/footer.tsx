import Link from "next/link";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-white/10 bg-surface-muted/80">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-zinc-400 md:flex-row md:items-center md:justify-between md:px-10">
        <p>© {year} Quant BOBE. MIT Licensed.</p>
        <div className="flex items-center gap-4">
          <Link href="https://github.com/ErenCAkpinar/quant-trade-first-project" target="_blank" rel="noreferrer">
            GitHub
          </Link>
          <Link href="/docs">Docs</Link>
          <Link href="/status">Status</Link>
        </div>
      </div>
    </footer>
  );
}
