import { Disclaimer } from "@/components/Disclaimer";
import { EmptyState } from "@/components/EmptyState";
import { Phase2Actions } from "@/components/Phase2Actions";
import { StatusPill } from "@/components/StatusPill";
import { api, number, Phase2Dashboard } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

async function getDashboard() {
  try {
    return await api<Phase2Dashboard>("/phase2/dashboard", { headers: await authHeaders() });
  } catch {
    return null;
  }
}

export default async function SignalsPage() {
  const dashboard = await getDashboard();

  return (
    <div className="space-y-6">
      <Disclaimer />
      <div className="grid gap-4 md:grid-cols-[1fr_auto]">
        <div>
          <h1 className="text-2xl font-semibold">Phase 2 Signals</h1>
          <p className="mt-2 max-w-3xl text-sm text-muted">Daily top-five watchlist candidates, weekly prediction tracking, and scoring feedback. These are educational scanner signals, not trade recommendations.</p>
        </div>
        <Phase2Actions />
      </div>

      {!dashboard ? (
        <EmptyState title="Phase 2 data unavailable" body="Confirm the backend is deployed with the Phase 2 migration, then refresh." />
      ) : (
        <>
          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Tier 1 Focus Group Watchlist</h2>
              <p className="mt-1 text-xs text-muted">Daily deeper analysis for {dashboard.prediction_symbols.join(", ")}.</p>
            </div>
            {dashboard.focus_group.length ? (
              <div className="grid gap-3 p-4 lg:grid-cols-2">
                {dashboard.focus_group.map((item) => (
                  <div key={item.id} className="rounded-md border border-border bg-panelSoft p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold">{item.symbol}</h3>
                        <p className="mt-1 text-xs text-muted">{item.analysis_date}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <StatusPill value={item.bias} />
                        <StatusPill value={`${number(item.confidence * 100, 0)}% confidence`} />
                        <StatusPill value={`${item.risk_level} risk`} />
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-muted">{item.summary}</p>
                    <div className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
                      <Metric label="Daily Move" value={item.daily_move_pct === null ? "-" : `${number(item.daily_move_pct)}%`} />
                      <Metric label="Weekly Move" value={item.weekly_move_pct === null ? "-" : `${number(item.weekly_move_pct)}%`} />
                      <Metric label="Rel Volume" value={item.relative_volume === null ? "-" : `${number(item.relative_volume)}x`} />
                    </div>
                    <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                      <div>
                        <div className="text-xs uppercase text-muted">Setup</div>
                        <p className="mt-1">{item.current_technical_setup}</p>
                      </div>
                      <div>
                        <div className="text-xs uppercase text-muted">Catalyst</div>
                        <p className="mt-1">{item.key_catalyst}</p>
                      </div>
                      <div>
                        <div className="text-xs uppercase text-muted">Watch Action</div>
                        <p className="mt-1">{item.suggested_watch_action}</p>
                      </div>
                      <div>
                        <div className="text-xs uppercase text-muted">Plan Zones</div>
                        <p className="mt-1">Entry: {item.entry_zone || "-"} | Stop: {item.stop_loss_area || "-"} | Target: {item.target_zone || "-"}</p>
                      </div>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-1">
                      {(item.relevance.tags || []).map((tag: string) => <StatusPill key={tag} value={tag} />)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4"><EmptyState title="No focus group analysis yet" body="Generate Focus Group analysis after a scan, or use it to collect fresh watchlist context." /></div>
            )}
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Tier 4 Broader Market Discovery</h2>
              <p className="mt-1 text-xs text-muted">Only high-confidence exceptional opportunities are surfaced from the broader scanner when available.</p>
            </div>
            {dashboard.daily_top_five.length ? (
              <div className="divide-y divide-border">
                {dashboard.daily_top_five.map((item) => (
                  <div key={item.id} className="grid gap-3 p-4 md:grid-cols-[40px_90px_80px_1fr]">
                    <div className="text-lg font-semibold text-positive">#{item.rank}</div>
                    <div className="font-semibold">{item.symbol}</div>
                    <div>{item.score_total}/100</div>
                    <div className="space-y-2">
                      <p className="text-sm text-muted">{item.rationale}</p>
                      <div className="flex flex-wrap gap-1">{item.setup_types.map((setup) => <StatusPill key={setup} value={setup} />)}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4"><EmptyState title="No daily top five yet" body="Generate the daily top five after running a market scan." /></div>
            )}
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Weekly Prediction Tracking</h2>
              <p className="mt-1 text-xs text-muted">Tracked symbols: {dashboard.prediction_symbols.join(", ")}</p>
            </div>
            {dashboard.weekly_predictions.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[920px] text-sm">
                  <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
                    <tr><th className="px-4 py-3">Symbol</th><th>Week</th><th>Direction</th><th>Range</th><th>Prob.</th><th>Confidence</th><th>Actual</th><th>Outcome</th><th>Reason</th><th>Drivers / Plan</th></tr>
                  </thead>
                  <tbody>
                    {dashboard.weekly_predictions.map((item) => (
                      <tr key={item.id} className="border-t border-border align-top">
                        <td className="px-4 py-3 font-semibold">{item.symbol}</td>
                        <td>{item.week_start} to {item.week_end}</td>
                        <td><StatusPill value={item.direction} /></td>
                        <td>{item.predicted_range_low === null || item.predicted_range_high === null ? `${number(item.predicted_return_pct)}%` : `$${number(item.predicted_range_low)}-$${number(item.predicted_range_high)}`}</td>
                        <td>B {number((item.bullish_probability || 0) * 100, 0)}% / R {number((item.bearish_probability || 0) * 100, 0)}%</td>
                        <td>{number(item.confidence * 100, 0)}%</td>
                        <td>{item.actual_return_pct === null ? "-" : `${number(item.actual_return_pct)}%`}</td>
                        <td>{item.outcome || item.status}{item.range_hit === null ? "" : item.range_hit ? " / range hit" : " / range miss"}</td>
                        <td className="max-w-xs text-muted">{item.outcome_reason || "-"}</td>
                        <td className="max-w-md text-muted">
                          <div>{(item.key_drivers || []).join("; ") || item.rationale}</div>
                          {item.suggested_trade_plan ? <div className="mt-1 text-xs">{item.suggested_trade_plan}</div> : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4"><EmptyState title="No weekly predictions yet" body="Generate predictions after the latest scan has results for the tracked symbols." /></div>
            )}
          </section>

          <section className="rounded-md border border-border bg-panel p-4">
            <h2 className="font-semibold">Weekly Evaluation</h2>
            {dashboard.latest_evaluation ? (
              <div className="mt-4 space-y-5">
                <div className="grid gap-3 md:grid-cols-5">
                  <Metric label="Accuracy" value={`${number(dashboard.latest_evaluation.accuracy * 100, 0)}%`} />
                  <Metric label="Wins" value={String(dashboard.latest_evaluation.wins)} />
                  <Metric label="Losses" value={String(dashboard.latest_evaluation.losses)} />
                  <Metric label="Win/Loss" value={dashboard.latest_evaluation.win_loss_ratio === null ? "-" : number(dashboard.latest_evaluation.win_loss_ratio)} />
                  <Metric label="False Positives" value={String(dashboard.latest_evaluation.false_positives)} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Market Conditions</h3>
                  <p className="mt-1 text-sm text-muted">
                    Regime: {String(dashboard.latest_evaluation.market_conditions.regime || "unknown")}
                    {dashboard.latest_evaluation.market_conditions.SPY ? ` | SPY ${number(dashboard.latest_evaluation.market_conditions.SPY.return_pct)}%` : ""}
                    {dashboard.latest_evaluation.market_conditions.QQQ ? ` | QQQ ${number(dashboard.latest_evaluation.market_conditions.QQQ.return_pct)}%` : ""}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Indicator Effectiveness</h3>
                  <div className="mt-3 grid gap-3 md:grid-cols-5">
                    {Object.entries(dashboard.latest_evaluation.indicator_effectiveness).map(([name, stats]) => (
                      <div key={name} className="rounded-md border border-border bg-panelSoft p-3">
                        <div className="text-xs uppercase text-muted">{name.replace("_", " ")}</div>
                        <div className="mt-1 text-lg font-semibold">{number((stats.hit_rate || 0) * 100, 0)}%</div>
                        <div className="mt-1 text-xs text-muted">FP {stats.false_positive_count || 0} | n={stats.sample_size || 0}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">News Sentiment Correlation</h3>
                  <p className="mt-1 text-sm text-muted">
                    Alignment {number((dashboard.latest_evaluation.news_sentiment_correlation.alignment_rate || 0) * 100, 0)}%
                    {" "}across {dashboard.latest_evaluation.news_sentiment_correlation.sample_size || 0} symbols.
                    Avg sentiment {number(dashboard.latest_evaluation.news_sentiment_correlation.average_sentiment_score || 0, 3)}.
                  </p>
                </div>
                <p className="text-sm text-muted">{dashboard.latest_evaluation.confidence_notes}</p>
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">No completed weekly evaluation yet. Click Evaluate Feedback after a tracked week has completed.</p>
            )}
          </section>

          <section className="rounded-md border border-border bg-panel p-4">
            <h2 className="font-semibold">Current Feedback Weights</h2>
            {dashboard.scoring_weights ? (
              <div className="mt-4 grid gap-3 md:grid-cols-5">
                {Object.entries(dashboard.scoring_weights.weights).map(([key, value]) => (
                  <div key={key} className="rounded-md border border-border bg-panelSoft p-3">
                    <div className="text-xs uppercase text-muted">{key.replace("_", " ")}</div>
                    <div className="mt-1 text-lg font-semibold">{number(value, 3)}x</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">Default weights are active until at least one weekly prediction batch is evaluated.</p>
            )}
            <p className="mt-3 text-xs text-muted">The feedback loop only nudges component weights between 0.8x and 1.2x. It remains transparent and bounded.</p>
          </section>
        </>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-panelSoft p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}
