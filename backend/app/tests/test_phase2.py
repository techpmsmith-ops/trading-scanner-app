from datetime import date, timedelta

from app.config import FOCUS_GROUP_SYMBOLS
from app.models import FocusGroupAnalysis, PriceBar, ScanResult, ScanRun, Ticker, WeeklyPrediction
from app.services.phase2 import adjust_scoring_weights, build_weekly_evaluation_report, current_week_bounds, focus_explanation_context, generate_daily_top_five, generate_focus_group_analysis, generate_weekly_predictions, regenerate_current_week_predictions


def test_daily_top_five_generates_from_latest_scan(db_session):
    ticker = Ticker(symbol="NVDA")
    run = ScanRun(run_date=date.today(), status="completed", universe_count=1, result_count=1)
    db_session.add_all([ticker, run])
    db_session.commit()
    result = ScanResult(
        scan_run_id=run.id,
        ticker_id=ticker.id,
        symbol="NVDA",
        close_price=100,
        score_total=88,
        score_trend=25,
        score_momentum=20,
        score_volume=15,
        score_risk=15,
        score_setup_quality=13,
        setup_types=["Momentum Strength"],
        risk_flags=[],
        indicators={},
        explanation="Test",
    )
    db_session.add(result)
    db_session.commit()

    rows = generate_daily_top_five(db_session)

    assert len(rows) == 1
    assert rows[0].symbol == "NVDA"
    assert rows[0].rank == 1
    assert "not a trade recommendation" in rows[0].disclaimer


def test_weekly_predictions_create_tracked_symbols(db_session):
    rows = generate_weekly_predictions(db_session)

    symbols = {row.symbol for row in rows}
    assert set(FOCUS_GROUP_SYMBOLS).issubset(symbols)
    assert all(row.status == "pending" for row in rows)
    assert all((row.week_end - row.week_start).days == 4 for row in rows)
    assert all(row.bullish_probability is not None for row in rows)


def test_regenerate_current_week_replaces_pending_predictions(db_session):
    rows = generate_weekly_predictions(db_session)
    assert len(rows) == len(FOCUS_GROUP_SYMBOLS)

    regenerated = regenerate_current_week_predictions(db_session)

    assert len(regenerated) == len(FOCUS_GROUP_SYMBOLS)
    assert {row.symbol for row in regenerated} == set(FOCUS_GROUP_SYMBOLS)
    assert all(row.week_start == current_week_bounds()[0] for row in regenerated)
    assert all((row.week_end - row.week_start).days == 4 for row in regenerated)


def test_feedback_adjusts_weight_bounds(db_session):
    prediction = WeeklyPrediction(
        week_start=date.today() - timedelta(days=14),
        week_end=date.today() - timedelta(days=8),
        symbol="AMD",
        direction="bullish",
        predicted_return_pct=2,
        confidence=0.7,
        score_total=75,
        component_scores={"trend": 20, "momentum": 20, "volume": 0, "risk": 10, "setup_quality": 10},
        rationale="Test",
        status="evaluated",
        actual_return_pct=3,
        outcome="hit",
    )

    report = build_weekly_evaluation_report(db_session, [prediction])
    row = adjust_scoring_weights(db_session, [prediction], report)

    assert row.weights["trend"] > 1
    assert 0.8 <= row.weights["trend"] <= 1.2
    assert report.accuracy == 1
    assert report.indicator_effectiveness["trend"]["hit_rate"] == 1


def test_weekly_report_tracks_false_positive_and_sentiment(db_session):
    prediction = WeeklyPrediction(
        week_start=date.today() - timedelta(days=14),
        week_end=date.today() - timedelta(days=8),
        symbol="NVDA",
        direction="bullish",
        predicted_return_pct=3,
        confidence=0.7,
        score_total=80,
        component_scores={"trend": 20, "momentum": 20, "volume": 15, "risk": 10, "setup_quality": 10},
        rationale="Test",
        status="evaluated",
        actual_return_pct=-2,
        outcome="miss",
        outcome_reason="Bullish missed because actual weekly return was negative at -2%.",
        false_positive=True,
        news_sentiment_score=0.5,
        news_sentiment_label="positive",
    )

    report = build_weekly_evaluation_report(db_session, [prediction])

    assert report.false_positives == 1
    assert report.accuracy == 0
    assert report.news_sentiment_correlation["sample_size"] == 1


def test_focus_group_analysis_generates_deeper_daily_rows(db_session, monkeypatch):
    ticker = Ticker(symbol="NVDA")
    run = ScanRun(run_date=date.today(), status="completed", universe_count=1, result_count=1)
    db_session.add_all([ticker, run])
    db_session.commit()
    for index in range(30):
        db_session.add(
            PriceBar(
                ticker_id=ticker.id,
                date=date.today() - timedelta(days=30 - index),
                open=100 + index,
                high=102 + index,
                low=99 + index,
                close=101 + index,
                adjusted_close=101 + index,
                volume=1_000_000 + index * 10_000,
            )
        )
    result = ScanResult(
        scan_run_id=run.id,
        ticker_id=ticker.id,
        symbol="NVDA",
        close_price=130,
        score_total=82,
        score_trend=26,
        score_momentum=18,
        score_volume=14,
        score_risk=14,
        score_setup_quality=10,
        setup_types=["Momentum Strength"],
        risk_flags=[],
        indicators={"rsi_14": 62, "macd_histogram": 1.2, "relative_volume": 1.3},
        explanation="Test",
    )
    db_session.add(result)
    db_session.commit()
    monkeypatch.setattr("app.services.phase2.FOCUS_GROUP_SYMBOLS", ["NVDA"])

    rows = generate_focus_group_analysis(db_session)

    assert len(rows) == 1
    assert rows[0].symbol == "NVDA"
    assert rows[0].bias in {"bullish", "bearish", "neutral"}
    assert rows[0].support_resistance["method"] == "20-bar high/low"


def test_focus_context_uses_scan_kronos_when_focus_kronos_is_stale(db_session):
    ticker = Ticker(symbol="MU")
    run = ScanRun(run_date=date.today(), status="completed", universe_count=1, result_count=1)
    db_session.add_all([ticker, run])
    db_session.commit()
    result = ScanResult(
        scan_run_id=run.id,
        ticker_id=ticker.id,
        symbol="MU",
        close_price=900,
        score_total=85,
        score_trend=25,
        score_momentum=20,
        score_volume=15,
        score_risk=15,
        score_setup_quality=10,
        setup_types=["Momentum Strength"],
        risk_flags=[],
        indicators={},
        explanation="Test",
        kronos_enabled=True,
        kronos_model_name="NeoQuasar/Kronos-mini",
        kronos_bias="bullish",
        kronos_confidence=77,
        kronos_expected_range_low=880,
        kronos_expected_range_high=940,
        kronos_raw_output_json={"forecast_horizon": 5},
    )
    db_session.add(result)
    db_session.commit()
    db_session.add(
        FocusGroupAnalysis(
            analysis_date=date.today(),
            symbol="MU",
            scan_run_id=None,
            scan_result_id=None,
            bias="neutral",
            confidence=0.25,
            current_technical_setup="Test",
            key_catalyst="Test",
            risk_level="low",
            suggested_watch_action="Watch",
            indicators={},
            support_resistance={},
            catalysts={},
            relevance={},
            kronos={"kronos_bias": "unavailable", "kronos_error": "No module named 'torch'"},
            summary="Test",
        )
    )
    db_session.commit()

    context = focus_explanation_context(db_session, "MU")

    assert context["latest_analysis"].kronos["source"] == "scanner_result"
    assert context["latest_analysis"].kronos["kronos_bias"] == "bullish"
    assert context["latest_analysis"].kronos["kronos_expected_range"]["high"] == 940
