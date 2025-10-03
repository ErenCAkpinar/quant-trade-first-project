import { NextResponse } from "next/server";
import { fetchAlpacaSnapshot } from "@/lib/server/alpaca";

export async function GET() {
  const { clock } = await fetchAlpacaSnapshot();
  if (!clock) {
    return NextResponse.json({ error: "Clock unavailable" }, { status: 503 });
  }
  return NextResponse.json(clock);
}
