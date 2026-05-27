from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from app.config import FOCUS_GROUP_SYMBOLS, KRONOS_ENABLED, SETUP_DISCLAIMER
from app.models import DailyRecommendation, FocusGroupAnalysis, FocusStockProfile, PriceBar, ScanResult, ScanRun, ScoringWeight, Ticker, WeeklyEvaluationReport, WeeklyPrediction
from app.services.alerts import send_alerts
from app.services.market_data import fetch_daily_bars, upsert_price_bars
from app.services.news_sentiment import score_symbol_news
from app.services.kronos.service import forecast_signal
from app.services.scoring import DEFAULT_COMPONENT_WEIGHTS


def latest_weights(db: Session) -> dict[str, float]:
    row = db.query(ScoringWeight).order_by(ScoringWeight.created_at.desc()).first()
    return row.weights if row else DEFAULT_COMPONENT_WEIGHTS.copy()


def latest_weight_row(db: Session) -> ScoringWeight | None:
    return db.query(ScoringWeight).order_by(ScoringWeight.created_at.desc()).first()


def latest_evaluation_report(db: Session) -> WeeklyEvaluationReport | None:
    return db.query(WeeklyEvaluationReport).order_by(WeeklyEvaluationReport.created_at.desc()).first()


def latest_focus_group(db: Session) -> list[FocusGroupAnalysis]:
    latest_date = db.query(FocusGroupAnalysis.analysis_date).order_by(FocusGroupAnalysis.analysis_date.desc()).first()
    if not latest_date:
        return []
    return (
        db.query(FocusGroupAnalysis)
        .filter(FocusGroupAnalysis.analysis_date == latest_date[0])
        .order_by(FocusGroupAnalysis.symbol.asc())
        .all()
    )


def focus_profiles(db: Session) -> list[FocusStockProfile]:
    return db.query(FocusStockProfile).order_by(FocusStockProfile.symbol.asc()).all()


def latest_scan(db: Session) -> ScanRun | None:
    return db.query(ScanRun).order_by(ScanRun.started_at.desc()).first()


def generate_daily_top_five(db: Session, force: bool = False) -> list[DailyRecommendation]:
    run = latest_scan(db)
    if not run:
        return []
    existing = (
        db.query(DailyRecommendation)
        .filter(DailyRecommendation.recommendation_date == date.today())
        .order_by(DailyRecommendation.rank.asc())
        .all()
    )
    if existing and not force:
        return existing
    if existing and force:
        for row in existing:
            db.delete(row)
        db.commit()

    pool = (
        db.query(ScanResult)
        .filter(ScanResult.scan_run_id == run.id, ScanResult.score_total >= 70)
        .order_by(ScanResult.score_total.desc())
        .limit(20)
        .all()
    )
    candidates = [result for result in pool if "Risk Warning / Avoid" not in (result.setup_types or [])][:5]
    if not candidates:
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


def generate_focus_group_analysis(db: Session, force: bool = False) -> list[FocusGroupAnalysis]:
    today = date.today()
    existing = (
        db.query(FocusGroupAnalysis)
        .filter(FocusGroupAnalysis.analysis_date == today)
        .order_by(FocusGroupAnalysis.symbol.asc())
        .all()
    )
    if existing and not force:
        return existing
    if existing and force:
        for row in existing:
            db.delete(row)
        db.commit()

    run = latest_scan(db)
    scan_results = {}
    if run:
        scan_results = {result.symbol: result for result in db.query(ScanResult).filter(ScanResult.scan_run_id == run.id).all()}

    rows: list[FocusGroupAnalysis] = []
    for symbol in FOCUS_GROUP_SYMBOLS:
        _ensure_symbol_price_data(db, symbol)
        result = scan_results.get(symbol)
        bars = _recent_bars(db, symbol, limit=260)
        metrics = _focus_price_metrics(bars)
        sentiment = score_symbol_news(symbol)
        relevance = _focus_relevance(symbol)
        kronos = _focus_kronos_signal(symbol, bars)
        bias = _focus_bias(result, metrics, sentiment)
        confidence = _focus_confidence(result, metrics, sentiment)
        support_resistance = _support_resistance(bars)
        risk_level = _risk_level(result, metrics)
        setup = _technical_setup(result, metrics)
        catalyst = _key_catalyst(symbol, sentiment, relevance, metrics)
        row = FocusGroupAnalysis(
            analysis_date=today,
            symbol=symbol,
            scan_run_id=run.id if run else None,
            scan_result_id=result.id if result else None,
            bias=bias,
            confidence=confidence,
            current_technical_setup=setup,
            key_catalyst=catalyst,
            risk_level=risk_level,
            suggested_watch_action=_watch_action(bias, risk_level, confidence),
            entry_zone=_entry_zone(result, support_resistance),
            stop_loss_area=_stop_area(result, support_resistance),
            target_zone=_target_zone(result, support_resistance, metrics),
            daily_move_pct=metrics.get("daily_move_pct"),
            weekly_move_pct=metrics.get("weekly_move_pct"),
            volume_spike=bool(metrics.get("volume_spike")),
            relative_volume=metrics.get("relative_volume"),
            indicators=_focus_indicators(result, metrics),
            support_resistance=support_resistance,
            catalysts={
                "earnings_date": "unavailable from configured free data sources",
                "recent_news": sentiment.get("headline_count", 0),
                "news_sentiment": sentiment["label"],
                "analyst_activity": "unavailable from configured free data sources",
            },
            relevance=relevance,
            news_sentiment_score=sentiment["score"],
            news_sentiment_label=sentiment["label"],
            kronos=kronos,
            summary=_focus_summary(symbol, bias, confidence, setup, catalyst, risk_level, kronos),
        )
        db.add(row)
        rows.append(row)
        _ensure_focus_profile(db, symbol)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def run_morning_phase2_pipeline(db: Session, scan_run: ScanRun | None = None) -> dict:
    focus_rows = generate_focus_group_analysis(db, force=True)
    top_five = generate_daily_top_five(db, force=True)
    message = _morning_alert_message(focus_rows, top_five)
    alert_results = send_alerts(db, "daily_top_five", message) if message else []
    return {
        "scan_run_id": scan_run.id if scan_run else None,
        "focus_count": len(focus_rows),
        "top_five_count": len(top_five),
        "alerts": alert_results,
    }


def focus_explanation_context(db: Session, symbol: str) -> dict:
    normalized = symbol.upper().strip()
    analysis = (
        db.query(FocusGroupAnalysis)
        .filter(FocusGroupAnalysis.symbol == normalized)
        .order_by(FocusGroupAnalysis.analysis_date.desc(), FocusGroupAnalysis.created_at.desc())
        .first()
    )
    predictions = (
        db.query(WeeklyPrediction)
        .filter(WeeklyPrediction.symbol == normalized)
        .order_by(WeeklyPrediction.week_start.desc())
        .limit(12)
        .all()
    )
    profile = db.query(FocusStockProfile).filter(FocusStockProfile.symbol == normalized).one_or_none()
    latest_prediction = predictions[0] if predictions else None
    linked_result = analysis.scan_result if analysis else latest_prediction.scan_result if latest_prediction else None
    latest_result = _latest_scan_result_for_symbol(db, normalized)
    result = latest_result or linked_result
    if analysis and _should_use_scan_kronos(analysis.kronos, result):
        analysis.kronos = _scan_result_kronos_payload(result)
    news_summary = {
        "sentiment_score": analysis.news_sentiment_score if analysis else latest_prediction.news_sentiment_score if latest_prediction else None,
        "sentiment_label": analysis.news_sentiment_label if analysis else latest_prediction.news_sentiment_label if latest_prediction else None,
        "headline_count": (analysis.catalysts or {}).get("recent_news") if analysis else None,
    }
    return {
        "symbol": normalized,
        "latest_analysis": analysis,
        "weekly_predictions": predictions,
        "profile": profile,
        "score_components": _score_breakdown(analysis, result),
        "why_this_rating": _why_this_rating(analysis, result, latest_prediction),
        "recent_news_summary": news_summary,
        "disclaimer": "Educational decision-support only. This is not financial advice or a trade recommendation.",
    }


def explain_focus_analysis(db: Session, symbol: str, question: str | None = None) -> dict:
    context = focus_explanation_context(db, symbol)
    analysis = context["latest_analysis"]
    if not analysis:
        return {
            "symbol": context["symbol"],
            "explanation": f"No Focus Group analysis is stored yet for {context['symbol']}. Generate Focus Group analysis first.",
            "disclaimer": context["disclaimer"],
        }
    why = context["why_this_rating"]
    components = context["score_components"]
    prediction = context["weekly_predictions"][0] if context["weekly_predictions"] else None
    question_note = f" Question focus: {question.strip()}" if question else ""
    explanation = (
        f"{analysis.symbol} is currently rated {analysis.bias} with {analysis.confidence:.0%} confidence and {analysis.risk_level} risk.{question_note} "
        f"The rating is grounded in a scan score of {components.get('scan_score', 'unavailable')}, setup types {', '.join(why.get('setup_types') or ['none'])}, "
        f"risk flags {', '.join(why.get('risk_flags') or ['none'])}, daily move {analysis.daily_move_pct}%, weekly move {analysis.weekly_move_pct}%, "
        f"relative volume {analysis.relative_volume}x, volume spike {analysis.volume_spike}, RSI {why.get('rsi_14')}, MACD histogram {why.get('macd_histogram')}, "
        f"support {why.get('support')}, resistance {why.get('resistance')}, and news sentiment {analysis.news_sentiment_label} ({analysis.news_sentiment_score}). "
        f"The watch action is: {analysis.suggested_watch_action} Entry/stop/target zones are {analysis.entry_zone or '-'}, {analysis.stop_loss_area or '-'}, and {analysis.target_zone or '-'}. "
    )
    if prediction:
        explanation += (
            f"The latest weekly prediction is {prediction.direction} with expected range "
            f"{prediction.predicted_range_low or '-'} to {prediction.predicted_range_high or '-'} and {prediction.confidence:.0%} confidence. "
        )
    explanation += "This is a grounded explanation of stored scanner data only, not a trade recommendation."
    return {"symbol": analysis.symbol, "explanation": explanation, "disclaimer": context["disclaimer"]}


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
    for symbol in FOCUS_GROUP_SYMBOLS:
        result = scan_results.get(symbol)
        bars = _recent_bars(db, symbol, limit=260)
        price_metrics = _focus_price_metrics(bars)
        sentiment = score_symbol_news(symbol)
        score = result.score_total if result else 50
        direction = "bullish" if score >= 65 else "bearish" if score <= 40 else "neutral"
        predicted_return = _predicted_return(score, direction)
        confidence = _confidence(score, result)
        component_scores = _components(result)
        predicted_low, predicted_high = _predicted_range(price_metrics, predicted_return)
        bullish_probability, bearish_probability = _direction_probabilities(score, sentiment)
        key_drivers = _key_drivers(symbol, result, sentiment, price_metrics)
        main_risks = _main_risks(result, price_metrics, sentiment)
        technical_setup = _technical_setup(result, price_metrics)
        sentiment_impact = f"Recent news sentiment is {sentiment['label']} with a bounded score of {sentiment['score']}."
        trade_plan = _suggested_trade_plan(direction, result, predicted_low, predicted_high)
        rationale = _prediction_rationale(symbol, result, score, direction)
        row = WeeklyPrediction(
            week_start=week_start,
            week_end=week_end,
            symbol=symbol,
            scan_run_id=run.id if run else None,
            scan_result_id=result.id if result else None,
            direction=direction,
            predicted_return_pct=predicted_return,
            predicted_range_low=predicted_low,
            predicted_range_high=predicted_high,
            bullish_probability=bullish_probability,
            bearish_probability=bearish_probability,
            confidence=round(confidence, 2),
            score_total=score,
            component_scores=component_scores,
            key_drivers=key_drivers,
            main_risks=main_risks,
            technical_setup=technical_setup,
            sentiment_impact=sentiment_impact,
            suggested_trade_plan=trade_plan,
            rationale=rationale,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def regenerate_current_week_predictions(db: Session) -> list[WeeklyPrediction]:
    week_start, _week_end = current_week_bounds()
    pending = db.query(WeeklyPrediction).filter(WeeklyPrediction.week_start == week_start, WeeklyPrediction.status == "pending").all()
    for row in pending:
        db.delete(row)
    db.commit()
    return generate_weekly_predictions(db)


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
        in_range = (
            prediction.predicted_range_low is not None
            and prediction.predicted_range_high is not None
            and prediction.predicted_range_low <= end_price <= prediction.predicted_range_high
        )
        volume_confirmation = _volume_confirmation(symbol_prices, prediction.direction)
        prediction.start_price = start_price
        prediction.end_price = end_price
        prediction.actual_return_pct = round(actual, 2)
        prediction.outcome = _outcome(prediction.direction, actual)
        prediction.outcome_reason = _outcome_reason(prediction.direction, actual)
        prediction.range_hit = in_range
        prediction.volume_confirmation = volume_confirmation
        prediction.sector_relative_behavior = _sector_relative_behavior(db, prediction.symbol, prediction.week_start, prediction.week_end, actual)
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
        update_focus_profiles(db, evaluated)
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


def update_focus_profiles(db: Session, predictions: list[WeeklyPrediction]) -> None:
    for prediction in predictions:
        profile = _ensure_focus_profile(db, prediction.symbol)
        stats = profile.accuracy_stats or {}
        total = int(stats.get("evaluated_weeks", 0)) + 1
        hits = int(stats.get("direction_hits", 0)) + (1 if prediction.outcome == "hit" else 0)
        range_hits = int(stats.get("range_hits", 0)) + (1 if prediction.range_hit else 0)
        false_positives = int(stats.get("false_positives", 0)) + (1 if prediction.false_positive else 0)
        profile.accuracy_stats = {
            "evaluated_weeks": total,
            "direction_hits": hits,
            "direction_accuracy": round(hits / total, 3),
            "range_hits": range_hits,
            "range_accuracy": round(range_hits / total, 3),
            "false_positives": false_positives,
            "last_outcome": prediction.outcome,
            "last_actual_return_pct": prediction.actual_return_pct,
        }
        behavior = profile.behavior_profile or {}
        behavior["last_volume_confirmation"] = prediction.volume_confirmation
        behavior["last_sector_relative_behavior"] = prediction.sector_relative_behavior
        behavior["confidence_calibration"] = "constructive" if prediction.outcome == "hit" and prediction.confidence >= 0.5 else "needs_review"
        profile.behavior_profile = behavior
        weights = profile.indicator_weights or DEFAULT_COMPONENT_WEIGHTS.copy()
        for component, score in (prediction.component_scores or {}).items():
            if score <= 0:
                continue
            delta = 0.02 if prediction.outcome == "hit" else -0.02
            if prediction.false_positive:
                delta -= 0.02
            weights[component] = round(min(1.25, max(0.75, weights.get(component, 1.0) + delta)), 3)
        profile.indicator_weights = weights
    db.commit()


def _ensure_focus_profile(db: Session, symbol: str) -> FocusStockProfile:
    profile = db.query(FocusStockProfile).filter(FocusStockProfile.symbol == symbol).one_or_none()
    if profile:
        return profile
    profile = FocusStockProfile(
        symbol=symbol,
        behavior_profile={"profile_status": "collecting_history"},
        indicator_weights=DEFAULT_COMPONENT_WEIGHTS.copy(),
        accuracy_stats={"evaluated_weeks": 0, "direction_accuracy": 0, "range_accuracy": 0, "false_positives": 0},
    )
    db.add(profile)
    return profile


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


def _recent_bars(db: Session, symbol: str, limit: int = 260) -> list[PriceBar]:
    return (
        db.query(PriceBar)
        .join(Ticker)
        .filter(Ticker.symbol == symbol)
        .order_by(PriceBar.date.desc())
        .limit(limit)
        .all()
    )[::-1]


def _focus_price_metrics(bars: list[PriceBar]) -> dict:
    if not bars:
        return {}
    latest = bars[-1]
    prior = bars[-2] if len(bars) >= 2 else latest
    week_prior = bars[-6] if len(bars) >= 6 else bars[0]
    avg_volume = sum(bar.volume for bar in bars[-20:]) / min(len(bars), 20)
    relative_volume = latest.volume / avg_volume if avg_volume else 0
    closes = [bar.close for bar in bars]
    return {
        "close": latest.close,
        "daily_move_pct": round(((latest.close - prior.close) / prior.close) * 100, 2) if prior.close else 0,
        "weekly_move_pct": round(((latest.close - week_prior.close) / week_prior.close) * 100, 2) if week_prior.close else 0,
        "relative_volume": round(relative_volume, 2),
        "volume_spike": relative_volume >= 1.5,
        "support": round(min(bar.low for bar in bars[-20:]), 2),
        "resistance": round(max(bar.high for bar in bars[-20:]), 2),
        "avg_close_20": round(sum(closes[-20:]) / min(len(closes), 20), 2),
    }


def _support_resistance(bars: list[PriceBar]) -> dict:
    if not bars:
        return {"support": None, "resistance": None, "method": "insufficient data"}
    lookback = bars[-20:]
    return {
        "support": round(min(bar.low for bar in lookback), 2),
        "resistance": round(max(bar.high for bar in lookback), 2),
        "method": "20-bar high/low",
    }


def _focus_relevance(symbol: str) -> dict:
    mapping = {
        "NVDA": ["AI infrastructure", "semiconductor", "data center"],
        "AMD": ["AI infrastructure", "semiconductor", "data center"],
        "INTC": ["semiconductor", "data center"],
        "IONQ": ["quantum computing"],
        "RGTI": ["quantum computing"],
        "NVTS": ["semiconductor", "data center infrastructure"],
        "SMCI": ["AI infrastructure", "data center"],
        "MU": ["semiconductor", "data center"],
        "RKLB": ["space/defense/advanced technology"],
        "RVI": ["advanced technology watchlist"],
    }
    tags = mapping.get(symbol, ["advanced technology watchlist"])
    return {
        "ai_infrastructure": "AI infrastructure" in tags,
        "quantum_computing": "quantum computing" in tags,
        "semiconductor": "semiconductor" in tags,
        "data_center": any("data center" in tag for tag in tags),
        "space_defense_advanced_technology": any("space" in tag or "advanced" in tag for tag in tags),
        "tags": tags,
    }


def _focus_bias(result: ScanResult | None, metrics: dict, sentiment: dict) -> str:
    score = result.score_total if result else 50
    if score >= 65 and metrics.get("weekly_move_pct", 0) >= 0 and sentiment["score"] >= -0.2:
        return "bullish"
    if score <= 40 or (metrics.get("weekly_move_pct", 0) < -4 and sentiment["score"] < 0):
        return "bearish"
    return "neutral"


def _focus_confidence(result: ScanResult | None, metrics: dict, sentiment: dict) -> float:
    score = result.score_total if result else 50
    confidence = min(0.85, max(0.25, abs(score - 50) / 55))
    if metrics.get("volume_spike"):
        confidence += 0.06
    if sentiment["label"] in {"positive", "negative"}:
        confidence += 0.04
    if result and result.risk_flags:
        confidence -= min(0.18, len(result.risk_flags) * 0.04)
    return round(min(0.9, max(0.2, confidence)), 2)


def _risk_level(result: ScanResult | None, metrics: dict) -> str:
    atr_pct = (result.indicators or {}).get("atr_percent") if result else None
    if result and result.risk_flags:
        return "high"
    if atr_pct and atr_pct > 6:
        return "high"
    if metrics.get("volume_spike") or (atr_pct and atr_pct > 4):
        return "medium"
    return "low"


def _technical_setup(result: ScanResult | None, metrics: dict) -> str:
    if result:
        return ", ".join(result.setup_types) or "No clear Stage 1 setup"
    if metrics.get("weekly_move_pct") is None:
        return "Insufficient fresh price data"
    return "Focus watchlist baseline; waiting for a full scanner result"


def _key_catalyst(symbol: str, sentiment: dict, relevance: dict, metrics: dict) -> str:
    if metrics.get("volume_spike"):
        return f"Volume spike with {metrics.get('relative_volume')}x relative volume."
    if sentiment["label"] != "neutral":
        return f"Recent news sentiment is {sentiment['label']}."
    return f"Theme exposure: {', '.join(relevance['tags'])}."


def _watch_action(bias: str, risk_level: str, confidence: float) -> str:
    if risk_level == "high":
        return "Watch only; require confirmation and smaller risk."
    if bias == "bullish" and confidence >= 0.45:
        return "Watch for confirmation near entry zone."
    if bias == "bearish":
        return "Avoid new long plans until price stabilizes."
    return "Monitor; wait for clearer setup or catalyst confirmation."


def _entry_zone(result: ScanResult | None, levels: dict) -> str | None:
    if result and result.entry_zone:
        return f"Near ${result.entry_zone:.2f}"
    if levels.get("resistance"):
        return f"Above ${levels['resistance']:.2f} confirmation"
    return None


def _stop_area(result: ScanResult | None, levels: dict) -> str | None:
    if result and result.stop_loss:
        return f"Below ${result.stop_loss:.2f}"
    if levels.get("support"):
        return f"Below ${levels['support']:.2f}"
    return None


def _target_zone(result: ScanResult | None, levels: dict, metrics: dict) -> str | None:
    if result and result.target_1 and result.target_2:
        return f"${result.target_1:.2f} to ${result.target_2:.2f}"
    close = metrics.get("close")
    resistance = levels.get("resistance")
    if close and resistance:
        return f"${resistance:.2f} to ${max(resistance, close * 1.08):.2f}"
    return None


def _focus_indicators(result: ScanResult | None, metrics: dict) -> dict:
    indicators = dict(result.indicators or {}) if result else {}
    indicators.update(
        {
            "daily_move_pct": metrics.get("daily_move_pct"),
            "weekly_move_pct": metrics.get("weekly_move_pct"),
            "relative_volume": metrics.get("relative_volume"),
            "volume_spike": metrics.get("volume_spike"),
        }
    )
    return indicators


def _focus_summary(symbol: str, bias: str, confidence: float, setup: str, catalyst: str, risk_level: str, kronos: dict | None = None) -> str:
    summary = (
        f"{symbol} focus view is {bias} with {confidence:.0%} confidence. "
        f"Technical setup: {setup}. Key catalyst: {catalyst} Risk level: {risk_level}. "
    )
    if kronos and kronos.get("kronos_bias") not in {None, "unavailable"}:
        summary += f"Kronos bias is {kronos.get('kronos_bias')} at {kronos.get('kronos_confidence')} confidence. "
    return summary + "This is focus-group research, not a trade recommendation."


def _focus_kronos_signal(symbol: str, bars: list[PriceBar]) -> dict | None:
    if not KRONOS_ENABLED:
        return {"enabled": False, "kronos_bias": "unavailable", "kronos_summary": "Kronos is disabled."}
    data = pd.DataFrame(
        [
            {
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ]
    )
    signal = forecast_signal(symbol, "1d", data)
    return signal.model_dump(mode="json")


def _should_use_scan_kronos(focus_kronos: dict | None, result: ScanResult | None) -> bool:
    if not result or not result.kronos_enabled or not result.kronos_bias or result.kronos_bias == "unavailable":
        return False
    if not focus_kronos:
        return True
    focus_bias = focus_kronos.get("kronos_bias") or focus_kronos.get("predicted_direction")
    focus_error = focus_kronos.get("error") or (focus_kronos.get("forecast") or {}).get("error")
    return focus_bias in {None, "unavailable"} or bool(focus_error)


def _latest_scan_result_for_symbol(db: Session, symbol: str) -> ScanResult | None:
    return (
        db.query(ScanResult)
        .join(ScanRun)
        .filter(ScanResult.symbol == symbol)
        .order_by(ScanRun.run_date.desc(), ScanRun.started_at.desc(), ScanResult.created_at.desc())
        .first()
    )


def _scan_result_kronos_payload(result: ScanResult) -> dict:
    return {
        "source": "scanner_result",
        "kronos_enabled": result.kronos_enabled,
        "kronos_model_name": result.kronos_model_name,
        "kronos_bias": result.kronos_bias,
        "kronos_confidence": result.kronos_confidence,
        "kronos_expected_range": {
            "low": result.kronos_expected_range_low,
            "high": result.kronos_expected_range_high,
        },
        "kronos_volatility_estimate": result.kronos_volatility_estimate,
        "kronos_summary": result.kronos_summary,
        "kronos_error": result.kronos_error,
        "forecast": result.kronos_raw_output_json or {},
    }


def _morning_alert_message(focus_rows: list[FocusGroupAnalysis], top_five: list[DailyRecommendation]) -> str:
    if not focus_rows and not top_five:
        return ""
    focus_lines = [
        f"{row.symbol}: {row.bias} ({row.confidence:.0%}), {row.risk_level} risk, {row.suggested_watch_action}"
        for row in focus_rows[:10]
    ]
    top_lines = [
        f"{row.rank}. {row.symbol} {row.score_total}/100 - {', '.join(row.setup_types) or 'No setup label'}"
        for row in top_five
    ]
    return (
        "Premarket Trading Scanner Briefing\n"
        "Educational decision-support only; not financial advice.\n\n"
        "Focus Group:\n"
        + ("\n".join(focus_lines) if focus_lines else "No Focus Group rows generated.")
        + "\n\nBroader discovery top five:\n"
        + ("\n".join(top_lines) if top_lines else "No broader discovery candidates generated.")
    )


def _score_breakdown(analysis: FocusGroupAnalysis | None, result: ScanResult | None) -> dict:
    indicators = analysis.indicators if analysis else {}
    sentiment_score = analysis.news_sentiment_score if analysis and analysis.news_sentiment_score is not None else 0
    risk_penalty = len(result.risk_flags or []) * 4 if result else 0
    return {
        "scan_score": result.score_total if result else None,
        "trend_component": result.score_trend if result else 0,
        "momentum_component": result.score_momentum if result else 0,
        "volume_component": result.score_volume if result else 0,
        "sentiment_component": round(max(-10, min(10, sentiment_score * 10)), 2),
        "setup_quality_component": result.score_setup_quality if result else 0,
        "risk_component": result.score_risk if result else 0,
        "risk_penalty": risk_penalty,
        "final_confidence_score": round((analysis.confidence if analysis else 0) * 100, 0),
        "rsi_14": indicators.get("rsi_14"),
        "macd_histogram": indicators.get("macd_histogram"),
        "ema_20": indicators.get("ema_20"),
        "sma_50": indicators.get("sma_50"),
        "sma_200": indicators.get("sma_200"),
    }


def _why_this_rating(analysis: FocusGroupAnalysis | None, result: ScanResult | None, prediction: WeeklyPrediction | None) -> dict:
    if not analysis:
        return {"summary": "No Focus Group analysis is stored yet."}
    indicators = analysis.indicators or {}
    levels = analysis.support_resistance or {}
    return {
        "bias": f"{analysis.bias} because score, recent movement, volume, risk flags, and sentiment were combined with bounded rules.",
        "confidence": f"{analysis.confidence:.0%} confidence reflects distance from neutral scan score, volume spike status, sentiment, and risk flags.",
        "risk_level": f"{analysis.risk_level} risk reflects scanner risk flags and volatility/ATR where available.",
        "watch_action": analysis.suggested_watch_action,
        "zones": {
            "entry": analysis.entry_zone,
            "stop": analysis.stop_loss_area,
            "target": analysis.target_zone,
            "support": levels.get("support"),
            "resistance": levels.get("resistance"),
        },
        "scan_score": result.score_total if result else None,
        "setup_types": result.setup_types if result else [],
        "risk_flags": result.risk_flags if result else [],
        "daily_move_pct": analysis.daily_move_pct,
        "weekly_move_pct": analysis.weekly_move_pct,
        "relative_volume": analysis.relative_volume,
        "volume_spike": analysis.volume_spike,
        "rsi_14": indicators.get("rsi_14"),
        "macd_histogram": indicators.get("macd_histogram"),
        "moving_averages": {
            "ema_20": indicators.get("ema_20"),
            "sma_50": indicators.get("sma_50"),
            "sma_200": indicators.get("sma_200"),
        },
        "news_sentiment_score": analysis.news_sentiment_score,
        "news_sentiment_label": analysis.news_sentiment_label,
        "relevance": analysis.relevance,
        "weekly_prediction": {
            "direction": prediction.direction,
            "confidence": prediction.confidence,
            "range_low": prediction.predicted_range_low,
            "range_high": prediction.predicted_range_high,
        } if prediction else None,
    }


def _predicted_range(metrics: dict, predicted_return_pct: float) -> tuple[float | None, float | None]:
    close = metrics.get("close")
    if not close:
        return None, None
    weekly_vol = max(abs(metrics.get("weekly_move_pct", 0)), 3.0)
    midpoint = close * (1 + predicted_return_pct / 100)
    width = close * (weekly_vol / 100)
    return round(midpoint - width, 2), round(midpoint + width, 2)


def _direction_probabilities(score: int, sentiment: dict) -> tuple[float, float]:
    bullish = min(0.8, max(0.2, 0.5 + ((score - 50) / 100) + (sentiment["score"] * 0.12)))
    bearish = min(0.8, max(0.2, 1 - bullish))
    return round(bullish, 2), round(bearish, 2)


def _key_drivers(symbol: str, result: ScanResult | None, sentiment: dict, metrics: dict) -> list[str]:
    drivers = []
    if result and result.setup_types:
        drivers.append(f"Scanner setup: {', '.join(result.setup_types[:2])}")
    if metrics.get("volume_spike"):
        drivers.append(f"Volume confirmation at {metrics.get('relative_volume')}x relative volume")
    if sentiment["label"] != "neutral":
        drivers.append(f"{sentiment['label'].title()} news sentiment")
    drivers.append(f"Theme exposure: {', '.join(_focus_relevance(symbol)['tags'])}")
    return drivers[:4]


def _main_risks(result: ScanResult | None, metrics: dict, sentiment: dict) -> list[str]:
    risks = list(result.risk_flags or []) if result else ["No current scan result"]
    if metrics.get("weekly_move_pct", 0) < -5:
        risks.append("Weak weekly price action")
    if sentiment["score"] < -0.2:
        risks.append("Negative news sentiment")
    return risks[:5] or ["Normal market risk"]


def _suggested_trade_plan(direction: str, result: ScanResult | None, low: float | None, high: float | None) -> str:
    if direction == "neutral":
        return "No directional plan; monitor for clearer confirmation."
    if direction == "bullish":
        return f"Research long setup only after confirmation; expected weekly range {low or '-'} to {high or '-'}."
    return f"Defensive watch; avoid bullish entries unless price reclaims key levels. Expected range {low or '-'} to {high or '-'}."


def _volume_confirmation(prices: list[PriceBar], direction: str) -> str:
    if len(prices) < 2:
        return "unknown"
    avg_volume = sum(price.volume for price in prices) / len(prices)
    latest = prices[-1]
    price_up = latest.close >= prices[0].close
    high_volume = latest.volume >= avg_volume * 1.1
    if direction == "bullish" and price_up and high_volume:
        return "confirmed"
    if direction == "bearish" and not price_up and high_volume:
        return "confirmed"
    if high_volume:
        return "contradicted"
    return "unconfirmed"


def _sector_relative_behavior(db: Session, symbol: str, week_start: date, week_end: date, actual_return_pct: float) -> str:
    benchmark = "QQQ" if symbol in {"NVDA", "AMD", "INTC", "SMCI", "MU", "NVTS"} else "SPY"
    _ensure_symbol_price_data(db, benchmark)
    bars = (
        db.query(PriceBar)
        .join(Ticker)
        .filter(Ticker.symbol == benchmark, PriceBar.date >= week_start, PriceBar.date <= week_end)
        .order_by(PriceBar.date.asc())
        .all()
    )
    if len(bars) < 2:
        return "benchmark unavailable"
    benchmark_return = ((bars[-1].close - bars[0].close) / bars[0].close) * 100
    spread = actual_return_pct - benchmark_return
    if spread > 2:
        return f"outperformed {benchmark}"
    if spread < -2:
        return f"underperformed {benchmark}"
    return f"tracked {benchmark}"


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


def _outcome_reason(direction: str, actual_return_pct: float) -> str:
    rounded = round(actual_return_pct, 2)
    if direction == "neutral":
        if abs(actual_return_pct) < 1:
            return f"Neutral hit because actual weekly move was {rounded}% within the +/-1% neutral band."
        return f"Neutral missed because actual weekly move was {rounded}%, outside the +/-1% neutral band."
    if direction == "bullish":
        if actual_return_pct > 0:
            return f"Bullish hit because actual weekly return was positive at {rounded}%."
        return f"Bullish missed because actual weekly return was negative at {rounded}%."
    if actual_return_pct < 0:
        return f"Bearish hit because actual weekly return was negative at {rounded}%."
    return f"Bearish missed because actual weekly return was positive at {rounded}%."
