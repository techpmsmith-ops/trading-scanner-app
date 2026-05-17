import Link from "next/link";
import { EmptyState } from "@/components/EmptyState";
import { StatusPill } from "@/components/StatusPill";
import { api, dateTime, ScanRun } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

async function getRuns() {
  try {
    return await api<ScanRun[]>("/scan/runs", { headers: await authHeaders() });
  } catch {
    return [];
  }
}

export default async function ScanRunsPage() {
  const runs = await getRuns();
  const lastSuccessful = runs.find((run) => ["completed", "partial_success"].includes(run.status) && run.result_count > 0);
  const failedRuns = runs.filter((run) => run.status === "failed" || run.status === "partial_success");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Scan Runs</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">Review historical scanner runs, partial failures, and the last successful market scan before relying on the latest results.</p>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <Metric label="Total Runs" value={`${runs.length}`} />
        <Metric label="Last Successful Scan" value={dateTime(lastSuccessful?.completed_at || lastSuccessful?.started_at)} />
        <Metric label="Runs Needing Review" value={`${failedRuns.length}`} />
      </section>

      {runs.length ? (
        <section className="rounded-md border border-border bg-panel">
          <div className="border-b border-border px-4 py-3">
            <h2 className="font-semibold">History</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[840px] text-sm">
              <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
                <tr>
                  <th className="px-4 py-3">Run</th>
                  <th>Status</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th>Duration</th>
                  <th>Universe</th>
                  <th>Results</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-t border-border align-top">
                    <td className="px-4 py-3 font-semibold">
                      <Link href={`/scanner/runs/${run.id}`} className="text-positive hover:underline">#{run.id}</Link>
                    </td>
                    <td><StatusPill value={run.status.replace("_", " ")} /></td>
                    <td>{dateTime(run.started_at)}</td>
                    <td>{dateTime(run.completed_at)}</td>
                    <td>{run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : "-"}</td>
                    <td>{run.universe_count}</td>
                    <td>{run.result_count}</td>
                    <td className="max-w-sm truncate text-muted" title={run.error_message || ""}>{run.error_message || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        <EmptyState title="No scan runs yet" body="Run the scanner from the dashboard after the backend and market data provider are configured." />
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
