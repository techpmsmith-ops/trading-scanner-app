from datetime import date, timedelta

from app.models import PriceBar, ScanResult, ScanRun, Ticker, WeeklyPrediction
from app.services.phase2 import adjust_scoring_weights, generate_daily_top_five, generate_weekly_predictions


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
    assert {"INTC", "NVDA", "AMD", "IONQ", "NVTS"}.issubset(symbols)
    assert all(row.status == "pending" for row in rows)


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

    row = adjust_scoring_weights(db_session, [prediction])

    assert row.weights["trend"] > 1
    assert 0.8 <= row.weights["trend"] <= 1.2
