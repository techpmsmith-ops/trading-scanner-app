"use client";

import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export function DeleteJournalButton({ id }: { id: number }) {
  const router = useRouter();
  async function remove() {
    await api(`/journal/${id}`, { method: "DELETE" });
    router.push("/journal");
    router.refresh();
  }
  return <button onClick={remove} className="inline-flex items-center gap-2 border border-danger/50 px-3 py-2 text-sm text-danger"><Trash2 size={16} />Delete</button>;
}
