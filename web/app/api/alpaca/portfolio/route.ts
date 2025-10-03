import { NextResponse } from "next/server";
import { fetchPortfolioHistory } from "@/lib/server/alpaca";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const timeframe = searchParams.get("timeframe") ?? "1D";
  const history = await fetchPortfolioHistory(timeframe as any);
  if (!history) {
    return NextResponse.json({ error: "Portfolio history unavailable" }, { status: 503 });
  }
  return NextResponse.json(history);
}
