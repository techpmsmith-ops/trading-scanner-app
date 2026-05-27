from datetime import date, datetime, timedelta
from pathlib import Path
import sys

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.models import KronosPredictionEvaluation, PriceBar, ScanResult, ScanRun, Ticker
from app.services.kronos.kronos_adapter import dataframe_to_kronos_bars, validate_ohlcv
from app.services.kronos.kronos_schema import KronosForecastResult, KronosSignal
from app.services.kronos.kronos_signal_mapper import direction_from_path, map_forecast_to_signal


def test_ohlcv_validation_accepts_valid_bars(sample_bars):
    bars = dataframe_to_kronos_bars(sample_bars.tail(120))
    ok, warnings = validate_ohlcv(bars, lookback_bars=120)
    assert ok
    assert warnings == []


def test_ohlcv_validation_rejects_missing_history(sample_bars):
    bars = dataframe_to_kronos_bars(sample_bars.tail(10))
    ok, warnings = validate_ohlcv(bars, lookback_bars=120)
    assert not ok
    assert "Insufficient history" in warnings[0]


def test_signal_mapping_bullish_bearish_neutral():
    assert direction_from_path(100, [102]) == "bullish"
    assert direction_from_path(100, [98]) == "bearish"
    assert direction_from_path(100, [100.5]) == "neutral"


def test_unavailable_signal_is_safe():
    forecast = KronosForecastResult(
        symbol="NVDA",
        timeframe="1d",
        forecast_horizon=5,
        predicted_direction="unavailable",
        confidence_score=0,
        model_name="test",
        lookback_bars_used=0,
        error="disabled",
    )
    signal = map_forecast_to_signal(forecast, 100)
    assert signal.kronos_bias == "unavailable"
    assert signal.kronos_confidence == 0


def test_scanner_survives_kronos_failure(monkeypatch, sample_bars):
    import app.services.scanner_engine as scanner_engine

    def failed_signal(symbol, timeframe, bars):
        forecast = KronosForecastResult(
            symbol=symbol,
            timeframe=timeframe,
            forecast_horizon=5,
            predicted_direction="unavailable",
            confidence_score=0,
            model_name="mock",
            lookback_bars_used=0,
            error="model failed",
        )
        return KronosSignal(
            kronos_bias="unavailable",
            kronos_confidence=0,
            kronos_expected_range={},
            kronos_risk_flag="unavailable",
            kronos_summary="model failed",
            forecast=forecast,
        )

    monkeypatch.setattr(scanner_engine, "KRONOS_ENABLED", True)
    monkeypatch.setattr(scanner_engine, "fetch_daily_bars", lambda symbol, lookback_days=300: sample_bars)
    monkeypatch.setattr(scanner_engine, "forecast_signal", failed_signal)
    with TestClient(app) as client:
        response = client.post("/scan/run")

    assert response.status_code == 200
    assert response.json()["result_count"] > 0


def test_kronos_health_route():
    with TestClient(app) as client:
        response = client.get("/api/kronos/health")
    assert response.status_code == 200
    assert "enabled" in response.json()


def test_kronos_forecast_route_with_mock(monkeypatch, sample_bars):
    import app.api.kronos as kronos_api

    forecast = KronosForecastResult(
        symbol="NVDA",
        timeframe="1d",
        forecast_horizon=5,
        predicted_direction="bullish",
        confidence_score=72,
        predicted_close_path=[101, 102, 103, 104, 105],
        predicted_high_low_range={"low": 99, "high": 106},
        model_name="mock",
        lookback_bars_used=120,
    )
    signal = KronosSignal(kronos_bias="bullish", kronos_confidence=72, kronos_expected_range={"low": 99, "high": 106}, kronos_summary="mock", forecast=forecast)
    monkeypatch.setattr(kronos_api, "forecast_signal", lambda symbol, timeframe, bars, forecast_bars: signal)

    with TestClient(app) as client:
        bars = sample_bars.tail(130).copy()
        bars["date"] = bars["date"].astype(str)
        response = client.post(
            "/api/kronos/forecast",
            json={"symbol": "NVDA", "bars": bars.to_dict("records"), "forecast_bars": 5},
        )
    assert response.status_code == 200
    assert response.json()["predicted_direction"] == "bullish"


def test_feedback_evaluation_logic(db_session, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    import scripts.evaluate_kronos_predictions as evaluator

    ticker = Ticker(symbol="NVDA")
    run = ScanRun(run_date=date.today(), status="completed")
    db_session.add_all([ticker, run])
    db_session.commit()
    result = ScanResult(
        scan_run_id=run.id,
        ticker_id=ticker.id,
        symbol="NVDA",
        close_price=100,
        score_total=80,
        score_trend=20,
        score_momentum=10,
        score_volume=10,
        score_risk=10,
        score_setup_quality=10,
        score_kronos=72,
        setup_types=["Momentum Strength"],
        risk_flags=[],
        indicators={},
        explanation="test",
        kronos_enabled=True,
        kronos_model_name="mock",
        kronos_bias="bullish",
        kronos_confidence=72,
        kronos_expected_range_low=99,
        kronos_expected_range_high=110,
        kronos_raw_output_json={"forecast_horizon": 5},
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    db_session.add(result)
    for index, close in enumerate([100, 101, 103, 104, 106, 107]):
        db_session.add(PriceBar(ticker_id=ticker.id, date=date.today() - timedelta(days=5 - index), open=close, high=close + 1, low=close - 1, close=close, adjusted_close=close, volume=1000))
    db_session.commit()
    monkeypatch.setattr(evaluator, "fetch_daily_bars", lambda symbol, lookback_days=40: pd.DataFrame())
    monkeypatch.setattr(evaluator, "upsert_price_bars", lambda db, ticker, bars: 0)

    assert evaluator.ensure_eval_rows(db_session) == 1
    evaluated = evaluator.evaluate_pending(db_session)
    assert len(evaluated) == 1
    assert db_session.query(KronosPredictionEvaluation).one().direction_correct is True
