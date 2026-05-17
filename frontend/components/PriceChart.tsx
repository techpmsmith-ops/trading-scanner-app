"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PriceBar } from "@/lib/api";

export function PriceChart({ bars }: { bars: PriceBar[] }) {
  const data = bars.slice(-120).map((bar) => ({ date: bar.date.slice(5), close: bar.close }));
  return (
    <div className="h-72 rounded-md border border-border bg-panel p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="date" stroke="#9aa7b8" tick={{ fontSize: 11 }} />
          <YAxis stroke="#9aa7b8" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#18202d", border: "1px solid #2d3747", color: "#edf2f7" }} />
          <Line type="monotone" dataKey="close" stroke="#2fd17c" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
