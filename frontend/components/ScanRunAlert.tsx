import { ScanRun } from "@/lib/api";

export function ScanRunAlert({ scan }: { scan: ScanRun | null }) {
  if (!scan) {
    return (
      <div className="rounded-md border border-caution/40 bg-caution/10 px-4 py-3 text-sm text-[#ffd88a]">
        No scan results exist yet. Run the scanner from the dashboard to populate ranked watchlist candidates.
      </div>
    );
  }

  if (scan.status === "completed") return null;

  const tone = scan.status === "failed"
    ? "border-danger/40 bg-danger/10 text-danger"
    : "border-caution/40 bg-caution/10 text-[#ffd88a]";
  const errors = scan.error_message?.split("\n").filter(Boolean).slice(0, 5) || [];

  return (
    <div className={`rounded-md border px-4 py-3 text-sm ${tone}`}>
      <div className="font-semibold">Latest scan status: {scan.status.replace("_", " ")}</div>
      {scan.result_count > 0 ? (
        <p className="mt-1">Partial results are available. Failed tickers can be retried later.</p>
      ) : (
        <p className="mt-1">No scanner results were saved for this run. Check market data connectivity and try again.</p>
      )}
      {errors.length ? <p className="mt-2 text-xs opacity-90">{errors.join(" | ")}{scan.error_message && scan.error_message.split("\n").length > errors.length ? " ..." : ""}</p> : null}
    </div>
  );
}
