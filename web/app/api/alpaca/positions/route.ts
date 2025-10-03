import { NextResponse } from "next/server";
import { fetchAlpacaSnapshot } from "@/lib/server/alpaca";

export async function GET() {
  const { positions } = await fetchAlpacaSnapshot();
  return NextResponse.json(positions);
}
