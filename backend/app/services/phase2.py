from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import PHASE2_PREDICTION_SYMBOLS, SETUP_DISCLAIMER
from app.models import DailyRecommendation, PriceBar, ScanResult, ScanRun, ScoringWeight, Ticker, WeeklyPrediction
from app.services.scoring import DEFAULT_COMPONENT_WEIGHTS


def latest_weights(db: Session) -> dict[str, float]:
    row = db.query(ScoringWeight).order_by(ScoringWeight.created_at.desc()).first()
    return row.weights if row else DEFAULT_COMPONENT_WEIGHTS.copy()


def latest_weight_row(db: Session) -> ScoringWeight | None:
    return db.query(ScoringWeight).order_by(ScoringWeight.created_at.desc()).first()


def latest_scan(db: Session) -> ScanRun | None:
    return db.query(ScanRun).order_by(ScanRun.started_at.desc()).first()


def generate_daily_top_five(db: Session) -> list[DailyRecommendation]:
    run = latest_scan(db)
    if not run:
        return []
    existing = (
        db.query(DailyRecommendation)
        .filter(DailyRecommendation.recommendation_date == date.today())
        .order_by(DailyRecommendation.rank.asc())
        .all()
    )
    if existing:
        return existing

    candidates = (
        db.query(ScanResult)
        .filter(ScanResult.scan_run_id == run.id)
        .order_by(ScanResult.score_total.desc())
        .limit(5)
        .all()
    )
    rows: list[DailyRecommendation] = []
    for index, result in enumerate(candidates, start=1):
        rationale = (
            f"{result.symbol} is ranked #{index} from the latest scan with a score of {result.score_total}/100. "
            f"Primary setups: {', '.join(result.setup_types) or 'none'}. "
            f"Risk flags: {', '.join(result.risk_flags) if result.risk_flags else 'none'}."
        )
        row = DailyRecommendation(
            recommendation_date=date.today(),
            scan_run_id=run.id,
            scan_result_id=result.id,
            symbol=result.symbol,
            rank=index,
            score_total=result.score_total,
            setup_types=result.setup_types,
            risk_flags=result.risk_flags,
            rationale=rationale,
            disclaimer=SETUP_DISCLAIMER,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def current_week_bounds(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=6)


def generate_weekly_predictions(db: Session) -> list[WeeklyPrediction]:
    week_start, week_end = current_week_bounds()
    existing = (
        db.query(WeeklyPrediction)
        .filter(WeeklyPrediction.week_start == week_start)
        .order_by(WeeklyPrediction.symbol.asc())
        .all()
    )
    if existing:
        return existing

    run = latest_scan(db)
    scan_results = {}
    if run:
        scan_results = {
            result.symbol: result
            for result in db.query(ScanResult).filter(ScanResult.scan_run_id == run.id).all()
        }
    rows: list[WeeklyPrediction] = []
    for symbol in PHASE2_PREDICTION_SYMBOLS:
        result = scan_results.get(symbol)
        score = result.score_total if result else 50
        direction = "bullish" if score >= 65 else "bearish" if score <= 40 else "neutral"
        predicted_return = _predicted_return(score, direction)
        confidence = min(0.85, max(0.35, abs(score - 50) / 50))
        component_scores = _components(result)
        rationale = _prediction_rationale(symbol, result, score, direction)
        row = WeeklyPrediction(
            week_start=week_start,
            week_end=week_end,
            symbol=symbol,
            scan_run_id=run.id if run else None,
            scan_result_id=result.id if result else None,
            direction=direction,
            predicted_return_pct=predicted_return,
            confidence=round(confidence, 2),
            score_total=score,
            component_scores=component_scores,
            rationale=rationale,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def evaluate_weekly_predictions(db: Session) -> list[WeeklyPrediction]:
    pending = db.query(WeeklyPrediction).filter(WeeklyPrediction.status == "pending", WeeklyPrediction.week_end < date.today()).all()
    evaluated: list[WeeklyPrediction] = []
    for prediction in pending:
        symbol_prices = (
            db.query(PriceBar)
            .join(Ticker)
            .filter(Ticker.symbol == prediction.symbol, PriceBar.date >= prediction.week_start, PriceBar.date <= prediction.week_end)
            .order_by(PriceBar.date.asc())
            .all()
        )
        if len(symbol_prices) < 2:
            continue
        start_price = symbol_prices[0].close
        end_price = symbol_prices[-1].close
        actual = ((end_price - start_price) / start_price) * 100
        prediction.start_price = start_price
        prediction.end_price = end_price
        prediction.actual_return_pct = round(actual, 2)
        prediction.outcome = _outcome(prediction.direction, actual)
        prediction.status = "evaluated"
        prediction.evaluated_at = datetime.utcnow()
        evaluated.append(prediction)
    if evaluated:
        db.commit()
        adjust_scoring_weights(db, evaluated)
    return evaluated


def adjust_scoring_weights(db: Session, predictions: list[WeeklyPrediction]) -> ScoringWeight:
    current = latest_weights(db)
    next_weights = current.copy()
    components = ["trend", "momentum", "volume", "risk", "setup_quality"]
    for component in components:
        successful = [p for p in predictions if p.outcome == "hit" and p.component_scores.get(component, 0) > 0]
        misses = [p for p in predictions if p.outcome == "miss" and p.component_scores.get(component, 0) > 0]
        delta = 0.02 * len(successful) - 0.02 * len(misses)
        next_weights[component] = round(min(1.2, max(0.8, next_weights.get(component, 1.0) + delta)), 3)
    row = ScoringWeight(
        effective_date=date.today(),
        weights=next_weights,
        reason="Adjusted after weekly prediction feedback; bounded to 0.8-1.2 per component.",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _predicted_return(score: int, direction: str) -> float:
    if direction == "neutral":
        return 0.0
    magnitude = round(min(6.0, max(1.0, abs(score - 50) / 8)), 2)
    return magnitude if direction == "bullish" else -magnitude


def _components(result: ScanResult | None) -> dict[str, int]:
    if not result:
        return {"trend": 0, "momentum": 0, "volume": 0, "risk": 0, "setup_quality": 0}
    return {
        "trend": result.score_trend,
        "momentum": result.score_momentum,
        "volume": result.score_volume,
        "risk": result.score_risk,
        "setup_quality": result.score_setup_quality,
    }


def _prediction_rationale(symbol: str, result: ScanResult | None, score: int, direction: str) -> str:
    if not result:
        return f"{symbol} has no latest scan result, so the weekly view is neutral until fresh scan data is available."
    return (
        f"{symbol} weekly view is {direction} based on a latest scanner score of {score}/100. "
        f"Setups: {', '.join(result.setup_types) or 'none'}. Risk flags: {', '.join(result.risk_flags) if result.risk_flags else 'none'}. "
        "This is prediction tracking for review, not a trade recommendation."
    )


def _outcome(direction: str, actual_return_pct: float) -> str:
    if direction == "neutral":
        return "hit" if abs(actual_return_pct) < 1 else "miss"
    if direction == "bullish":
        return "hit" if actual_return_pct > 0 else "miss"
    return "hit" if actual_return_pct < 0 else "miss"
