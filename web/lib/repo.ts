import path from "path";
import { promises as fs } from "fs";
import YAML from "yaml";

const REPO_ROOT = path.resolve(process.cwd(), "..");

function resolveRepoPath(...segments: string[]) {
  return path.join(REPO_ROOT, ...segments);
}

export async function readYamlConfig(file = "src/quantbobe/config/default.yaml") {
  try {
    const raw = await fs.readFile(resolveRepoPath(file), "utf8");
    return YAML.parse(raw);
  } catch (error) {
    console.error("Failed to read YAML config", error);
    return null;
  }
}

export interface TradeLogRow {
  date: string;
  symbol: string;
  quantity: number;
  price: number;
  notional: number;
  sleeve: string;
}

export async function readTradesCsv(file = "reports/trades.csv"): Promise<TradeLogRow[]> {
  try {
    const raw = await fs.readFile(resolveRepoPath(file), "utf8");
    const [headerLine, ...rows] = raw.trim().split(/\r?\n/);
    const headers = headerLine.split(",");
    return rows.map((row) => {
      const values = row.split(",");
      const record: Record<string, string> = {};
      headers.forEach((key, idx) => {
        record[key] = values[idx] ?? "";
      });
      return {
        date: record.date,
        symbol: record.symbol,
        quantity: Number(record.quantity),
        price: Number(record.price),
        notional: Number(record.notional),
        sleeve: record.sleeve
      };
    });
  } catch (error) {
    console.warn("Trades CSV unavailable", error);
    return [];
  }
}

export interface PnlPoint {
  timestamp: string;
  equity: number;
  cash: number;
}

export async function readLivePnlCsv(file = "reports/live_pnl.csv"): Promise<PnlPoint[]> {
  try {
    const raw = await fs.readFile(resolveRepoPath(file), "utf8");
    const [headerLine, ...rows] = raw.trim().split(/\r?\n/);
    const headers = headerLine.split(",");
    return rows.map((row) => {
      const values = row.split(",");
      const record: Record<string, string> = {};
      headers.forEach((key, idx) => {
        record[key] = values[idx] ?? "";
      });
      return {
        timestamp: record.timestamp,
        equity: Number(record.equity),
        cash: Number(record.cash)
      };
    });
  } catch (error) {
    console.warn("Live PnL CSV unavailable", error);
    return [];
  }
}

export async function readReadme(file = "README.md") {
  try {
    return await fs.readFile(resolveRepoPath(file), "utf8");
  } catch (error) {
    console.warn("README not found", error);
    return "# Documentation\nRepository README is unavailable.";
  }
}

export async function readSummary() {
  const config = await readYamlConfig();
  const trades = await readTradesCsv();
  const pnl = await readLivePnlCsv();
  const latestPnl = pnl[pnl.length - 1];
  const recentTrades = trades.slice(-5).reverse();

  return {
    config,
    pnl: latestPnl ?? null,
    tradeCount: trades.length,
    recentTrades
  };
}
