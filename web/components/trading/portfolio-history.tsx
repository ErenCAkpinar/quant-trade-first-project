import { LineChart } from "@/components/charts/line-chart";

interface PortfolioHistoryProps {
  series: Array<{ timestamp: string; equity: number }>;
  title?: string;
}

export function PortfolioHistory({ series, title = "Portfolio Equity" }: PortfolioHistoryProps) {
  const data = series.map((point) => ({ x: point.timestamp, y: point.equity }));
  return <LineChart data={data} title={title} yLabel="Equity" />;
}
