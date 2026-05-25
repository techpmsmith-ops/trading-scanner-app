"use client";

import { Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

const blank = {
  symbol: "",
  position_type: "shares",
  role: "core",
  theme: "AI infrastructure",
  thesis: "",
  conviction: "medium",
  quantity: "",
  average_cost: "",
  current_price: "",
  contracts: "",
  option_type: "call",
  strike_price: "",
  expiration_date: "",
  premium_paid: "",
  current_contract_price: "",
  break_even: "",
  notes: ""
};

type FormState = typeof blank;

export function ResearchPositionForm() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(blank);
  const [message, setMessage] = useState("");

  function update(key: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    const payload = {
      ...form,
      quantity: toNumber(form.quantity),
      average_cost: toNumber(form.average_cost),
      current_price: toNumber(form.current_price),
      contracts: form.contracts === "" ? null : Number(form.contracts),
      strike_price: toNumber(form.strike_price),
      expiration_date: form.expiration_date || null,
      premium_paid: toNumber(form.premium_paid),
      current_contract_price: toNumber(form.current_contract_price),
      break_even: toNumber(form.break_even),
    };
    try {
      await api("/research-portfolio/positions", { method: "POST", body: JSON.stringify(payload) });
      setMessage("Saved.");
      setForm(blank);
      router.refresh();
    } catch (exc) {
      setMessage(exc instanceof Error ? exc.message : "Save failed.");
    }
  }

  const isLeaps = form.position_type === "leaps";

  return (
    <form onSubmit={submit} className="grid gap-3 rounded-md border border-border bg-panel p-4">
      <div className="grid gap-3 md:grid-cols-5">
        <Field label="Symbol" value={form.symbol} onChange={(value) => update("symbol", value)} required />
        <Select label="Type" value={form.position_type} onChange={(value) => update("position_type", value)} options={["shares", "leaps"]} />
        <Select label="Role" value={form.role} onChange={(value) => update("role", value)} options={["core", "growth", "speculative", "hedge", "watchlist"]} />
        <Select label="Conviction" value={form.conviction} onChange={(value) => update("conviction", value)} options={["low", "medium", "high", "very_high"]} />
        <Field label="Theme" value={form.theme} onChange={(value) => update("theme", value)} />
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        {isLeaps ? (
          <>
            <Field label="Contracts" value={form.contracts} onChange={(value) => update("contracts", value)} type="number" />
            <Select label="Option type" value={form.option_type} onChange={(value) => update("option_type", value)} options={["call", "put"]} />
            <Field label="Strike" value={form.strike_price} onChange={(value) => update("strike_price", value)} type="number" />
            <Field label="Expiration" value={form.expiration_date} onChange={(value) => update("expiration_date", value)} type="date" />
            <Field label="Premium paid" value={form.premium_paid} onChange={(value) => update("premium_paid", value)} type="number" />
            <Field label="Current contract" value={form.current_contract_price} onChange={(value) => update("current_contract_price", value)} type="number" />
            <Field label="Break-even" value={form.break_even} onChange={(value) => update("break_even", value)} type="number" />
          </>
        ) : (
          <>
            <Field label="Shares" value={form.quantity} onChange={(value) => update("quantity", value)} type="number" />
            <Field label="Average cost" value={form.average_cost} onChange={(value) => update("average_cost", value)} type="number" />
            <Field label="Current price" value={form.current_price} onChange={(value) => update("current_price", value)} type="number" />
          </>
        )}
      </div>
      <Textarea label="Thesis" value={form.thesis} onChange={(value) => update("thesis", value)} />
      <Textarea label="Notes" value={form.notes} onChange={(value) => update("notes", value)} />
      <div className="flex items-center gap-3">
        <button className="inline-flex items-center gap-2 bg-positive px-4 py-2 text-sm font-semibold text-[#07130d]"><Save size={16} />Save Position</button>
        {message ? <span className="text-sm text-muted">{message}</span> : null}
      </div>
    </form>
  );
}

function Field({ label, value, onChange, type = "text", required = false }: { label: string; value: string; onChange: (value: string) => void; type?: string; required?: boolean }) {
  return <label className="grid gap-1 text-sm text-muted">{label}<input required={required} value={value} type={type} step="any" onChange={(event) => onChange(event.target.value)} className="px-3 py-2" /></label>;
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return <label className="grid gap-1 text-sm text-muted">{label}<select value={value} onChange={(event) => onChange(event.target.value)} className="px-3 py-2">{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
}

function Textarea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="grid gap-1 text-sm text-muted">{label}<textarea value={value} onChange={(event) => onChange(event.target.value)} className="min-h-20 px-3 py-2" /></label>;
}

function toNumber(value: string) {
  return value === "" ? null : Number(value);
}
