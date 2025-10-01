import { NextResponse } from "next/server";
import { readSummary } from "@/lib/repo";

export async function GET() {
  const summary = await readSummary();
  return NextResponse.json(summary);
}
