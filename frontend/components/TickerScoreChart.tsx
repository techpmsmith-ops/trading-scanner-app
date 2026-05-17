"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ScanResult } from "@/lib/api";

export function TickerScoreChart({ result }: { result: ScanResult }) {
  const data = [
    { name: "Trend", value: result.score_trend, max: 30 },
    { name: "Momentum", value: result.score_momentum, max: 20 },
    { name: "Volume", value: result.score_volume, max: 15 },
    { name: "Risk", value: result.score_risk, max: 15 },
    { name: "Setup", value: result.score_setup_quality, max: 20 }
  ].map((item) => ({ ...item, percent: Math.round((item.value / item.max) * 100) }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="#243044" vertical={false} />
          <XAxis dataKey="name" stroke="#9aa7b8" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} stroke="#9aa7b8" tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#18202d", border: "1px solid #2d3747" }}
            formatter={(value, _name, item) => [`${item.payload.value}/${item.payload.max} (${value}%)`, "Score"]}
          />
          <Bar dataKey="percent" fill="#5aa7ff" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
