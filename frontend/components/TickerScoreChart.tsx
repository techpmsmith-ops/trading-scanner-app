import { ScanResult } from "@/lib/api";

export function TickerScoreChart({ result }: { result: ScanResult }) {
  const data = [
    { name: "Trend", value: result.score_trend, max: 30 },
    { name: "Momentum", value: result.score_momentum, max: 20 },
    { name: "Volume", value: result.score_volume, max: 15 },
    { name: "Risk", value: result.score_risk, max: 15 },
    { name: "Setup", value: result.score_setup_quality, max: 20 }
  ];

  return (
    <div className="mb-4 space-y-3">
      {data.map((item) => {
        const percent = Math.round((item.value / item.max) * 100);
        return (
          <div key={item.name}>
            <div className="mb-1 flex justify-between text-xs text-muted">
              <span>{item.name}</span>
              <span>{item.value}/{item.max}</span>
            </div>
            <div className="h-3 rounded bg-panelSoft">
              <div className="h-3 rounded bg-[#5aa7ff]" style={{ width: `${Math.min(percent, 100)}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
