import { BacktestRunner } from "@/components/BacktestRunner";
import { Disclaimer } from "@/components/Disclaimer";

export default function BacktestsPage() {
  return (
    <div className="space-y-6">
      <Disclaimer />
      <div>
        <h1 className="text-2xl font-semibold">Backtesting Lab</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted">
          Test transparent strategy profiles against historical market data across daily, weekly, and monthly timeframes. Results are educational research only and do not predict future performance.
        </p>
      </div>
      <BacktestRunner />
    </div>
  );
}
