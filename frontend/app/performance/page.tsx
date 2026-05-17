import { MistakeChart } from "@/components/MistakeChart";
import { api, currency } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

type Summary = {
  total_trades: number;
  wins: number;
  losses: number;
  breakeven_trades: number;
  win_rate: number;
  average_gain: number;
  average_loss: number;
  total_pnl: number;
  best_trade: number | null;
  worst_trade: number | null;
  most_common_mistake_tags: { tag: string; count: number }[];
};

export default async function PerformancePage() {
  const summary = await api<Summary>("/performance/summary", { headers: await authHeaders() });
  const mistakes = summary.most_common_mistake_tags;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Performance</h1>
        <p className="mt-2 text-sm text-muted">Basic closed-trade metrics from the journal.</p>
      </div>
      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Total trades" value={String(summary.total_trades)} />
        <Metric label="Win rate" value={`${summary.win_rate}%`} />
        <Metric label="Total P&L" value={currency(summary.total_pnl)} />
        <Metric label="Average win" value={currency(summary.average_gain)} />
        <Metric label="Average loss" value={currency(summary.average_loss)} />
        <Metric label="Best trade" value={currency(summary.best_trade)} />
        <Metric label="Worst trade" value={currency(summary.worst_trade)} />
        <Metric label="Breakeven" value={String(summary.breakeven_trades)} />
      </section>
      <section className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Mistake Frequency</h2>
        {mistakes.length ? (
          <MistakeChart data={mistakes} />
        ) : (
          <p className="text-sm text-muted">No mistake tags recorded yet.</p>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-border bg-panel p-4"><div className="text-xs uppercase text-muted">{label}</div><div className="mt-2 text-xl font-semibold">{value}</div></div>;
}
