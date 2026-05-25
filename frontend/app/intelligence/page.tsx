import Link from "next/link";
import type { ReactNode } from "react";
import { BrainCircuit, RadioTower, ShieldAlert, Target, TrendingUp } from "lucide-react";
import { Disclaimer } from "@/components/Disclaimer";
import { EmptyState } from "@/components/EmptyState";
import { StatusPill } from "@/components/StatusPill";
import { api, IntelligenceDashboard, number } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

async function getIntelligenceDashboard() {
  try {
    return await api<IntelligenceDashboard>("/intelligence/dashboard", { headers: await authHeaders() });
  } catch {
    return null;
  }
}

export default async function IntelligencePage() {
  const dashboard = await getIntelligenceDashboard();

  return (
    <div className="space-y-6">
      <Disclaimer />
      <section className="grid gap-4 md:grid-cols-[1fr_auto]">
        <div>
          <h1 className="text-2xl font-semibold text-ink">AI Infrastructure Market Intelligence</h1>
          <p className="mt-2 max-w-4xl text-sm text-muted">
            Institutional-style research cockpit for long-term asymmetric AI infrastructure opportunities, swing setups, prediction feedback, and agent scenario stress tests.
          </p>
        </div>
        <Link href="/signals" className="inline-flex items-center gap-2 rounded-md border border-border bg-panelSoft px-3 py-2 text-sm text-muted hover:text-ink">
          <Target size={16} /> Phase Signals
        </Link>
      </section>

      {!dashboard ? (
        <EmptyState title="Market intelligence unavailable" body="Confirm the backend is running and the intelligence migration has been applied." />
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <Metric icon={<BrainCircuit size={17} />} label="Active Modules" value={`${dashboard.modules.filter((item) => item.status === "active").length}/${dashboard.modules.length}`} />
            <Metric icon={<RadioTower size={17} />} label="Watchlist" value={`${dashboard.watchlist.length} names`} />
            <Metric icon={<TrendingUp size={17} />} label="Top Conviction" value={dashboard.opportunities[0] ? `${dashboard.opportunities[0].symbol} ${number(dashboard.opportunities[0].conviction_score, 0)}` : "-"} />
            <Metric icon={<ShieldAlert size={17} />} label="Risk Regime" value={dashboard.risk_overview.regime} />
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Mission Control</h2>
              <p className="mt-1 text-sm text-muted">{dashboard.mission}</p>
            </div>
            <div className="grid gap-4 p-4 lg:grid-cols-[1.2fr_0.8fr]">
              <div>
                <h3 className="text-sm font-semibold">Next Actions</h3>
                <div className="mt-3 space-y-2">
                  {dashboard.next_actions.map((action) => (
                    <div key={action} className="rounded-md border border-border bg-panelSoft px-3 py-2 text-sm text-muted">{action}</div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold">Learning Status</h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <SmallStat label="Accuracy" value={dashboard.prediction_accuracy.accuracy === null || dashboard.prediction_accuracy.accuracy === undefined ? "Collecting" : `${number(dashboard.prediction_accuracy.accuracy * 100, 0)}%`} />
                  <SmallStat label="Evaluated" value={String(dashboard.prediction_accuracy.evaluated_count || 0)} />
                  <SmallStat label="False Positives" value={String(dashboard.prediction_accuracy.false_positives || 0)} />
                  <SmallStat label="Crowding" value={dashboard.risk_overview.crowded_trade_risk} />
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">High-Upside Opportunity Matrix</h2>
              <p className="mt-1 text-xs text-muted">Ranks long-term asymmetric opportunity, swing/momentum quality, AI relevance, institutional interest, and risk.</p>
            </div>
            {dashboard.opportunities.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1080px] text-sm">
                  <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
                    <tr>
                      <th className="px-4 py-3">Symbol</th>
                      <th>Bias</th>
                      <th>Conviction</th>
                      <th>Asymmetry</th>
                      <th>Momentum</th>
                      <th>AI Relevance</th>
                      <th>Institutional</th>
                      <th>Risk</th>
                      <th>Horizon</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.opportunities.map((item) => (
                      <tr key={item.symbol} className="border-t border-border align-top">
                        <td className="px-4 py-3 font-semibold"><Link href={`/focus/${item.symbol}`} className="hover:text-positive">{item.symbol}</Link></td>
                        <td><StatusPill value={item.bias} /></td>
                        <td className="text-positive">{number(item.conviction_score, 1)}</td>
                        <td>{number(item.asymmetric_score, 1)}</td>
                        <td>{number(item.momentum_score, 1)}</td>
                        <td>{number(item.ai_relevance_score, 1)}</td>
                        <td>{number(item.institutional_interest_score, 1)}</td>
                        <td className={item.risk_score >= 65 ? "text-danger" : "text-muted"}>{number(item.risk_score, 1)}</td>
                        <td>{item.time_horizon}</td>
                        <td className="max-w-xs text-muted">{item.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4"><EmptyState title="No opportunities yet" body="Run the scanner and focus-group pipeline to populate opportunity scores." /></div>
            )}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-md border border-border bg-panel">
              <div className="border-b border-border px-4 py-3">
                <h2 className="font-semibold">AI Infrastructure Theme Strength</h2>
              </div>
              <div className="space-y-3 p-4">
                {dashboard.theme_trends.map((theme) => (
                  <div key={theme.theme}>
                    <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                      <span>{theme.theme}</span>
                      <span className="text-muted">{number(theme.strength, 0)} / 100</span>
                    </div>
                    <div className="h-3 rounded bg-panelSoft">
                      <div className="h-3 rounded bg-positive" style={{ width: `${Math.min(theme.strength, 100)}%` }} />
                    </div>
                    <p className="mt-1 text-xs text-muted">{theme.summary} Leaders: {theme.leaders.join(", ") || "-"}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-border bg-panel">
              <div className="border-b border-border px-4 py-3">
                <h2 className="font-semibold">Risk Overview</h2>
              </div>
              <div className="space-y-4 p-4">
                <SmallStat label="Concentration" value={dashboard.risk_overview.portfolio_concentration} />
                <SmallStat label="Fragile Setups" value={dashboard.risk_overview.fragile_setups.join(", ") || "None flagged"} />
                <div className="space-y-2">
                  {dashboard.risk_overview.notes.map((note) => (
                    <p key={note} className="text-sm text-muted">{note}</p>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Agent Simulation Lab</h2>
              <p className="mt-1 text-xs text-muted">Separate from execution. Scenario outputs feed confidence and risk validation only.</p>
            </div>
            <div className="grid gap-4 p-4 lg:grid-cols-3">
              {dashboard.simulations.map((scenario) => (
                <article key={scenario.scenario} className="rounded-md border border-border bg-panelSoft p-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-semibold">{scenario.scenario}</h3>
                    <StatusPill value={`${number(scenario.probability * 100, 0)}%`} />
                  </div>
                  <p className="mt-3 text-sm text-muted">{scenario.expected_reaction}</p>
                  <div className="mt-4 grid gap-2 text-xs text-muted">
                    <div>Beneficiaries: {scenario.likely_beneficiaries.join(", ") || "-"}</div>
                    <div>Vulnerable: {scenario.vulnerable_symbols.join(", ") || "-"}</div>
                    <div>Confidence adj: {number(scenario.confidence_adjustment * 100, 0)}%</div>
                    <div>Risk adj: {number(scenario.risk_adjustment * 100, 0)}%</div>
                  </div>
                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-semibold">Agent reactions</summary>
                    <div className="mt-2 space-y-1 text-xs text-muted">
                      {Object.entries(scenario.agent_consensus).map(([agent, view]) => (
                        <div key={agent}>{agent.replaceAll("_", " ")}: {view}</div>
                      ))}
                    </div>
                  </details>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Modular Architecture</h2>
            </div>
            <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
              {dashboard.modules.map((module) => (
                <div key={module.key} className="rounded-md border border-border bg-panelSoft p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{module.name}</h3>
                      <p className="mt-1 text-xs text-muted">Phase {module.phase}</p>
                    </div>
                    <StatusPill value={module.status} />
                  </div>
                  <p className="mt-3 text-sm text-muted">{module.responsibilities.join("; ")}</p>
                  <p className="mt-3 text-xs text-muted">Feeds: {module.output_feeds.join(", ")}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-border bg-panel">
            <div className="border-b border-border px-4 py-3">
              <h2 className="font-semibold">Dynamic Watchlist</h2>
            </div>
            <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
              {dashboard.watchlist.map((item) => (
                <div key={item.id} className="rounded-md border border-border bg-panelSoft p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold">{item.symbol}</h3>
                      <p className="text-xs text-muted">{item.company_name || "Tracked company"}</p>
                    </div>
                    <StatusPill value={item.priority} />
                  </div>
                  <p className="mt-3 text-sm text-muted">{item.thesis || "Research thesis pending."}</p>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {item.themes.map((theme) => <StatusPill key={theme} value={theme} />)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-panel p-4">
      <div className="flex items-center gap-2 text-xs uppercase text-muted">{icon}{label}</div>
      <div className="mt-2 text-lg font-semibold text-ink">{value}</div>
    </div>
  );
}

function SmallStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-panelSoft p-3">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  );
}
