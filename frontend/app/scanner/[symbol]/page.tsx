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

