import { Disclaimer } from "@/components/Disclaimer";
import { EmptyState } from "@/components/EmptyState";
import { ResultsTable } from "@/components/ResultsTable";
import { ScanRunAlert } from "@/components/ScanRunAlert";
import { ScannerCharts } from "@/components/ScannerCharts";
import { api, ScanRun } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

export default async function ScannerPage() {
  let latest: ScanRun | null = null;
  try {
    latest = await api<ScanRun>("/scan/latest", { headers: await authHeaders() });
  } catch {
    latest = null;
  }

  return (
    <div className="space-y-6">
      <Disclaimer />
      <ScanRunAlert scan={latest} />
      <div>
        <h1 className="text-2xl font-semibold">Scanner Results</h1>
        <p className="mt-2 text-sm text-muted">Sort, filter, and inspect scanner-generated watchlist candidates.</p>
      </div>
      {latest?.results?.length ? (
        <>
          <ScannerCharts results={latest.results} />
          <ResultsTable results={latest.results} />
        </>
      ) : <EmptyState title="No scanner results" body="Run a scan from the dashboard to populate this table. If a scan failed, the status message above will show the first provider errors." />}
    </div>
  );
}
