import { EmptyState } from "@/components/EmptyState";
import { ResearchPositionForm } from "@/components/ResearchPositionForm";
import { StatusPill } from "@/components/StatusPill";
import { api, currency, number, ResearchPortfolioDashboard } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

async function getDashboard() {
  try {
    return await api<ResearchPortfolioDashboard>("/research-portfolio", { headers: await authHeaders() });
  } catch {
    return null;
  }
}

export default async function PortfolioResearchPage() {
  const dashboard = await getDashboard();
  const summary = dashboard?.summary;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Portfolio Research</h1>
        <p className="mt-2 max-w-4xl text-sm text-muted">Manual research-side tracking for shares, LEAPS, thesis conviction, theme exposure, and the $250K base / $400K stretch path by December 31, 2026.</p>
      </div>

      {summary ? (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Research Value" value={currency(summary.current_value)} />
            <Metric label="Unrealized P&L" value={`${currency(summary.unrealized_pnl)} (${summary.unrealized_pnl_pct === null ? "-" : `${number(summary.unrealized_pnl_pct)}%`})`} />
            <Metric label="Shares / LEAPS" value={`${currency(summary.shares_value)} / ${currency(summary.leaps_value)}`} />
            <Metric label="LEAPS Exposure" value={`${number(summary.leaps_exposure_pct)}%`} />
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            {summary.goals.map((goal) => (
              <div key={goal.label} className="rounded-md border border-border bg-panel p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-semibold">{goal.label}</h2>
                    <p className="mt-1 text-sm text-muted">Target {currency(goal.target_value)} by Dec 31, 2026</p>
                  </div>
                  <StatusPill value={`${number(goal.months_remaining, 1)} months`} />
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <SmallStat label="Gap" value={currency(goal.gap)} />
                  <SmallStat label="Return Needed" value={goal.required_return_pct === null ? "-" : `${number(goal.required_return_pct)}%`} />
                  <SmallStat label="Monthly Pace" value={goal.required_monthly_return_pct === null ? "-" : `${number(goal.required_monthly_return_pct)}%`} />
                </div>
              </div>
            ))}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Allocation title="Theme Allocation" rows={summary.theme_allocations} />
            <Allocation title="Role Allocation" rows={summary.role_allocations} />
          </section>
        </>
      ) : (
        <EmptyState title="Portfolio research unavailable" body="Confirm the backend has the research portfolio migration applied." />
      )}

      <ResearchPositionForm />

      {dashboard?.positions.length ? (
        <div className="overflow-x-auto rounded-md border border-border">
          <table className="w-full min-w-[1080px] bg-panel text-sm">
            <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
              <tr><th className="px-4 py-3">Symbol</th><th>Type</th><th>Role</th><th>Theme</th><th>Conviction</th><th>Value</th><th>Cost</th><th>P&L</th><th>LEAPS</th><th>Thesis</th></tr>
            </thead>
            <tbody>
              {dashboard.positions.map((position) => (
                <tr key={position.id} className="border-t border-border align-top">
                  <td className="px-4 py-3 font-semibold">{position.symbol}</td>
                  <td>{position.position_type}</td>
                  <td>{position.role}</td>
                  <td>{position.theme || "-"}</td>
                  <td><StatusPill value={position.conviction} /></td>
                  <td>{currency(position.market_value)}</td>
                  <td>{currency(position.cost_basis)}</td>
                  <td className={position.unrealized_pnl >= 0 ? "text-positive" : "text-danger"}>{currency(position.unrealized_pnl)} {position.unrealized_pnl_pct === null ? "" : `(${number(position.unrealized_pnl_pct)}%)`}</td>
                  <td>{position.position_type === "leaps" ? `${position.contracts || 0}x ${currency(position.strike_price)} ${position.expiration_date || ""}` : "-"}</td>
                  <td className="max-w-md text-muted">{position.thesis || position.notes || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="No research positions yet" body="Add shares or LEAPS manually to start tracking goal pace and theme exposure." />
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-border bg-panel p-4"><div className="text-xs uppercase text-muted">{label}</div><div className="mt-2 text-lg font-semibold">{value}</div></div>;
}

function SmallStat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-border bg-panelSoft p-3"><div className="text-xs uppercase text-muted">{label}</div><div className="mt-1 text-sm font-semibold">{value}</div></div>;
}

function Allocation({ title, rows }: { title: string; rows: { name: string; market_value: number; allocation_pct: number }[] }) {
  return (
    <div className="rounded-md border border-border bg-panel p-4">
      <h2 className="font-semibold">{title}</h2>
      <div className="mt-3 space-y-3">
        {rows.length ? rows.map((row) => (
          <div key={row.name}>
            <div className="mb-1 flex justify-between gap-3 text-sm"><span>{row.name}</span><span className="text-muted">{currency(row.market_value)} / {number(row.allocation_pct)}%</span></div>
            <div className="h-2 rounded bg-panelSoft"><div className="h-2 rounded bg-positive" style={{ width: `${Math.min(row.allocation_pct, 100)}%` }} /></div>
          </div>
        )) : <p className="text-sm text-muted">No allocation data yet.</p>}
      </div>
    </div>
  );
}
