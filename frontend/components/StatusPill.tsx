export function StatusPill({ value }: { value: string }) {
  const tone = value.includes("Risk") || value.includes("failed") || value.includes("low")
    ? "border-danger/40 bg-danger/10 text-danger"
    : value.includes("partial") || value.includes("Watch")
      ? "border-caution/40 bg-caution/10 text-caution"
      : "border-positive/40 bg-positive/10 text-positive";
  return <span className={`inline-flex rounded-full border px-2 py-1 text-xs ${tone}`}>{value}</span>;
}
