"use client";

import { useMemo, useState } from "react";
import { PriceBar } from "@/lib/api";

export function PriceChart({ bars }: { bars: PriceBar[] }) {
  const [period, setPeriod] = useState<PeriodKey>("3M");
  const data = useMemo(() => filterBars(bars, period), [bars, period]);
  if (data.length < 2) {
    return (
      <div className="rounded-md border border-border bg-panel p-4 text-sm text-muted">
        Not enough price history to draw a chart.
      </div>
    );
  }

  const closes = data.map((bar) => bar.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const width = 960;
  const height = 260;
  const padX = 42;
  const padY = 24;
  const chartWidth = width - padX * 2;
  const chartHeight = height - padY * 2;
  const points = data.map((bar, index) => {
    const x = padX + (index / (data.length - 1)) * chartWidth;
    const y = padY + (1 - (bar.close - min) / range) * chartHeight;
    return { x, y, bar };
  });
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
  const first = data[0];
  const last = data[data.length - 1];

  return (
    <div className="rounded-md border border-border bg-panel p-4">
      <div className="mb-3 flex flex-col gap-3 text-sm md:flex-row md:items-center md:justify-between">
        <span className="text-muted">{PERIODS.find((item) => item.key === period)?.label} daily closes</span>
        <span className={last.close >= first.close ? "text-positive" : "text-danger"}>
          ${first.close.toFixed(2)} to ${last.close.toFixed(2)}
        </span>
      </div>
      <div className="mb-4 flex flex-wrap gap-2">
        {PERIODS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setPeriod(item.key)}
            className={`rounded-md border px-3 py-1 text-xs font-semibold transition ${
              period === item.key
                ? "border-positive bg-positive text-[#07130d]"
                : "border-border bg-panelSoft text-muted hover:text-ink"
            }`}
          >
            {item.shortLabel}
          </button>
        ))}
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Price history line chart" className="h-72 w-full">
        <rect x="0" y="0" width={width} height={height} fill="#111927" />
        {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
          const y = padY + tick * chartHeight;
          const value = max - tick * range;
          return (
            <g key={tick}>
              <line x1={padX} x2={width - padX} y1={y} y2={y} stroke="#243044" />
              <text x={width - padX + 8} y={y + 4} fill="#9aa7b8" fontSize="12">${value.toFixed(2)}</text>
            </g>
          );
        })}
        <path d={path} fill="none" stroke="#2fd17c" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="5" fill="#2fd17c" />
        <text x={padX} y={height - 6} fill="#9aa7b8" fontSize="12">{String(first.date).slice(0, 10)}</text>
        <text x={width - padX - 70} y={height - 6} fill="#9aa7b8" fontSize="12">{String(last.date).slice(0, 10)}</text>
      </svg>
    </div>
  );
}

type PeriodKey = "1M" | "3M" | "YTD" | "1Y" | "ALL";

const PERIODS: { key: PeriodKey; shortLabel: string; label: string }[] = [
  { key: "1M", shortLabel: "1M", label: "1 month" },
  { key: "3M", shortLabel: "3M", label: "quarter" },
  { key: "YTD", shortLabel: "YTD", label: "year to date" },
  { key: "1Y", shortLabel: "1Y", label: "1 year" },
  { key: "ALL", shortLabel: "All", label: "all available" }
];

function filterBars(bars: PriceBar[], period: PeriodKey) {
  const sorted = bars.slice().sort((a, b) => String(a.date).localeCompare(String(b.date)));
  if (period === "ALL") return sorted;
  if (!sorted.length) return [];

  const lastDate = new Date(sorted[sorted.length - 1].date);
  let startDate: Date;
  if (period === "YTD") {
    startDate = new Date(lastDate.getFullYear(), 0, 1);
  } else {
    const days = period === "1M" ? 31 : period === "3M" ? 93 : 366;
    startDate = new Date(lastDate);
    startDate.setDate(startDate.getDate() - days);
  }

  const filtered = sorted.filter((bar) => new Date(bar.date) >= startDate);
  return filtered.length >= 2 ? filtered : sorted.slice(-Math.min(sorted.length, 2));
}
