import { NextResponse } from "next/server";
import { fetchQuote } from "@/lib/server/yahoo";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbolsParam = searchParams.get("symbols");
  if (!symbolsParam) {
    return NextResponse.json({ error: "symbols is required" }, { status: 400 });
  }
  const symbols = symbolsParam.split(",").map((s) => s.trim()).filter(Boolean);
  const quotes = await Promise.all(symbols.map((symbol) => fetchQuote(symbol)));
  const payload = symbols.map((symbol, idx) => ({ symbol, quote: quotes[idx] }));
  return NextResponse.json(payload);
}
