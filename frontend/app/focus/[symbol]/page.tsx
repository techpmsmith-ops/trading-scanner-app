import Link from "next/link";
import { Disclaimer } from "@/components/Disclaimer";
import { EmptyState } from "@/components/EmptyState";
import { FocusExplainPanel } from "@/components/FocusExplainPanel";
import { PriceChart } from "@/components/PriceChart";
import { StatusPill } from "@/components/StatusPill";
import { api, currency, FocusExplanationContext, number, PriceBar } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

export default async function FocusSymbolPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const headers = await authHeaders();
  let context: FocusExplanationContext | null = null;
  try {
    context = await api<FocusExplanationContext>(`/phase2/focus/${symbol}/explanation-context`, { headers });
  } catch {
    context = null;
  }
  const normalizedSymbol = context?.symbol || symbol.toUpperCase();
  const analysis = context?.latest_analysis;
  const kronos = analysis?.kronos || null;
  let bars: PriceBar[] = [];
  try {
    bars = await api<PriceBar[]>(`/data/${normalizedSymbol}`, { headers });
  } catch {
    bars = [];
  }
  const latestPrediction = context?.weekly_predictions[0];

  if (!context || !analysis) {
    return (
      <div className="space-y-6">
        <Disclaimer />
        <div>
          <Link href="/signals" className="text-sm text-muted hover:text-ink">Back to Signals</Link>
          <h1 className="mt-2 text-2xl font-semibold">{normalizedSymbol} Focus Analysis</h1>
          <p className="mt-2 max-w-3xl text-sm text-muted">
            Focus detail pages render after the backend has stored a Focus Group analysis for the symbol.
          </p>
        </div>
        {bars.length ? <PriceChart bars={bars} /> : null}
        <EmptyState
          title="No Focus Group analysis yet"
          body="Go to Signals and click Focus Group to generate the latest daily analysis, then reopen this page."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Disclaimer />
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <Link href="/signals" className="text-sm text-muted hover:text-ink">Back to Signals</Link>
          <h1 className="mt-2 text-2xl font-semibold">{context.symbol} Focus Analysis</h1>
          <p className="mt-2 max-w-4xl text-sm text-muted">{analysis.summary}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusPill value={analysis.bias} />
          <StatusPill value={`${number(analysis.confidence * 100, 0)}% confidence`} />
          <StatusPill value={`${analysis.risk_level} risk`} />
        </div>
      </div>

      {bars.length ? <PriceChart bars={bars} /> : <div className="rounded-md border border-caution/40 bg-caution/10 px-4 py-3 text-sm text-[#ffd88a]">Price history is unavailable right now.</div>}

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel title="Price And Volume">
          <Fact label="Daily move" value={analysis.daily_move_pct === null ? "-" : `${number(analysis.daily_move_pct)}%`} />
          <Fact label="Weekly move" value={analysis.weekly_move_pct === null ? "-" : `${number(analysis.weekly_move_pct)}%`} />
          <Fact label="Relative volume" value={analysis.relative_volume === null ? "-" : `${number(analysis.relative_volume)}x`} />
          <Fact label="Volume spike" value={analysis.volume_spike ? "Yes" : "No"} />
        </Panel>
        <Panel title="Indicators">
          <Fact label="RSI" value={number(analysis.indicators.rsi_14)} />
          <Fact label="MACD histogram" value={number(analysis.indicators.macd_histogram)} />
          <Fact label="20 EMA" value={number(analysis.indicators.ema_20)} />
          <Fact label="50 SMA" value={number(analysis.indicators.sma_50)} />
          <Fact label="200 SMA" value={number(analysis.indicators.sma_200)} />
        </Panel>
        <Panel title="Support / Resistance">
          <Fact label="Support" value={currency(analysis.support_resistance.support)} />
          <Fact label="Resistance" value={currency(analysis.support_resistance.resistance)} />
          <Fact label="Entry zone" value={analysis.entry_zone || "-"} />
          <Fact label="Stop area" value={analysis.stop_loss_area || "-"} />
          <Fact label="Target zone" value={analysis.target_zone || "-"} />
        </Panel>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel title="Current Setup">
          <Fact label="Technical setup" value={analysis.current_technical_setup} />
          <Fact label="Key catalyst" value={analysis.key_catalyst} />
          <Fact label="Watch action" value={analysis.suggested_watch_action} />
          <Fact label="News sentiment" value={`${analysis.news_sentiment_label || "-"} (${number(analysis.news_sentiment_score, 3)})`} />
          <div className="mt-3 flex flex-wrap gap-1">{(analysis.relevance.tags || []).map((tag: string) => <StatusPill key={tag} value={tag} />)}</div>
        </Panel>
        <Panel title="Kronos Forecast">
          {kronos ? (
            <>
              <Fact label="Bias" value={titleCase(kronos.kronos_bias || kronos.predicted_direction || kronos.forecast?.predicted_direction || "unavailable")} />
              <Fact label="Confidence" value={kronosConfidence(kronos)} />
              <Fact label="Model" value={kronos.kronos_model_name || kronos.model_name || kronos.forecast?.model_name || "-"} />
              <Fact label="Expected low" value={currency(kronos.kronos_expected_range?.low ?? kronos.kronos_expected_range_low ?? kronos.predicted_high_low_range?.low ?? kronos.forecast?.predicted_high_low_range?.low)} />
              <Fact label="Expected high" value={currency(kronos.kronos_expected_range?.high ?? kronos.kronos_expected_range_high ?? kronos.predicted_high_low_range?.high ?? kronos.forecast?.predicted_high_low_range?.high)} />
              <Fact label="Horizon" value={kronos.forecast?.forecast_horizon || kronos.forecast_horizon ? `${kronos.forecast?.forecast_horizon || kronos.forecast_horizon} bars` : "-"} />
              {kronos.kronos_summary ? <p className="mt-3 text-sm text-muted">{kronos.kronos_summary}</p> : null}
              {kronos.kronos_error || kronos.forecast?.error || kronos.error ? <p className="mt-3 text-sm text-[#ffd88a]">{kronos.kronos_error || kronos.forecast?.error || kronos.error}</p> : null}
            </>
          ) : <p className="text-sm text-muted">Kronos has not run for this Focus Group analysis yet. Run the scanner to refresh this signal.</p>}
        </Panel>
        <Panel title="Weekly Prediction">
          {latestPrediction ? (
            <>
              <Fact label="Direction" value={latestPrediction.direction} />
              <Fact label="Expected range" value={latestPrediction.predicted_range_low === null || latestPrediction.predicted_range_high === null ? "-" : `$${number(latestPrediction.predicted_range_low)} - $${number(latestPrediction.predicted_range_high)}`} />
              <Fact label="Bullish probability" value={`${number((latestPrediction.bullish_probability || 0) * 100, 0)}%`} />
              <Fact label="Bearish probability" value={`${number((latestPrediction.bearish_probability || 0) * 100, 0)}%`} />
              <Fact label="Confidence" value={`${number(latestPrediction.confidence * 100, 0)}%`} />
              <p className="mt-3 text-sm text-muted">{latestPrediction.suggested_trade_plan}</p>
            </>
          ) : <p className="text-sm text-muted">No weekly prediction stored yet.</p>}
        </Panel>
      </section>

      <Panel title="Score Component Breakdown">
        <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
          <Metric label="Trend" value={number(context.score_components.trend_component, 0)} />
          <Metric label="Momentum" value={number(context.score_components.momentum_component, 0)} />
          <Metric label="Volume" value={number(context.score_components.volume_component, 0)} />
          <Metric label="Sentiment" value={number(context.score_components.sentiment_component)} />
          <Metric label="Setup Quality" value={number(context.score_components.setup_quality_component, 0)} />
          <Metric label="Risk Penalty" value={number(context.score_components.risk_penalty, 0)} />
        </div>
        <p className="mt-3 text-sm text-muted">Final confidence score: {number(context.score_components.final_confidence_score, 0)}%</p>
      </Panel>

      <details className="rounded-md border border-border bg-panel p-4">
        <summary className="cursor-pointer font-semibold">Why this rating?</summary>
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
          {Object.entries(context.why_this_rating).map(([key, value]) => (
            <div key={key} className="rounded-md border border-border bg-panelSoft p-3">
              <div className="text-xs uppercase text-muted">{key.replaceAll("_", " ")}</div>
              <pre className="mt-1 whitespace-pre-wrap font-sans text-muted">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre>
            </div>
          ))}
        </div>
      </details>

      <FocusExplainPanel context={context} />

      <Panel title="Prediction Accuracy History">
        {context.profile ? (
          <div className="grid gap-3 md:grid-cols-4">
            <Metric label="Weeks" value={String(context.profile.accuracy_stats.evaluated_weeks || 0)} />
            <Metric label="Direction Accuracy" value={`${number((context.profile.accuracy_stats.direction_accuracy || 0) * 100, 0)}%`} />
            <Metric label="Range Accuracy" value={`${number((context.profile.accuracy_stats.range_accuracy || 0) * 100, 0)}%`} />
            <Metric label="False Positives" value={String(context.profile.accuracy_stats.false_positives || 0)} />
          </div>
        ) : <p className="text-sm text-muted">No accuracy profile has been built yet.</p>}
      </Panel>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="rounded-md border border-border bg-panel p-4"><h2 className="mb-3 font-semibold">{title}</h2>{children}</div>;
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 border-t border-border py-2 text-sm"><span className="text-muted">{label}</span><span className="text-right">{value}</span></div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-border bg-panelSoft p-3"><div className="text-xs uppercase text-muted">{label}</div><div className="mt-1 text-lg font-semibold">{value}</div></div>;
}

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function kronosConfidence(kronos: Record<string, any>) {
  const confidence = kronos.kronos_confidence ?? kronos.confidence_score ?? kronos.forecast?.confidence_score;
  return confidence === null || confidence === undefined ? "-" : `${number(confidence, 0)}/100`;
}
