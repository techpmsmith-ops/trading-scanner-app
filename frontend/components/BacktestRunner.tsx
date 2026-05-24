"use client";

import { BarChart3, LineChart, Play, ShieldAlert } from "lucide-react";
import type { FormEvent } from "react";
import { useMemo, useState } from "react";
import { api, BacktestResponse, BacktestResult, currency, number } from "@/lib/api";

const strategies = [
  { key: "trend_following", name: "Trend Following" },
  { key: "momentum_strength", name: "Momentum Strength" },
  { key: "breakout", name: "Breakout" },
  { key: "mean_reversion", name: "Mean Reversion" },
  { key: "ai_composite", name: "AI-Assisted Composite" }
];

export function BacktestRunner() {
  const [symbols, setSymbols] = useState("SPY, QQQ, NVDA");
  const [timeframe, setTimeframe] = useState("daily");
  const [lookbackDays, setLookbackDays] = useState(756);
  const [initialCapital, setInitialCapital] = useState(10000);
  const [selectedStrategies, setSelectedStrategies] = useState(strategies.map((item) => item.key));
  const [report, setReport] = useState<BacktestResponse | null>(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const validResults = report?.comparison.filter((item) => item.metrics) || [];
  const selectedResult = useMemo(() => {
    if (!validResults.length) return null;
    return validResults.find((item) => resultKey(item) === selectedKey) || validResults[0];
  }, [selectedKey, validResults]);

  async function runBacktest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api<BacktestResponse>("/backtests/run", {
        method: "POST",
        body: JSON.stringify({
          symbols: symbols.split(",").map((item) => item.trim()).filter(Boolean),
          timeframe,
          strategies: selectedStrategies,
          lookback_days: lookbackDays,
          initial_capital: initialCapital
        })
      });
      setReport(response);
      setSelectedKey(resultKey(response.comparison[0]));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Backtest failed.");
    } finally {
      setLoading(false);
    }
  }

  function toggleStrategy(key: string) {
    setSelectedStrategies((current) => {
      if (current.includes(key)) return current.length === 1 ? current : current.filter((item) => item !== key);
      return [...current, key];
    });
  }

  return (
    <div className="space-y-6">
      <form onSubmit={runBacktest} className="rounded-md border border-border bg-panel p-4">
        <div className="grid gap-4 lg:grid-cols-[1.3fr_180px_150px_170px]">
          <label className="text-sm">
            <span className="text-muted">Symbols</span>
            <input value={symbols} onChange={(event) => setSymbols(event.target.value)} className="mt-1 w-full px-3 py-2" placeholder="SPY, QQQ, NVDA" />
          </label>
          <label className="text-sm">
            <span className="text-muted">Timeframe</span>
            <select value={timeframe} onChange={(event) => setTimeframe(event.target.value)} className="mt-1 w-full px-3 py-2">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="text-muted">Lookback Days</span>
            <input type="number" min={120} max={2500} value={lookbackDays} onChange={(event) => setLookbackDays(Number(event.target.value))} className="mt-1 w-full px-3 py-2" />
          </label>
          <label className="text-sm">
            <span className="text-muted">Initial Capital</span>
            <input type="number" min={1} value={initialCapital} onChange={(event) => setInitialCapital(Number(event.target.value))} className="mt-1 w-full px-3 py-2" />
          </label>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {strategies.map((strategy) => (
            <button
              type="button"
              key={strategy.key}
              onClick={() => toggleStrategy(strategy.key)}
              className={`inline-flex items-center gap-2 border px-3 py-2 text-sm ${selectedStrategies.includes(strategy.key) ? "border-positive bg-positive text-[#07130d]" : "border-border bg-panelSoft text-muted"}`}
            >
              <BarChart3 size={15} /> {strategy.name}
            </button>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button type="submit" disabled={loading || !selectedStrategies.length} className="inline-flex items-center gap-2 bg-positive px-4 py-2 text-sm font-semibold text-[#07130d] disabled:opacity-60">
            <Play size={16} /> {loading ? "Running..." : "Run Backtest"}
          </button>
          <p className="text-xs text-muted">Backtests use historical bars and transparent rule-based strategy profiles for research only.</p>
        </div>
        {error ? <p className="mt-3 text-sm text-negative">{error}</p> : null}
      </form>

      {report ? (
        <>
          <div className="rounded-md border border-caution/50 bg-[#1e1a10] p-3 text-sm text-caution">
            <div className="flex items-start gap-2"><ShieldAlert size={16} className="mt-0.5" /> <span>{report.disclaimer}</span></div>
          </div>

          {selectedResult ? (
            <section className="rounded-md border border-border bg-panel p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold">Equity Curve</h2>
                  <p className="mt-1 text-sm text-muted">{selectedResult.symbol} | {selectedResult.strategy_name} | {report.timeframe}</p>
                </div>
                <select value={resultKey(selectedResult)} onChange={(event) => setSelectedKey(event.target.value)} className="px-3 py-2 text-sm">
                  {validResults.map((item) => (
                    <option key={resultKey(item)} value={resultKey(item)}>{item.symbol} | {item.strategy_name}</option>
                  ))}
                </select>
              </div>
              <EquityCurve result={selectedResult} />
            </section>
          ) : null}

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Strategy Comparison</h2>
              <p className="mt-1 text-xs text-muted">Sorted by Sharpe ratio. Compare win rate, drawdown, volatility, and benchmark-relative curve behavior.</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[920px] text-sm">
                <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
                  <tr>
                    <th className="px-4 py-3">Symbol</th><th>Strategy</th><th>Return</th><th>Win Rate</th><th>Max DD</th><th>Sharpe</th><th>Volatility</th><th>Trades</th><th>Final Equity</th>
                  </tr>
                </thead>
                <tbody>
                  {validResults.map((item) => item.metrics ? (
                    <tr key={resultKey(item)} className="border-t border-border">
                      <td className="px-4 py-3 font-semibold">{item.symbol}</td>
                      <td>{item.strategy_name}</td>
                      <td className={item.metrics.total_return_pct >= 0 ? "text-positive" : "text-negative"}>{number(item.metrics.total_return_pct)}%</td>
                      <td>{number(item.metrics.win_rate_pct)}%</td>
                      <td className="text-negative">{number(item.metrics.max_drawdown_pct)}%</td>
                      <td>{number(item.metrics.sharpe_ratio, 3)}</td>
                      <td>{number(item.metrics.annualized_volatility_pct)}%</td>
                      <td>{item.metrics.trade_count}</td>
                      <td>{currency(item.metrics.final_equity)}</td>
                    </tr>
                  ) : null)}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-md border border-border bg-panel p-4">
            <h2 className="font-semibold">Recent Trades</h2>
            {selectedResult?.trades.length ? (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[680px] text-sm">
                  <thead className="text-left text-xs uppercase text-muted">
                    <tr><th>Entry</th><th>Exit</th><th>Entry Price</th><th>Exit Price</th><th>Return</th><th>Result</th></tr>
                  </thead>
                  <tbody>
                    {selectedResult.trades.slice(-12).map((trade) => (
                      <tr key={`${trade.entry_date}-${trade.exit_date}-${trade.entry_price}`} className="border-t border-border">
                        <td className="py-2">{trade.entry_date}</td>
                        <td>{trade.exit_date}</td>
                        <td>{currency(trade.entry_price)}</td>
                        <td>{currency(trade.exit_price)}</td>
                        <td className={trade.return_pct >= 0 ? "text-positive" : "text-negative"}>{number(trade.return_pct)}%</td>
                        <td>{trade.result}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">No closed trades were produced for the selected strategy and timeframe.</p>
            )}
          </section>

          {report.results.some((item) => item.error) ? (
            <section className="rounded-md border border-border bg-panel p-4">
              <h2 className="font-semibold">Data Issues</h2>
              <div className="mt-2 space-y-1 text-sm text-muted">
                {report.results.filter((item) => item.error).map((item) => <p key={item.symbol}>{item.symbol}: {item.error}</p>)}
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function resultKey(result?: BacktestResult) {
  if (!result) return "";
  return `${result.symbol}:${result.strategy}`;
}

function EquityCurve({ result }: { result: BacktestResult }) {
  const points = result.equity_curve;
  if (!points.length) return <p className="mt-4 text-sm text-muted">No equity curve available.</p>;
  const values = points.flatMap((point) => [point.equity, point.benchmark_equity]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = 900;
  const height = 280;
  const x = (index: number) => (points.length === 1 ? 0 : (index / (points.length - 1)) * width);
  const y = (value: number) => height - ((value - min) / Math.max(max - min, 1)) * height;
  const pathFor = (key: "equity" | "benchmark_equity") => points.map((point, index) => `${index === 0 ? "M" : "L"} ${x(index).toFixed(2)} ${y(point[key]).toFixed(2)}`).join(" ");
  const last = points[points.length - 1];

  return (
    <div className="mt-4">
      <div className="h-[320px] w-full overflow-hidden rounded-md border border-border bg-panelSoft p-3">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" preserveAspectRatio="none" role="img" aria-label="Backtest equity curve">
          <path d={pathFor("benchmark_equity")} fill="none" stroke="#7c8aa0" strokeWidth="2" vectorEffect="non-scaling-stroke" />
          <path d={pathFor("equity")} fill="none" stroke="#38d987" strokeWidth="3" vectorEffect="non-scaling-stroke" />
        </svg>
      </div>
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
        <span className="inline-flex items-center gap-1"><LineChart size={14} className="text-positive" /> Strategy {currency(last.equity)}</span>
        <span>Benchmark {currency(last.benchmark_equity)}</span>
        <span>{points[0].date} to {last.date}</span>
      </div>
    </div>
  );
}
