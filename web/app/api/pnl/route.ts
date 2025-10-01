import { NextResponse } from "next/server";
import { readLivePnlCsv } from "@/lib/repo";

export async function GET() {
  const pnl = await readLivePnlCsv();
  return NextResponse.json({ pnl });
}
