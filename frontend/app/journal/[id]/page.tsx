import { DeleteJournalButton } from "@/components/DeleteJournalButton";
import { JournalForm } from "@/components/JournalForm";
import { api, JournalEntry } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

export default async function JournalDetail({ params }: { params: { id: string } }) {
  const entry = await api<JournalEntry>(`/journal/${params.id}`, { headers: await authHeaders() });
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{entry.symbol} Journal Entry</h1>
          <p className="mt-2 text-sm text-muted">Update trade plan, actual execution, reflection notes, and lesson learned.</p>
        </div>
        <DeleteJournalButton id={entry.id} />
      </div>
      <JournalForm entry={entry} />
    </div>
  );
}
