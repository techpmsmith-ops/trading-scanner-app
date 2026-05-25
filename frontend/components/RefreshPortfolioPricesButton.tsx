"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export function RefreshPortfolioPricesButton() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    setMessage("");
    try {
      const result = await api<{ summary: { last_refresh_result: { refreshed: number; failed: { symbol: string; error: string }[] } | null } }>("/research-portfolio/refresh-prices", { method: "POST" });
      const refreshResult = result.summary.last_refresh_result;
      const failures = refreshResult?.failed.length || 0;
      setMessage(`Updated ${refreshResult?.refreshed || 0} positions${failures ? `; ${failures} failed` : ""}.`);
      router.refresh();
    } catch (exc) {
      setMessage(exc instanceof Error ? exc.message : "Refresh failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button onClick={refresh} disabled={loading} className="inline-flex items-center gap-2 rounded-md border border-border bg-panel px-3 py-2 text-sm text-ink disabled:opacity-60">
        <RefreshCw size={16} /> {loading ? "Refreshing..." : "Refresh Prices"}
      </button>
      {message ? <span className="text-sm text-muted">{message}</span> : null}
    </div>
  );
}
