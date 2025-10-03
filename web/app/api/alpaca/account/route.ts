import { NextResponse } from "next/server";
import { fetchAlpacaSnapshot } from "@/lib/server/alpaca";

export async function GET() {
  const { account } = await fetchAlpacaSnapshot();
  if (!account) {
    return NextResponse.json(
      { error: "Alpaca account unavailable" },
      { status: 503 }
    );
  }
  return NextResponse.json(account);
}
