import Link from "next/link";
import { EmptyState } from "@/components/EmptyState";
import { JournalForm } from "@/components/JournalForm";
import { api, currency, JournalEntry } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

export default async function JournalPage() {
  const entries = await api<JournalEntry[]>("/journal", { headers: await authHeaders() });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Trade Journal</h1>
        <p className="mt-2 text-sm text-muted">Plan, review, and reflect on trades without order execution.</p>
      </div>
      <JournalForm />
      {entries.length ? (
        <div className="overflow-x-auto rounded-md border border-border">
          <table className="w-full min-w-[900px] bg-panel text-sm">
            <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
              <tr><th className="px-4 py-3">Symbol</th><th>Setup</th><th>Status</th><th>Result</th><th>Entry</th><th>Exit</th><th>P&L</th><th></th></tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-t border-border">
                  <td className="px-4 py-3 font-semibold">{entry.symbol}</td>
                  <td>{entry.setup_type}</td>
                  <td>{entry.status}</td>
                  <td>{entry.result || "-"}</td>
                  <td>{currency(entry.actual_entry || entry.planned_entry)}</td>
                  <td>{currency(entry.exit_price)}</td>
                  <td className={(entry.pnl_amount || 0) >= 0 ? "text-positive" : "text-danger"}>{currency(entry.pnl_amount)}</td>
                  <td><Link className="text-positive hover:underline" href={`/journal/${entry.id}`}>Edit</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="No journal entries yet" body="Add a scan result to the journal or create a manual trade plan above." />
      )}
    </div>
  );
}
