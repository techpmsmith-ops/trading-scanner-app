import { notFound } from "next/navigation";
import { AddToJournalButton } from "@/components/AddToJournalButton";
import { Disclaimer } from "@/components/Disclaimer";
import { PriceChart } from "@/components/PriceChart";
import { StatusPill } from "@/components/StatusPill";
import { TickerScoreChart } from "@/components/TickerScoreChart";
import { api, currency, number, PriceBar, ScanRun } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

export default async function TickerDetail({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const headers = await authHeaders();
  let latest: ScanRun;
  try {
    latest = await api<ScanRun>("/scan/latest", { headers });
  } catch {
    notFound();
  }
  const result = latest.results.find((item) => item.symbol === symbol.toUpperCase());
  if (!result) notFound();
  let bars: PriceBar[] = [];
  try {
    bars = await api<PriceBar[]>(`/data/${result.symbol}`, { headers });
  } catch {
    bars = [];
  }

  return (
    <div className="space-y-6">
      <Disclaimer />
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{result.symbol}</h1>
          {result.ticker_name ? <p className="mt-1 text-sm text-ink">{result.ticker_name}</p> : null}
          {result.ticker_description ? <p className="mt-1 max-w-3xl text-sm text-muted">{result.ticker_description}</p> : null}
          <p className="mt-2 text-sm text-muted">{result.explanation}</p>
        </div>
        <AddToJournalButton result={result} />
      </div>
      {bars.length ? (
        <PriceChart bars={bars} />
      ) : (
        <div className="rounded-md border border-caution/40 bg-caution/10 px-4 py-3 text-sm text-[#ffd88a]">
          Price history is unavailable for this ticker right now. The scanner result below is still available for review.
        </div>
      )}
      <section className="grid gap-4 lg:grid-cols-3">
        <Panel title="Score Breakdown">
          <TickerScoreChart result={result} />
        </Panel>
        <Panel title="Risk / Reward">
          <Fact label="Entry zone" value={currency(result.entry_zone)} />
          <Fact label="Stop loss" value={currency(result.stop_loss)} />
          <Fact label="Target 1" value={currency(result.target_1)} />
          <Fact label="Target 2" value={currency(result.target_2)} />
          <Fact label="R/R" value={number(result.risk_reward)} />
        </Panel>
        <Panel title="Indicators">
          <Fact label="Close" value={currency(result.close_price)} />
          <Fact label="RSI 14" value={number(result.indicators.rsi_14)} />
          <Fact label="Relative volume" value={`${number(result.indicators.relative_volume)}x`} />
          <Fact label="ATR %" value={`${number(result.indicators.atr_percent)}%`} />
          <Fact label="20 EMA" value={number(result.indicators.ema_20)} />
          <Fact label="50 SMA" value={number(result.indicators.sma_50)} />
          <Fact label="200 SMA" value={number(result.indicators.sma_200)} />
        </Panel>
      </section>
      <Panel title="Kronos Forecast">
        <KronosHorizons kronos={result.kronos_raw_output_json} fallbackBias={result.kronos_bias ? titleCase(result.kronos_bias) : result.kronos_enabled ? "Unavailable" : "Disabled"} />
        {result.kronos_summary ? <p className="mt-3 text-sm text-muted">{result.kronos_summary}</p> : null}
        {result.kronos_error ? <p className="mt-3 text-sm text-[#ffd88a]">{result.kronos_error}</p> : null}
        {result.kronos_raw_output_json ? (
          <details className="mt-3 text-sm">
            <summary className="cursor-pointer text-muted">Raw Kronos details</summary>
            <pre className="mt-2 max-h-80 overflow-auto rounded-md border border-border bg-background p-3 text-xs">
              {JSON.stringify(result.kronos_raw_output_json, null, 2)}
            </pre>
          </details>
        ) : null}
      </Panel>
      <section className="grid gap-4 md:grid-cols-2">
        <Panel title="Setup Types"><div className="flex flex-wrap gap-2">{result.setup_types.map((item) => <StatusPill key={item} value={item} />)}</div></Panel>
        <Panel title="Risk Flags"><div className="flex flex-wrap gap-2">{result.risk_flags.length ? result.risk_flags.map((item) => <StatusPill key={item} value={item} />) : <span className="text-muted">None</span>}</div></Panel>
      </section>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="rounded-md border border-border bg-panel p-4"><h2 className="mb-3 font-semibold">{title}</h2>{children}</div>;
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between border-t border-border py-2 text-sm"><span className="text-muted">{label}</span><span>{value}</span></div>;
}

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function KronosHorizons({ kronos, fallbackBias }: { kronos: Record<string, any> | null; fallbackBias: string }) {
  const horizons = kronos?.standardized_horizons;
  const summary = kronos?.horizon_summary;
  if (!horizons) {
    return <div className="grid gap-3 md:grid-cols-3"><Fact label="Bias" value={fallbackBias} /><Fact label="Horizon" value={kronos?.forecast_horizon ? `${kronos.forecast_horizon} bars` : "-"} /><Fact label="Model" value={kronos?.model_name || "-"} /></div>;
  }
  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
        {(["next_session", "three_trading_days", "one_week", "one_month", "one_quarter"] as const).map((key) => (
          <div key={key} className="rounded-md border border-border bg-panelSoft p-3">
            <div className="text-xs uppercase text-muted">{horizons[key]?.label || key.replaceAll("_", " ")}</div>
            <div className="mt-2 text-sm font-semibold">{titleCase(horizons[key]?.bias || "unavailable")}</div>
            <div className="mt-1 text-xs text-muted">Confidence: {horizons[key]?.confidence ?? 0}/100</div>
            <div className="mt-1 text-xs text-muted">Range: {horizons[key]?.expected_range || "-"}</div>
            <div className="mt-1 text-xs text-muted">Move: {horizons[key]?.expected_move_pct || "-"}</div>
            <p className="mt-2 text-xs text-muted">{horizons[key]?.trade_interpretation}</p>
          </div>
        ))}
      </div>
      {summary ? (
        <div className="grid gap-2 text-sm md:grid-cols-2">
          <Fact label="Best trading horizon" value={summary.best_trading_horizon || "-"} />
          <Fact label="Highest confidence" value={summary.highest_confidence_horizon || "-"} />
          <Fact label="Timeframe conflict" value={summary.timeframe_conflict || "-"} />
          <Fact label="Suggested action" value={summary.suggested_action || "-"} />
        </div>
      ) : null}
    </div>
  );
}

