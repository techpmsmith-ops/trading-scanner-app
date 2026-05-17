import Link from "next/link";
import { Disclaimer } from "@/components/Disclaimer";
import { EmptyState } from "@/components/EmptyState";
import { RunScannerButton } from "@/components/RunScannerButton";
import { ScanRunAlert } from "@/components/ScanRunAlert";
import { StatusPill } from "@/components/StatusPill";
import { api, currency, dateTime, number, ScanRun, ScanStatus } from "@/lib/api";
import { authHeaders } from "@/lib/server-auth";

async function getLatest() {
  try {
    return await api<ScanRun>("/scan/latest", { headers: await authHeaders() });
  } catch {
    return null;
  }
}

async function getScanStatus() {
  try {
    return await api<ScanStatus>("/scan/status", { headers: await authHeaders() });
  } catch {
    return null;
  }
}

export default async function Dashboard() {
  const latest = await getLatest();
  const scanStatus = await getScanStatus();
  const top = latest?.results?.slice(0, 10) || [];

  return (
    <div className="space-y-6">
      <Disclaimer />
      <ScanRunAlert scan={latest} />
      <section className="grid gap-4 md:grid-cols-[1fr_auto]">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Daily Market Scanner</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">Review ranked watchlist candidates, inspect rule-based setup context, and journal trade plans without broker execution.</p>
        </div>
        <RunScannerButton />
      </section>
      {latest ? (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Last Scan" value={new Date(latest.started_at).toLocaleString()} />
            <Metric label="Status" value={latest.status} />
            <Metric label="Last Successful" value={dateTime(scanStatus?.last_successful_scan?.completed_at || scanStatus?.last_successful_scan?.started_at)} />
            <Metric label="Universe" value={`${latest.universe_count} tickers`} />
            <Metric label="Results" value={`${latest.result_count}`} />
          </section>
          {top.length ? <section className="rounded-md border border-border bg-panel">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="font-semibold">Top 10 Opportunities</h2>
              <Link href="/scanner" className="text-sm text-positive hover:underline">All results</Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-sm">
                <thead className="bg-panelSoft text-left text-xs uppercase text-muted">
                  <tr><th className="px-4 py-3">Symbol</th><th>Score</th><th>Setup</th><th>Close</th><th>RSI</th><th>R/R</th></tr>
                </thead>
                <tbody>
                  {top.map((result) => (
                    <tr key={result.id} className="border-t border-border">
                      <td className="px-4 py-3 font-semibold"><Link href={`/scanner/${result.symbol}`}>{result.symbol}</Link></td>
                      <td className="text-positive">{result.score_total}</td>
                      <td><div className="flex flex-wrap gap-1">{result.setup_types.map((item) => <StatusPill key={item} value={item} />)}</div></td>
                      <td>{currency(result.close_price)}</td>
                      <td>{number(result.indicators.rsi_14)}</td>
                      <td>{number(result.risk_reward)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section> : <EmptyState title="No ranked results in latest scan" body="The latest scan did not save any results. Review the scan status message above, then run the scanner again when market data is available." />}
        </>
      ) : (
        <EmptyState title="No scan results yet" body="Run the scanner to fetch daily candles and create the first ranked watchlist." />
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
