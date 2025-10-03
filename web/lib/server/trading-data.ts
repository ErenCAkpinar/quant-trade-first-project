import 'server-only';

import { fetchAlpacaSnapshot, fetchPortfolioHistory, fetchRecentOrders } from '@/lib/server/alpaca';
import { readLivePnlCsv, readTradesCsv } from '@/lib/repo';
import { fetchQuote } from '@/lib/server/yahoo';

export const WATCH_SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'ES=F', 'NQ=F', 'CL=F'];

export async function loadTradingData() {
  const [snapshot, pnlHistory, orderHistory, trades] = await Promise.all([
    fetchAlpacaSnapshot(),
    readLivePnlCsv(),
    fetchRecentOrders(50),
    readTradesCsv()
  ]);

  const portfolioHistory = await fetchPortfolioHistory('1D');
  const watchlist = await Promise.all(WATCH_SYMBOLS.map((symbol) => fetchQuote(symbol)));

  const historySeries =
    portfolioHistory?.timestamp && portfolioHistory.equity
      ? portfolioHistory.timestamp.map((ts: number, idx: number) => ({
          timestamp: new Date(ts * 1000).toISOString(),
          equity: Number(portfolioHistory.equity[idx])
        }))
      : [];

  return {
    snapshot,
    pnlHistory,
    orderHistory,
    trades,
    portfolioHistory: historySeries,
    watchlist: WATCH_SYMBOLS.map((symbol, idx) => ({ symbol, quote: watchlist[idx] }))
  };
}
