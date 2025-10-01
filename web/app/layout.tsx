import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

export const metadata: Metadata = {
  title: "Quant BOBE | Ensemble Equities Platform",
  description:
    "Open-source quant equities infrastructure featuring ensemble sleeves, Alpaca paper trading, and production-grade tooling.",
  openGraph: {
    title: "Quant BOBE",
    description: "Equities ensemble stack with Alpaca paper trading.",
    type: "website"
  }
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface text-white">
        <Navbar />
        <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-16 px-6 pb-16 pt-24 md:px-10">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
