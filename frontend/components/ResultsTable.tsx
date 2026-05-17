"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { number, ScanResult } from "@/lib/api";
import { StatusPill } from "./StatusPill";

export function ResultsTable({ results }: { results: ScanResult[] }) {
  const [setup, setSetup] = useState("");
  const [threshold, setThreshold] = useState(0);
  const [riskOnly, setRiskOnly] = useState(false);
  const [search, setSearch] = useState("");

  const setupOptions = Array.from(new Set(results.flatMap((result) => result.setup_types))).sort();
  const filtered = useMemo(() => {
    return results
      .filter((result) => !setup || result.setup_types.includes(setup))
      .filter((result) => result.score_total >= threshold)
      .filter((result) => !riskOnly || result.risk_flags.length > 0)
      .filter((result) => result.symbol.includes(search.trim().toUpperCase()))
      .sort((a, b) => b.score_total - a.score_total);
  }, [results, setup, threshold, riskOnly, search]);

  return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-md border border-border bg-panel p-4 md:grid-cols-4">
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search ticker" className="px-3 py-2 text-sm" />
        <select value={setup} onChange={(event) => setSetup(event.target.value)} className="px-3 py-2 text-sm">
          <option value="">All setup types</option>
          {setupOptions.map((option) => <option key={option}>{option}</option>)}
        </select>
        <input type="number" min={0} max={100} value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} className="px-3 py-2 text-sm" />
        <label className="flex items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={riskOnly} onChange={(event) => setRiskOnly(event.target.checked)} />
          Risk flags only
        </label>
      </div>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full min-w-[980px] border-collapse bg-panel text-sm">
          <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
            <tr>
              {["Symbol", "Score", "Setup Type", "Close", "RSI", "Rel Vol", "ATR %", "R/R", "Risk Flags", ""].map((heading) => (
                <th key={heading} className="px-3 py-3">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((result) => (
              <tr key={result.id} className="border-t border-border">
                <td className="px-3 py-3 font-semibold text-ink">{result.symbol}</td>
                <td className="px-3 py-3 text-positive">{result.score_total}</td>
                <td className="px-3 py-3"><div className="flex flex-wrap gap-1">{result.setup_types.map((item) => <StatusPill key={item} value={item} />)}</div></td>
                <td className="px-3 py-3">{number(result.close_price)}</td>
                <td className="px-3 py-3">{number(result.indicators.rsi_14)}</td>
                <td className="px-3 py-3">{number(result.indicators.relative_volume)}x</td>
                <td className="px-3 py-3">{number(result.indicators.atr_percent)}%</td>
                <td className="px-3 py-3">{number(result.risk_reward)}</td>
                <td className="px-3 py-3 text-danger">{result.risk_flags.join(", ") || "-"}</td>
                <td className="px-3 py-3"><Link className="text-positive hover:underline" href={`/scanner/${result.symbol}`}>View</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
