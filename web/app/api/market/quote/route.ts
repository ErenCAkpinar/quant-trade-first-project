import { NextResponse } from "next/server";
import { fetchQuote } from "@/lib/server/yahoo";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol");
  if (!symbol) {
    return NextResponse.json({ error: "symbol is required" }, { status: 400 });
  }
  const quote = await fetchQuote(symbol);
  if (!quote) {
    return NextResponse.json({ error: "Quote unavailable" }, { status: 503 });
  }
  return NextResponse.json(quote);
}
