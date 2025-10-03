import 'server-only';

import path from 'path';
import { promises as fs } from 'fs';

const REPO_ROOT = path.resolve(process.cwd(), '..');

function resolveRepoPath(...segments: string[]) {
  return path.join(REPO_ROOT, ...segments);
}

export interface LivePnlRow {
  timestamp: string;
  equity: number;
  cash: number;
}

export async function readLivePnl(file = 'reports/live_pnl.csv'): Promise<LivePnlRow[]> {
  try {
    const raw = await fs.readFile(resolveRepoPath(file), 'utf8');
    const [headerLine, ...rows] = raw.trim().split(/\r?\n/);
    if (!headerLine) return [];
    const headers = headerLine.split(',');
    return rows.map((row) => {
      const values = row.split(',');
      const record: Record<string, string> = {};
      headers.forEach((key, idx) => {
        record[key] = values[idx] ?? '';
      });
      return {
        timestamp: record.timestamp,
        equity: Number(record.equity ?? '0'),
        cash: Number(record.cash ?? '0')
      };
    });
  } catch (error) {
    console.warn('Live PnL CSV unavailable', error);
    return [];
  }
}

export async function latestLivePnl() {
  const rows = await readLivePnl();
  return rows.length ? rows[rows.length - 1] : null;
}
