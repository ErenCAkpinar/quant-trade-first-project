"use client";

import dynamic from "next/dynamic";
import type { Layout, Data } from "plotly.js";
import { useMemo } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface LineChartProps {
  data: Array<{ x: string | number | Date; y: number }>;
  title: string;
  yLabel?: string;
}

export function LineChart({ data, title, yLabel }: LineChartProps) {
  const plotData = useMemo<Data[]>(
    () => [
      {
        type: "scatter",
        mode: "lines",
        x: data.map((point) => point.x),
        y: data.map((point) => point.y),
        line: { color: "#5CE1E6", width: 2 },
        fill: "tozeroy",
        fillcolor: "rgba(92, 225, 230, 0.15)",
        hovertemplate: "%{x}<br>%{y:.2f}<extra></extra>"
      }
    ],
    [data]
  );

  const layout = useMemo<Partial<Layout>>(
    () => ({
      title: { text: title, font: { color: "white", size: 18 } },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      margin: { l: 50, r: 20, t: 40, b: 40 },
      xaxis: {
        color: "#cbd5f5",
        showgrid: false
      },
      yaxis: {
        color: "#cbd5f5",
        showgrid: true,
        gridcolor: "rgba(255,255,255,0.05)",
        title: yLabel ? { text: yLabel } : undefined
      },
      font: { color: "#e5e7ff" },
      responsive: true,
      autosize: true
    }),
    [title, yLabel]
  );

  return (
    <div className="card">
      <Plot data={plotData} layout={layout} useResizeHandler style={{ width: "100%", height: "100%", minHeight: 320 }} />
    </div>
  );
}
