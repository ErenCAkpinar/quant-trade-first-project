import 'server-only';

import Alpaca from '@alpacahq/alpaca-trade-api';

export interface AlpacaSnapshot {
  account: Awaited<ReturnType<Alpaca['getAccount']>> | null;
  positions: Awaited<ReturnType<Alpaca['getPositions']>>;
  openOrders: Awaited<ReturnType<Alpaca['getOrders']>>;
  clock: Awaited<ReturnType<Alpaca['getClock']>> | null;
}

export function getAlpacaClient(): Alpaca | null {
  const keyId = process.env.ALPACA_API_KEY_ID;
  const secretKey = process.env.ALPACA_API_SECRET_KEY;
  if (!keyId || !secretKey) {
    console.warn('Alpaca credentials are missing; set ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY');
    return null;
  }
  const baseUrl = process.env.ALPACA_BASE_URL || 'https://paper-api.alpaca.markets';
  const paper = baseUrl.includes('paper');
  return new Alpaca({
    keyId,
    secretKey,
    paper,
    baseUrl
  });
}

export async function fetchAlpacaSnapshot(): Promise<AlpacaSnapshot> {
  const client = getAlpacaClient();
  if (!client) {
    return {
      account: null,
      positions: [],
      openOrders: [],
      clock: null
    };
  }
  const [account, positions, openOrders, clock] = await Promise.all([
    client.getAccount().catch((error: unknown) => {
      console.error('Failed to load Alpaca account', error);
      return null;
    }),
    client.getPositions().catch((error: unknown) => {
      console.error('Failed to load Alpaca positions', error);
      return [] as Awaited<ReturnType<Alpaca['getPositions']>>;
    }),
    client
      .getOrders({
        status: 'open',
        direction: 'desc',
        nested: true,
        limit: 50
      } as any)
      .catch((error: unknown) => {
        console.error('Failed to load Alpaca orders', error);
        return [] as Awaited<ReturnType<Alpaca['getOrders']>>;
      }),
    client.getClock().catch((error: unknown) => {
      console.error('Failed to load Alpaca clock', error);
      return null;
    })
  ]);
  return {
    account,
    positions,
    openOrders,
    clock
  };
}

export async function fetchRecentOrders(limit = 20) {
  const client = getAlpacaClient();
  if (!client) return [];
  try {
    return await client.getOrders({
      status: 'all',
      direction: 'desc',
      nested: true,
      limit
    } as any);
  } catch (error: unknown) {
    console.error('Failed to load Alpaca order history', error);
    return [];
  }
}

export async function fetchPortfolioHistory(timeframe = '1D') {
  const client = getAlpacaClient();
  if (!client) return null;
  try {
    return await client.getPortfolioHistory({
      period: '1M',
      timeframe,
      extended_hours: false
    } as any);
  } catch (error: unknown) {
    console.error('Failed to load Alpaca portfolio history', error);
    return null;
  }
}
