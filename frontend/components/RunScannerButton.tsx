"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export function RunScannerButton() {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setRunning(true);
    setError("");
    try {
      await api("/scan/run", { method: "POST" });
      router.refresh();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Scanner failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <button onClick={run} disabled={running} className="inline-flex items-center gap-2 bg-positive px-4 py-2 text-sm font-semibold text-[#07130d] disabled:opacity-60">
        <RefreshCw size={16} className={running ? "animate-spin" : ""} />
        {running ? "Running scan" : "Run Scanner"}
      </button>
      {running ? <p className="mt-2 max-w-xl text-sm text-muted">Fetching daily candles and calculating scanner scores. This can take a minute for the full universe.</p> : null}
      {error ? <p className="mt-2 max-w-xl text-sm text-danger">Scanner could not complete: {error}</p> : null}
    </div>
  );
}
