import { NextResponse } from "next/server";
import { fetchHistorical } from "@/lib/server/yahoo";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol");
  if (!symbol) {
    return NextResponse.json({ error: "symbol is required" }, { status: 400 });
  }
  const interval = (searchParams.get("interval") ?? "1d") as any;
  const range = searchParams.get("range") ?? undefined;
  const period1 = searchParams.get("period1") ?? undefined;
  const period2 = searchParams.get("period2") ?? undefined;
  const data = await fetchHistorical({ symbol, interval, range, period1, period2 });
  return NextResponse.json(data);
}
