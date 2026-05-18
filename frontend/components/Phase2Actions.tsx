"use client";

import { Bell, RefreshCw, Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export function Phase2Actions() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");

  async function run(path: string, label: string) {
    setBusy(label);
    setMessage("");
    try {
      await api(path, { method: "POST" });
      setMessage(`${label} completed.`);
      router.refresh();
    } catch (exc) {
      setMessage(exc instanceof Error ? exc.message : `${label} failed.`);
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="flex flex-wrap items-start gap-2">
      <button onClick={() => run("/phase2/recommendations/generate", "Daily top five")} disabled={Boolean(busy)} className="inline-flex items-center gap-2 bg-positive px-3 py-2 text-sm font-semibold text-[#07130d] disabled:opacity-60">
        <RefreshCw size={16} /> Top Five
      </button>
      <button onClick={() => run("/phase2/predictions/generate", "Weekly predictions")} disabled={Boolean(busy)} className="inline-flex items-center gap-2 rounded-md border border-border bg-panel px-3 py-2 text-sm text-ink disabled:opacity-60">
        <Bell size={16} /> Weekly Predictions
      </button>
      <button onClick={() => run("/phase2/predictions/evaluate", "Prediction evaluation")} disabled={Boolean(busy)} className="inline-flex items-center gap-2 rounded-md border border-border bg-panel px-3 py-2 text-sm text-ink disabled:opacity-60">
        <Send size={16} /> Evaluate Feedback
      </button>
      {message ? <p className="basis-full text-sm text-muted">{message}</p> : null}
    </div>
  );
}
