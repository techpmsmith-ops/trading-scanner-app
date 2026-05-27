from app.config import (
    KRONOS_BEARISH_THRESHOLD_PCT,
    KRONOS_BULLISH_THRESHOLD_PCT,
    KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT,
)
from app.services.kronos.kronos_schema import KronosDirection, KronosForecastResult, KronosSignal


def direction_from_path(latest_close: float, predicted_close_path: list[float]) -> KronosDirection:
    if not latest_close or not predicted_close_path:
        return "unavailable"
    move_pct = ((predicted_close_path[-1] - latest_close) / latest_close) * 100
    if move_pct >= KRONOS_BULLISH_THRESHOLD_PCT:
        return "bullish"
    if move_pct <= KRONOS_BEARISH_THRESHOLD_PCT:
        return "bearish"
    return "neutral"


def confidence_from_move(latest_close: float, predicted_close_path: list[float], volatility_pct: float | None) -> float:
    if not latest_close or not predicted_close_path:
        return 0.0
    move_pct = abs(((predicted_close_path[-1] - latest_close) / latest_close) * 100)
    threshold = max(abs(KRONOS_BULLISH_THRESHOLD_PCT), abs(KRONOS_BEARISH_THRESHOLD_PCT), 0.01)
    confidence = min(85.0, 35.0 + (move_pct / threshold) * 20.0)
    if volatility_pct and volatility_pct > KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT:
        confidence -= min(20.0, (volatility_pct - KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT) * 2.0)
    return round(max(0.0, min(100.0, confidence)), 2)


def map_forecast_to_signal(forecast: KronosForecastResult, latest_close: float) -> KronosSignal:
    if forecast.error or forecast.predicted_direction == "unavailable":
        summary = forecast.error or "Kronos forecast is unavailable."
        return KronosSignal(
            kronos_bias="unavailable",
            kronos_confidence=0,
            kronos_expected_range=forecast.predicted_high_low_range,
            kronos_risk_flag="unavailable",
            kronos_summary=summary,
            forecast=forecast,
        )
    risk_flag = None
    if forecast.volatility_estimate and forecast.volatility_estimate > KRONOS_HIGH_VOLATILITY_THRESHOLD_PCT:
        risk_flag = "high_forecast_volatility"
    end_close = forecast.predicted_close_path[-1] if forecast.predicted_close_path else latest_close
    move_pct = ((end_close - latest_close) / latest_close) * 100 if latest_close else 0
    summary = (
        f"Kronos {forecast.model_name} projects a {forecast.predicted_direction} "
        f"{forecast.forecast_horizon}-bar path ({move_pct:.2f}% from latest close)."
    )
    return KronosSignal(
        kronos_bias=forecast.predicted_direction,
        kronos_confidence=forecast.confidence_score,
        kronos_expected_range=forecast.predicted_high_low_range,
        kronos_risk_flag=risk_flag,
        kronos_summary=summary,
        forecast=forecast,
    )
