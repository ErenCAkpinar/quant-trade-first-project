import { NextResponse } from "next/server";
import { readTradesCsv } from "@/lib/repo";

export async function GET() {
  const trades = await readTradesCsv();
  return NextResponse.json({ trades });
}
