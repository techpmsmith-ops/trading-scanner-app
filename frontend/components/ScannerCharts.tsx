"use client";

import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ScanResult } from "@/lib/api";

export function ScannerCharts({ results }: { results: ScanResult[] }) {
  const topScores = results
    .slice()
    .sort((a, b) => b.score_total - a.score_total)
    .slice(0, 10)
    .map((result) => ({ symbol: result.symbol, score: result.score_total }));
  const setupCounts = countSetups(results);

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Top Scores</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topScores}>
              <CartesianGrid stroke="#243044" vertical={false} />
              <XAxis dataKey="symbol" stroke="#9aa7b8" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} stroke="#9aa7b8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#18202d", border: "1px solid #2d3747" }} />
              <Bar dataKey="score" fill="#2fd17c" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Setup Mix</h2>
        {setupCounts.length ? (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={setupCounts} dataKey="count" nameKey="setup" innerRadius={55} outerRadius={95} paddingAngle={2}>
                  {setupCounts.map((entry, index) => (
                    <Cell key={entry.setup} fill={SETUP_COLORS[index % SETUP_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#18202d", border: "1px solid #2d3747" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-sm text-muted">No setup categories found in this scan.</p>
        )}
      </div>
    </section>
  );
}

const SETUP_COLORS = ["#2fd17c", "#f5b84b", "#5aa7ff", "#ff6b6b", "#b58cff", "#8bd3dd"];

function countSetups(results: ScanResult[]) {
  const counts = new Map<string, number>();
  for (const result of results) {
    for (const setup of result.setup_types) {
      counts.set(setup, (counts.get(setup) || 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .map(([setup, count]) => ({ setup, count }))
    .sort((a, b) => b.count - a.count);
}
