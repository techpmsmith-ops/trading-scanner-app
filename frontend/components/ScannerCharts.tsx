import { ScanResult } from "@/lib/api";

export function ScannerCharts({ results }: { results: ScanResult[] }) {
  const topScores = results
    .slice()
    .sort((a, b) => b.score_total - a.score_total)
    .slice(0, 10);
  const setupCounts = countSetups(results);

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Top Scores</h2>
        <div className="space-y-3">
          {topScores.map((result) => (
            <div key={result.id} className="grid grid-cols-[54px_1fr_36px] items-center gap-3 text-sm">
              <span className="font-semibold">{result.symbol}</span>
              <div className="h-3 rounded bg-panelSoft">
                <div className="h-3 rounded bg-positive" style={{ width: `${Math.min(result.score_total, 100)}%` }} />
              </div>
              <span className="text-right text-positive">{result.score_total}%</span>
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-md border border-border bg-panel p-4">
        <h2 className="mb-4 font-semibold">Setup Mix</h2>
        {setupCounts.length ? (
          <div className="space-y-3">
            {setupCounts.map((item, index) => {
              const percent = Math.round((item.count / results.length) * 100);
              return (
                <div key={item.setup}>
                  <div className="mb-1 flex justify-between text-xs text-muted">
                    <span>{item.setup}</span>
                    <span>{item.count} ({percent}%)</span>
                  </div>
                  <div className="h-3 rounded bg-panelSoft">
                    <div className="h-3 rounded" style={{ width: `${Math.max(percent, 5)}%`, backgroundColor: SETUP_COLORS[index % SETUP_COLORS.length] }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-muted">No setup categories found in this scan.</p>
        )}
      </div>
    </section>
  );
}

const SETUP_COLORS = ["#2fd17c", "#f5b84b", "#5aa7ff", "#ff6b6b", "#b58cff", "#8bd3dd"];

function countSetups(results: ScanResult[]) {
  const counts = new Map<string, number>();
  for (const result of results) {
    for (const setup of result.setup_types) {
      counts.set(setup, (counts.get(setup) || 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .map(([setup, count]) => ({ setup, count }))
    .sort((a, b) => b.count - a.count);
}
