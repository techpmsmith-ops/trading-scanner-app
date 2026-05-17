import Link from "next/link";
import { EmptyState } from "@/components/EmptyState";
import { StatusPill } from "@/components/StatusPill";
import { api, currency, dateTime, number, ScanRun } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

async function getRun(id: string) {
  try {
    return await api<ScanRun>(`/scan/runs/${id}`, { headers: await authHeaders() });
  } catch {
    return null;
  }
}

export default async function ScanRunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = await getRun(id);

  if (!run) {
    return <EmptyState title="Scan run not found" body="The selected scan run could not be loaded. Return to scan history and choose another run." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/scanner/runs" className="text-sm text-positive hover:underline">Back to scan history</Link>
        <h1 className="mt-3 text-2xl font-semibold text-ink">Scan Run #{run.id}</h1>
        <p className="mt-2 text-sm text-muted">Started {dateTime(run.started_at)}. Status: {run.status.replace("_", " ")}.</p>
      </div>

      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Completed" value={dateTime(run.completed_at)} />
        <Metric label="Duration" value={run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : "-"} />
        <Metric label="Universe" value={`${run.universe_count}`} />
        <Metric label="Results" value={`${run.result_count}`} />
      </section>

      {run.error_message ? (
        <section className="rounded-md border border-caution/40 bg-caution/10 p-4 text-sm text-[#ffd88a]">
          <h2 className="font-semibold">Run messages</h2>
          <pre className="mt-2 whitespace-pre-wrap font-sans text-xs">{run.error_message}</pre>
        </section>
      ) : null}

      {run.results.length ? (
        <section className="rounded-md border border-border bg-panel">
          <div className="border-b border-border px-4 py-3">
            <h2 className="font-semibold">Saved Results</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-sm">
              <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
                <tr><th className="px-4 py-3">Symbol</th><th>Score</th><th>Setup</th><th>Close</th><th>RSI</th><th>Rel Vol</th><th>ATR %</th><th>R/R</th></tr>
              </thead>
              <tbody>
                {run.results.map((result) => (
                  <tr key={result.id} className="border-t border-border">
                    <td className="px-4 py-3 font-semibold"><Link href={`/scanner/${result.symbol}`}>{result.symbol}</Link></td>
                    <td className="text-positive">{result.score_total}</td>
                    <td><div className="flex flex-wrap gap-1">{result.setup_types.map((item) => <StatusPill key={item} value={item} />)}</div></td>
                    <td>{currency(result.close_price)}</td>
                    <td>{number(result.indicators.rsi_14)}</td>
                    <td>{number(result.indicators.relative_volume)}</td>
                    <td>{number(result.indicators.atr_percent)}</td>
                    <td>{number(result.risk_reward)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        <EmptyState title="No results saved" body="This run did not save scanner results. Review the run messages above before retrying." />
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-panel p-4">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-2 text-lg font-semibold text-ink">{value}</div>
    </div>
  );
}
