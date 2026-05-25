import { JournalEntry, currency } from "@/lib/api";

export function PerformanceCharts({ entries }: { entries: JournalEntry[] }) {
  const closed = entries
    .filter((entry) => entry.status === "closed" && typeof entry.pnl_amount === "number")
    .sort((a, b) => chartDate(a).localeCompare(chartDate(b)));
  const equity = buildEquityCurve(closed);
  const outcomes = [
    { name: "Wins", count: closed.filter((entry) => entry.result === "win").length, color: "#2fd17c" },
    { name: "Losses", count: closed.filter((entry) => entry.result === "loss").length, color: "#ff6b6b" },
    { name: "Breakeven", count: closed.filter((entry) => entry.result === "breakeven").length, color: "#f5b84b" }
  ];

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Equity Curve</h2>
        {equity.length ? <EquitySvg data={equity} /> : <p className="text-sm text-muted">Close journal entries with P&L to build an equity curve.</p>}
      </div>
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Trade Outcomes</h2>
        <div className="space-y-3">
          {outcomes.map((item) => {
            const max = Math.max(...outcomes.map((outcome) => outcome.count), 1);
            const percent = closed.length ? Math.round((item.count / closed.length) * 100) : 0;
            return (
              <div key={item.name} className="grid grid-cols-[78px_1fr_62px] items-center gap-3 text-sm">
                <span>{item.name}</span>
                <div className="h-3 rounded bg-panelSoft">
                  <div className="h-3 rounded" style={{ width: `${(item.count / max) * 100}%`, backgroundColor: item.color }} />
                </div>
                <span className="text-right">{item.count} ({percent}%)</span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function EquitySvg({ data }: { data: { label: string; pnl: number }[] }) {
  const width = 640;
  const height = 220;
  const padX = 36;
  const padY = 22;
  const values = data.map((point) => point.pnl);
  const min = Math.min(0, ...values);
  const max = Math.max(0, ...values);
  const range = max - min || 1;
  const points = data.map((point, index) => {
    const x = padX + (index / Math.max(data.length - 1, 1)) * (width - padX * 2);
    const y = padY + (1 - (point.pnl - min) / range) * (height - padY * 2);
    return { x, y, point };
  });
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Equity curve" className="h-72 w-full">
      <rect width={width} height={height} fill="#111927" />
      {[0, 0.5, 1].map((tick) => {
        const y = padY + tick * (height - padY * 2);
        const value = max - tick * range;
        return (
          <g key={tick}>
            <line x1={padX} x2={width - padX} y1={y} y2={y} stroke="#243044" />
            <text x={width - padX + 6} y={y + 4} fill="#9aa7b8" fontSize="11">{currency(value)}</text>
          </g>
        );
      })}
      <path d={path} fill="none" stroke="#2fd17c" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function buildEquityCurve(entries: JournalEntry[]) {
  let cumulative = 0;
  return entries.map((entry, index) => {
    cumulative += entry.pnl_amount || 0;
    return {
      label: entry.symbol || `Trade ${index + 1}`,
      pnl: Number(cumulative.toFixed(2))
    };
  });
}

function chartDate(entry: JournalEntry) {
  return entry.exit_date || entry.entry_date || entry.created_at || "";
}
