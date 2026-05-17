"use client";

import { BookPlus } from "lucide-react";
import { useState } from "react";
import { api, ScanResult } from "@/lib/api";

export function AddToJournalButton({ result }: { result: ScanResult }) {
  const [message, setMessage] = useState("");

  async function add() {
    setMessage("");
    try {
      await api("/journal", {
        method: "POST",
        body: JSON.stringify({
          symbol: result.symbol,
          setup_type: result.setup_types.find((item) => item !== "Risk Warning / Avoid") || "scanner watchlist",
          direction: "watchlist",
          status: "planned",
          planned_entry: result.entry_zone,
          stop_loss: result.stop_loss,
          target_1: result.target_1,
          target_2: result.target_2,
          linked_scan_result_id: result.id,
          notes: result.explanation
        })
      });
      setMessage("Added to journal.");
    } catch (exc) {
      setMessage(exc instanceof Error ? exc.message : "Could not add journal entry");
    }
  }

  return (
    <div>
      <button onClick={add} className="inline-flex items-center gap-2 bg-positive px-4 py-2 text-sm font-semibold text-[#07130d]">
        <BookPlus size={16} />
        Add to Journal
      </button>
      {message ? <p className="mt-2 text-sm text-muted">{message}</p> : null}
    </div>
  );
}
