from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import PHASE2_PREDICTION_SYMBOLS, SETUP_DISCLAIMER
from app.models import DailyRecommendation, PriceBar, ScanResult, ScanRun, ScoringWeight, Ticker, WeeklyEvaluationReport, WeeklyPrediction
from app.services.market_data import fetch_daily_bars, upsert_price_bars
from app.services.news_sentiment import score_symbol_news
from app.services.scoring import DEFAULT_COMPONENT_WEIGHTS


def latest_weights(db: Session) -> dict[str, float]:
    row = db.query(ScoringWeight).order_by(ScoringWeight.created_at.desc()).first()
    return row.weights if row else DEFAULT_COMPONENT_WEIGHTS.copy()


def latest_weight_row(db: Session) -> ScoringWeight | None:
    return db.query(ScoringWeight).order_by(ScoringWeight.created_at.desc()).first()


def latest_evaluation_report(db: Session) -> WeeklyEvaluationReport | None:
    return db.query(WeeklyEvaluationReport).order_by(WeeklyEvaluationReport.created_at.desc()).first()


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
    return start, start + timedelta(days=4)


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
        confidence = _confidence(score, result)
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
    pending = db.query(WeeklyPrediction).filter(WeeklyPrediction.status == "pending", WeeklyPrediction.week_end <= date.today()).all()
    evaluated: list[WeeklyPrediction] = []
    for prediction in pending:
        _ensure_symbol_price_data(db, prediction.symbol)
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
        sentiment = score_symbol_news(prediction.symbol)
        prediction.start_price = start_price
        prediction.end_price = end_price
        prediction.actual_return_pct = round(actual, 2)
        prediction.outcome = _outcome(prediction.direction, actual)
        prediction.false_positive = prediction.outcome == "miss" and prediction.direction in {"bullish", "bearish"} and prediction.confidence >= 0.5
        prediction.news_sentiment_score = sentiment["score"]
        prediction.news_sentiment_label = sentiment["label"]
        prediction.status = "evaluated"
        prediction.evaluated_at = datetime.utcnow()
        evaluated.append(prediction)
    if evaluated:
        db.commit()
        report = build_weekly_evaluation_report(db, evaluated)
        adjust_scoring_weights(db, evaluated, report)
    return evaluated


def build_weekly_evaluation_report(db: Session, predictions: list[WeeklyPrediction]) -> WeeklyEvaluationReport:
    week_start = min(prediction.week_start for prediction in predictions)
    week_end = max(prediction.week_end for prediction in predictions)
    existing = db.query(WeeklyEvaluationReport).filter(WeeklyEvaluationReport.week_start == week_start, WeeklyEvaluationReport.week_end == week_end).one_or_none()
    if existing:
        return existing

    wins = len([prediction for prediction in predictions if prediction.outcome == "hit"])
    losses = len([prediction for prediction in predictions if prediction.outcome == "miss"])
    false_positives = len([prediction for prediction in predictions if prediction.false_positive])
    report = WeeklyEvaluationReport(
        week_start=week_start,
        week_end=week_end,
        evaluated_count=len(predictions),
        accuracy=round(wins / len(predictions), 3) if predictions else 0,
        wins=wins,
        losses=losses,
        win_loss_ratio=round(wins / losses, 3) if losses else None,
        false_positives=false_positives,
        indicator_effectiveness=_indicator_effectiveness(predictions),
        news_sentiment_correlation=_news_sentiment_correlation(predictions),
        market_conditions=_market_conditions(db, week_start, week_end),
        weight_changes={},
        confidence_notes=_confidence_notes(predictions),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def adjust_scoring_weights(db: Session, predictions: list[WeeklyPrediction], report: WeeklyEvaluationReport | None = None) -> ScoringWeight:
    current = latest_weights(db)
    next_weights = current.copy()
    components = ["trend", "momentum", "volume", "risk", "setup_quality"]
    effectiveness = _indicator_effectiveness(predictions)
    changes: dict[str, dict] = {}
    for component in components:
        stats = effectiveness.get(component, {})
        delta = 0.0
        if stats.get("sample_size", 0) >= 1:
            hit_rate = stats.get("hit_rate", 0)
            if hit_rate >= 0.6:
                delta += 0.03
            elif hit_rate <= 0.4:
                delta -= 0.03
            if stats.get("false_positive_count", 0) > 0:
                delta -= 0.02
        next_weights[component] = round(min(1.2, max(0.8, next_weights.get(component, 1.0) + delta)), 3)
        changes[component] = {"before": current.get(component, 1.0), "after": next_weights[component], "delta": round(delta, 3), **stats}
    row = ScoringWeight(
        effective_date=date.today(),
        weights=next_weights,
        reason="Adjusted after weekly prediction feedback using hit rate, false positives, and bounded component changes.",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if report:
        report.weight_changes = changes
        db.commit()
    return row


def _ensure_symbol_price_data(db: Session, symbol: str) -> None:
    ticker = db.query(Ticker).filter(Ticker.symbol == symbol).one_or_none()
    if not ticker:
        ticker = Ticker(symbol=symbol, active=True)
        db.add(ticker)
        db.commit()
        db.refresh(ticker)
    latest_bar = db.query(PriceBar).filter(PriceBar.ticker_id == ticker.id).order_by(PriceBar.date.desc()).first()
    if latest_bar and latest_bar.date >= date.today() - timedelta(days=4):
        return
    try:
        bars = fetch_daily_bars(symbol, lookback_days=60)
        upsert_price_bars(db, ticker, bars)
    except Exception:
        return


def _indicator_effectiveness(predictions: list[WeeklyPrediction]) -> dict:
    components = ["trend", "momentum", "volume", "risk", "setup_quality"]
    output = {}
    for component in components:
        present = [p for p in predictions if p.component_scores.get(component, 0) > 0]
        hits = [p for p in present if p.outcome == "hit"]
        false_positives = [p for p in present if p.false_positive]
        hit_returns = [p.actual_return_pct or 0 for p in hits]
        miss_returns = [p.actual_return_pct or 0 for p in present if p.outcome == "miss"]
        output[component] = {
            "sample_size": len(present),
            "hit_count": len(hits),
            "miss_count": len(present) - len(hits),
            "hit_rate": round(len(hits) / len(present), 3) if present else 0,
            "false_positive_count": len(false_positives),
            "avg_hit_return_pct": round(sum(hit_returns) / len(hit_returns), 3) if hit_returns else 0,
            "avg_miss_return_pct": round(sum(miss_returns) / len(miss_returns), 3) if miss_returns else 0,
        }
    return output


def _news_sentiment_correlation(predictions: list[WeeklyPrediction]) -> dict:
    with_sentiment = [p for p in predictions if p.news_sentiment_score is not None]
    aligned = []
    for prediction in with_sentiment:
        sentiment = prediction.news_sentiment_score or 0
        if prediction.direction == "bullish" and sentiment > 0 and prediction.outcome == "hit":
            aligned.append(prediction)
        elif prediction.direction == "bearish" and sentiment < 0 and prediction.outcome == "hit":
            aligned.append(prediction)
        elif prediction.direction == "neutral" and abs(sentiment) < 0.15 and prediction.outcome == "hit":
            aligned.append(prediction)
    return {
        "sample_size": len(with_sentiment),
        "aligned_count": len(aligned),
        "alignment_rate": round(len(aligned) / len(with_sentiment), 3) if with_sentiment else 0,
        "average_sentiment_score": round(sum((p.news_sentiment_score or 0) for p in with_sentiment) / len(with_sentiment), 3) if with_sentiment else 0,
        "by_symbol": {p.symbol: {"score": p.news_sentiment_score, "label": p.news_sentiment_label, "outcome": p.outcome} for p in with_sentiment},
    }


def _market_conditions(db: Session, week_start: date, week_end: date) -> dict:
    conditions = {}
    for symbol in ["SPY", "QQQ"]:
        _ensure_symbol_price_data(db, symbol)
        bars = (
            db.query(PriceBar)
            .join(Ticker)
            .filter(Ticker.symbol == symbol, PriceBar.date >= week_start, PriceBar.date <= week_end)
            .order_by(PriceBar.date.asc())
            .all()
        )
        if len(bars) >= 2:
            conditions[symbol] = {
                "start": bars[0].close,
                "end": bars[-1].close,
                "return_pct": round(((bars[-1].close - bars[0].close) / bars[0].close) * 100, 2),
            }
    returns = [item["return_pct"] for item in conditions.values()]
    avg_return = sum(returns) / len(returns) if returns else 0
    conditions["regime"] = "risk-on" if avg_return > 1 else "risk-off" if avg_return < -1 else "mixed"
    return conditions


def _confidence_notes(predictions: list[WeeklyPrediction]) -> str:
    high_conf = [p for p in predictions if p.confidence >= 0.6]
    false_positive_high_conf = [p for p in high_conf if p.false_positive]
    if high_conf and len(false_positive_high_conf) / len(high_conf) > 0.4:
        return "High-confidence signals produced too many false positives; future confidence should be discounted until hit rate improves."
    if high_conf and all(p.outcome == "hit" for p in high_conf):
        return "High-confidence signals aligned well with actual weekly movement; confidence calibration can remain constructive."
    return "Confidence calibration is mixed; keep confidence bounded and review signal quality before acting."


def _predicted_return(score: int, direction: str) -> float:
    if direction == "neutral":
        return 0.0
    magnitude = round(min(6.0, max(1.0, abs(score - 50) / 8)), 2)
    return magnitude if direction == "bullish" else -magnitude


def _confidence(score: int, result: ScanResult | None) -> float:
    base = min(0.8, max(0.3, abs(score - 50) / 55))
    if result and result.risk_flags:
        base -= min(0.2, len(result.risk_flags) * 0.04)
    if result and any(setup in result.setup_types for setup in ["Breakout Candidate", "Momentum Strength", "Trend Continuation Pullback"]):
        base += 0.08
    return round(min(0.85, max(0.25, base)), 2)


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
