import 'server-only';

import yahooFinance from 'yahoo-finance2';

export interface HistoricalParams {
  symbol: string;
  interval?: '1d' | '1wk' | '1mo' | '1h' | '15m';
  range?: string;
  period1?: Date | string | number;
  period2?: Date | string | number;
}

export async function fetchHistorical({
  symbol,
  interval = '1d',
  range = '1mo',
  period1,
  period2
}: HistoricalParams) {
  const queryOptions = {
    period1,
    period2,
    interval,
    range
  };
  try {
    const results = await yahooFinance.historical(symbol, queryOptions as any, { validateResult: false });
    return results ?? [];
  } catch (error: unknown) {
    console.error('Failed to fetch Yahoo data', { symbol, error });
    return [];
  }
}

export async function fetchQuote(symbol: string) {
  try {
    return await yahooFinance.quote(symbol);
  } catch (error: unknown) {
    console.error('Failed to fetch Yahoo quote', { symbol, error });
    return null;
  }
}
