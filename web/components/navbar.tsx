"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import classNames from "classnames";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/strategy", label: "Strategy" },
  { href: "/performance", label: "Performance" },
  { href: "/trading", label: "Trading" },
  { href: "/paper-trading", label: "Paper" },
  { href: "/live-trading", label: "Live" },
  { href: "/docs", label: "Docs" },
  { href: "/status", label: "Status" }
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4 md:px-10">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="h-2 w-2 rounded-full bg-primary shadow shadow-primary/50" />
          Quant BOBE
        </Link>
        <nav className="flex items-center gap-3 text-sm">
          {LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={classNames(
                "rounded-full px-3 py-1 transition",
                pathname === item.href ? "bg-primary/20 text-primary" : "text-zinc-300 hover:text-white"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
