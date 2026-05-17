"use client";

import { Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, JournalEntry } from "@/lib/api";

type FormState = {
  symbol: string;
  setup_type: string;
  direction: string;
  status: string;
  planned_entry: string;
  actual_entry: string;
  stop_loss: string;
  target_1: string;
  target_2: string;
  exit_price: string;
  position_size: string;
  result: string;
  notes: string;
  emotions: string;
  mistake_tags: string;
  lesson_learned: string;
};

const blank: FormState = {
  symbol: "",
  setup_type: "manual",
  direction: "watchlist",
  status: "planned",
  planned_entry: "",
  actual_entry: "",
  stop_loss: "",
  target_1: "",
  target_2: "",
  exit_price: "",
  position_size: "",
  result: "",
  notes: "",
  emotions: "",
  mistake_tags: "",
  lesson_learned: ""
};

export function JournalForm({ entry }: { entry?: JournalEntry }) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(entry ? {
    symbol: entry.symbol,
    setup_type: entry.setup_type,
    direction: entry.direction,
    status: entry.status,
    planned_entry: entry.planned_entry?.toString() || "",
    actual_entry: entry.actual_entry?.toString() || "",
    stop_loss: entry.stop_loss?.toString() || "",
    target_1: entry.target_1?.toString() || "",
    target_2: entry.target_2?.toString() || "",
    exit_price: entry.exit_price?.toString() || "",
    position_size: entry.position_size?.toString() || "",
    result: entry.result || "",
    notes: entry.notes || "",
    emotions: entry.emotions || "",
    mistake_tags: entry.mistake_tags?.join(", ") || "",
    lesson_learned: entry.lesson_learned || ""
  } : blank);
  const [message, setMessage] = useState("");

  function update(key: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    const payload = {
      ...form,
      planned_entry: toNumber(form.planned_entry),
      actual_entry: toNumber(form.actual_entry),
      stop_loss: toNumber(form.stop_loss),
      target_1: toNumber(form.target_1),
      target_2: toNumber(form.target_2),
      exit_price: toNumber(form.exit_price),
      position_size: toNumber(form.position_size),
      result: form.result || null,
      mistake_tags: form.mistake_tags ? form.mistake_tags.split(",").map((tag) => tag.trim()).filter(Boolean) : null
    };
    try {
      await api(entry ? `/journal/${entry.id}` : "/journal", {
        method: entry ? "PATCH" : "POST",
        body: JSON.stringify(payload)
      });
      router.refresh();
      setMessage("Saved.");
      if (!entry) setForm(blank);
    } catch (exc) {
      setMessage(exc instanceof Error ? exc.message : "Save failed");
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-3 rounded-md border border-border bg-panel p-4">
      <div className="grid gap-3 md:grid-cols-4">
        <Field label="Symbol" value={form.symbol} onChange={(value) => update("symbol", value)} required />
        <Field label="Setup" value={form.setup_type} onChange={(value) => update("setup_type", value)} />
        <Select label="Direction" value={form.direction} onChange={(value) => update("direction", value)} options={["watchlist", "long", "short"]} />
        <Select label="Status" value={form.status} onChange={(value) => update("status", value)} options={["planned", "open", "closed", "skipped"]} />
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <Field label="Planned entry" value={form.planned_entry} onChange={(value) => update("planned_entry", value)} type="number" />
        <Field label="Actual entry" value={form.actual_entry} onChange={(value) => update("actual_entry", value)} type="number" />
        <Field label="Stop loss" value={form.stop_loss} onChange={(value) => update("stop_loss", value)} type="number" />
        <Field label="Exit price" value={form.exit_price} onChange={(value) => update("exit_price", value)} type="number" />
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <Field label="Target 1" value={form.target_1} onChange={(value) => update("target_1", value)} type="number" />
        <Field label="Target 2" value={form.target_2} onChange={(value) => update("target_2", value)} type="number" />
        <Field label="Position size" value={form.position_size} onChange={(value) => update("position_size", value)} type="number" />
        <Select label="Result" value={form.result} onChange={(value) => update("result", value)} options={["", "win", "loss", "breakeven", "skipped"]} />
      </div>
      <Textarea label="Notes" value={form.notes} onChange={(value) => update("notes", value)} />
      <Textarea label="Emotions" value={form.emotions} onChange={(value) => update("emotions", value)} />
      <Field label="Mistake tags" value={form.mistake_tags} onChange={(value) => update("mistake_tags", value)} placeholder="late entry, moved stop" />
      <Textarea label="Lesson learned" value={form.lesson_learned} onChange={(value) => update("lesson_learned", value)} />
      <div className="flex items-center gap-3">
        <button className="inline-flex items-center gap-2 bg-positive px-4 py-2 text-sm font-semibold text-[#07130d]"><Save size={16} />Save Entry</button>
        {message ? <span className="text-sm text-muted">{message}</span> : null}
      </div>
    </form>
  );
}

function Field({ label, value, onChange, type = "text", required = false, placeholder = "" }: { label: string; value: string; onChange: (value: string) => void; type?: string; required?: boolean; placeholder?: string }) {
  return <label className="grid gap-1 text-sm text-muted">{label}<input required={required} value={value} type={type} step="any" placeholder={placeholder} onChange={(event) => onChange(event.target.value)} className="px-3 py-2" /></label>;
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return <label className="grid gap-1 text-sm text-muted">{label}<select value={value} onChange={(event) => onChange(event.target.value)} className="px-3 py-2">{options.map((option) => <option key={option} value={option}>{option || "unset"}</option>)}</select></label>;
}

function Textarea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="grid gap-1 text-sm text-muted">{label}<textarea value={value} onChange={(event) => onChange(event.target.value)} className="min-h-20 px-3 py-2" /></label>;
}

function toNumber(value: string) {
  return value === "" ? null : Number(value);
}
