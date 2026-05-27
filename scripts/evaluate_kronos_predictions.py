from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal
from app.models import KronosPredictionEvaluation, PriceBar, ScanResult, Ticker
from app.services.kronos.kronos_adapter import STANDARD_HORIZONS
from app.services.market_data import fetch_daily_bars, upsert_price_bars


def ensure_eval_rows(db) -> int:
    existing = {
        (row.scan_result_id, row.horizon_key)
        for row in db.query(KronosPredictionEvaluation.scan_result_id, KronosPredictionEvaluation.horizon_key).filter(KronosPredictionEvaluation.scan_result_id.isnot(None)).all()
    }
    created = 0
    rows = (
        db.query(ScanResult)
        .filter(ScanResult.kronos_enabled.is_(True), ScanResult.kronos_raw_output_json.isnot(None))
        .all()
    )
    for result in rows:
        raw = result.kronos_raw_output_json or {}
        horizons = raw.get("standardized_horizons") or {}
        if not horizons and result.kronos_bias and result.kronos_bias != "unavailable":
            horizons = {
                "one_week": {
                    "direction": result.kronos_bias,
                    "confidence": float(result.kronos_confidence or 0),
                    "expected_range_values": {"low": result.kronos_expected_range_low, "high": result.kronos_expected_range_high},
                    "bars": int(raw.get("forecast_horizon") or 5),
                }
            }
        for horizon_key, meta in STANDARD_HORIZONS.items():
            if (result.id, horizon_key) in existing:
                continue
            horizon = horizons.get(horizon_key) or {}
            if (horizon.get("direction") or horizon.get("bias")) in {None, "unavailable"}:
                continue
            expected_range = horizon.get("expected_range_values") or {}
            db.add(
                KronosPredictionEvaluation(
                    scan_result_id=result.id,
                    horizon_key=horizon_key,
                    predicted_direction=horizon.get("direction") or result.kronos_bias or "unavailable",
                    predicted_range_low=expected_range.get("low"),
                    predicted_range_high=expected_range.get("high"),
                    confidence_score=float(horizon.get("confidence") or 0),
                    model_name=result.kronos_model_name or raw.get("model_name") or "unknown",
                    symbol=result.symbol,
                    timeframe="1d",
                    forecast_horizon=int(horizon.get("bars") or meta["bars"]),
                    prediction_created_at=result.created_at,
                )
            )
            created += 1
    if created:
        db.commit()
    return created


def evaluate_pending(db) -> list[KronosPredictionEvaluation]:
    pending = db.query(KronosPredictionEvaluation).filter(KronosPredictionEvaluation.evaluation_completed_at.is_(None)).all()
    evaluated = []
    for row in pending:
        ticker = db.query(Ticker).filter(Ticker.symbol == row.symbol).one_or_none()
        if ticker:
            try:
                bars = fetch_daily_bars(row.symbol, lookback_days=max(row.forecast_horizon + 20, 40))
                upsert_price_bars(db, ticker, bars)
            except Exception:
                pass
        prices = (
            db.query(PriceBar)
            .join(Ticker)
            .filter(Ticker.symbol == row.symbol, PriceBar.date >= row.prediction_created_at.date())
            .order_by(PriceBar.date.asc())
            .limit(row.forecast_horizon + 1)
            .all()
        )
        if len(prices) <= row.forecast_horizon:
            continue
        start_close = prices[0].close
        actual_close = prices[row.forecast_horizon].close
        actual_direction = "bullish" if actual_close > start_close else "bearish" if actual_close < start_close else "neutral"
        row.actual_close_after_horizon = actual_close
        row.actual_direction = actual_direction
        row.direction_correct = row.predicted_direction == actual_direction or (row.predicted_direction == "neutral" and abs(actual_close - start_close) / start_close < 0.01)
        row.range_hit = (
            row.predicted_range_low is not None
            and row.predicted_range_high is not None
            and row.predicted_range_low <= actual_close <= row.predicted_range_high
        )
        row.evaluation_completed_at = datetime.utcnow()
        evaluated.append(row)
    if evaluated:
        db.commit()
    return evaluated


def print_summary(rows: list[KronosPredictionEvaluation]) -> None:
    if not rows:
        print("No completed Kronos predictions were ready for evaluation.")
        return
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row.symbol, row.model_name, row.horizon_key)].append(row)
    for (symbol, model, horizon_key), values in sorted(grouped.items()):
        direction_hits = sum(1 for value in values if value.direction_correct)
        range_hits = sum(1 for value in values if value.range_hit)
        print(
            f"{symbol} | {model} | {horizon_key}: {direction_hits}/{len(values)} direction correct "
            f"({direction_hits / len(values):.0%}), {range_hits}/{len(values)} range hits"
        )


def main() -> int:
    db = SessionLocal()
    try:
        created = ensure_eval_rows(db)
        evaluated = evaluate_pending(db)
        print(f"Prepared {created} new evaluation row(s). Evaluated {len(evaluated)} row(s).")
        print_summary(evaluated)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
