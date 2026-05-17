"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function MistakeChart({ data }: { data: { tag: string; count: number }[] }) {
  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="tag" stroke="#9aa7b8" />
          <YAxis allowDecimals={false} stroke="#9aa7b8" />
          <Tooltip contentStyle={{ background: "#18202d", border: "1px solid #2d3747" }} />
          <Bar dataKey="count" fill="#f5b84b" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
