import { NextResponse } from "next/server";
import { fetchAlpacaSnapshot, fetchRecentOrders } from "@/lib/server/alpaca";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const scope = searchParams.get("scope") ?? "open";
  if (scope === "history") {
    const orders = await fetchRecentOrders(50);
    return NextResponse.json(orders);
  }
  const { openOrders } = await fetchAlpacaSnapshot();
  return NextResponse.json(openOrders);
}
