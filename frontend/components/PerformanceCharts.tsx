"use client";

import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { JournalEntry, currency } from "@/lib/api";

export function PerformanceCharts({ entries }: { entries: JournalEntry[] }) {
  const closed = entries
    .filter((entry) => entry.status === "closed" && typeof entry.pnl_amount === "number")
    .sort((a, b) => chartDate(a).localeCompare(chartDate(b)));
  const equity = buildEquityCurve(closed);
  const outcomes = [
    { name: "Wins", count: closed.filter((entry) => entry.result === "win").length, fill: "#2fd17c" },
    { name: "Losses", count: closed.filter((entry) => entry.result === "loss").length, fill: "#ff6b6b" },
    { name: "Breakeven", count: closed.filter((entry) => entry.result === "breakeven").length, fill: "#f5b84b" }
  ];

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Equity Curve</h2>
        {equity.length ? (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equity}>
                <CartesianGrid stroke="#243044" vertical={false} />
                <XAxis dataKey="label" stroke="#9aa7b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#9aa7b8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#18202d", border: "1px solid #2d3747" }} formatter={(value) => [currency(Number(value)), "Cumulative P&L"]} />
                <Line type="monotone" dataKey="pnl" stroke="#2fd17c" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-sm text-muted">Close journal entries with P&L to build an equity curve.</p>
        )}
      </div>
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Trade Outcomes</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={outcomes}>
              <CartesianGrid stroke="#243044" vertical={false} />
              <XAxis dataKey="name" stroke="#9aa7b8" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} stroke="#9aa7b8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#18202d", border: "1px solid #2d3747" }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

function buildEquityCurve(entries: JournalEntry[]) {
  let cumulative = 0;
  return entries.map((entry, index) => {
    cumulative += entry.pnl_amount || 0;
    return {
      label: entry.symbol || `Trade ${index + 1}`,
      pnl: Number(cumulative.toFixed(2))
    };
  });
}

function chartDate(entry: JournalEntry) {
  return entry.exit_date || entry.entry_date || entry.created_at || "";
}
